from django import template
import os, smhasher
from linky.settings import STATIC_URL, PROJECT_ROOT, GENERATED_ASSETS_STORAGE
from linky.tasks import instapaper_capture
register = template.Library()


@register.tag
def diff(parser, token):
    name, link = token.split_contents()
    return Diff_Node(link)

class Diff_Node(template.Node):
    def __init__(self, link):
        self.link = template.Variable(link)

    def render(self, context):
        link = self.link.resolve(context)
        id, cap = instapaper_capture(link.submitted_url, link.submitted_title)

        if cap is not None and str(smhasher.murmur3_x86_128(cap)) == link.instapaper_hash:
            return ''
        else:
            return ' (changed)'
