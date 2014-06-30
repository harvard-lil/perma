import datetime
from functools import wraps
import pytz

from django.utils.decorators import available_attrs


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

def no_mirror_forwarding(view_func):
    """
    Marks a view function so it won't be forwarded from main server to mirror server or vice versa.
    """
    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapped_view.no_mirror_forwarding = True
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)


### datetime helpers ###
# TODO: should we use built-in Django serializer instead?

def serialize_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def unserialize_datetime(dt_string):
    return pytz.UTC.localize(datetime.datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S"))

