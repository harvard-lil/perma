import Cookie
import StringIO
from collections import defaultdict
from contextlib import contextmanager

import os
import random
import threading
import re
from urlparse import urljoin
from pywb.rewrite.header_rewriter import HeaderRewriter
import requests
from surt import surt

# configure Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "perma.settings")
import django
django.setup()

from django.conf import settings
from django.template.loader import get_template
from django.core.files.storage import default_storage
from django.core.exceptions import DisallowedHost
from django.core.cache import cache as django_cache
from django.apps import apps

from pywb.cdx.cdxserver import CDXServer
from pywb.cdx.cdxsource import CDXSource
from pywb.framework import archivalrouter
from pywb.framework.wbrequestresponse import WbResponse
from pywb.framework.memento import MementoResponse, make_timemap, LINK_FORMAT
from pywb.rewrite.wburl import WbUrl
from pywb.utils.loaders import BlockLoader, LimitReader
from pywb.webapp.handlers import WBHandler
from pywb.webapp.query_handler import QueryHandler
from pywb.webapp.pywb_init import create_wb_handler
from pywb.webapp.views import MementoTimemapView
from pywb.webapp.pywb_init import create_wb_router
from pywb.utils.wbexception import NotFoundException

from perma.utils import opbeat_trace

# Use lazy model imports because Django models aren't ready yet when this file is loaded by wsgi.py
CDXLine = apps.get_model('perma', 'CDXLine')
Link = apps.get_model('perma', 'Link')
Mirror = apps.get_model('lockss', 'Mirror')

import logging
logger = logging.getLogger(__name__)


newstyle_guid_regex = r'[A-Z0-9]{1,4}(-[A-Z0-9]{4})+'  # post Nov. 2013
oldstyle_guid_regex = r'0[a-zA-Z0-9]{9,10}'  # pre Nov. 2013
GUID_REGEX = r'(%s|%s)' % (oldstyle_guid_regex, newstyle_guid_regex)
WARC_STORAGE_PATH = os.path.join(settings.MEDIA_ROOT, settings.WARC_STORAGE_DIR)
thread_local_data = threading.local()

@contextmanager
def close_database_connection():
    """
        Normally Django closes its connections at the end of the request.
        Here there's no Django request, so if we use the DB we close it manually.
        See http://stackoverflow.com/a/1346401/307769
    """
    try:
        yield
    finally:
        if settings.TESTING:
            return
        from django.db import connection
        connection.close()

def get_archive_path():
    # Get root storage location for warcs, based on default_storage.
    # archive_path should be the location pywb can find warcs, like 'file://generated/' or 'http://perma.s3.amazonaws.com/generated/'
    # We can get it by requesting the location of a blank file from default_storage.
    # default_storage may use disk or network storage depending on config, so we look for either a path() or url()
    try:
        archive_path = 'file://' + default_storage.path('') + '/'
    except NotImplementedError:
        archive_path = default_storage.url('/')
        archive_path = archive_path.split('?', 1)[0]  # remove query params

    # must be ascii, for some reason, else you'll get
    # 'unicode' object has no attribute 'get'
    return archive_path.encode('ascii', 'ignore')

def raise_not_found(url):
    raise NotFoundException('No Captures found for: %s' % url, url=url)

