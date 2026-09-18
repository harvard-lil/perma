from django import template

register = template.Library()


@register.filter
def absolute_url(url, base):
    """
    Make `url` absolute against `base` (scheme and host, e.g. "https://perma.cc").

    Templates that need a full URL for a static file -- social-preview meta
    tags -- used to write "{{ base }}{{ STATIC_URL }}path", which is right
    while STATIC_URL is a path and doubled ("https://perma.cchttps://static...")
    once STATIC_URL is itself absolute, as on a static subdomain. An absolute
    url is returned unchanged; a scheme-relative one takes base's scheme; a
    path is appended to base, exactly as before.
    """
    url = str(url)
    if url.startswith(("http://", "https://")):
        return url
    if url.startswith("//"):
        return base.split("//", 1)[0] + url
    return base + url
