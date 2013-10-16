from django import template

register = template.Library()

@register.filter(name="startswith")
def startswith(value, arg):
    """Usage, {% if value|starts_with:"arg" %}"""
    return value.startswith(arg)
