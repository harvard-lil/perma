from django import template

register = template.Library()

@register.filter
def get_item_from_dict(dictionary, key):
    """ Return the item from a dictionary """
    return dictionary.get(key)
