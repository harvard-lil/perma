import * as Sentry from '@sentry/browser'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// A DSN of the standard Sentry shape (public key + ingest host + numeric project id) that
// resolves to nothing real; every test below also supplies its own no-op transport, so no
// event can ever leave the process even if the DSN were dialed.
const FAKE_DSN = 'https://examplePublicKey@o0.ingest.sentry.io/0'
const PLAYBACK_HOST = 'perma-archives.org'

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

  const initSentry = (denyUrls) => {
    envelopes = []
    return Sentry.init({
      dsn: FAKE_DSN,
      environment: 'test',
      denyUrls,
      tracesSampleRate: 0.5,
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
      client = initSentry([`^https://${PLAYBACK_HOST}/.*$`])
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

  describe('denyUrls filtering mechanism (RegExp pattern)', () => {
    // Sentry's InboundFilters integration only regex-tests denyUrls entries that are actual
    // RegExp instances (see the string-vs-regex test below); use one here to isolate and pin
    // the filtering mechanism itself, independent of Perma's own (string) configuration.
    beforeEach(() => {
      client = initSentry([new RegExp(`^https://${PLAYBACK_HOST}/.*$`)])
    })

    it('drops an event whose innermost stack frame targets the playback host', async () => {
      Sentry.captureEvent({
        exception: {
          values: [{
            type: 'Error',
            value: 'from playback iframe',
            stacktrace: { frames: [{ filename: `https://${PLAYBACK_HOST}/embed/replay.js`, function: 'boot' }] },
          }],
        },
      })
      await Sentry.flush(1000)

      expect(envelopes).toHaveLength(0)
    })

    it("does not drop an ordinary event from Perma's own origin", async () => {
      Sentry.captureEvent({
        exception: {
          values: [{
            type: 'Error',
            value: 'from perma app code',
            stacktrace: { frames: [{ filename: 'https://perma.cc/static/js/global.js', function: 'boot' }] },
          }],
        },
      })
      await Sentry.flush(1000)

      expect(envelopes).toHaveLength(1)
    })
  })

  describe("Perma's actual denyUrls value, as literally constructed by global.js (string, not RegExp)", () => {
    beforeEach(() => {
      client = initSentry([`^https://${PLAYBACK_HOST}/.*$`])
    })

    // Sentry 7.108.0's InboundFilters integration (@sentry/core inboundfilters.js ->
    // @sentry/utils isMatchingPattern) only regex-tests denyUrls entries that are RegExp
    // instances; a string entry is matched with plain `value.includes(pattern)`. global.js
    // builds denyUrls as a string that *looks* like a regex
    // (`'^https\:\/\/' + PLAYBACK_HOST + '\/.*$'`, which is `'^https://HOST/.*$'` once JS
    // string-literal escaping is applied - see sentry-init.spec.js), so it never appears as a
    // literal substring of any real URL. This is not a JSDOM artifact: the exact same
    // non-filtering happens in a real browser, confirmed by calling the integration's
    // processEvent directly outside of any stack-parsing path. This test pins that current,
    // surprising reality so an upgrade that starts (or ever stops) compiling string denyUrls
    // into regexes shows up as a visible behavior change here, in either direction.
    it('does not filter a matching playback-host event, because the pattern is a string, not a RegExp', async () => {
      Sentry.captureEvent({
        exception: {
          values: [{
            type: 'Error',
            value: 'from playback iframe, via the literal config string',
            stacktrace: { frames: [{ filename: `https://${PLAYBACK_HOST}/embed/replay.js`, function: 'boot' }] },
          }],
        },
      })
      await Sentry.flush(1000)

      expect(envelopes).toHaveLength(1)
    })
  })
})
