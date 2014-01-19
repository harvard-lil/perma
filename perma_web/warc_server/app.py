# this is a wsgi application that gets included with its own url prefix
# alongside the main Django app in wsgi.py

import sys, os

# make sure pywb.wbapp finds our globalwb module
# this is a weird way to do it -- hopefully pywb will change to support passing settings directly
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

# import app
from pywb.wbapp import application