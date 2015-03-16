import StringIO
import os
import re
from surt import surt

# configure Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "perma.settings")
import django
django.setup()

from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from django.core.files.storage import default_storage
from django.core.exceptions import DisallowedHost
from django.core.cache import cache as django_cache

from pywb.cdx.cdxserver import CDXServer
from pywb.cdx.cdxsource import CDXSource
from pywb.framework import archivalrouter
from pywb.framework.wbrequestresponse import WbResponse
from pywb.framework.memento import MementoResponse, LINK_FORMAT
from pywb.rewrite.wburl import WbUrl
from pywb.utils.loaders import BlockLoader, LimitReader
from pywb.webapp.handlers import WBHandler
from pywb.webapp.query_handler import QueryHandler
from pywb.webapp.pywb_init import create_wb_handler
from pywb.webapp.views import add_env_globals
from pywb.webapp.pywb_init import create_wb_router

from perma.models import CDXLine, Asset

# Assumes post November 2013 GUID format
GUID_REGEX = r'([a-zA-Z0-9]+(-[a-zA-Z0-9]+)+)'


# include guid in CDX requests
class PermaRoute(archivalrouter.Route):
    def apply_filters(self, wbrequest, matcher):
        """Parse the GUID and find the CDXLine in the DB"""

        guid = matcher.group(1)
        urlkey = surt(wbrequest.wb_url_str)

        # Legacy archives didn't generate CDXLines during
        # capture so generate them on demand if not found
        try:
            line = CDXLine.objects.get(urlkey=urlkey,
                                       asset__link_id=guid)
        except CDXLine.DoesNotExist:
            asset = Asset.objects.get(link_id=guid)
            lines = CDXLine.objects.create_all_from_asset(asset)
            line = next(line for line in lines if line.urlkey==urlkey)

        # Store the line for use in PermaCDXSource
        # so we don't need to hit the DB again
        wbrequest.custom_params['line'] = line
        wbrequest.custom_params['guid'] = guid

        # Adds the Memento-Datetime header
        # Normally this is done in MementoReqMixin#_parse_extra
        # but we need the GUID to make the DB query and that
        # isn't parsed from the url until this point
        wbrequest.wb_url.set_replay_timestamp(line.timestamp)


# prevent mod getting added to rewritten urls
# timestamp already disabled via 'redir_to_exact' flag
class PermaUrl(WbUrl):
    def to_str(self, **overrides):
        overrides['mod'] = ''
        overrides['timestamp'] = ''
        return WbUrl.to_str(self, **overrides)


class PermaMementoResponse(MementoResponse):
    def make_link(self, url, type):
        if type == 'timegate':
            # Remove the GUID from the url using regex since
            # we don't have access to the request or params here
            url = re.compile(GUID_REGEX+'/').sub('', url, 1)
        return '<{0}>; rel="{1}"'.format(url, type)

    def make_timemap_link(self, wbrequest):
        format_ = '<{0}>; rel="timemap"; type="{1}"'

        url = wbrequest.urlrewriter.get_new_url(mod='timemap',
                                                timestamp='',
                                                type=wbrequest.wb_url.QUERY)

        # Remove the GUID from the url
        url = url.replace(wbrequest.custom_params['guid']+'/', '', 1)
        return format_.format(url, LINK_FORMAT)


class PermaHandler(WBHandler):
    def __init__(self, query_handler, config=None):
        super(PermaHandler, self).__init__(query_handler, config)
        self.response_class = PermaMementoResponse

    def _init_replay_view(self, config):
        replay_view = super(PermaHandler, self)._init_replay_view(config)
        replay_view.response_class = PermaMementoResponse
        return replay_view

    def get_wburl_type(self):
        return PermaUrl


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


class PermaRouter(archivalrouter.ArchivalRouter):
    def __call__(self, env):
        """
            Before routing requests, make sure that host is equal to WARC_HOST or DIRECT_WARC_HOST if set.
        """
        if settings.WARC_HOST and env.get('HTTP_HOST') != settings.WARC_HOST and not \
                (settings.DIRECT_WARC_HOST and env.get('HTTP_HOST') == settings.DIRECT_WARC_HOST):
            raise DisallowedHost("Playback request used invalid domain.")
        return super(PermaRouter, self).__call__(env)


class PermaCDXServer(CDXServer):
    def _create_cdx_source(self, filename, config):
        if filename == 'PermaCDXSource':
            return PermaCDXSource()
        return super(PermaCDXServer, self)._create_cdx_source(filename, config)


class PermaCDXSource(CDXSource):
    def load_cdx(self, query):
        """
            This function accepts a standard CDX request, except with a GUID instead of date, and returns a standard CDX 11 response.
        """
        # When a GUID is in the url, we'll have already queried for the line
        # in order to grab the timestamp for Memento-Datetime header
        if query.params.get('line'):
            return (query.params.get('line').raw,)

        filters = {'urlkey': query.key}
        if query.params.get('guid'):
            filters['asset__link_id'] = query.params.get('guid')

        return CDXLine.objects.filter(**filters).values_list('raw', flat=True)


class CachedLoader(BlockLoader):
    """
        File loader that stores requested file in key-value cache for quick retrieval.
    """
    def load(self, url, offset=0, length=-1):
        # first try to fetch url contents from cache
        cache_key = 'warc-'+re.sub('[^\w-]', '', url)
        file_contents = django_cache.get(cache_key)
        if not file_contents:
            # url wasn't in cache -- fetch entire contents of url from super() and put in cache
            file_contents = super(CachedLoader, self).load(url).read()
            django_cache.set(cache_key, file_contents, timeout=60)  # use a short timeout so large warcs don't evict everything else in the cache

        # turn string contents of url into file-like object
        afile = StringIO.StringIO(file_contents)

        # --- from here down is taken from super() ---
        if offset > 0:
            afile.seek(offset)

        if length >= 0:
            return LimitReader(afile, length)
        else:
            return afile


# =================================================================
def create_perma_wb_router(config={}):
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

    query_handler = QueryHandler.init_from_config(PermaCDXSource())

    # pywb template vars (used in templates called by pywb, such as head_insert.html, but not our ErrorTemplateView)
    add_env_globals({'static_path': settings.STATIC_URL})

    # use util func to create the handler
    wb_handler = create_wb_handler(query_handler,
                                   dict(archive_paths=[archive_path],
                                        wb_handler_class=PermaHandler,
                                        buffer_response=True,
                                        head_insert_html=os.path.join(script_path, 'head_insert.html'),
                                        enable_memento=True,
                                        redir_to_exact=False))

    wb_handler.replay.content_loader.record_loader.loader = CachedLoader()

    route = PermaRoute(GUID_REGEX, wb_handler)

    router = create_wb_router(config)
    router.error_view = ErrorTemplateView()
    router.routes.insert(0, route)

    return router