# include guid in CDX requests
class PermaRoute(archivalrouter.Route):
    @opbeat_trace()
    def apply_filters(self, wbrequest, matcher):
        """Parse the GUID and find the CDXLine in the DB"""

        guid = matcher.group(1)
        cache_key = Link.get_cdx_cache_key(guid)
        cached_cdx = django_cache.get(cache_key)
        redirect_matcher = re.compile(r' 30[1-7] ')
        if cached_cdx is None or not wbrequest.wb_url:
            with opbeat_trace('cdx-cache-miss'), close_database_connection():
                try:
                    # This will filter out links that have user_deleted=True
                    link = Link.objects.get(guid=guid)
                except Link.DoesNotExist:
                    raise_not_found(wbrequest.wb_url)

                if not wbrequest.wb_url:
                    # This is a bare request to /warc/1234-5678/ -- return so we can send a forward to submitted_url in PermaGUIDHandler.
                    wbrequest.custom_params['guid'] = guid
                    wbrequest.custom_params['url'] = link.safe_url
                    return

                # Legacy archives didn't generate CDXLines during
                # capture so generate them on demand if not found, unless
                # A: the warc capture hasn't been generated OR
                # B: we know other cdx lines have already been generated
                #    and the requested line is simply missing
                lines = CDXLine.objects.filter(link_id=link.guid)

                if not lines:
                    lines = CDXLine.objects.create_all_from_link(link)

                # build a lookup of all cdx lines for this link indexed by urlkey, like:
                # cached_cdx = {'urlkey1':['raw1','raw2'], 'urlkey2':['raw3','raw4']}
                cached_cdx = defaultdict(list)
                for line in lines:
                    cached_cdx[line.urlkey].append(str(line.raw))

                # remove any redirects if we also have a non-redirect capture for the same URL, to prevent redirect loops
                for urlkey, lines in cached_cdx.iteritems():
                    if len(lines) > 1:
                        lines_without_redirects = [line for line in lines if not redirect_matcher.search(line)]
                        if lines_without_redirects:
                            cached_cdx[urlkey] = lines_without_redirects

                # record whether link is private so we can enforce permissions
                cached_cdx['is_private'] = link.is_private

                django_cache.set(cache_key, cached_cdx)

        # enforce permissions
        if cached_cdx.get('is_private'):
            # if user is allowed to access this private link, they will have a cookie like GUID=<token>,
            # which can be validated with link.validate_access_token()
            cookie = Cookie.SimpleCookie(wbrequest.env.get('HTTP_COOKIE')).get(guid)
            valid_token = cookie and Link(pk=guid).validate_access_token(cookie.value, 3600)
            if not valid_token:
                raise_not_found(wbrequest.wb_url)

        # check whether archive contains the requested URL
        urlkey = surt(wbrequest.wb_url.url)
        cdx_lines = cached_cdx.get(urlkey)
        if not cdx_lines:
            raise_not_found(wbrequest.wb_url)

        # Store the line for use in PermaCDXSource
        # so we don't need to hit the DB again
        wbrequest.custom_params['lines'] = cdx_lines
        wbrequest.custom_params['guid'] = guid

        # Adds the Memento-Datetime header
        # Normally this is done in MementoReqMixin#_parse_extra
        # but we need the GUID to make the DB query and that
        # isn't parsed from the url until this point
        wbrequest.wb_url.set_replay_timestamp(CDXLine(raw=cdx_lines[0]).timestamp)


# prevent mod getting added to rewritten urls
# timestamp already disabled via 'redir_to_exact' flag
class PermaUrl(WbUrl):
    def to_str(self, **overrides):
        overrides['mod'] = ''
        overrides['timestamp'] = ''
        return super(PermaUrl, self).to_str(**overrides)


class PermaMementoResponse(MementoResponse):
    def _init_derived(self, params):
        """
            Override MementoResponse to set cache time based on type of response (single memento or timegate).
        """
        # is_timegate logic via super _init_derived function:
        wbrequest = params.get('wbrequest')
        if not wbrequest or not wbrequest.wb_url:
            return
        is_top_frame = wbrequest.options.get('is_top_frame', False)
        is_timegate = (wbrequest.options.get('is_timegate', False) and not is_top_frame)

        # set cache time
        cache_time = settings.CACHE_MAX_AGES["timegate"] if is_timegate else settings.CACHE_MAX_AGES["memento"]
        self.status_headers.headers.append(('Cache-Control', 'max-age={}'.format(cache_time)))

        return super(PermaMementoResponse, self)._init_derived(params)


