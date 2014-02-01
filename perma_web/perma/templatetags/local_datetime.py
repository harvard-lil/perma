from django import template

register = template.Library()


from django.utils.safestring import mark_safe
from django.template.defaultfilters import date as date_filter
import time

@register.filter
def local_datetime(datetime):
    """
        Given a date, print Javascript to print local date/time if available.
    """
    return mark_safe("<script>document.write(localDateTime(%s))</script><noscript>%s</noscript>" % (
        time.mktime(datetime.timetuple()),
        date_filter(datetime, "DATETIME_FORMAT")
    ))