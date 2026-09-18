// Form submission, validation-error, and failure-path coverage for the jQuery-driven legacy
// modules ahead of the jQuery 3.7.1 -> 4.0.0 upgrade (.plans/plan_dependency-upgrade-roadmap-5.md,
// sub-batch 5A). single.link.permissions.module.spec.js already covers the module's basic import;
// this file exercises its actual DOM/network behavior instead and is not meant to duplicate it.
import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest'
import * as APIModule from '../../static/js/helpers/api.module.js'
import * as DOMHelpers from '../../static/js/helpers/dom.helpers.js'
import * as GeneralHelpers from '../../static/js/helpers/general.helpers.js'

// Perma never hits the network in tests; this stands in for the browser transport. `networkError`
// simulates a transport-level failure (fires onerror, status 0, no response body) as distinct from
// an ordinary HTTP error status (completes normally via onload with a response body) -- jQuery's
// XHR transport treats these as different code paths.
function installFakeXHR({status = 200, responseText = '{}', networkError = false} = {}) {
  const requests = []
  class FakeXHR {
    open(method, url) {
      this.method = method
      this.url = url
      this.headers = {}
      requests.push(this)
    }
    setRequestHeader(name, value) {
      this.headers[name] = value
    }
    getAllResponseHeaders() {
      return ''
    }
    getResponseHeader() {
      return null
    }
    send() {
      if (networkError) {
        this.readyState = 4
        this.status = 0
        this.onerror ? this.onerror() : this.onreadystatechange()
        return
      }
      this.readyState = 4
      this.status = status
      this.responseText = responseText
      this.onload ? this.onload() : this.onreadystatechange()
    }
    abort() {}
  }
  globalThis.XMLHttpRequest = FakeXHR
  return requests
}

