import datetime
from functools import wraps
import pytz

from django.utils.decorators import available_attrs


### must_be_mirrored decorator ###

def must_be_mirrored(view_func):
    """
        If mirroring is enabled, then a view func marked with this decorator must be served at mirror domain instead of main domain
        (e.g. perma.cc instead of dashboard.perma.cc).

        Conversely, a view func without this decorator must be served at main domain instead
        of mirror domain, unless @may_be_mirrored is applied instead.
    """
    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapped_view.must_be_mirrored = True
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)

def may_be_mirrored(view_func):
    """
        If mirroring is enabled, a view func with this decorator can be served at either main domain or mirror domain
        (dashboard.perma.cc or perma.cc).

        Otherwise, the view can only be served at one or the other, depending whether @must_be_mirrored is applied.
        If viewed at the wrong domain, it will be forwarded.
    """
    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapped_view.may_be_mirrored = True
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)


### datetime helpers ###
# TODO: should we use built-in Django serializer instead?

def serialize_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def unserialize_datetime(dt_string):
    return pytz.UTC.localize(datetime.datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S"))

