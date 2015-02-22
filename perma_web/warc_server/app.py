# this is a wsgi application that gets included with its own url prefix
# alongside the main Django app in wsgi.py

from pywb.framework.wsgi_wrappers import init_app
from pywb_config import PermaCDXServer, create_perma_pywb_app
from pywb.webapp.pywb_init import create_wb_router

application = init_app(create_wb_router,
                       load_yaml=False,
                       config={
                           'collections': {'pywb': '/Users/leppert/github/perma/services/django/generated_assets/'},
                           'archive_paths': '/Users/leppert/github/perma/services/django/generated_assets/',
                           'server_cls': PermaCDXServer
                       })