class PermaGUIDMementoResponse(PermaMementoResponse):
    def make_link(self, url, type):
        if type == 'timegate':
            # Remove the GUID from the url using regex since
            # we don't have access to the request or params here
            url = re.compile(GUID_REGEX+'/').sub('', url, 1)
            url = url.replace(settings.WARC_ROUTE, settings.TIMEGATE_WARC_ROUTE)
        return '<{0}>; rel="{1}"'.format(url, type)

    def make_timemap_link(self, wbrequest):
        url = super(PermaMementoResponse, self).make_timemap_link(wbrequest)
        url = url.replace(wbrequest.custom_params['guid']+'/', '', 1)
        return url


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

    def handle_request(self, wbrequest):
        # include wbrequest in thread locals for later access
        wbrequest.mirror_name = None
        thread_local_data.wbrequest = wbrequest
        return super(PermaHandler, self).handle_request(wbrequest)


class PermaGUIDHandler(PermaHandler):
    def __init__(self, query_handler, config=None):
        super(PermaGUIDHandler, self).__init__(query_handler, config)
        self.response_class = PermaGUIDMementoResponse

    def __call__(self, wbrequest):
        """
            If someone requests a bare GUID url like /warc/1234-5678/, forward them to the submitted_url playback for that GUID.
        """
        if wbrequest.wb_url_str == '/':
            return WbResponse.redir_response("/%s/%s/%s" % (settings.WARC_ROUTE, wbrequest.custom_params['guid'], wbrequest.custom_params['url']), status='301 Moved Permanently')
        return super(PermaGUIDHandler, self).__call__(wbrequest)

    def _init_replay_view(self, config):
        replay_view = super(PermaGUIDHandler, self)._init_replay_view(config)
        replay_view.response_class = PermaGUIDMementoResponse
        return replay_view

    def get_wburl_type(self):
        return PermaUrl


class PermaMementoTimemapView(MementoTimemapView):
    """
        Returns a timemap response, basically a list of links.
        One of the links is type timegate, so we have to rewrite the '/timegate' route by hand, as pywb only expects
        one wb_prefix (in our case, '/warc') for timegate, memento, and timemap.
    """
    def fix_timegate_line(self, memento_lines):
        for line in memento_lines:
            if 'rel="timegate"' in line:
                line = line.replace(settings.WARC_ROUTE, settings.TIMEGATE_WARC_ROUTE)
            yield line

    def render_response(self, wbrequest, cdx_lines, **kwargs):
        memento_lines = make_timemap(wbrequest, cdx_lines)

        new_memento_lines = self.fix_timegate_line(memento_lines)

        response = WbResponse.text_stream(new_memento_lines, content_type=LINK_FORMAT, )
        response.status_headers.headers.append(('Cache-Control',
                                                'max-age={}'.format(settings.CACHE_MAX_AGES['timemap'])))

        return response


class PermaTemplateView(object):
    def __init__(self, filename):
        self.template = get_template(filename)

    def render_to_string(self, **kwargs):
        return unicode(self.template.render(kwargs))

    def render_response(self, **kwargs):
        template_result = self.render_to_string(**dict(kwargs,
                                                       STATIC_URL=settings.STATIC_URL,
                                                       DEBUG=settings.DEBUG))
        status = kwargs.get('status', '200 OK')
        content_type = kwargs.get('content_type', 'text/html; charset=utf-8')
        return WbResponse.text_response(template_result, status=status, content_type=content_type)


