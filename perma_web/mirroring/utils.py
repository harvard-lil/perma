import datetime
from functools import wraps
import hashlib
import gnupg
import pytz
import re

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


### datetime helpers ###
# TODO: should we use built-in Django serializer instead?

def serialize_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def unserialize_datetime(dt_string):
    return pytz.UTC.localize(datetime.datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S"))


### gpg ###

gpg = gnupg.GPG(gnupghome=settings.GPG_DIRECTORY)
_fingerprint_cache = {}

def get_fingerprint(key):
    """
        Because gnupg calls out to a command-line tool, we don't pass keys directly. Instead we have to install the
        key in gpg's keychain and then refer to it by fingerprint. This function installs the key (if we haven't done
        that yet this run) then returns the fingerprint.
    """
    if key not in _fingerprint_cache:
        _fingerprint_cache[key] = gpg.import_keys(key).fingerprints[0]
    return _fingerprint_cache[key]

def sign_message(message, key=settings.GPG_PRIVATE_KEY):
    if not key:
        return message
    fingerprint = get_fingerprint(key)
    return gpg.sign(message, keyid=fingerprint)

def read_signed_message(message, key=settings.UPSTREAM_SERVER.get('public_key')):
    if not key:
        return message

    # We cache decoded cookies because this will have to be done on each request.
    cache_key = 'gpg-' + hashlib.sha256(message).hexdigest()
    verified_message = django_cache.get(cache_key)

    if not verified_message:
        # Not in cache, run decode.
        fingerprint = get_fingerprint(key)
        verified_message = gpg.decrypt(message)  # decrypt instead of verify, even if message isn't encrypted, so we get the message content in verified_message.data
        if verified_message.fingerprint != fingerprint:
            raise Exception("Signature verification failed: fingerprint does not match %s for message %s." % (fingerprint, message))
        verified_message = verified_message.data[:-1]  # strip extra \n that gpg adds
        django_cache.set(cache_key, verified_message)

    return verified_message