import { afterEach, vi } from 'vitest'
import jQuery from 'jquery'

globalThis.$ = jQuery
globalThis.jQuery = jQuery
globalThis.waffle = {FLAGS: {}}
globalThis.links_remaining = Infinity
globalThis.is_nonpaying = false
globalThis.is_individual = true
globalThis.is_organization_user = false
globalThis.is_registrar_user = false
globalThis.is_sponsored_user = false
globalThis.is_staff = false
globalThis.link_creation_allowed = true
globalThis.subscription_status = ''
globalThis.max_size = 0
globalThis.urls = {}
globalThis.current_user = {top_level_folders: []}

// The Webpack build contract runs in the node environment but still loads this
// shared setup file, so every DOM touch below has to be guarded.
const hasDom = typeof document !== 'undefined'

if (hasDom) {
  if (!HTMLDialogElement.prototype.showModal) {
    HTMLDialogElement.prototype.showModal = function showModal() {
      this.open = true
    }
  }

  if (!HTMLDialogElement.prototype.close) {
    HTMLDialogElement.prototype.close = function close() {
      this.open = false
    }
  }

  if (!window.matchMedia) {
    window.matchMedia = (query) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    })
  }
}

// JSDOM silently ignores `document.cookie = ''`; each cookie must be expired by name.
const clearCookies = () => {
  for (const pair of document.cookie.split(';')) {
    const name = pair.split('=')[0].trim()
    if (name) {
      document.cookie = `${name}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT`
    }
  }
}

afterEach(() => {
  if (hasDom) {
    document.body.innerHTML = ''
    clearCookies()
    localStorage.clear()
  }
  vi.restoreAllMocks()
})
