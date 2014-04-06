import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "perma.settings")
from django.conf import settings
from django.core.files.storage import default_storage

from pywb.rewrite.rewriterules import use_lxml_parser
from pywb.rewrite.wburl import WbUrl

from pywb.framework import archivalrouter

from pywb.webapp.handlers import WBHandler
from pywb.webapp.query_handler import QueryHandler
from pywb.webapp.pywb_init import create_wb_handler


# include guid in CDX requests
class Route(archivalrouter.Route):
    def _apply_filters(self, wbrequest, matcher):
        wbrequest.custom_params['guid'] = matcher.group(1)

# prevent mod getting added to rewritten urls
# timestamp already disabled via 'redir_to_exact' flag
class Url(WbUrl):
    def to_str(self, **overrides):
        overrides['mod'] = ''
        overrides['timestamp'] = ''
        return WbUrl.to_str(self, **overrides)

class Handler(WBHandler):
    def get_wburl_type(self):
        return Url


#=================================================================
def create_perma_pywb_app():
    """
        Configure server.
    """
    query_handler = QueryHandler.init_from_config(settings.CDX_SERVER_URL)

    # enable lxml parsing if available
    #use_lxml_parser()

    # get root storage location for warcs
    try:
        # access via local disk if we can
        archive_path = 'file://' + default_storage.path('') + '/'
    except NotImplementedError:
        # else access via url
        archive_path = default_storage.url('') + '/'

    # use util func to create the handler
    wb_handler = create_wb_handler(query_handler,
                                   dict(archive_paths=[archive_path],
                                        wb_handler_class=Handler,
                                        buffer_response=True,

                                        head_insert_html='ui/head_insert.html',
                                        template_globals={'static_path': 'static/js'},

                                        redir_to_exact=False))

    # Finally, create wb router
    return archivalrouter.ArchivalRouter(
        {
            Route(r'([a-zA-Z0-9\-]+)', wb_handler)
        },
        # Specify hostnames that pywb will be running on
        # This will help catch occasionally missed rewrites that fall-through to the host
        # (See archivalrouter.ReferRedirect)
        hostpaths=['http://localhost:8000/'],
        port=8000
    )
