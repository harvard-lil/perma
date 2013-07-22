from django import template
import os
from linky.settings import STATIC_URL, PROJECT_ROOT
STATIC_PREFIX = STATIC_URL
register = template.Library()

@register.tag
def file_exists(parser, token):
    name, file_path, id, url = token.split_contents()
    return File_exists_node(id, url)

class File_exists_node(template.Node):
    def __init__(self, id, url):
        self.id = template.Variable(id)
        self.url = template.Variable(url)

    def render(self, context):
        id = str(self.id.resolve(context))
        url = self.url.resolve(context)
        if os.path.exists(PROJECT_ROOT + self.pdf_path(id)):
            return ''.join(['<a href="', self.pdf_path(id), '"> PDF </a>'])
        elif os.path.exists(PROJECT_ROOT + self.jpg_path(id)):
            return ''.join(['<a href="', url, 
                            '"><img class="linky-image" src="',
                            self.jpg_path(id),
                            '"></a>'])
        else:
            return ''.join(['<a href="', url, 
                            '"><img class="linky-image" src="',
                            self.png_path(id),
                            '"></a>'])

    def pdf_path(self, id):
        return STATIC_PREFIX + 'generated/' + id + '/cap.pdf'
 
    def png_path(self, id):
        return STATIC_PREFIX + 'generated/' + id + '/cap.png'

    def jpg_path(self, id):
        return STATIC_PREFIX + 'generated/' + id + '/cap.jpg'
       
