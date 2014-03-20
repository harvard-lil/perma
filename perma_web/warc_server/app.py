# this is a wsgi application that gets included with its own url prefix
# alongside the main Django app in wsgi.py

import os, site

# include our third-party libs
PROJECT_ROOT = os.path.abspath(os.path.dirname(__name__))
site.addsitedir(os.path.join(PROJECT_ROOT, 'lib'))


#=================================================================
# init cdx server app
#=================================================================

from pywb.framework.wsgi_wrappers import init_app

from pywb_config import create_perma_pywb_app

# cdx-server only config
#DEFAULT_CONFIG = 'config.yaml'

application = init_app(create_perma_pywb_app,
                       load_yaml=False)