class PermaCapturesView(PermaTemplateView):
    def render_response(self, wbrequest, cdx_lines, **kwargs):
        response = PermaTemplateView.render_response(self,
                                                     cdx_lines=list(cdx_lines),
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
            return query.params['lines']

        filters = {
            'urlkey': query.key,
            'is_unlisted': False,
            'is_private': False,
        }
        if query.params.get('guid'):
            filters['link_id'] = query.params['guid']

        return [str(i) for i in CDXLine.objects.filter(**filters).values_list('raw', flat=True)]


class CachedLoader(BlockLoader):
    """
        File loader that stores requested file in key-value cache for quick retrieval.
    """
    @opbeat_trace()
    def load(self, url, offset=0, length=-1):

        # first try to fetch url contents from cache
        cache_key = Link.get_warc_cache_key(url.split(settings.MEDIA_ROOT,1)[-1])


        mirror_name_cache_key = cache_key+'-mirror-name'
        mirror_name = ''

        file_contents = django_cache.get(cache_key)

        if file_contents is None:
            # url wasn't in cache -- load contents

            with opbeat_trace('file-loader-cache-miss'):

                # try fetching from each mirror in the LOCKSS network, in random order
                if settings.USE_LOCKSS_REPLAY:

                    mirrors = Mirror.get_cached_mirrors()
                    random.shuffle(mirrors)

                    for mirror in mirrors:
                        lockss_key = url.replace('file://', '').replace(WARC_STORAGE_PATH, 'https://' + settings.HOST + '/lockss/fetch')
                        lockss_url = urljoin(mirror['content_url'], 'ServeContent')
                        try:
                            logging.info("Fetching from %s?url=%s" % (lockss_url, lockss_key))
                            response = requests.get(lockss_url, params={'url': lockss_key})
                            assert response.ok
                            file_contents = response.content
                            mirror_name = mirror['name']
                            logging.info("Got content from lockss")
                        except (requests.ConnectionError, requests.Timeout, AssertionError) as e:
                            logging.info("Couldn't get from lockss: %s" % e)

                # If url wasn't in LOCKSS yet or LOCKSS is disabled, fetch from local storage using super()
                if file_contents is None:
                    file_contents = super(CachedLoader, self).load(url).read()
                    logging.info("Got content from local disk")

                # cache file contents
                # use a short timeout so large warcs don't evict everything else in the cache
                django_cache.set(cache_key, file_contents, timeout=60)
                django_cache.set(mirror_name_cache_key, mirror_name, timeout=60)

        else:
            mirror_name = django_cache.get(mirror_name_cache_key)

        # set wbrequest.mirror_name so it can be displayed in template later
        thread_local_data.wbrequest.mirror_name = mirror_name

        # turn string contents of url into file-like object
        afile = StringIO.StringIO(file_contents)

        # --- from here down is taken from super() ---
        if offset > 0:
            afile.seek(offset)

        if length >= 0:
            return LimitReader(afile, length)
        else:
            return afile


# Monkey patch HeaderRewriter to remove the content-disposition header
# if content-type is PDF, so that PDFs display in the browser instead of downloading.
orig_HeaderRewriter_rewrite = HeaderRewriter.rewrite
def new_rewrite(self, status_headers, urlrewriter, cookie_rewriter):
    result = orig_HeaderRewriter_rewrite(self, status_headers, urlrewriter, cookie_rewriter)
    if status_headers.get_header('Content-Type') == 'application/pdf':
        content_disposition = status_headers.get_header('Content-Disposition')
        if content_disposition and 'attachment' in content_disposition:
            result.status_headers.headers = [h for h in result.status_headers.headers if h[0].lower() != 'content-disposition']
            result.removed_header_dict['content-disposition'] = content_disposition
            result.status_headers.headers.append((self.header_prefix + 'Content-Disposition', content_disposition))
    return result
HeaderRewriter.rewrite = new_rewrite


# =================================================================
def create_perma_wb_router(config={}):
    """
        Configure server.

        This should do basically the same stuff as pywb.webapp.pywb_init.create_wb_router()
    """
    # start with the default PyWB router
    router = create_wb_router(config)

    # insert a custom route that knows how to play back based on GUID
    wb_handler = create_wb_handler(QueryHandler.init_from_config(PermaCDXSource()),
                                   dict(archive_paths=[get_archive_path()],
                                        wb_handler_class=PermaGUIDHandler,
                                        buffer_response=True,
                                        # head_insert_html=os.path.join(os.path.dirname(__file__), 'head_insert.html'),
                                        enable_memento=True,
                                        redir_to_exact=False))
    wb_handler.replay.content_loader.record_loader.loader = CachedLoader()
    route = PermaRoute(GUID_REGEX, wb_handler)
    router.routes.insert(0, route)

    # use our Django error view
    router.error_view = PermaTemplateView('archive/archive-error.html')
    wb_handler.not_found_view = router.error_view

    return router
