from django.core.urlresolvers import reverse


def new_class(name, *args, **kwargs):
    return type(name, args, kwargs)
