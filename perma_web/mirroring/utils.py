import datetime
from functools import wraps
import hashlib
import json
from django.views.decorators.csrf import csrf_exempt
import gnupg
import pytz
import time

from django.conf import settings
from django.utils.decorators import available_attrs
from django.core.cache import cache as django_cache


### must_be_mirrored decorator ###

def must_be_mirrored(view_func):
    """
        If mirroring is enabled, then a view func marked with this decorator must be served at mirror domain instead of main domain
        (e.g. perma.cc instead of dashboard.perma.cc).

        Conversely, a view func without this decorator must be served at main domain instead
        of mirror domain, unless @may_be_mirrored is applied instead.
    """
    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapped_view.must_be_mirrored = True
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)

def may_be_mirrored(view_func):
    """
        If mirroring is enabled, a view func with this decorator can be served at either main domain or mirror domain
        (dashboard.perma.cc or perma.cc).

        Otherwise, the view can only be served at one or the other, depending whether @must_be_mirrored is applied.
        If viewed at the wrong domain, it will be forwarded.
    """
    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapped_view.may_be_mirrored = True
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)


### gpg ###

# cache some one-time setup stuff
_gpg = None
_fingerprint_cache = {}
def get_gpg():
    global _gpg
    if not _gpg:
        _gpg = gnupg.GPG(gnupghome=settings.GPG_DIRECTORY)
    return _gpg

def get_fingerprint(key):
    """
        Because gnupg calls out to a command-line tool, we don't pass keys directly. Instead we have to install the
        key in gpg's keychain and then refer to it by fingerprint. This function installs the key (if we haven't done
        that yet this run) then returns the fingerprint.
    """
    if key not in _fingerprint_cache:
        _fingerprint_cache[key] = get_gpg().import_keys(key).fingerprints[0]
    return _fingerprint_cache[key]

def sign_message(message, key=settings.GPG_PRIVATE_KEY):
    if not key:
        return message
    fingerprint = get_fingerprint(key)
    return get_gpg().sign(message, keyid=fingerprint)

def read_signed_message(message, valid_keys, max_age=None, cache=False):
    """
        Read a PGP-signed message and return its data, if the signing key matches `key`.
        If max_age is not None, we will raise an exception if the message was signed more than max_age seconds ago.
    """
    verified_message = None
    cache_key = None

    # deal with single key passed as valid_keys
    if isinstance(valid_keys, basestring):
        valid_keys = [valid_keys]

    if cache:
        # Try to fetch from cache.
        cache_key = 'gpg-' + hashlib.sha256(message).hexdigest()
        verified_message = django_cache.get(cache_key)

    if not verified_message:
        # Not in cache, run decode.
        valid_fingerprints = set(get_fingerprint(key) for key in valid_keys)
        verified_message = get_gpg().decrypt(message)  # decrypt instead of verify, even if message isn't encrypted, so we get the message content in verified_message.data
        if verified_message.fingerprint not in valid_fingerprints:
            raise Exception("Signature verification failed: fingerprint does not match %s for message %s." % (valid_fingerprints, message))
        if max_age is not None and time.time() - int(verified_message.timestamp) > max_age:
            raise Exception("Message is too old.")
        verified_message = verified_message.data[:-1]  # strip extra \n that gpg adds

        if cache:
            django_cache.set(cache_key, verified_message)

    return verified_message


### auth ###

def sign_post_data(json_data):
    return {'signed_data':sign_message(json.dumps(json_data))}

def read_request_decorator(func, valid_keys):
    @csrf_exempt  # don't want/need CSRF because we're making sure these requests are signed
    @wraps(func)
    def decode(request):
        message = read_signed_message(request.POST['signed_data'], valid_keys, max_age=60*5)
        kwargs = json.loads(message)
        return func(request, **kwargs)
    return decode

def read_upstream_request(func):
    return read_request_decorator(func, [settings.UPSTREAM_SERVER.get('public_key')])

def read_downstream_request(func):
    return read_request_decorator(func, [server['public_key'] for server in settings.DOWNSTREAM_SERVERS])