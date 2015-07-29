import urllib
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def current_query_string(context, **kwargs):
    """
        Given {% current_query_string page=1 q='' %}, return the current query string but with page and q values changed.
    """
    query_params = dict(context['request'].GET, **kwargs)
    query_params = dict((k,v) for k, v in query_params.items() if v is not None and v != '')
    return urllib.urlencode(query_params, doseq=True)