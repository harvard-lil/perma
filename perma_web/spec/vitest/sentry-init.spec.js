import Module from 'node:module'
import { afterAll, afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// A DSN of the standard Sentry shape (public key + ingest host + numeric project id) that
// resolves to nothing real; global.js's Sentry.init call is mocked below anyway, so no event
// could ever leave the process even if the DSN were dialed.
const FAKE_DSN = 'https://examplePublicKey@o0.ingest.sentry.io/0'
const RELEASE = 'perma@abc1234'

const djangoSettings = (overrides = {}) => ({
  API_VERSION: 1,
  STATIC_URL: '/static/',
  MEDIA_URL: '/media/',
  DEBUG: false,
  USE_SENTRY: true,
  SENTRY_DSN: FAKE_DSN,
  SENTRY_ENVIRONMENT: 'test',
  SENTRY_TRACES_SAMPLE_RATE: 0.5,
  SENTRY_RELEASE: RELEASE,
  ...overrides,
})

// vi.mock factories are hoisted above all other module code, so the mock fn they close over
// must come from vi.hoisted() rather than a plain top-level const.
const { initMock } = vi.hoisted(() => ({ initMock: vi.fn() }))
vi.mock('@sentry/browser', () => ({ init: initMock }))

describe('global.js Sentry configuration contract', () => {
  // global.js also `require()`s 'bootstrap-js/*' as a side effect unrelated to Sentry.
  // Under Vitest's vite-node runtime, a bare `require()` call (unlike `import`) bypasses Vite's
  // resolver entirely and hits Node's real module system directly, so neither a vitest.config.mjs
  // alias nor vi.mock() can reach it - confirmed by probing both independently. Stub that
  // Node-level require directly so the real, unmodified global.js loads exactly as production
  // does, without pulling in DOM-heavy plugins that have nothing to do with Sentry.
  const originalRequire = Module.prototype.require
  beforeEach(() => {
    Module.prototype.require = function (request, ...rest) {
      if (request.startsWith('bootstrap-js/')) return {}
      return originalRequire.call(this, request, ...rest)
    }
    vi.resetModules()
    initMock.mockClear()
  })

  afterEach(() => {
    delete globalThis.settings
    delete globalThis.api_path
  })

  afterAll(() => {
    Module.prototype.require = originalRequire
  })

  it('calls Sentry.init exactly once, with the exact constructed option object, when USE_SENTRY is true', async () => {
    globalThis.settings = djangoSettings({ USE_SENTRY: true })
    globalThis.api_path = '/api/v1'

    await import('../../static/js/global.js')

    expect(initMock).toHaveBeenCalledTimes(1)
    expect(initMock).toHaveBeenCalledWith({
      dsn: FAKE_DSN,
      environment: 'test',
      release: RELEASE,
      // strings, which the SDK matches as substrings: see spec/vitest/sentry-sdk.spec.js
      allowUrls: [`${window.location.origin}/`],
      ignoreErrors: [
        'Object Not Found Matching Id',
        'Could not establish connection. Receiving end does not exist.',
        'Invalid call to runtime.sendMessage(). Tab not found.',
      ],
      tracesSampleRate: 0.5,
    })
  })

  it('never calls Sentry.init when USE_SENTRY is false', async () => {
    globalThis.settings = djangoSettings({ USE_SENTRY: false })
    globalThis.api_path = '/api/v1'

    await import('../../static/js/global.js')

    expect(initMock).not.toHaveBeenCalled()
  })

  it('leaves the release unset when the image has none', async () => {
    globalThis.settings = djangoSettings({ SENTRY_RELEASE: '' })
    globalThis.api_path = '/api/v1'

    await import('../../static/js/global.js')

    expect(initMock.mock.calls[0][0].release).toBeUndefined()
  })

  it('also allows STATIC_URL when static files come from another host', async () => {
    globalThis.settings = djangoSettings({ STATIC_URL: 'https://static.example.test/static/' })
    globalThis.api_path = '/api/v1'

    await import('../../static/js/global.js')

    expect(initMock.mock.calls[0][0].allowUrls).toEqual([
      `${window.location.origin}/`,
      'https://static.example.test/static/',
    ])
  })
})
