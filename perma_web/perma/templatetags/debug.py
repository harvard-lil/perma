from django import template

register = template.Library()

@register.simple_tag
def debug(*args):
    """ Handy for figuring out what's going on in a template. Usage: {% debug "print" some_var "stuff" %}. """
    print(*args)
