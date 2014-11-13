from django.db.models import Q
import operator

        
class favicon:
    
    def get_favicon(target_url, parsed_html, link_guid, disk_path, url_details):
        """ Given a URL and the markup, see if we can find a favicon.
            TODO: this is a rough draft. cleanup and move to an appropriate place. """

        # We already have the parsed HTML, let's see if there is a favicon in the META elements
        favicons = parsed_html.xpath('//link[@rel="icon"]/@href')

        favicon = False

        if len(favicons) > 0:
            favicon = favicons[0]

        if not favicon:
            favicons = parsed_html.xpath('//link[@rel="shortcut"]/@href')
            if len(favicons) > 0:
                favicon = favicons[0]

        if not favicon:
            favicons = parsed_html.xpath('//link[@rel="shortcut icon"]/@href')
            if len(favicons) > 0:
                favicon = favicons[0]

        if favicon:

            if re.match(r'^//', favicon):
                favicon = url_details.scheme + ':' + favicon
            elif not re.match(r'^http', favicon):
                favicon = url_details.scheme + '://' + url_details.netloc + '/' + favicon

            try:
              f = urllib2.urlopen(favicon)
              data = f.read()

              with open(disk_path + 'fav.png', "wb") as asset:
                asset.write(data)

              return 'fav.png'
            except urllib2.HTTPError:
              pass

        # If we haven't returned True above, we didn't find a favicon in the markup.
        # let's try the favicon convention: http://example.com/favicon.ico
        target_favicon_url = url_details.scheme + '://' + url_details.netloc + '/favicon.ico'

        try:
            f = urllib2.urlopen(target_favicon_url)
            data = f.read()
            with open(disk_path + 'fav.ico' , "wb") as asset:
                asset.write(data)

            return 'fav' + '.ico'
        except urllib2.HTTPError:
            pass


        return False



### require_group decorator ###

from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.conf import settings

def require_group(group, redirect_url=settings.LOGIN_REDIRECT_URL):
    """
        Require user to be logged in and belong to group with given name.
        If group is a list, user must have one of the named groups.
        If user does not belong to group, they will be sent to redirect_url.
    """
    def require_group_decorator(wrapped_func):
        @login_required
        @wraps(wrapped_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.has_group(group):
                return HttpResponseRedirect(redirect_url)
            return wrapped_func(request, *args, **kwargs)
        return wrapper
    return require_group_decorator


### celery helpers ###

def run_task(task, *args, **kwargs):
    """
        Run a celery task either async or directly, depending on settings.RUN_TASKS_ASYNC.
    """
    if settings.RUN_TASKS_ASYNC:
        return task.delay(*args, **kwargs)
    else:
        return task.apply(args, kwargs)

### simple search ###

def get_search_query(target, search_string, fields):
    """
        For the given `target` (either a Model or QuerySet),
        apply consecutive .filter()s such that each word
        in `search_string` appears in one of the `fields`.
    """
    # get words in search_string
    required_words = search_string.strip().split()
    if not required_words:
        return target

    # if we got a Model, turn into a QuerySet
    if hasattr(target, 'objects'):
        target = target.objects

    for required_word in required_words:
        # apply the equivalent of target = target.filter(Q(field1__icontains=required_word) | Q(field2__icontains=required_word) | ...)
        query_parts = [Q(**{field+"__icontains":required_word}) for field in fields]
        query_parts_joined = reduce(operator.or_, query_parts, Q())
        target = target.filter(query_parts_joined)

    return target
    
### url manipulation ###

def absolute_url(request, url):
    """
        Get absolute URL for relative URL based on request.
        We wrap Django's version to also check for '//' absolute links.
    """
    if url.startswith('//'):
        return url
    return request.build_absolute_uri(url)

def direct_media_url(url):
    """
        Given a URL that includes MEDIA_URL, convert it to include DIRECT_MEDIA_URL instead if that is set.
    """
    if not settings.DIRECT_MEDIA_URL:
        return url
    return url.replace(settings.MEDIA_URL, settings.DIRECT_MEDIA_URL, 1)

### debug toolbar ###

def show_debug_toolbar(request):
    """ Used by django-debug-toolbar in settings_dev.py to decide whether to show debug toolbar. """
    return settings.DEBUG