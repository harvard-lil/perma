# this is a wsgi application that gets included with its own url prefix
# alongside the main Django app in wsgi.py

from pywb.framework.wsgi_wrappers import init_app
from pywb_config import create_perma_pywb_app

application = init_app(create_perma_pywb_app,
                       load_yaml=False)
