from django import template

register = template.Library()

@register.filter()
def has_group(user, group_name):
    """Usage: {% if user|has_group:"group_name,another_group_name" %}"""
    if "," in group_name:
        group_name = [n.strip() for n in group_name.split(',')]
    return user.has_group(group_name)


@register.filter()
def has_group_by_id(user, group_id):
    """Usage: {% if user|has_group:1 %}"""
    return user.groups.filter(pk=int(group_id)).exists()