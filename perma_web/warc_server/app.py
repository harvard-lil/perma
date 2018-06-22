# this is a wsgi application that gets included with its own url prefix
# alongside the main Django app in wsgi.py

from django.conf import settings

from pywb.framework.wsgi_wrappers import init_app
from .pywb_config import (PermaCDXServer,
                         PermaHandler,
                         create_perma_wb_router,
                         get_archive_path)


application = init_app(create_perma_wb_router,
                       load_yaml=False,
                       config={
                           'port': 8000,
                           'collections': {'': 'PermaCDXSource'},
                           'archive_paths': get_archive_path(),
                           'server_cls': PermaCDXServer,
                           'wb_handler_class': PermaHandler,
                           'enable_memento': True,
                           'framed_replay': False,

                           # pywb template vars (used in templates called by pywb, such as head_insert.html, but not our ErrorTemplateView)
                           'template_globals': {
                               'static_path': settings.STATIC_URL.rstrip('/')+'/pywb'
                           },

                           # so pywb's Jinja2 templates find our warc_server/templates dir
                           'template_packages': ['warc_server', 'pywb'],
                       })
