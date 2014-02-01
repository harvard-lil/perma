# this is a wsgi application that gets included with its own url prefix
# alongside the main Django app in wsgi.py

import os, site

# include our third-party libs
PROJECT_ROOT = os.path.abspath(os.path.dirname(__name__))
site.addsitedir(os.path.join(PROJECT_ROOT, 'lib'))

# tell pywb where to find our config
os.environ['PYWB_CONFIG_MODULE'] = 'warc_server.pywb_config'

from pywb.wbapp import application