from django import template

register = template.Library()

@register.filter
def archive_description(submitted_description, fallback_description):
    return submitted_description if submitted_description else fallback_description
