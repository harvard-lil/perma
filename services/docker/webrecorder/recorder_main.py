from gevent import monkey; monkey.patch_all()

### BEGIN PERMA CUSTOMIZATIONS
### Temporary monkey patches:
### these changes to pywb should eventually appear upstream,
### after we are confident enough to submit PRs.
###

# First pass fix for https://github.com/webrecorder/pywb/issues/471
# https://github.com/webrecorder/pywb/blob/master/pywb/warcserver/inputrequest.py#L232
from pywb.warcserver.inputrequest import MethodQueryCanonicalizer
def catch_unicode_exception(self, method, mime, length, stream,
                            buffered_stream=None,
                            environ=None):
    from pywb.warcserver.inputrequest import (to_native_str, unquote_plus,
        urlencode, PY3, cgi, base64)

    self.query = b''

    method = method.upper()

    if method in ('OPTIONS', 'HEAD'):
        self.query = '__pywb_method=' + method.lower()
        return

    if method != 'POST':
        return

    try:
        length = int(length)
    except (ValueError, TypeError):
        return

    if length <= 0:
        return

    query = b''

    while length > 0:
        buff = stream.read(length)
        length -= len(buff)

        if not buff:
            break

        query += buff

    if buffered_stream:
        buffered_stream.write(query)
        buffered_stream.seek(0)

    if not mime:
        mime = ''

    if mime.startswith('application/x-www-form-urlencoded'):
        # begin Perma customization
        try:
            query = to_native_str(query)
            query = unquote_plus(query)
        except UnicodeDecodeError:
            query = to_native_str(query, 'iso-8859-1')
        # end Perma customization

    elif mime.startswith('multipart/'):
        env = {'REQUEST_METHOD': 'POST',
               'CONTENT_TYPE': mime,
               'CONTENT_LENGTH': len(query)}

        args = dict(fp=BytesIO(query),
                    environ=env,
                    keep_blank_values=True)

        if PY3:
            args['encoding'] = 'utf-8'

        data = cgi.FieldStorage(**args)

        values = []
        for item in data.list:
            values.append((item.name, item.value))

        query = urlencode(values, True)

    elif mime.startswith('application/x-amf'):
        query = self.amf_parse(query, environ)

    else:
        query = base64.b64encode(query)
        query = to_native_str(query)
        query = '__wb_post_data=' + query

    self.query = query

MethodQueryCanonicalizer.__init__ = catch_unicode_exception

#
# END PERMA CUSTOMIZATIONS
#

import os
from ast import literal_eval

from webrecorder.utils import load_wr_config, init_logging, spawn_once
from webrecorder.rec.webrecrecorder import WebRecRecorder


# =============================================================================
def init():
    init_logging(debug=literal_eval(os.environ.get('WR_DEBUG', 'True')))

    config = load_wr_config()

    wr = WebRecRecorder(config)

    spawn_once(wr.msg_listen_loop)

    wr.init_app()
    wr.app.wr = wr

    return wr.app