describe('helpers/api.module.js', () => {
  let OriginalXHR

  beforeEach(() => {
    OriginalXHR = globalThis.XMLHttpRequest
    window.api_path = '/api/v1'
  })

  afterEach(() => {
    globalThis.XMLHttpRequest = OriginalXHR
    document.body.innerHTML = ''
    delete window.api_path
  })

  it('request() sends the CSRF header from ajaxSetup on a non-safe method', async () => {
    document.cookie = 'csrftoken=test-token-123'
    const requests = installFakeXHR({status: 200, responseText: '{}'})
    await new Promise((resolve) => {
      APIModule.request('PATCH', '/archives/ABCD-1234/', {is_private: true}, {success: resolve})
    })
    expect(requests[0].headers['X-CSRFToken']).toBe('test-token-123')
  })

  it('request() omits the CSRF header on a safe method (GET)', async () => {
    document.cookie = 'csrftoken=test-token-123'
    const requests = installFakeXHR({status: 200, responseText: '{}'})
    await new Promise((resolve) => {
      APIModule.request('GET', '/archives/ABCD-1234/', null, {success: resolve})
    })
    expect(requests[0].headers['X-CSRFToken']).toBeUndefined()
  })

  it('request() falls back to showError on failure when no error callback is supplied', async () => {
    installFakeXHR({status: 400, responseText: JSON.stringify({url: 'Bad request message'})})
    // jqXHR is itself thenable; resolving a native Promise with it directly makes the Promise
    // machinery adopt jqXHR's rejected state instead of fulfilling with it as a value, so discard
    // the callback args here and just wait for the request to settle.
    await new Promise((resolve) => {
      APIModule.request('PATCH', '/archives/ABCD-1234/', {is_private: true}).always(() => resolve())
    })
    const alert = document.querySelector('.popup-alert')
    expect(alert).not.toBeNull()
    expect(alert.textContent).toContain('Bad request message')
  })

  it('getErrorMessage extracts the first string from a 400 JSON error body', () => {
    const jqXHR = {status: 400, responseText: JSON.stringify({field: ['Bad request message']})}
    expect(APIModule.getErrorMessage(jqXHR)).toBe('Bad request message')
  })

  it('getErrorMessage falls back to a generic message when 400 responseText is not valid JSON', () => {
    const jqXHR = {status: 400, responseText: 'not json'}
    expect(APIModule.getErrorMessage(jqXHR)).toBe("We're sorry, we've encountered an error processing your request.")
  })

  it('getErrorMessage returns a login prompt on 401', () => {
    const jqXHR = {status: 401, responseText: ''}
    expect(APIModule.getErrorMessage(jqXHR)).toContain('logged out')
  })

  it('getErrorMessage returns a bare "Error <status>" for other statuses', () => {
    const jqXHR = {status: 503, responseText: ''}
    expect(APIModule.getErrorMessage(jqXHR)).toBe('Error 503')
  })

  it('getErrorMessage falls back to a generic message when there is no status (network failure)', () => {
    const jqXHR = {status: 0, responseText: ''}
    expect(APIModule.getErrorMessage(jqXHR)).toBe("We're sorry, we've encountered an error processing your request.")
  })

  it('stringFromNestedObject finds the first string value at any nesting depth', () => {
    expect(APIModule.stringFromNestedObject({url: 'message'})).toBe('message')
    expect(APIModule.stringFromNestedObject({errors: ['nested message']})).toBe('nested message')
    expect(APIModule.stringFromNestedObject({a: {b: {c: 'deep message'}}})).toBe('deep message')
    expect(APIModule.stringFromNestedObject({})).toBeNull()
    expect(APIModule.stringFromNestedObject(null)).toBeNull()
  })

  it('showError renders the message as a dismissible alert', () => {
    APIModule.showError({status: 500, responseText: ''})
    const alert = document.querySelector('.popup-alert')
    expect(alert).not.toBeNull()
    expect(alert.textContent).toContain('Error 500')
    expect(alert.className).toContain('alert-danger')
  })

  it('showError attempts to dismiss a prior alert by clicking its close button, but that click is a no-op here', () => {
    // informUser()/showError() click any existing '.popup-alert button.close' before appending a
    // new alert, relying on Bootstrap's alert plugin to remove it on that click. These helper
    // modules never load Bootstrap's JS themselves, so in isolation the click does nothing and
    // repeated calls accumulate alerts rather than replacing them.
    APIModule.showError({status: 500, responseText: ''})
    APIModule.showError({status: 401, responseText: ''})
    expect(document.querySelectorAll('.popup-alert')).toHaveLength(2)
  })
})

