import imghdr
from collections import OrderedDict
from functools import wraps

from django.http import Http404
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.settings import api_settings

from perma.models import Folder


class TastypiePagination(LimitOffsetPagination):
    """
        Modify DRF's LimitOffsetPagination to return results in the same format as paginated results returned by Tastypie.
    """
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('meta', OrderedDict([
                ('limit', self.limit),
                ('next', self.get_next_link()),
                ('offset', self.offset),
                ('previous', self.get_previous_link()),
                ('total_count', self.count)
            ])),
            ('objects', data)
        ]))


def raise_validation_error(message):
    raise serializers.ValidationError({
        api_settings.NON_FIELD_ERRORS_KEY: [message]
    })


def log_api_call(func):
    """
        Handy function to wrap around view methods to log input and output for debugging.
    """
    @wraps(func)
    def func_wrapper(self, request, *args, **kwargs):
        print func.__name__, "called with", request, request.data, args, kwargs
        try:
            result = func(self, request, *args, **kwargs)
        except Exception as e:
            print "returning exception:", e
            raise
        print "returning to user", request.user, result.status_code, result.data
        return result
    return func_wrapper


parent_classes = {
    'folders': Folder,
}
def load_parent(func):
    """
        Decorator to set request.parent for nested views. For example, if we have

            /folders/1/folders/2

        And

            class FolderDetailView():

                @load_parent
                def get(request, pk):
                    ...

        This decorator will make sure that request.parent is set to Folder(pk=1),
        and that request.user is allowed to access that folder.

        For this to work, "folders" should be captured as parent_type in the urlconf, and "1" should be captured as parent_id.
    """
    @wraps(func)
    def func_wrapper(self, request, *args, **kwargs):
        parent_type = kwargs.pop('parent_type', None)
        parent_id = kwargs.pop('parent_id', None)

        if parent_type:
            ParentClass = parent_classes[parent_type]
            try:
                request.parent = ParentClass.objects.get(id=parent_id)
            except ParentClass.DoesNotExist:
                raise Http404
            if not request.parent.accessible_to(request.user):
                raise PermissionDenied()
        else:
            request.parent = None

        return func(self, request, *args, **kwargs)
    return func_wrapper


# Map allowed file extensions to mime types.
# WARNING: If you change this, also change `accept=""` in create-link.html
file_extension_lookup = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'pdf': 'application/pdf',
    'png': 'image/png',
    'gif': 'image/gif',
}


# Map allowed mime types to new file extensions and validation functions.
# We manually pick the new extension instead of using MimeTypes().guess_extension,
# because that varies between systems.
mime_type_lookup = {
    'image/jpeg': {
        'new_extension': 'jpg',
        'valid_file': lambda f: imghdr.what(f) == 'jpeg',
    },
    'image/png': {
        'new_extension': 'png',
        'valid_file': lambda f: imghdr.what(f) == 'png',
    },
    'image/gif': {
        'new_extension': 'gif',
        'valid_file': lambda f: imghdr.what(f) == 'gif',
    },
    'application/pdf': {
        'new_extension': 'pdf',
        'valid_file': lambda f: '%PDF-' in f.read(10),
    }
}


def get_mime_type(file_name):
    """ Return mime type (for a valid file extension) or None if file extension is unknown. """
    file_extension = file_name.rsplit('.', 1)[-1].lower()
    return file_extension_lookup.get(file_extension)
