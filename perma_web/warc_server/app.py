# this is a wsgi application that gets included with its own url prefix
# alongside the main Django app in wsgi.py
import logging
import traceback

from django.core.handlers.wsgi import WSGIRequest
from django.core.files.storage import default_storage
from pywb.framework.wsgi_wrappers import init_app, WSGIApp
from pywb_config import (PermaCDXServer,
                         PermaHandler,
                         create_perma_wb_router)


# monkey-patch WSGIApp.handle_exception to log exceptions as errors
real_handle_exception = WSGIApp.handle_exception
def handle_exception(self, env, exc, print_trace):
    if print_trace:
        try:
            extra = {'request':WSGIRequest(env)}
        except:
            extra = {}
        logging.error(traceback.format_exc(exc), extra=extra)
    return real_handle_exception(self, env, exc, print_trace)
WSGIApp.handle_exception = handle_exception


# must be ascii, for some reason, else you'll get
# 'unicode' object has no attribute 'get'
path = default_storage.path('').encode('ascii', 'ignore') + '/'
application = init_app(create_perma_wb_router,
                       load_yaml=False,
                       config={
                           'port': 8000,
                           'collections': {'': 'PermaCDXSource'},
                           'archive_paths': path,
                           'server_cls': PermaCDXServer,
                           'wb_handler_class': PermaHandler,
                           'enable_memento': True
                       })
