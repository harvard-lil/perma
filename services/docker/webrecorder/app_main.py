from gevent import monkey; monkey.patch_all()

# patch cookie rewriting to be quieter
from pywb.rewrite.cookie_rewriter import WbUrlBaseCookieRewriter
import six
from six.moves.http_cookies import SimpleCookie, CookieError
import logging
def quiet_rewrite(self, cookie_str, header='Set-Cookie'):
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

#from app import init
from webrecorder.maincontroller import MainController
from bottle import run


# ============================================================================
application = MainController().app

if __name__ == "__main__":
    run(app=application, port=8088)
