from django.urls import reverse
from django.shortcuts import redirect


def bookmarklet_create(request):
    '''Handle incoming requests from the bookmarklet.

    Currently, the bookmarklet takes two parameters:
    - v (version)
    - url

    This function accepts URLs like this:

    /service/bookmarklet-create/?v=[...]&url=[...]

    ...and passes the query string values to /manage/create/
    '''
    tocapture = request.GET.get('url', '')
    add_url = f"{reverse('create_link')}?url={tocapture}"
    return redirect(add_url)
