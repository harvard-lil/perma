import datetime
from django import template

register = template.Library()

@register.filter
def timedelta_from_now(delta):
    """
    Add a timedelta to now, plus a fudge factor of a few seconds.
    Most useful for chaining with Django's builtin filter "timeuntil",
    for producing a humanized timedelta.
    """
    return datetime.datetime.utcnow() + delta + datetime.timedelta(seconds=5)