describe('helpers/general.helpers.js', () => {
  let OriginalXHR

  beforeEach(() => {
    OriginalXHR = globalThis.XMLHttpRequest
    window.api_path = '/api/v1'
  })

  afterEach(() => {
    globalThis.XMLHttpRequest = OriginalXHR
    document.body.innerHTML = ''
    delete window.api_path
  })

  it('sendFormData builds a FormData body and PATCHes to api_path + url', async () => {
    const requests = installFakeXHR({status: 200, responseText: '{}'})
    // real callers (submitFile(), below) always pass contentType/processData: false so jQuery
    // ships the FormData body as-is instead of trying to serialize it as plain params.
    await new Promise((resolve) => {
      GeneralHelpers.sendFormData('PATCH', '/archives/ABCD-1234/', {is_private: true}, {
        contentType: false, processData: false, success: resolve,
      })
    })
    expect(requests[0].method).toBe('PATCH')
    expect(requests[0].url).toBe('/api/v1/archives/ABCD-1234/')
  })

  it('sendFormData has no default failure handling, unlike api.module.js request()', async () => {
    // SUSPECT PRE-EXISTING DEFECT: api.module.js's request() defaults `error` to showError when
    // the caller doesn't supply one; sendFormData has no equivalent, so a caller (submitFile(),
    // below) that doesn't attach its own .fail()/.error handler gets total silence on failure.
    installFakeXHR({status: 500, responseText: JSON.stringify({error: 'boom'})})
    let settled = false
    GeneralHelpers.sendFormData('PATCH', '/archives/ABCD-1234/', {is_private: true}, {
      contentType: false, processData: false,
    }).always(() => {
      settled = true
    })
    await new Promise((resolve) => setTimeout(resolve, 0))
    expect(settled).toBe(true)
    expect(document.querySelectorAll('.popup-alert')).toHaveLength(0)
  })

  it('informUser renders a dismissible alert carrying the given class and message', () => {
    GeneralHelpers.informUser('first message', 'success')
    const alert = document.querySelector('.popup-alert')
    expect(alert.className).toContain('alert-success')
    expect(alert.textContent).toContain('first message')
  })

  it('informUser attempts to dismiss a prior alert by clicking its close button, but that click is a no-op here', () => {
    // See the equivalent note on showError above: without Bootstrap's JS loaded, the close-button
    // click this fires does not actually remove the previous alert.
    GeneralHelpers.informUser('first message', 'success')
    GeneralHelpers.informUser('second message', 'danger')
    expect(document.querySelectorAll('.popup-alert')).toHaveLength(2)
  })

  it('informUser defaults to alert-info when no class is given', () => {
    GeneralHelpers.informUser('a message')
    expect(document.querySelector('.popup-alert').className).toContain('alert-info')
  })

  it('csrfSafeMethod treats GET/HEAD/OPTIONS/TRACE as safe and others as unsafe', () => {
    expect(GeneralHelpers.csrfSafeMethod('GET')).toBe(true)
    expect(GeneralHelpers.csrfSafeMethod('HEAD')).toBe(true)
    expect(GeneralHelpers.csrfSafeMethod('PATCH')).toBe(false)
    expect(GeneralHelpers.csrfSafeMethod('DELETE')).toBe(false)
  })

  it('setCookie/getCookie round-trip a value', () => {
    GeneralHelpers.setCookie('test_cookie', 'hello world', 1)
    expect(GeneralHelpers.getCookie('test_cookie')).toBe('hello world')
  })

  it('getCookie returns undefined for a cookie that is not set', () => {
    expect(GeneralHelpers.getCookie('does_not_exist')).toBeUndefined()
  })
})

describe('helpers/dom.helpers.js', () => {
  beforeEach(() => {
    document.body.innerHTML = `<button id="btn">Click</button><div id="target">text</div>`
  })

  it('toggleBtnDisable sets the disabled property from a boolean', () => {
    DOMHelpers.toggleBtnDisable('#btn', true)
    expect(document.getElementById('btn').disabled).toBe(true)
    DOMHelpers.toggleBtnDisable('#btn', false)
    expect(document.getElementById('btn').disabled).toBe(false)
  })

  it('changeText/changeHTML/emptyElement operate on the matched element', () => {
    DOMHelpers.changeText('#target', '<b>x</b>')
    expect(document.getElementById('target').textContent).toBe('<b>x</b>')

    DOMHelpers.changeHTML('#target', '<span class="y"></span>')
    expect(document.getElementById('target').querySelector('.y')).not.toBeNull()

    DOMHelpers.emptyElement('#target')
    expect(document.getElementById('target').children.length).toBe(0)
  })

  it('removeElement removes the element from the document', () => {
    DOMHelpers.removeElement('#target')
    expect(document.getElementById('target')).toBeNull()
  })
})

