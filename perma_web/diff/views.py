from django.shortcuts import render

def diff_entry(request, guid):
    """
    here, we want to grab the guid coming in, and create a new archive of it
    we then do a diff on that archive using diff.warc_compare_text.*
    """

    context = {
    }

    response = render(request, 'panoramic.html', context)
    return response
