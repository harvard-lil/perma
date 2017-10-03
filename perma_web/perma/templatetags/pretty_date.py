import inflect

from django import template

register = template.Library()

@register.filter
def pretty_date(date):
    i = inflect.engine()
    return "{date:%B} {day}, {date:%Y}".format(date=date, day=i.ordinal(date.day))
