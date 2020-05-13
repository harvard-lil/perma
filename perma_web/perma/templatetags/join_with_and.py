from django import template
from django.utils.text import get_text_list

register = template.Library()

@register.filter
def join_with_and(list_, attr=None):
    if attr:
        list_ = [getattr(o, attr) for o in list_]
    return get_text_list(list_, 'and')
