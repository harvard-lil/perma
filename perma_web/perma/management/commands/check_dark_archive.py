from optparse import make_option
import os
import re

from django.conf import settings
from django.core.management.base import BaseCommand
import requests
import sys

from perma.models import Link


class Command(BaseCommand):
    """
        Look at each of our existing archives and confirm their dark_archived_robots_txt_blocked status.
    """
    option_list = BaseCommand.option_list + (
        make_option('-H', '--host',
                    dest='host',
                    help='Fetch archive playbacks from HOST (default %default)',
                    default=settings.HOST,
                    metavar="HOST",
        ),
        make_option('-s', '--start',
                    dest='start_guid',
                    help='Start checking immediately *after* this GUID (checking is alphabetical)',
                    metavar="GUID",
                    default=None,
        ),
        make_option('-f', '--file',
                    dest='file',
                    help='File path to save update SQL to (default %default).',
                    default='check_dark_archive.sql',
        ),
        make_option('-d', '--date',
                    dest='start_date',
                    help='Check links created on or after DATE (YYYY-MM-DD)',
                    metavar="DATE",
                    default=None,
        ),
    )

    args = ''
    help = 'Confirm dark archive robots.txt status of links.'

    def handle(self, *args, **options):
        # TODO: This needs to be re-written for Capture model
        pass

        # # setup
        # meta_tag_re_template = r'<\s*meta\s+[^>]*name\s*=\s*[\'"]?\s*%(meta_name)s\b[^>]*>'
        # perma_meta_tag_re = re.compile(meta_tag_re_template % {'meta_name': 'perma'}, flags=re.IGNORECASE)
        # robots_meta_tag_re = re.compile(meta_tag_re_template % {'meta_name': 'robots'}, flags=re.IGNORECASE)
        # host = options['host']
        # out_file_path = options['file']
        # out_file_mode = 'w'
        # start_date = options['start_date']
        #
        # # open file to save updating SQL to
        # print "Saving SQL to %s" % out_file_path
        # if os.path.exists(out_file_path):
        #     while True:
        #         answer = raw_input("File already exists. [O]verwrite, [A]ppend, or [C]ancel? ").lower()
        #         if answer == 'c':
        #             sys.exit()
        #         elif answer == 'o':
        #             break
        #         elif answer == 'a':
        #             out_file_mode = 'a'
        #             break
        # out_file = open(out_file_path, out_file_mode)
        #
        #
        # # find links to check
        # query = Asset.objects.filter(warc_capture__in=('archive.warc.gz','source/index.html')).order_by('link').select_related('link')
        # if options['start_guid']:
        #     query = query.filter(link_id__gt=options['start_guid'])
        # if options['start_date']:
        #     query = query.filter(link__creation_timestamp__gte=options['start_date'])
        #
        # # check each link by loading it from server
        # for asset in query:
        #     print "Testing", asset.link_id, asset.link.submitted_url
        #     try:
        #         response = requests.get("http://"+host+asset.warc_url())
        #     except requests.TooManyRedirects:
        #         print "Too many redirects!"
        #         continue
        #     html = response.content
        #     if response.status_code == 200 and html:
        #         meta_tag = perma_meta_tag_re.search(html) or robots_meta_tag_re.search(html)
        #         if meta_tag:
        #             meta_tag = meta_tag.group(0).lower()
        #             print "Found %s" % meta_tag
        #             if 'noarchive' in meta_tag:
        #                 if not asset.link.dark_archived_robots_txt_blocked:
        #                     print "Darchiving."
        #                     out_file.write("UPDATE perma_link SET dark_archived_robots_txt_blocked=true WHERE guid='%s';\n" % asset.link_id)
        #                     # asset.link.dark_archived_robots_txt_blocked = True
        #                     # asset.link.save()
        #                 else:
        #                     print "Already darchived."
        #         elif asset.link.dark_archived_robots_txt_blocked:
        #             print "WARNING: Didn't find meta but dark archive was set."
        #     else:
        #         print "Status %s, skipping." % response.status_code





