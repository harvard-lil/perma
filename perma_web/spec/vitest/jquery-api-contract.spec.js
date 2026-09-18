// Pins the exact jQuery API surface Perma depends on, ahead of the 3.7.1 -> 4.0.0 upgrade
// (see .plans/plan_dependency-upgrade-roadmap-5.md, sub-batch 5A). jQuery 4.0.0 removes
// jQuery.camelCase/cssNumber/cssProps/isArray/isFunction/isNumeric/isWindow/nodeName/now/
// parseJSON/trim/type/unique and jQuery.fn.push/sort/splice. Every assertion below exercises
// real behavior against jsdom, not just presence, so a removal that slips past the measured
// inventory still trips this file.
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

function listFiles(dir, extensions) {
  const out = []
  for (const entry of fs.readdirSync(dir, {withFileTypes: true})) {
    if (entry.name === 'node_modules') continue
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      out.push(...listFiles(full, extensions))
    } else if (extensions.some((ext) => entry.name.endsWith(ext))) {
      out.push(full)
    }
  }
  return out
}

describe('jQuery API contract Perma depends on', () => {
  describe('statics', () => {
    it('$.each iterates arrays by index and objects by key, binding `this` to the value', () => {
      const arraySeen = []
      $.each(['a', 'b'], function (i, v) {
        arraySeen.push([i, v, this])
      })
      expect(arraySeen).toEqual([
        [0, 'a', 'a'],
        [1, 'b', 'b'],
      ])

      const objectSeen = []
      $.each({x: 1, y: 2}, function (k, v) {
        objectSeen.push([k, v])
      })
      expect(objectSeen).toEqual([
        ['x', 1],
        ['y', 2],
      ])
    })

    it('$.each stops early when the callback returns false', () => {
      const seen = []
      $.each([1, 2, 3], function (i, v) {
        seen.push(v)
        return v !== 2
      })
      expect(seen).toEqual([1, 2])
    })

    describe('$.ajax / $.ajaxSetup / $.getJSON', () => {
      let OriginalXHR

      beforeEach(() => {
        OriginalXHR = globalThis.XMLHttpRequest
      })

      afterEach(() => {
        globalThis.XMLHttpRequest = OriginalXHR
        $.ajaxSetup({beforeSend: undefined})
      })

      // Perma never hits the network in tests; this stands in for the browser transport so the
      // ajax family's real request/response contract (headers, status, body) can be asserted.
      //
      // `networkError` simulates a transport-level failure (connection refused, CORS, timeout):
      // jQuery's XHR transport fires `onerror` and never reads a response body, so jqXHR.status
      // is 0 and responseText is never populated. That is a different jQuery code path from an
      // HTTP error status (500, 404, ...), which completes normally via onload/onreadystatechange
      // with a real response body -- calling `onerror` for an ordinary HTTP error status produces
      // a jqXHR with no responseText, which silently does not match a real server error response.
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

      it('$.ajax sends the declared method/url and resolves success with parsed JSON', async () => {
        const requests = installFakeXHR({status: 200, responseText: JSON.stringify({ok: true})})
        const data = await new Promise((resolve) => {
          $.ajax({url: '/thing', method: 'GET', dataType: 'json', success: resolve})
        })
        expect(data).toEqual({ok: true})
        expect(requests[0].method).toBe('GET')
        expect(requests[0].url).toBe('/thing')
      })

      it('$.ajax routes a server error to the fail/error path with the jqXHR', async () => {
        installFakeXHR({status: 500, responseText: JSON.stringify({error: 'boom'})})
        // jqXHR is itself thenable, so resolving a native Promise directly with it (`.fail(resolve)`)
        // makes the Promise machinery adopt jqXHR's (rejected) state instead of fulfilling with it
        // as a value -- wrap it so the outer await actually settles.
        const [jqXHR] = await new Promise((resolve) => {
          $.ajax({url: '/thing', method: 'GET'}).fail((xhr) => resolve([xhr]))
        })
        expect(jqXHR.status).toBe(500)
        expect(JSON.parse(jqXHR.responseText)).toEqual({error: 'boom'})
      })

      it('$.ajaxSetup defaults (e.g. beforeSend) are applied to later $.ajax calls', async () => {
        installFakeXHR({status: 200, responseText: '{}'})
        const seenUrls = []
        $.ajaxSetup({beforeSend: (xhr, settings) => seenUrls.push(settings.url)})

        await new Promise((resolve) => {
          $.ajax({url: '/setup-check', method: 'GET', success: resolve})
        })

        expect(seenUrls).toEqual(['/setup-check'])
      })

      it('$.getJSON issues a GET and parses the JSON response', async () => {
        const requests = installFakeXHR({status: 200, responseText: JSON.stringify({n: 1})})
        const data = await new Promise((resolve) => {
          $.getJSON('/data.json', resolve)
        })
        expect(data).toEqual({n: 1})
        expect(requests[0].method).toBe('GET')
      })

      it('$.getJSON routes a failed request to .fail() with the jqXHR', async () => {
        installFakeXHR({status: 404, responseText: ''})
        const [jqXHR] = await new Promise((resolve) => {
          $.getJSON('/missing.json').fail((xhr) => resolve([xhr]))
        })
        expect(jqXHR.status).toBe(404)
      })

      it('$.ajax routes a network-level failure (no response) to fail with status 0', async () => {
        installFakeXHR({networkError: true})
        const [jqXHR, textStatus] = await new Promise((resolve) => {
          $.ajax({url: '/thing', method: 'GET'}).fail((xhr, status) => resolve([xhr, status]))
        })
        expect(jqXHR.status).toBe(0)
        expect(textStatus).toBe('error')
      })
    })

    it('$.when waits for every deferred and passes their resolved values through in order', () => {
      const d1 = $.Deferred()
      const d2 = $.Deferred()
      let result
      $.when(d1, d2).done((a, b) => {
        result = [a, b]
      })

      expect(result).toBeUndefined()
      d1.resolve('one')
      d2.resolve('two')
      expect(result).toEqual(['one', 'two'])
    })

    it('$.when routes to .fail() if any deferred rejects', () => {
      const d1 = $.Deferred()
      const d2 = $.Deferred()
      let failedWith
      $.when(d1, d2).fail((reason) => {
        failedWith = reason
      })

      d1.reject('nope')
      d2.resolve('two')
      expect(failedWith).toBe('nope')
    })
  })

  describe('instance methods', () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <div id="root">
          <ul id="list"><li class="item">one</li><li class="item">two</li></ul>
          <button id="btn">Click</button>
          <form id="form"><input type="text" id="text-input" name="name"/></form>
          <div id="target">content</div>
        </div>
      `
    })

    it('on/trigger bind and fire an arbitrary named event', () => {
      let count = 0
      $('#btn').on('custom:event', () => count++)
      $('#btn').trigger('custom:event')
      expect(count).toBe(1)
    })

    it('click binds a handler and fires it via trigger and via the zero-arg shorthand', () => {
      let count = 0
      $('#btn').click(() => count++)
      $('#btn').trigger('click')
      $('#btn').click()
      expect(count).toBe(2)
    })

    it('submit binds a handler that can preventDefault the native submission', () => {
      let count = 0
      $('#form').submit((e) => {
        e.preventDefault()
        count++
      })
      $('#form').trigger('submit')
      expect(count).toBe(1)
    })

    it('change binds and fires, observing the field value at fire time', () => {
      let seenValue
      $('#text-input').change(function () {
        seenValue = $(this).val()
      })
      $('#text-input').val('typed value').trigger('change')
      expect(seenValue).toBe('typed value')
    })

    it('select binds and fires', () => {
      let count = 0
      $('#text-input').select(() => count++)
      $('#text-input').trigger('select')
      expect(count).toBe(1)
    })

    it('val gets and sets a form field value', () => {
      expect($('#text-input').val()).toBe('')
      $('#text-input').val('hello')
      expect($('#text-input').val()).toBe('hello')
    })

    it('text gets and sets text content, treating input as literal (not markup)', () => {
      $('#target').text('<b>hi</b>')
      expect($('#target').text()).toBe('<b>hi</b>')
      expect($('#target').html()).toBe('&lt;b&gt;hi&lt;/b&gt;')
    })

    it('html gets and sets innerHTML, parsing input as markup', () => {
      $('#target').html('<span class="inner">hey</span>')
      expect($('#target').find('.inner').text()).toBe('hey')
    })

    it('addClass/removeClass toggle classList membership', () => {
      $('#target').addClass('flag')
      expect(document.getElementById('target').classList.contains('flag')).toBe(true)
      $('#target').removeClass('flag')
      expect(document.getElementById('target').classList.contains('flag')).toBe(false)
    })

    it('prop gets and sets a DOM property (disabled)', () => {
      $('#btn').prop('disabled', true)
      expect(document.getElementById('btn').disabled).toBe(true)
      $('#btn').prop('disabled', false)
      expect(document.getElementById('btn').disabled).toBe(false)
    })

    it('css gets and sets an inline style property', () => {
      $('#target').css('color', 'red')
      expect(document.getElementById('target').style.color).toBe('red')
      // the getter reads computed style, which jsdom normalizes to rgb().
      expect($('#target').css('color')).toBe('rgb(255, 0, 0)')
    })

    it('show/hide toggle visibility via inline display', () => {
      $('#target').hide()
      expect(document.getElementById('target').style.display).toBe('none')
      $('#target').show()
      expect(document.getElementById('target').style.display).not.toBe('none')
    })

    it('find locates descendants by selector', () => {
      expect($('#list').find('.item')).toHaveLength(2)
    })

    it('closest walks up to the nearest matching ancestor, including self', () => {
      expect($('.item').first().closest('#root').attr('id')).toBe('root')
      expect($('#root').closest('#root').length).toBe(1)
    })

    it('append adds content as the last child', () => {
      $('#target').append('<span class="added"></span>')
      expect(document.getElementById('target').lastElementChild.className).toBe('added')
    })

    it('remove detaches the element from the document', () => {
      $('#target').remove()
      expect(document.getElementById('target')).toBeNull()
    })

    it('empty clears all children but keeps the element itself', () => {
      $('#list').empty()
      expect(document.getElementById('list')).not.toBeNull()
      expect(document.getElementById('list').children.length).toBe(0)
    })

    it('each iterates the matched set with `this` bound to each element', () => {
      const texts = []
      $('.item').each(function () {
        texts.push($(this).text())
      })
      expect(texts).toEqual(['one', 'two'])
    })

    it('ready defers its callback to a later tick even when the document is already complete', async () => {
      let ran = false
      $(() => {
        ran = true
      })
      expect(ran).toBe(false)
      await new Promise((resolve) => setTimeout(resolve, 0))
      expect(ran).toBe(true)
    })
  })

  // jQuery 3.7.1 (the current, unchanged stack) still defines every one of these — so asserting
  // their absence from `$` here would test the library, not Perma. Instead this scans Perma's own
  // jQuery-driven source for any reference to a jQuery-4-removed API, so a future change that adds
  // one is caught by this file before the dependency bump ever lands, not discovered by it.
  describe('removed-in-4.0.0 API canary (Perma source must not reference any of these)', () => {
    const REMOVED_STATICS = [
      'camelCase', 'cssNumber', 'cssProps', 'isArray', 'isFunction',
      'isNumeric', 'isWindow', 'nodeName', 'now', 'parseJSON', 'trim', 'type', 'unique',
    ]

    const projectRoot = path.resolve(import.meta.dirname, '..', '..')
    const sourceFiles = [
      ...listFiles(path.join(projectRoot, 'static', 'js'), ['.js']),
      ...listFiles(path.join(projectRoot, 'static', 'frontend'), ['.js', '.vue']),
    ]

    it('finds a non-empty set of source files to scan (guards against a silently-empty test)', () => {
      expect(sourceFiles.length).toBeGreaterThan(10)
    })

    for (const name of REMOVED_STATICS) {
      it(`does not call jQuery.${name} / $.${name} anywhere in static/`, () => {
        const pattern = new RegExp(`(\\$|\\bjQuery)\\s*\\.\\s*${name}\\b`)
        const hits = sourceFiles.filter((file) => pattern.test(fs.readFileSync(file, 'utf8')))
        expect(hits).toEqual([])
      })
    }

    it('does not chain .push/.sort/.splice off a jQuery collection', () => {
      // Matches $(...) or $(...).method(...) chains ending in .push(/.sort(/.splice(. Does not
      // catch a jQuery object stashed in a variable first (e.g. `var $x = $(...); $x.push(...)`)
      // -- a known gap in this static scan, acceptable for a tripwire rather than a full analyzer.
      const pattern = /\$\([^)]*\)(?:\s*\.\s*\w+\([^)]*\))*\s*\.\s*(push|sort|splice)\s*\(/g
      const hits = []
      for (const file of sourceFiles) {
        const content = fs.readFileSync(file, 'utf8')
        if (pattern.test(content)) hits.push(file)
        pattern.lastIndex = 0
      }
      expect(hits).toEqual([])
    })
  })
})
