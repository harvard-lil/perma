import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import * as LinkHelpers from '../../static/js/helpers/link.helpers'

describe('Test link.helpers.js', () => {
  beforeEach(() => {
    expect(LinkHelpers).toBeDefined()
    window.linkObj = {
      captures: [
        {
          content_type: 'text/html',
          playback_url: '//perma.test:8000/warc/ZFK8-B42T/http://example.com',
          record_type: 'response',
          role: 'primary',
          status: 'success',
          url: 'http://example.com',
          user_upload: false,
        },
        {
          content_type: 'image/png',
          playback_url: '//perma.test:8000/warc/ZFK8-B42T/id_/file:///ZFK8-B42T/cap.png',
          record_type: 'resource',
          role: 'screenshot',
          status: 'success',
          url: 'file:///ZFK8-B42T/cap.png',
          user_upload: false,
        },
        {
          content_type: 'favicon',
          playback_url: '//perma.test:8000/warc/ZFK8-B42T/id_/file:///ZFK8-B42T/favicon.ico',
          record_type: 'resource',
          role: 'favicon',
          status: 'success',
          url: 'file:///ZFK8-B42T/favicon.ico',
          user_upload: false,
        },
      ],
      creation_timestamp: '2016-08-18T20:55:18Z',
      creation_timestamp_formatted: 'August 18, 2016',
      expiration_date_formatted: 'undefined NaN, NaN',
      favicon_url: '',
      guid: 'ZFK8-B42T',
      local_url: 'localhost:8000/ZFK8-B42T',
      title: 'Example Domain',
      url: 'http://example.com',
      warc_size: 21030,
    }
  })

  afterEach(() => {
    delete window.linkObj
    delete window.host
  })

  describe('Test findFaviconUrl', () => {
    it('finds favicon url when one exists', () => {
      const url = LinkHelpers.findFaviconURL(window.linkObj)

      expect(url).toEqual('//perma.test:8000/warc/ZFK8-B42T/id_/file:///ZFK8-B42T/favicon.ico')
    })

    it('does not error when favicon does not exist', () => {
      const linkObjCopy = {...window.linkObj, captures: window.linkObj.captures.slice(0, 2)}
      const url = LinkHelpers.findFaviconURL(linkObjCopy)

      expect(url).toEqual('')
    })
  })

  describe('Test generateLinkFields', () => {
    it('returns a more robust link object', () => {
      const linkObjCopy = {...window.linkObj}
      const newLink = LinkHelpers.generateLinkFields(linkObjCopy)

      expect(newLink.expiration_date_formatted).toBeDefined()
      expect(newLink.creation_timestamp_formatted).toBeDefined()
    })

    it('calls findFaviconURL', () => {
      const findFaviconURL = vi.spyOn(LinkHelpers, 'findFaviconURL')

      LinkHelpers.generateLinkFields({...window.linkObj})

      expect(findFaviconURL).toHaveBeenCalled()
    })

    it('adds local_url if host is available', () => {
      window.host = 'perma-stage.org'
      const linkObjCopy = {...window.linkObj}

      LinkHelpers.generateLinkFields(linkObjCopy)

      expect(linkObjCopy.local_url).toBe(`perma-stage.org/${linkObjCopy.guid}`)
    })
  })
})
