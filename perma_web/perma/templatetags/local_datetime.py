import os

from django import template
from django.conf import settings

register = template.Library()


import random
import calendar

from django.utils.safestring import mark_safe
from django.template.defaultfilters import date as date_filter

@register.filter
def local_datetime(datetime, format_string="F j, Y g:i a"):
    """
        Given a date, print Javascript to print local date/time if available.

        If this filter is used, {% local_datetime_js %} should also be included in the <head>.
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

@register.simple_tag
def local_datetime_js():
    """
        Return an inline script block with the support javascript for the local_datetime filter.
    """
    return mark_safe("<script>%s</script>" % open(os.path.join(settings.PROJECT_ROOT, "static/js/helpers/local-datetime.js")).read())