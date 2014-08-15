from django import template

register = template.Library()


from django.conf import settings
from django.template.defaulttags import url as url_filter, URLNode

from ..middleware import get_main_server_host, get_url_for_host

class MainURLNode(URLNode):
    def render(self, context):
        url = super(MainURLNode, self).render(context)
        return get_url_for_host(context['request'], get_main_server_host(context['request']), url)

@register.tag
def main_url(parser, token):
    url_node = url_filter(parser, token)
    if not settings.MIRRORING_ENABLED:
        return url_node
    return MainURLNode(url_node.view_name, url_node.args, url_node.kwargs, url_node.asvar)
