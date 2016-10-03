from django import template

register = template.Library()

@register.filter
def input_type(field):
    """
        Return the type of a form field.
    """
    return field.field.widget.__class__.__name__
