import os
import re
from django.conf import settings

protocol = "https://" if settings.SECURE_SSL_REDIRECT else "http://"

def rewrite_html(html_page, guid):
    tmp_html = re.sub("/{0}".format(guid), "/warc/{0}".format(guid), html_page)
    return re.sub("http://localhost/warc", "{0}{1}{2}".format(protocol, settings.WARC_HOST, settings.WARC_ROUTE), tmp_html)

def write_to_static(new_string, filename,  old_guid, new_guid):
    dirpath = get_compare_dir_path(old_guid, new_guid)
    filepath = os.path.join(dirpath, filename)
    with open(filepath, 'w+') as f:
        f.write(new_string)

def create_compare_dir(old_guid, new_guid):
    dirpath = get_compare_dir_path(old_guid, new_guid)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

def compare_dir_exists(old_guid, new_guid):
    dirpath = get_compare_dir_path(old_guid, new_guid)
    return os.path.exists(dirpath)

def get_compare_dir_path(old_guid, new_guid):
    dirname = "{0}_compare_{1}".format(old_guid, new_guid)
    return os.path.join(settings.STATIC_ROOT, dirname)
