# this is a wsgi application that gets included with its own url prefix
# alongside the main Django app in wsgi.py

from pywb.framework.wsgi_wrappers import init_app
from django.core.files.storage import default_storage
from pywb_config import (PermaCDXServer,
                         create_perma_wb_router)

# must be ascii, for some reason, else you'll get
# 'unicode' object has no attribute 'get'
path = default_storage.path('').encode('ascii', 'ignore') + '/'
application = init_app(create_perma_wb_router,
                       load_yaml=False,
                       config={
                           'port': 8000,
                           'collections': {'pywb': 'PermaCDXSource'},
                           'archive_paths': path,
                           'server_cls': PermaCDXServer,
                           'enable_memento': True
                       })
