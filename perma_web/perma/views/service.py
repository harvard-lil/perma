from django.urls import reverse
from django.shortcuts import redirect
from urllib.parse import urlencode


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
    if tocapture:
        params = urlencode({'url': tocapture})
        add_url = f"{reverse('create_link')}?{params}"
    else:
        add_url = reverse('create_link')
    return redirect(add_url)
