import Module from 'node:module'
import { afterAll, afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// A DSN of the standard Sentry shape (public key + ingest host + numeric project id) that
// resolves to nothing real; global.js's Sentry.init call is mocked below anyway, so no event
// could ever leave the process even if the DSN were dialed.
const FAKE_DSN = 'https://examplePublicKey@o0.ingest.sentry.io/0'
const PLAYBACK_HOST = 'perma-archives.org'

const djangoSettings = (overrides = {}) => ({
  API_VERSION: 1,
  STATIC_URL: '/static/',
  MEDIA_URL: '/media/',
  DEBUG: false,
  USE_SENTRY: true,
  SENTRY_DSN: FAKE_DSN,
  SENTRY_ENVIRONMENT: 'test',
  SENTRY_TRACES_SAMPLE_RATE: 0.5,
  PLAYBACK_HOST,
  ...overrides,
})

// vi.mock factories are hoisted above all other module code, so the mock fn they close over
// must come from vi.hoisted() rather than a plain top-level const.
const { initMock } = vi.hoisted(() => ({ initMock: vi.fn() }))
vi.mock('@sentry/browser', () => ({ init: initMock }))

describe('global.js Sentry configuration contract', () => {
  // global.js also `require()`s 'bootstrap/js/dist/*' as a side effect unrelated to Sentry.
  // Under Vitest's vite-node runtime, a bare `require()` call (unlike `import`) bypasses Vite's
  // resolver entirely and hits Node's real module system directly, so neither a vitest.config.mjs
  // alias nor vi.mock() can reach it - confirmed by probing both independently. Stub that
  // Node-level require directly so the real, unmodified global.js loads exactly as production
  // does, without pulling in DOM-heavy plugins that have nothing to do with Sentry.
  const originalRequire = Module.prototype.require
  beforeEach(() => {
    Module.prototype.require = function (request, ...rest) {
      if (request.startsWith('bootstrap/js/dist/')) return {}
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
      // The source's `\:` and `\/` are not real regex escapes in a JS string literal - they
      // collapse to plain `:` and `/`, so the resulting denyUrls entry is a literal string
      // (not a RegExp), which matters a great deal - see spec/vitest/sentry-sdk.spec.js.
      denyUrls: [`^https://${PLAYBACK_HOST}/.*$`],
      tracesSampleRate: 0.5,
    })
  })

  it('never calls Sentry.init when USE_SENTRY is false', async () => {
    globalThis.settings = djangoSettings({ USE_SENTRY: false })
    globalThis.api_path = '/api/v1'

    await import('../../static/js/global.js')

    expect(initMock).not.toHaveBeenCalled()
  })

  it('interpolates PLAYBACK_HOST into denyUrls verbatim, including hosts with regex metacharacters', async () => {
    globalThis.settings = djangoSettings({ PLAYBACK_HOST: 'perma-archives.test' })
    globalThis.api_path = '/api/v1'

    await import('../../static/js/global.js')

    expect(initMock).toHaveBeenCalledWith(
      expect.objectContaining({ denyUrls: ['^https://perma-archives.test/.*$'] }),
    )
  })
})
