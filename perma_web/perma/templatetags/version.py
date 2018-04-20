from django import template
from django.conf import settings
import os

register = template.Library()

@register.simple_tag
def perma_version():
    try:
        with open(os.path.join(settings.STATIC_ROOT, 'version.txt'), 'r') as f:
            return f.read().strip()
    except IOError:
        return False
