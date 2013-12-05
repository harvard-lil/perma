from django import template

register = template.Library()

@register.filter
def repeat(value, times):
    """
        Given {{ "foo"|repeat:3 }}, prints "foofoofoo"
    """
    return value * times