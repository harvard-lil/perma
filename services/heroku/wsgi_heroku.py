# for Heroku, wrap wsgi app to serve static files

from dj_static import Cling

from .wsgi import application as wrapped_application

application = Cling(wrapped_application)