from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def as_json(context, obj):
    return obj.as_json(context['request'])