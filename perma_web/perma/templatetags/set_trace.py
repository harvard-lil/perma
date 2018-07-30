import pdb
from pprint import pprint

from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def set_trace(context):
    """ Handy for figuring out what's going on in a template. Usage: {% set_trace %}. """
    pprint(context)
    pdb.set_trace()
