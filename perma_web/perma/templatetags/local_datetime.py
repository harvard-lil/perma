from django import template

register = template.Library()


from django.utils.safestring import mark_safe
from django.template.defaultfilters import date as date_filter
import time

@register.filter
def local_datetime(datetime, format_string="M. d, Y, g:i a"):
    """
        Given a date, print Javascript to print local date/time if available.
    """
    if not datetime:
        return ""
    return mark_safe("<script>document.write(localDateTime(%s, '%s'))</script><noscript>%s</noscript>" % (
        time.mktime(datetime.timetuple()),
        format_string,
        date_filter(datetime, format_string)
    ))