import StringIO
from django.core.files import File
from django.core.files.storage import default_storage
from django.utils.decorators import available_attrs


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


### can_be_mirrored decorator ###

def can_be_mirrored(view_func):
    """
    Marks a view function as capable of being served by a mirror.
    Modeled on csrf_exempt.
    """
    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapped_view.can_be_mirrored = True
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)




def store_file(file_object, file_path, overwrite=False, storage=default_storage):
    """
        Given an open file_object ready for reading,
        and the file_path to store it to,
        save the file and return the new file name.

        File name will only change if file_path conflicts with an existing file.
        If overwrite=True, existing file will instead be deleted and overwritten.
    """
    if overwrite:
        if storage.exists(file_path):
            storage.delete(file_path)
    new_file_path = storage.save(file_path, File(file_object))
    return new_file_path.split('/')[-1]

def store_data_to_file(data, file_path, overwrite=False, storage=default_storage):
    file_object = StringIO.StringIO()
    file_object.write(data)
    file_object.seek(0)
    return store_file(file_object, file_path, overwrite, storage)