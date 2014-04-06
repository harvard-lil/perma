from django import template
import os
from django.conf import settings

register = template.Library()

@register.tag
def file_exists(parser, token):
    name, file_path, id, url = token.split_contents()
    return File_exists_node(file_path, id, url)

class File_exists_node(template.Node):
    def __init__(self, path, id, url):
        self.id = template.Variable(id)
        self.url = template.Variable(url)
        self.path = template.Variable(path)

    def render(self, context):
        id = str(self.id.resolve(context))
        url = self.url.resolve(context)
        path = self.path.resolve(context)
        if os.path.exists(settings.MEDIA_ROOT + '/' + path + '/cap.pdf'):
            return ''.join(['<a id="linky-pdf" href="', self.pdf_path(id, path), '">View this PDF</a>'])
        elif os.path.exists(settings.MEDIA_ROOT + '/' + path + '/cap.jpg'):
            return ''.join(['<a href="', url,
                            '"><img class="linky-image" src="',
                            self.jpg_path(id, path),
                            '"></a>'])
        else:
            return ''.join(['<a href="', url,
                            '"><img class="linky-image" src="',
                            self.png_path(id, path),
                            '"></a>'])

    def pdf_path(self, id, path):
        return settings.MEDIA_URL + path + '/cap.pdf'

    def png_path(self, id, path):
        return settings.MEDIA_URL + path + '/cap.png'

    def jpg_path(self, id, path):
        return settings.MEDIA_URL + path + '/cap.jpg'


