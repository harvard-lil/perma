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
from pywb.framework.memento import MementoResponse
from pywb.rewrite.wburl import WbUrl
from pywb.utils.loaders import BlockLoader, LimitReader
from pywb.webapp.handlers import WBHandler
from pywb.webapp.query_handler import QueryHandler
from pywb.webapp.pywb_init import create_wb_handler
from pywb.webapp.views import add_env_globals, MementoTimemapView
from pywb.webapp.pywb_init import create_wb_router
from pywb.utils.wbexception import NotFoundException

from perma.models import CDXLine, Asset, Link

# Assumes post November 2013 GUID format
GUID_REGEX = r'([a-zA-Z0-9]+(-[a-zA-Z0-9]+)+)'


# include guid in CDX requests
class PermaRoute(archivalrouter.Route):
    def apply_filters(self, wbrequest, matcher):
        """Parse the GUID and find the CDXLine in the DB"""

        guid = matcher.group(1)
        urlkey = surt(wbrequest.wb_url.url)

        try:
            # This will filter out links that have user_deleted=True
            link = Link.objects.get(guid=guid)
        except Link.DoesNotExist:
            raise NotFoundException()

        lines = CDXLine.objects.filter(urlkey=urlkey, asset__link_id=guid)

        # Legacy archives didn't generate CDXLines during
        # capture so generate them on demand if not found, unless
        # A: the warc capture hasn't been generated OR
        # B: we know other cdx lines have already been generated
        #    and the requested line is simply missing
        if lines.count() == 0:
            asset = Asset.objects.get(link_id=guid)
            if asset.warc_capture in [Asset.CAPTURE_STATUS_PENDING, Asset.CAPTURE_STATUS_FAILED] or asset.cdx_lines.count() > 0:
                raise NotFoundException()

            CDXLine.objects.create_all_from_asset(asset)
            lines = CDXLine.objects.filter(urlkey=urlkey, asset__link_id=guid)
            if not len(lines):
                raise NotFoundException()

        # Store the line for use in PermaCDXSource
        # so we don't need to hit the DB again
        wbrequest.custom_params['lines'] = lines
        wbrequest.custom_params['guid'] = guid

        # Adds the Memento-Datetime header
        # Normally this is done in MementoReqMixin#_parse_extra
        # but we need the GUID to make the DB query and that
        # isn't parsed from the url until this point
        wbrequest.wb_url.set_replay_timestamp(lines.first().timestamp)


# prevent mod getting added to rewritten urls
# timestamp already disabled via 'redir_to_exact' flag
class PermaUrl(WbUrl):
    def to_str(self, **overrides):
        overrides['mod'] = ''
        overrides['timestamp'] = ''
        return super(PermaUrl, self).to_str(**overrides)


class PermaMementoResponse(MementoResponse):
    def _init_derived(self, params):
        self.set_cache_header(params)
        super(PermaMementoResponse, self)._init_derived(params)

    # is_x logic taken verbatim from MementoResponse#_init_derived
    def set_cache_header(self, params):
        is_timegate = False
        is_memento = False

        wbrequest = params.get('wbrequest')
        cdx = params.get('cdx')

        if wbrequest and wbrequest.wb_url:

            is_top_frame = wbrequest.wb_url.is_top_frame

            is_timegate = (wbrequest.options.get('is_timegate', False) and
                           not is_top_frame)

            # if no cdx included, not a memento, unless top-frame special
            if not cdx:
                # special case: include the headers but except Memento-Datetime
                # since this is really an intermediate resource
                if is_top_frame:
                    is_memento = True

            # otherwise, if in proxy mode, then always a memento
            elif wbrequest.options['is_proxy']:
                is_memento = True

            # otherwise only if timestamp replay (and not a timegate)
            elif not is_timegate:
                is_memento = (wbrequest.wb_url.type == wbrequest.wb_url.REPLAY)

        if is_timegate:
            req_type = 'timegate'
        elif is_memento:
            req_type = 'memento'
        else:
            req_type = 'default'

        self.status_headers.headers.append(('Cache-Control',
                                            'max-age={}'.format(settings.CACHE_MAX_AGES[req_type])))


