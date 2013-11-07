from django import template

register = template.Library()

@register.filter(name="startswith")
def startswith(value, arg):
    """Usage, {{ startswith }}"""
    return value.startswith(arg)
