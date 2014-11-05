import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "perma.settings")
from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from django.core.files.storage import default_storage
from django.core.exceptions import DisallowedHost

from pywb.rewrite.wburl import WbUrl
from pywb.framework import archivalrouter
from pywb.framework.wbrequestresponse import WbResponse
from pywb.webapp.handlers import WBHandler
from pywb.webapp.query_handler import QueryHandler
from pywb.webapp.pywb_init import create_wb_handler
from pywb.webapp.views import add_env_globals


# include guid in CDX requests
class Route(archivalrouter.Route):
    def apply_filters(self, wbrequest, matcher):
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


class ErrorTemplateView(object):
    """ View for pywb errors -- basically just hands off to the archive-error.html Django template. """
    def __init__(self):
        self.template = get_template('archive-error.html')

    def render_to_string(self, **kwargs):
        return unicode(self.template.render(Context(kwargs)))

    def render_response(self, **kwargs):
        template_result = self.render_to_string(**dict(kwargs,
                                                     STATIC_URL=settings.STATIC_URL,
                                                     DEBUG=settings.DEBUG))
        status = kwargs.get('status', '200 OK')
        content_type = kwargs.get('content_type', 'text/html; charset=utf-8')
        return WbResponse.text_response(template_result.encode('utf-8'), status=status, content_type=content_type)


class Router(archivalrouter.ArchivalRouter):
    def __call__(self, env):
        """
            Before routing requests, make sure that host is equal to WARC_HOST or DIRECT_WARC_HOST if set.
        """
        if settings.WARC_HOST and env.get('HTTP_HOST') != settings.WARC_HOST and not \
                (settings.DIRECT_WARC_HOST and env.get('HTTP_HOST') == settings.DIRECT_WARC_HOST):
            raise DisallowedHost("Playback request used invalid domain.")
        return super(Router, self).__call__(env)


#=================================================================
def create_perma_pywb_app(config):
    """
        Configure server.

        This should do basically the same stuff as pywb.webapp.pywb_init.create_wb_router()
    """
    # paths
    script_path = os.path.dirname(__file__)

    # Get root storage location for warcs.
    # archive_path should be the location pywb can find warcs, like 'file://generated/' or 'http://perma.s3.amazonaws.com/generated/'
    # We can get it by requesting the location of a blank file from default_storage.
    # default_storage may use disk or network storage depending on config, so we look for either a path() or url()
    try:
        archive_path = 'file://' + default_storage.path('') + '/'
    except NotImplementedError:
        archive_path = default_storage.url('/')
        archive_path = archive_path.split('?', 1)[0]  # remove query params

    query_handler = QueryHandler.init_from_config(settings.CDX_SERVER_URL)

    # pywb template vars (used in templates called by pywb, such as head_insert.html, but not our ErrorTemplateView)
    add_env_globals({'static_path': settings.STATIC_URL})

    # use util func to create the handler
    wb_handler = create_wb_handler(query_handler,
                                   dict(archive_paths=[archive_path],
                                        wb_handler_class=Handler,
                                        buffer_response=True,

                                        head_insert_html=os.path.join(script_path, 'head_insert.html'),

                                        redir_to_exact=False))


    # Finally, create wb router
    return Router(
        {
            Route(r'([a-zA-Z0-9\-]+)', wb_handler)
        },
        # Specify hostnames that pywb will be running on
        # This will help catch occasionally missed rewrites that fall-through to the host
        # (See archivalrouter.ReferRedirect)
        hostpaths=['http://localhost:8000/'],
        port=8000,
        error_view=ErrorTemplateView()
    )

