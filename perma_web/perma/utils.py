from django.db.models import Q
import operator


class base:
    """
    Member methods perform base conversion for us.
    """
    
    
    BASE2 = "01"
    BASE10 = "0123456789"
    BASE16 = "0123456789ABCDEF"
    BASE32 = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    BASE58 = "123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
    BASE62 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz"
 
    @staticmethod
    def convert(number,fromdigits,todigits):
        """ 
        Converts a "number" between two bases of arbitrary digits
 
       The input number is assumed to be a string of digits from the
       fromdigits string (which is in order of smallest to largest
       digit). The return value is a string of elements from todigits
       (ordered in the same way). The input and output bases are
       determined from the lengths of the digit strings. Negative
       signs are passed through.
 
       This is modified source from http://pastebin.com/f54dd69d6#
 
       decimal to binary
       >>> baseconvert(555,BASE10,BASE2)
       '1000101011'
 
       binary to decimal
       >>> convert('1000101011',BASE2,BASE10)
       '555'
 
       """
 
        if str(number)[0]=='-':
            number = str(number)[1:]
            neg=1
        else:
            neg=0
 
        # make an integer out of the number
        x=0
        for digit in str(number):
           x = x*len(fromdigits) + fromdigits.index(digit)
   
        # create the result in base 'len(todigits)'
        if x == 0:
            res = todigits[0]
        else:
            res=""
            while x>0:
                digit = x % len(todigits)
                res = todigits[digit] + res
                x = int(x / len(todigits))
            if neg:
                res = "-"+res
 
        return res

        
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

### user content url ###

def absolute_url(request, url):
    """
        Get absolute URL for relative URL based on request.
        We wrap Django's version to also check for '//' absolute links.
    """
    if url.startswith('//'):
        return url
    return request.build_absolute_uri(url)