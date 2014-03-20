import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "perma.settings")
from django.conf import settings

from pywb.framework import archivalrouter
from pywb.rewrite.wburl import WbUrl
from pywb.core.handlers import WBHandler
from pywb.core.indexreader import IndexReader

from pywb.cdx.cdxserver import create_cdx_server
from pywb.core.pywb_init import create_wb_handler
from pywb.rewrite.rewriterules import use_lxml_parser

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
DEFAULT_RULES = 'pywb/rules.yaml'


def create_perma_pywb_app():
    """
        Configure server.
    """
    cdx_server = create_cdx_server(settings.CDX_SERVER_URL, DEFAULT_RULES)
    index_reader = IndexReader(cdx_server)

    # enable lxml parsing if available
    use_lxml_parser()

    # use util func to create the handler
    wb_handler = create_wb_handler(index_reader,
                                   dict(archive_paths=['file://'],
                                        wb_handler_class=Handler,
                                        buffer_response=True,
                                        redir_to_exact=False),
                                   DEFAULT_RULES)

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