describe('static/js/single-link-permissions.module.js', () => {
  const FIXTURE = `
    <button id="details-button" class="btn" type="button">Show record details</button>
    <div class="view-mode">Preview</div>
    <div id="collapse-details" class="details-segment">
      <label>Notes <span class="notes-save-status"></span>
        <input type="text" name="notes" value=""/>
      </label>
      <form id="archive_upload_form">
        <input id="file" class="file" name="file" type="file"/>
        <button id="updatePermalink" type="submit">Upload</button>
        <button id="cancelUpdatePermalink" type="reset">Cancel</button>
      </form>
    </div>
    <a class="edit-link" style="cursor:pointer;">Edit link details</a>
    <button class="btn btn-dashboard darchive">Mark as Private</button>
    <select name="private_reason"><option value="user" selected>User</option></select>
  `

  async function mount(html = FIXTURE, globals = {}) {
    document.body.innerHTML = html
    window.archive = {guid: 'ABCD-1234'}
    window.api_path = '/api/v1'
    Object.assign(window, globals)
    vi.resetModules()
    return import('../../static/js/single-link-permissions.module.js')
  }

  let OriginalXHR

  beforeEach(() => {
    OriginalXHR = globalThis.XMLHttpRequest
  })

  afterEach(() => {
    globalThis.XMLHttpRequest = OriginalXHR
    delete window.archive
    delete window.api_path
    document.body.innerHTML = ''
  })

  it('strips a leftover ?safari=1 query param from the URL on load', async () => {
    window.history.pushState({}, '', '/archives/ABCD-1234?safari=1')
    await mount()
    expect(window.location.href).not.toContain('safari=1')
    window.history.pushState({}, '', '/')
  })

  it('starts with the upload form buttons disabled', async () => {
    await mount()
    expect(document.getElementById('updatePermalink').disabled).toBe(true)
    expect(document.getElementById('cancelUpdatePermalink').disabled).toBe(true)
  })

  it('clicking .edit-link proxies a click to the details button, toggling the details tray', async () => {
    await mount()
    expect(document.getElementById('collapse-details').style.display).not.toBe('block')

    $('.edit-link').trigger('click')

    expect(document.getElementById('collapse-details').style.display).toBe('block')
    expect(document.querySelector('.view-mode').style.display).toBe('none')
    expect(document.getElementById('details-button').textContent).toBe('Hide record details')
  })

  it('.edit-link responds to a native click the same as a mouse click (keyboard-equivalent activation)', async () => {
    // jsdom does not synthesize a click from an Enter/Space keydown on a focused element the way a
    // real browser does; calling the native .click() DOM method exercises the same 'click' event
    // the browser's keyboard-activation steps would ultimately dispatch.
    await mount()
    document.querySelector('.edit-link').click()
    expect(document.getElementById('collapse-details').style.display).toBe('block')
  })

  it('darchive click on success: sends the expected payload and does not throw', async () => {
    const requests = installFakeXHR({status: 200, responseText: '{}'})
    await mount()

    document.querySelector('button.darchive').click()
    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(requests[0].method).toBe('PATCH')
    expect(requests[0].url).toBe('/api/v1/archives/ABCD-1234/')
    expect(document.querySelector('button.darchive').textContent).toBe('Updating ...')
  })

  it('darchive click on failure: restores the button, but shows no error to the user', async () => {
    // SUSPECT PRE-EXISTING DEFECT: handleDarchiving() supplies its own `error` callback that only
    // resets the button; unlike link-delete-confirm.js it never calls APIModule.showError(), so a
    // failed darchive toggle gives the user no visible feedback about what happened.
    installFakeXHR({status: 500, responseText: JSON.stringify({error: 'boom'})})
    await mount()

    const btn = document.querySelector('button.darchive')
    const originalText = btn.textContent
    btn.click()
    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(btn.classList.contains('disabled')).toBe(false)
    expect(btn.textContent).toBe(originalText)
    expect(document.querySelectorAll('.popup-alert')).toHaveLength(0)
  })

  it('darchive click is a no-op while already mid-request (disabled)', async () => {
    const requests = installFakeXHR({status: 200, responseText: '{}'})
    await mount()

    const btn = document.querySelector('button.darchive')
    btn.click()
    btn.click() // second click while the first request is still "in flight" and button is .disabled
    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(requests).toHaveLength(1)
  })

  it('input:file change enables the upload buttons when a file is chosen, disables when cleared', async () => {
    await mount()
    const fileInput = document.querySelector('#archive_upload_form .file')

    // jsdom rejects assignment of a non-empty value to a file input's `.value` (a real browser
    // restriction it enforces too); shadow it with an own property to simulate a chosen file.
    Object.defineProperty(fileInput, 'value', {value: 'C:\\fakepath\\photo.png', configurable: true, writable: true})
    $(fileInput).trigger('change')
    expect(document.getElementById('updatePermalink').disabled).toBe(false)
    expect(document.getElementById('cancelUpdatePermalink').disabled).toBe(false)

    Object.defineProperty(fileInput, 'value', {value: '', configurable: true, writable: true})
    $(fileInput).trigger('change')
    expect(document.getElementById('updatePermalink').disabled).toBe(true)
    expect(document.getElementById('cancelUpdatePermalink').disabled).toBe(true)
  })

  it('button:reset click always disables the upload buttons', async () => {
    await mount()
    document.getElementById('updatePermalink').disabled = false
    document.getElementById('cancelUpdatePermalink').disabled = false

    document.querySelector('button[type=reset]').click()

    expect(document.getElementById('updatePermalink').disabled).toBe(true)
    expect(document.getElementById('cancelUpdatePermalink').disabled).toBe(true)
  })

  it('submitting the upload form prevents the native submit and sends a PATCH on success', async () => {
    const requests = installFakeXHR({status: 200, responseText: '{}'})
    await mount()

    $('#archive_upload_form').trigger('submit')
    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(requests[0].method).toBe('PATCH')
    expect(requests[0].url).toBe('/api/v1/archives/ABCD-1234/')
  })

  it('a failed upload leaves the form silently, permanently disabled', async () => {
    // SUSPECT PRE-EXISTING DEFECT: submitFile() chains only .done() on sendFormData()'s jqXHR, with
    // no .fail()/.error handler at all (and sendFormData itself has no default one -- see
    // general.helpers.js above). A failed upload never re-enables the buttons and never surfaces
    // any message, unlike link-delete-confirm.js's error path.
    installFakeXHR({status: 500, responseText: JSON.stringify({error: 'boom'})})
    await mount()

    $('#archive_upload_form').trigger('submit')
    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(document.getElementById('updatePermalink').disabled).toBe(true)
    expect(document.getElementById('cancelUpdatePermalink').disabled).toBe(true)
    expect(document.querySelectorAll('.popup-alert, #upload-error')).toHaveLength(0)
  })

  it('shows an in-page message instead of submitting when the browser lacks FormData support', async () => {
    await mount(FIXTURE + '<div id="upload-error"></div>')
    const OriginalFormData = window.FormData
    delete window.FormData

    $('#archive_upload_form').trigger('submit')

    expect(document.getElementById('upload-error').textContent).toContain('more modern browser')
    window.FormData = OriginalFormData
  })

  it('typing in a details-tray input debounce-saves it and reports the outcome', async () => {
    const requests = installFakeXHR({status: 200, responseText: '{}'})
    await mount()

    const notesInput = document.querySelector('input[name="notes"]')
    $(notesInput).val('updated notes').trigger('input')

    expect(document.querySelector('.notes-save-status').innerHTML).toBe('Saving...')
    expect(requests).toHaveLength(0) // save is debounced, not immediate

    await new Promise((resolve) => setTimeout(resolve, 600))

    expect(requests).toHaveLength(1)
    expect(requests[0].method).toBe('PATCH')
    expect(document.querySelector('.notes-save-status').innerHTML).toBe('Saved!')
  })

  it('does not re-save when the input fires again with an unchanged value', async () => {
    const requests = installFakeXHR({status: 200, responseText: '{}'})
    await mount()

    const notesInput = document.querySelector('input[name="notes"]')
    $(notesInput).val('same value').trigger('input')
    await new Promise((resolve) => setTimeout(resolve, 600))
    expect(requests).toHaveLength(1)

    $(notesInput).trigger('input') // value unchanged from the cached last-saved value
    await new Promise((resolve) => setTimeout(resolve, 600))
    expect(requests).toHaveLength(1)
  })

  it('does not run the debounced save for the file input nested inside #collapse-details', async () => {
    const requests = installFakeXHR({status: 200, responseText: '{}'})
    await mount()

    $('#archive_upload_form .file').trigger('input')
    await new Promise((resolve) => setTimeout(resolve, 600))

    expect(requests).toHaveLength(0)
  })
})

