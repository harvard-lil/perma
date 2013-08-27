from django import template
import os, smhasher
from linky.settings import STATIC_URL, PROJECT_ROOT, GENERATED_ASSETS_STORAGE
from linky.tasks import instapaper_capture
register = template.Library()


@register.tag
def diff(parser, token):
    name, asset, linky = token.split_contents()
    return Diff_Node(asset, linky)

class Diff_Node(template.Node):
    def __init__(self, asset, linky):
        self.asset = template.Variable(asset)
        self.linky = template.Variable(linky)

    def render(self, context):
        asset = self.asset.resolve(context)
        linky = self.linky.resolve(context)
        id, cap = instapaper_capture(linky.submitted_url, linky.submitted_title)

        # Only say it's changed if we are sure it has changed.
        if asset.instapaper_hash is None or str(smhasher.murmur3_x86_128(cap)) == asset.instapaper_hash:
            return ''
        else:
            return ' (changed)'
