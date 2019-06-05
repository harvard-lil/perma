from gevent import monkey; monkey.patch_all()

### BEGIN PERMA CUSTOMIZATIONS
### Temporary monkey patches:
### these changes to pywb should eventually appear upstream,
### after we are confident enough to submit PRs.
###

# patch cookie rewriting to be quieter
# https://github.com/webrecorder/pywb/blob/master/pywb/rewrite/cookie_rewriter.py#L15
from pywb.rewrite.cookie_rewriter import WbUrlBaseCookieRewriter
def quiet_rewrite(self, cookie_str, header='Set-Cookie'):
   # begin Perma customization
    from pywb.rewrite.cookie_rewriter import six
    from six.moves.http_cookies import SimpleCookie, CookieError
    import logging
    # end Perma customization

    results = []
    cookie_str = self.REMOVE_EXPIRES.sub('', cookie_str)
    try:
        cookie = SimpleCookie(cookie_str)
    except CookieError as e:
        # begin Perma customization
        logger = logging.getLogger(__name__)
        logger.info(e, exc_info=True)
        # end Perma customization
        return results

    for name, morsel in six.iteritems(cookie):
        morsel = self.rewrite_cookie(name, morsel)

        self._filter_morsel(morsel)

        if not self.add_prefix_cookie_for_all_mods(morsel, results, header):
            value = morsel.OutputString()
            results.append((header, value))

    return results
WbUrlBaseCookieRewriter.rewrite = quiet_rewrite


# patch invalid CXDline logging to be more informative
# https://github.com/webrecorder/pywb/blob/master/pywb/warcserver/index/cdxobject.py#L153
from pywb.warcserver.index.cdxobject import CDXObject
def log_invalid_cdx(self, cdxline=b''):
    # begin Perma customization
    from pywb.warcserver.index.cdxobject import (OrderedDict, to_native_str,
        json_decode, six, quote, CDXException, URLKEY, TIMESTAMP)
    # end Perma customization

    OrderedDict.__init__(self)

    cdxline = cdxline.rstrip()
    self._from_json = False
    self._cached_json = None

    # Allows for filling the fields later or in a custom way
    if not cdxline:
        self.cdxline = cdxline
        return

    fields = cdxline.split(b' ' , 2)

    # Check for CDX JSON
    if fields[-1].startswith(b'{'):
        self[URLKEY] = to_native_str(fields[0], 'utf-8')
        self[TIMESTAMP] = to_native_str(fields[1], 'utf-8')
        json_fields = json_decode(to_native_str(fields[-1], 'utf-8'))
        for n, v in six.iteritems(json_fields):
            n = to_native_str(n, 'utf-8')
            n = self.CDX_ALT_FIELDS.get(n, n)

            if n == 'url':
                try:
                    v.encode('ascii')
                except UnicodeEncodeError:
                    v = quote(v.encode('utf-8'), safe=':/')

            if n != 'filename':
                v = to_native_str(v, 'utf-8')

            self[n] = v

        self.cdxline = cdxline
        self._from_json = True
        return

    more_fields = fields.pop().split(b' ')
    fields.extend(more_fields)

    cdxformat = None
    for i in self.CDX_FORMATS:
        if len(i) == len(fields):
            cdxformat = i
    if not cdxformat:
        # begin Perma customization
        msg = 'unknown {0}-field cdx format: {1}'.format(len(fields), fields)
        # begin Perma customization
        raise CDXException(msg)

    for header, field in zip(cdxformat, fields):
        self[header] = to_native_str(field, 'utf-8')

    self.cdxline = cdxline

CDXObject.__init__ = log_invalid_cdx

#
# END PERMA CUSTOMIZATIONS
#

#from app import init
from webrecorder.maincontroller import MainController
from bottle import run


# ============================================================================
application = MainController().app

if __name__ == "__main__":
    run(app=application, port=8088)