describe('static/js/link-delete-confirm.js', () => {
  const FIXTURE = `<a href="/refer">Cancel</a> <button type="submit" class="btn delete-confirm">Delete Perma Link</button>`

  async function mount() {
    document.body.innerHTML = FIXTURE
    window.archive = {guid: 'ABCD-1234'}
    window.url_link_browser = '/'
    window.api_path = '/api/v1'
    vi.resetModules()
    await import('../../static/js/link-delete-confirm.js')
    // the module wraps its setup in jQuery's $(fn) document-ready handler, which jQuery defers to
    // a later tick even when jsdom's document is already "complete" -- wait for it before using it.
    await new Promise((resolve) => setTimeout(resolve, 0))
  }

  let OriginalXHR

  beforeEach(() => {
    OriginalXHR = globalThis.XMLHttpRequest
  })

  afterEach(() => {
    globalThis.XMLHttpRequest = OriginalXHR
    delete window.archive
    delete window.url_link_browser
    delete window.api_path
    document.body.innerHTML = ''
  })

  it('clicking delete-confirm disables the button and updates its text immediately', async () => {
    const requests = installFakeXHR({status: 200, responseText: '{}'})
    await mount()

    document.querySelector('.delete-confirm').click()

    expect(document.querySelector('.delete-confirm').classList.contains('disabled')).toBe(true)
    expect(document.querySelector('.delete-confirm').textContent).toBe('Deleting link...')
    expect(requests[0].method).toBe('DELETE')
    expect(requests[0].url).toBe('/api/v1/archives/ABCD-1234/')
  })

  it('a native (keyboard-equivalent) click activates delete the same as a mouse click', async () => {
    // See the equivalent note in the single-link-permissions suite: jsdom does not synthesize a
    // click from Enter/Space, so this exercises the underlying 'click' event directly.
    const requests = installFakeXHR({status: 200, responseText: '{}'})
    await mount()

    document.querySelector('.delete-confirm').click()

    expect(requests).toHaveLength(1)
  })

  it('a second click while a request is in flight (disabled) does not send a second request', async () => {
    const requests = installFakeXHR({status: 200, responseText: '{}'})
    await mount()

    document.querySelector('.delete-confirm').click()
    document.querySelector('.delete-confirm').click()

    expect(requests).toHaveLength(1)
  })

  it('on server error: restores the button and surfaces the error message to the user', async () => {
    installFakeXHR({status: 400, responseText: JSON.stringify({detail: 'Cannot delete this link'})})
    await mount()

    const btn = document.querySelector('.delete-confirm')
    btn.click()
    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(btn.classList.contains('disabled')).toBe(false)
    expect(btn.textContent).toBe('Delete Perma Link')
    const alert = document.querySelector('.popup-alert')
    expect(alert).not.toBeNull()
    expect(alert.textContent).toContain('Cannot delete this link')
  })

  it('on a network failure (no response): restores the button and surfaces a generic error', async () => {
    installFakeXHR({networkError: true})
    await mount()

    const btn = document.querySelector('.delete-confirm')
    btn.click()
    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(btn.classList.contains('disabled')).toBe(false)
    // a network failure has no status/response to derive a specific message from, so
    // getErrorMessage falls back to its generic message rather than an "Error <status>" string.
    const alert = document.querySelector('.popup-alert')
    expect(alert).not.toBeNull()
    expect(alert.textContent).toContain("we've encountered an error processing your request")
  })
})
