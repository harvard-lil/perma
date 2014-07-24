import os
import re
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from perma.models import Link, Asset
from pywb.warc.archiveiterator import create_index_iter


class Command(BaseCommand):
    """
        Look at each of our existing archives and confirm their dark_archived_robots_txt_blocked status.
    """
    args = ''
    help = 'Confirm dark archive robots.txt status of links.'

    def handle(self, *args, **options):
        # setup
        meta_tag_re_template = r'<\s*meta\s+[^>]*name\s*=\s*[\'"]?\s*%(meta_name)s\b[^>]*>'
        perma_meta_tag_re = re.compile(meta_tag_re_template % {'meta_name': 'perma'}, flags=re.IGNORECASE)
        robots_meta_tag_re = re.compile(meta_tag_re_template % {'meta_name': 'robots'}, flags=re.IGNORECASE)

        # helpers
        def open_warc_capture(asset):
            path = os.path.join(asset.base_storage_path, asset.warc_capture)
            try:
                return default_storage.open(path)
            except IOError:
                print "File %s not found for %s! Skipping." % (path, asset.link_id)
                return None


        for asset in Asset.objects.order_by('link'):

            # load in main html file for this asset, if any
            html = None
            if asset.warc_capture == 'archive.warc.gz':
                warc_file = open_warc_capture(asset)
                for entry in create_index_iter(warc_file):
                    import ipdb; ipdb.set_trace()

            elif asset.warc_capture == 'source/index.html':
                warc_file = open_warc_capture(asset)
                if not warc_file:
                    continue
                html = warc_file.read()

            if html:
                meta_tag = perma_meta_tag_re.search(html) or robots_meta_tag_re.search(html)
                if meta_tag and 'noarchive' in meta_tag.group(0).lower():
                    asset.link.dark_archived_robots_txt_blocked = True
                    asset.link.save()





