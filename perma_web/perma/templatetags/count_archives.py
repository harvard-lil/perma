from django import template

register = template.Library()

"""
It can be nice to tell the user how many capture types we have
for a given archive. Do that here, and return the number
in a friendly way.
"""

@register.filter()
def count_archives(asset):
    """Usage: {{ asset|count_archives }}"""
    archive_count = 0

    if asset.pdf_capture and asset.pdf_capture != 'failed':
        archive_count += 1

    if asset.image_capture and asset.image_capture != 'failed':
        archive_count += 1

    if asset.warc_capture and asset.warc_capture != 'failed':
        archive_count += 1


    if archive_count == 0:
        return "zero captures"

    if archive_count == 1:
        return "one capture type"

    if archive_count == 2:
        return "two capture types"