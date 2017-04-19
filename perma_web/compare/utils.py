import re
from django.conf import settings

protocol = "https://" if settings.SECURE_SSL_REDIRECT else "http://"

def rewrite_html(html_page, guid):
    tmp_html = re.sub("/{0}".format(guid), "/warc/{0}".format(guid), html_page)
    return re.sub("http://localhost/warc", "{0}{1}{2}".format(protocol, settings.WARC_HOST, settings.WARC_ROUTE), tmp_html)

def write_to_static(new_string, filename):
    with open(settings.STATIC_ROOT+filename, 'w+') as f: 
        f.write(new_string)
