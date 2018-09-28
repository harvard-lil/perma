import requests
import os

# django
from django.core.files.storage import default_storage
from django.apps import apps
from django.conf import settings

CDXLine = apps.get_model('perma', 'CDXLine')

WR_API = settings.WR_INTERNAL_API_HOST + '/api/v1'


# ============================================================================
def init_replay(request, link):
    """ Set up for WR replay, initing new user (if needed), new collection for guid (if needed)
        Return WR username and session cookie
    """
    wr_user, wr_cookie, is_new = init_wr_user(request)

    coll = link.guid.lower()

    # if not new session, check if collection exists, create otherwise
    if not is_new:
        res = requests.get(WR_API + '/collection/{coll}?user={user}'.format(user=wr_user, coll=coll),
                           headers={'Host': settings.HOST},
                           cookies={'__wr_sesh': wr_cookie})

        is_new = (res.status_code == 404)

    if is_new:
        if not create_new_collection(wr_user, wr_cookie, link):
            clear_session(request)

    return wr_user, wr_cookie


# ============================================================================
def create_new_collection(wr_user, wr_cookie, link):
    """ Create new collection for link guid
        Returns true if succeeded adding warc and cdx
    """
    # create collection if doesn't exist
    data = {'title': link.guid,
            'external': True
           }

    res = requests.post(WR_API + '/collections?user={user}'.format(user=wr_user),
                        headers={'Host': settings.HOST},
                        json=data, cookies={'__wr_sesh': wr_cookie})

    if res.status_code == 200:
        coll = res.json()['collection']['slug']
    elif res.status_code == 400 and res.json() == {'error': 'duplicate_name'}:
        # if collection already exists, not an error, just readd cdx and warc just in case
        # collection slug is always lowercase, so lowercase guid
        coll = link.guid.lower()
    else:
        # some other error?
        print(res.status_code)
        return False

    # add warc
    warc = link.warc_storage_file()
    data = {'warcs': {warc: get_archive_path() + warc}}

    res = requests.put(WR_API + '/collection/{coll}/warc?user={user}'.format(user=wr_user, coll=coll),
                       headers={'Host': settings.HOST},
                       json=data, cookies={'__wr_sesh': wr_cookie})

    # ensure the one warc was added
    if res.json().get('success') != 1:
        print(res.json())
        return False

    # add cdx
    lines = CDXLine.objects.filter(link_id=link.guid)

    num_cdx = len(lines)

    text = ''.join(line.raw for line in lines).encode('utf-8')

    res = requests.put(WR_API + '/collection/{coll}/cdx?user={user}'.format(user=wr_user, coll=coll),
                       headers={'Host': settings.HOST},
                       cookies={'__wr_sesh': wr_cookie}, data=text)

    # ensure all cdx lines have been added! (too strict?)
    if res.json().get('success') != num_cdx:
        print(res.json())
        return False

    return True


# ============================================================================
def clear_session(request):
    """ Clear stored WR session info, forcing a new WR session next time
    """
    wr_user = request.session.pop('wr_user', '')
    wr_cookie = request.session.pop('wr_cookie', '')

    if not wr_user or not wr_cookie:
        return

    try:
        res = requests.delete(WR_API + '/user/{user}'.format(user=wr_user),
                              headers={'Host': settings.HOST},
                              cookies={'__wr_sesh': wr_cookie})

        print('WR User Deleted', res.json())
    except:
        print('WR User Not Deleted!')


# ============================================================================
def init_wr_user(request):
    """ Initialize new temp WR user or get existing stored WR user
        If WR session has expired, a new one is created
        is_new indicates if a new WR session was created
        Returns wr_user, wr_cookie, is_new
    """
    wr_user = request.session.get('wr_user')
    wr_cookie = request.session.get('wr_cookie')
    is_new = False

    if wr_cookie:
        cookies = {'__wr_sesh': wr_cookie}
    else:
        cookies = None

    res = requests.post(WR_API + '/auth/anon_user',
                        headers={'Host': settings.HOST},
                        cookies=cookies)

    new_user = res.json()['user']['username']

    if new_user != wr_user:
        request.session['wr_user'] = new_user
        wr_user = new_user
        is_new = True

    new_cookie = res.cookies.get('__wr_sesh')
    if new_cookie and new_cookie != wr_cookie:
        request.session['wr_cookie'] = new_cookie
        wr_cookie = new_cookie
        is_new = True

    return wr_user, wr_cookie, is_new


# ============================================================================
def get_wr_iframe_prefix(wr_user, guid):
    """ Get iframe prefix to inject
    """
    return settings.WR_CONTENT_HOST + '/' + wr_user + '/' + guid.lower() + '/'


# ============================================================================
def get_archive_path():
    """ Absolute path prefix for WARC, from existing replay
    """
    # Get root storage location for warcs, based on default_storage.
    # archive_path should be the location pywb can find warcs, like 'file://generated/' or 'http://perma.s3.amazonaws.com/generated/'
    # We can get it by requesting the location of a blank file from default_storage.
    # default_storage may use disk or network storage depending on config, so we look for either a path() or url()
    try:
        archive_path = 'file://' + default_storage.path('') + '/'

    except NotImplementedError:
        archive_path = default_storage.url('')
        archive_path = archive_path.split('?', 1)[0]  # remove query params

    return archive_path
    # must be ascii, for some reason, else you'll get
    # 'unicode' object has no attribute 'get'
    #return archive_path.encode('ascii', 'ignore')


