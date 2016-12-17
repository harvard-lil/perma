from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def as_json(context, obj):
    return mark_safe(obj.as_json(context['request']))
