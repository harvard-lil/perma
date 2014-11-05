import StringIO
from itertools import groupby
import json
import os
import re
from surt import surt

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "perma.settings")
from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from django.core.files.storage import default_storage
from django.core.exceptions import DisallowedHost
from django.core.cache import cache as django_cache

from pywb.cdx.cdxsource import CDXSource
from pywb.framework import archivalrouter
from pywb.framework.wbrequestresponse import WbResponse
from pywb.rewrite.wburl import WbUrl
from pywb.utils.loaders import BlockLoader, LimitReader
from pywb.warc.cdxindexer import write_cdx_index
from pywb.webapp.handlers import WBHandler
from pywb.webapp.query_handler import QueryHandler
from pywb.webapp.pywb_init import create_wb_handler
from pywb.webapp.views import add_env_globals

from perma.models import Link


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
            Before routing requests, make sure that host is equal to WARC_HOST if set.
        """
        if settings.WARC_HOST and env.get('HTTP_HOST') != settings.WARC_HOST:
            raise DisallowedHost("Playback request used invalid domain.")
        return super(Router, self).__call__(env)


class PermaCDXSource(CDXSource):
    def load_cdx(self, query):
        """
            This function accepts a standard CDX request, except with a GUID instead of date, and returns a standard CDX 11 response.
        """
        guid = query.params['guid']
        url = query.url

        # We'll first check the key-value store to see if we cached the lookup for this guid on a previous request.
        # This will be common, since each playback triggers lots of requests for the same .warc file.
        cache_key = guid + '-surts'
        url_key = guid+'-url'
        surt_lookup = django_cache.get(cache_key)
        url = url or django_cache.get(url_key)
        if surt_lookup and url:
            print "USING CACHE"
            surt_lookup = json.loads(surt_lookup)

        else:
            # nothing in cache; find requested link in database
            try:
                link = Link.objects.select_related().get(pk=guid)
            except Link.DoesNotExist:
                print "COULDN'T FIND LINK"
                return []

            # cache url, which may be blank if this is the first request
            if not url:
                url = link.submitted_url
            django_cache.set(url_key, url, timeout=60*60)

            # get warc file
            for asset in link.assets.all():
                if '.warc' in asset.warc_capture:
                    warc_path = os.path.join(asset.base_storage_path, asset.warc_capture)
                    break
            else:
                print "COULDN'T FIND WARC"
                return []  # no .warc file -- do something to handle this?

            # now we have to get an index of all the URLs in this .warc file
            # first try fetching it from a .cdx file on disk
            cdx_path = warc_path.replace('.gz', '').replace('.warc', '.cdx')

            if not default_storage.exists(cdx_path):
                # there isn't a .cdx file on disk either -- let's create it
                print "REGENERATING CDX"
                with default_storage.open(warc_path, 'rb') as warc_file, default_storage.open(cdx_path, 'wb') as cdx_file:
                    write_cdx_index(cdx_file, warc_file, warc_path, sort=True)

            # now load the URL index from disk and stick it in the cache
            print "LOADING FROM DISK"
            cdx_lines = (line.strip() for line in default_storage.open(cdx_path, 'rb'))
            surt_lookup = dict((key, list(val)) for key, val in groupby(cdx_lines, key=lambda line: line.split(' ', 1)[0]))
            django_cache.set(cache_key, json.dumps(surt_lookup), timeout=60*60)

        # find cdx lines for url
        sorted_url = surt(url)
        if sorted_url in surt_lookup:
            return (str(i) for i in surt_lookup[sorted_url])

        # didn't find requested url in this archive
        print "COULDN'T FIND URL"
        return []


class CachedLoader(BlockLoader):
    """
        File loader that stores requested file in key-value cache for quick retrieval.
    """
    def load(self, url, offset=0, length=-1):
        # first try to fetch url contents from cache
        cache_key = 'warc-'+re.sub('[^\w-]', '', url)
        file_contents = django_cache.get(cache_key)
        if file_contents:
            print "USING CACHED WARC"

        else:
            # url wasn't in cache -- fetch entire contents of url from super() and put in cache
            file_contents = super(CachedLoader, self).load(url).read()
            django_cache.set(cache_key, file_contents, timeout=60)  # use a short timeout so large warcs don't evict everything else in the cache
            print "LOADED AND CACHED WARC"

        # turn string contents of url into file-like object
        afile = StringIO.StringIO(file_contents)

        # proceed as in the normal BlockLoader
        if offset > 0:
            afile.seek(offset)

        if length >= 0:
            return LimitReader(afile, length)
        else:
            return afile


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

    query_handler = QueryHandler.init_from_config(PermaCDXSource())

    # pywb template vars (used in templates called by pywb, such as head_insert.html, but not our ErrorTemplateView)
    add_env_globals({'static_path': settings.STATIC_URL})

    # use util func to create the handler
    wb_handler = create_wb_handler(query_handler,
                                   dict(archive_paths=[archive_path],
                                        wb_handler_class=Handler,
                                        buffer_response=True,

                                        head_insert_html=os.path.join(script_path, 'head_insert.html'),

                                        redir_to_exact=False))

    wb_handler.replay.content_loader.record_loader.loader = CachedLoader()

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

