import Module from 'node:module'
import * as Sentry from '@sentry/browser'
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'

// global.js calls Sentry.init; record the options it builds instead, so the tests below can
// run Perma's own configuration through the real SDK with a fake transport.
const { recordedOptions } = vi.hoisted(() => ({ recordedOptions: [] }))
vi.mock('@sentry/browser', async (importOriginal) => {
  const real = await importOriginal()
  return { ...real, init: (options) => { recordedOptions.push(options) } }
})

// A DSN of the standard Sentry shape (public key + ingest host + numeric project id) that
// resolves to nothing real; every test below also supplies its own no-op transport, so no
// event can ever leave the process even if the DSN were dialed.
const FAKE_DSN = 'https://examplePublicKey@o0.ingest.sentry.io/0'
const PLAYBACK_HOST = 'perma-archives.org'
const OWN_SCRIPT = () => `${window.location.origin}/static/bundles/global.js`

// Envelope shape is [header, [[itemHeader, itemPayload], ...]]; pull out the first itemPayload
// tagged as an event, ignoring any other item types the SDK may add.
const eventPayload = (envelope) => envelope[1].find(([itemHeader]) => itemHeader.type === 'event')?.[1]

describe('Sentry SDK behavior contract (real @sentry/browser, fake transport)', () => {
  let envelopes
  let client

  const makeFakeTransport = () => () => ({
    send: (envelope) => {
      envelopes.push(envelope)
      return Promise.resolve({})
    },
    flush: () => Promise.resolve(true),
  })

  let actualInit
  beforeAll(async () => {
    actualInit = (await vi.importActual('@sentry/browser')).init
  })

  const initSentry = (options = {}) => {
    envelopes = []
    return actualInit({
      dsn: FAKE_DSN,
      environment: 'test',
      tracesSampleRate: 0.5,
      ...options,
      transport: makeFakeTransport(),
    })
  }

  afterEach(async () => {
    // Release the client so its internal outcome/report timers don't leak into later tests.
    await client?.close()
    client = undefined
  })

  describe('envelope and event shape', () => {
    beforeEach(() => {
      client = initSentry()
    })

    it('transmits nothing over a real network channel - the fake transport is the only sink', async () => {
      const fetchSpy = typeof fetch === 'function' ? vi.spyOn(globalThis, 'fetch') : null
      const xhrOpenSpy = vi.spyOn(XMLHttpRequest.prototype, 'open')

      Sentry.captureException(new Error('no network probe'))
      await Sentry.flush(1000)

      expect(envelopes).toHaveLength(1)
      expect(fetchSpy).not.toHaveBeenCalled()
      expect(xhrOpenSpy).not.toHaveBeenCalled()
    })

    it('captureException produces exactly one envelope carrying the configured environment and exception type/value', async () => {
      Sentry.captureException(new Error('characterization probe'))
      await Sentry.flush(1000)

      expect(envelopes).toHaveLength(1)
      const event = eventPayload(envelopes[0])
      expect(event.environment).toBe('test')
      expect(event.exception.values[0]).toMatchObject({ type: 'Error', value: 'characterization probe' })
    })

    it('stamps event_id, platform, and an SDK name/version block on the envelope', async () => {
      Sentry.captureException(new Error('metadata probe'))
      await Sentry.flush(1000)

      const [header] = envelopes[0]
      const event = eventPayload(envelopes[0])
      expect(header.event_id).toMatch(/^[0-9a-f]{32}$/)
      expect(event.platform).toBe('javascript')
      expect(header.sdk.name).toMatch(/^sentry\.javascript\./)
      expect(header.sdk.version).toEqual(expect.any(String))
    })
  })

  describe("Perma's filters, as global.js builds them", () => {
    let permaOptions

    beforeAll(async () => {
      // global.js also `require()`s 'bootstrap-js/*', which bypasses Vite's resolver; see
      // sentry-init.spec.js.
      const originalRequire = Module.prototype.require
      Module.prototype.require = function (request, ...rest) {
        if (request.startsWith('bootstrap-js/')) return {}
        return originalRequire.call(this, request, ...rest)
      }
      globalThis.settings = {
        API_VERSION: 1, STATIC_URL: '/static/', MEDIA_URL: '/media/', DEBUG: false,
        USE_SENTRY: true, SENTRY_DSN: FAKE_DSN, SENTRY_ENVIRONMENT: 'test',
        SENTRY_TRACES_SAMPLE_RATE: 0.5, SENTRY_RELEASE: 'perma@abc1234',
      }
      globalThis.api_path = '/api/v1'
      try {
        await import('../../static/js/global.js')
      } finally {
        Module.prototype.require = originalRequire
        delete globalThis.settings
        delete globalThis.api_path
      }
      permaOptions = recordedOptions.at(-1)
    })

    beforeEach(() => {
      client = initSentry(permaOptions)
    })

    const captureFrom = async (filename, value = 'probe') => {
      Sentry.captureEvent({
        exception: { values: [{ type: 'Error', value, stacktrace: { frames: [{ filename, function: 'boot' }] } }] },
      })
      await Sentry.flush(1000)
    }

    it("keeps an event from Perma's own scripts", async () => {
      await captureFrom(OWN_SCRIPT())
      expect(envelopes).toHaveLength(1)
      expect(eventPayload(envelopes[0]).release).toBe('perma@abc1234')
    })

    it.each([
      ['the playback host', `https://${PLAYBACK_HOST}/embed/replay.js`],
      ['a browser extension', 'chrome-extension://abcdefghijklmnop/content.js'],
      ['a Safari app extension', '/Applications/PayPal%20Honey.app/Contents/Resources/Honey.safariextension/h0.js'],
      ['a page saved and opened from disk', 'file:///Users/someone/Downloads/Perma.html'],
    ])('drops an event from %s', async (_, filename) => {
      await captureFrom(filename)
      expect(envelopes).toHaveLength(0)
    })

    it('keeps an event with no stack trace, which allowUrls cannot place', async () => {
      Sentry.captureEvent({ exception: { values: [{ type: 'UnhandledRejection', value: 'no frames' }] } })
      await Sentry.flush(1000)
      expect(envelopes).toHaveLength(1)
    })

    it.each([
      'Non-Error promise rejection captured with value: Object Not Found Matching Id:2, MethodName:update, ParamCount:4',
      'Could not establish connection. Receiving end does not exist.',
      'Invalid call to runtime.sendMessage(). Tab not found.',
    ])('drops %s', async (message) => {
      await captureFrom(OWN_SCRIPT(), message)
      expect(envelopes).toHaveLength(0)
    })
  })
})