class PermaGUIDMementoResponse(PermaMementoResponse):
    def make_link(self, url, type):
        if type == 'timegate':
            # Remove the GUID from the url using regex since
            # we don't have access to the request or params here
            url = re.compile(GUID_REGEX+'/').sub('', url, 1)
        return '<{0}>; rel="{1}"'.format(url, type)

    def make_timemap_link(self, wbrequest):
        url = super(PermaMementoResponse, self).make_timemap_link(wbrequest)
        return url.replace(wbrequest.custom_params['guid']+'/', '', 1)


class PermaHandler(WBHandler):
    """ A roundabout way of using a custom class for query_handler views since pywb provides no config option for those properties """
    def __init__(self, query_handler, config=None):
        # Renders our Perma styled Timemap HTML with Cache-Control header
        query_handler.views['html'] = PermaCapturesView('memento/query.html')
        # Renders the Timemap plain text download with Cache-Control header
        query_handler.views['timemap'] = PermaMementoTimemapView()
        super(PermaHandler, self).__init__(query_handler, config)
        self.response_class = PermaMementoResponse

    def _init_replay_view(self, config):
        replay_view = super(PermaHandler, self)._init_replay_view(config)
        replay_view.response_class = PermaMementoResponse
        return replay_view


class PermaGUIDHandler(PermaHandler):
    def __init__(self, query_handler, config=None):
        super(PermaGUIDHandler, self).__init__(query_handler, config)
        self.response_class = PermaGUIDMementoResponse

    def _init_replay_view(self, config):
        replay_view = super(PermaGUIDHandler, self)._init_replay_view(config)
        replay_view.response_class = PermaGUIDMementoResponse
        return replay_view

    def get_wburl_type(self):
        return PermaUrl


class PermaMementoTimemapView(MementoTimemapView):
    def render_response(self, wbrequest, cdx_lines, **kwargs):
        response = super(PermaMementoTimemapView, self).render_response(wbrequest, cdx_lines, **kwargs)
        response.status_headers.headers.append(('Cache-Control',
                                                'max-age={}'.format(settings.CACHE_MAX_AGES['timemap'])))
        return response


class PermaTemplateView(object):
    def __init__(self, filename):
        self.template = get_template(filename)

    def render_to_string(self, **kwargs):
        return unicode(self.template.render(Context(kwargs)))

    def render_response(self, **kwargs):
        template_result = self.render_to_string(**dict(kwargs,
                                                       STATIC_URL=settings.STATIC_URL,
                                                       DEBUG=settings.DEBUG))
        status = kwargs.get('status', '200 OK')
        content_type = kwargs.get('content_type', 'text/html; charset=utf-8')
        return WbResponse.text_response(template_result.encode('utf-8'), status=status, content_type=content_type)


class PermaCapturesView(PermaTemplateView):
    def render_response(self, wbrequest, cdx_lines, **kwargs):
        def format_cdx_lines():
            for cdx in cdx_lines:
                cdx['url'] = wbrequest.wb_url.get_url(url=cdx['original'])
                yield cdx

        response = PermaTemplateView.render_response(self,
                                                     cdx_lines=list(format_cdx_lines()),
                                                     url=wbrequest.wb_url.get_url(),
                                                     type=wbrequest.wb_url.type,
                                                     prefix=wbrequest.wb_prefix,
                                                     **kwargs)

        response.status_headers.headers.append(('Cache-Control',
                                                'max-age={}'.format(settings.CACHE_MAX_AGES['timemap'])))
        return response


class PermaRouter(archivalrouter.ArchivalRouter):
    def __call__(self, env):
        """
            Before routing requests, make sure that host is equal to WARC_HOST.
        """
        if settings.WARC_HOST and env.get('HTTP_HOST') != settings.WARC_HOST:
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
        # When a GUID is in the url, we'll have already queried for the lines
        # in order to grab the timestamp for Memento-Datetime header
        if query.params.get('lines'):
            return query.params.get('lines').values_list('raw', flat=True)

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
                                        wb_handler_class=PermaGUIDHandler,
                                        buffer_response=True,
                                        head_insert_html=os.path.join(script_path, 'head_insert.html'),
                                        enable_memento=True,
                                        redir_to_exact=False))

    wb_handler.replay.content_loader.record_loader.loader = CachedLoader()

    route = PermaRoute(GUID_REGEX, wb_handler)

    router = create_wb_router(config)
    router.error_view = PermaTemplateView('archive-error.html')
    router.routes.insert(0, route)

    return router
