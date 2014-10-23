from django import template

register = template.Library()


import random
import calendar

from django.utils.safestring import mark_safe
from django.template.defaultfilters import date as date_filter

@register.filter
def local_datetime(datetime, format_string="F j, Y g:i a"):
    """
        Given a date, print Javascript to print local date/time if available.
    """
    if not datetime:
        return ""
    random_id = 'date_'+str(random.random())[2:]
    return mark_safe("<script id='%s'>insertLocalDateTime('%s', %s, '%s')</script><noscript>%s</noscript>" % (
        random_id,
        random_id,
        calendar.timegm(datetime.utctimetuple()),
        format_string,
        date_filter(datetime, format_string)
    ))