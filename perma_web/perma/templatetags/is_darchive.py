from django import template

register = template.Library()

@register.filter()
def is_darchive(link):
    """Usage: {% if link|is_darchive %}"""
    return link.dark_archived or link.dark_archived_robots_txt_blocked