import urllib.request, urllib.parse, urllib.error
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def current_query_string(context, **kwargs):
    """
        Given {% current_query_string page=1 q='' %}, return the current query string but with page and q values changed.
    """
    query_params = dict(context['request'].GET, **kwargs)
    query_params_bytes = {}
    for k, v in query_params.items():
        if v is not None and v != '':
            # This is complex because we need to handle unicode and lists of unicode
            # in addition to ints, longs, and possibly other data types.
            # This should improve in python 3.
            try:
                query_params_bytes[k] = v.encode('utf-8')
            except AttributeError:
                try:
                    query_params_bytes[k] = [i.encode('utf-8') for i in v]
                except TypeError:
                    query_params_bytes[k] = v
    return urllib.parse.urlencode(query_params_bytes, doseq=True)
