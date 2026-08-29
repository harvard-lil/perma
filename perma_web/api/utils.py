import unicodedata
from collections import OrderedDict
from collections.abc import Mapping
from functools import wraps
import json

from django.conf import settings
from django.http import Http404
from django.urls import resolve, reverse
from django.urls.exceptions import NoReverseMatch
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.reverse import reverse as drf_reverse
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory
from rest_framework.views import exception_handler

from perma.models import Folder

import logging
logger = logging.getLogger(__name__)


class TastypiePagination(LimitOffsetPagination):
    """
        Modify DRF's LimitOffsetPagination to return results in the same format as paginated results returned by Tastypie. Omit count from output and use a false, large count internally to allow `next` links to work. This breaks the convention that the last page has a null `next` link -- instead, a consumer of the paginated API should follow next links until `objects` is an empty list.
    """

    # Enforce a hard cap on the page size. DRF's `max_limit` is only applied
    # when a `limit` query param is provided, so we also cap the resolved limit
    # in `get_limit()` to ensure the cap is always respected.
    max_limit = api_settings.PAGE_SIZE

    def get_limit(self, request):
        limit = super().get_limit(request)
        if limit is None:
            return None
        if self.max_limit is None:
            return limit
        return min(limit, self.max_limit)

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('meta', OrderedDict([
                ('limit', self.limit),
                ('next', self.get_next_link()),
                ('offset', self.offset),
                ('previous', self.get_previous_link())
            ])),
            ('objects', data)
        ]))

    def get_count(self, queryset):
        return 2**31

class LongTastypiePagination(TastypiePagination):
    max_limit = settings.API_LONG_PAGE_SIZE

class LimitedTastypiePagination(TastypiePagination):
    """
        Limits users to the first API_MAX_PAGES pages to prevent expensive database queries.
    """
    max_pages = settings.API_MAX_PAGES

    def paginate_queryset(self, queryset, request, view=None):
        self.limit = self.get_limit(request)

        # Defensive coding:
        # disabling pagination isn't currently possible, because we have
        # PAGE_SIZE: 300 in our REST_FRAMEWORK configuration, but, double check
        # here so this code doesn't error out if that ever changes.
        if self.limit is None:
            return None

        self.offset = self.get_offset(request)

        # Calculate max offset based on limit and max_pages
        max_offset = self.limit * (self.max_pages - 1)

        if self.offset > max_offset:
            raise ValidationError({
                'offset': f'Maximum offset is {max_offset}. Results are limited to {self.max_pages} pages to prevent expensive queries.'
            })

        # Continue with normal pagination
        return super().paginate_queryset(queryset, request, view)


def raise_general_validation_error(message):
    raise serializers.ValidationError({
        api_settings.NON_FIELD_ERRORS_KEY: [message]
    })

def raise_invalid_capture_job(capture_job, err):
    error_dict = err if isinstance(err, Mapping) else {
        api_settings.NON_FIELD_ERRORS_KEY: [err]
    }
    capture_job.message = json.dumps(error_dict)
    capture_job.save(update_fields=['message'])
    raise serializers.ValidationError(error_dict)

def log_api_call(func):
    """
        Handy function to wrap around view methods to log input and output for debugging.
    """
    @wraps(func)
    def func_wrapper(self, request, *args, **kwargs):
        print(func.__name__, "called with", request, request.data, args, kwargs)
        try:
            result = func(self, request, *args, **kwargs)
        except Exception as e:
            print("returning exception:", e)
            raise
        print("returning to user", request.user, result.status_code, result.data)
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


def _image_type(file_obj):
    position = file_obj.tell()
    header = file_obj.read(32)
    file_obj.seek(position)

    if header[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    if header[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    if header[6:10] in (b'JFIF', b'Exif') or header[:4] == b'\xff\xd8\xff\xdb':
        return 'jpeg'
    return None


# Map allowed mime types to new file extensions and validation functions.
# We manually pick the new extension instead of using MimeTypes().guess_extension,
# because that varies between systems.
mime_type_lookup = {
    'image/jpeg': {
        'new_extension': 'jpg',
        'valid_file': lambda f: _image_type(f) == 'jpeg',
    },
    'image/png': {
        'new_extension': 'png',
        'valid_file': lambda f: _image_type(f) == 'png',
    },
    'image/gif': {
        'new_extension': 'gif',
        'valid_file': lambda f: _image_type(f) == 'gif',
    },
    'application/pdf': {
        'new_extension': 'pdf',
        'valid_file': lambda f: b'%PDF-' in f.read(10),
    }
}


def get_mime_type(file_name):
    """ Return mime type (for a valid file extension) or None if file extension is unknown. """
    file_extension = file_name.rsplit('.', 1)[-1].lower()
    return file_extension_lookup.get(file_extension)

def url_is_invalid_unicode(url_string):
    """ Check for unicode control characters in URL """
    for x in str(url_string):
        if unicodedata.category(x)[0] == "C":
            return True
    return False

def reverse_api_view(viewname, *args, **kwargs):
    # Requires request as a kwarg.
    #
    # Reverse needs to be called with the api namespace when the
    # request is made to perma.cc/api, and cannot be called with
    # a namespace when the request is made to api.perma.cc
    try:
        return drf_reverse('api:' + viewname, *args, **kwargs)
    except NoReverseMatch:
        return drf_reverse(viewname, *args, **kwargs)

def reverse_api_view_relative(viewname, *args, **kwargs):
    # Reverse needs to be called with the api namespace when the
    # request is made to perma.cc/api, and cannot be called with
    # a namespace when the request is made to api.perma.cc
    try:
        return reverse('api:' + viewname, *args, **kwargs)
    except NoReverseMatch:
        return reverse(viewname, *args, **kwargs)


def dispatch_multiple_requests(request, call_list, custom_request_attributes=None):
    """
    Makes a series of internal api "calls" on behalf of a user,
    all within a single http request/response cycle.

    The first argument should be the Django request object from the initiating
    api call.

    The call_list should be series of dictionaries specifying:
        "path", the api route to "call" (e.g. /v1/folders/22/archives/)
        "verb", the http verb to use (e.g. "GET")
        (optional)
        "data": a dictionary of data to send with the request,
                i.e., the data that would normally be sent as JSON
                when hitting the api route

    If you need to customize the request object passed to the
    api's view function, pass a dict of attribute/value pairs.
    For example, {"parent": 1} will set request.parent = 1 on
    every generated request object.

    A list of dictionaries will be returned reporting:
        "status_code": the http status code returned by the "call"
        "status_text": the text associated with the http status code
        "data": the data returned by the call, i.e., the data that would
                normally be converted to JSON and transmitted as the http body
    """
    factory = APIRequestFactory()
    responses = []
    for call in call_list:
        try:
            view, args, kwargs = resolve(call['path'])
            new_request = getattr(factory, call['verb'].lower())(call['path'], data=call.get('data', {}))
            new_request.user = request.user
            new_request.META['HTTP_HOST'] = request._get_raw_host()
            if custom_request_attributes:
                for attribute, value in custom_request_attributes.items():
                    setattr(new_request, attribute, value)
            response = view(new_request, *args, **kwargs)
        except Exception as exception:
            response = exception_handler(exception, {})
            if not response:
                logger.exception("Internal Server Error")
                class SpoofResponse:
                    pass
                response = SpoofResponse()
                response.status_code = 500
                response.status_text = 'Internal Server Error',
                response.data = {
                    'path': call['path'],
                    'verb': call['verb'],
                    'data': call['data']
                }
        responses.append({
            'status_code': response.status_code,
            'status_text': response.status_text,
            'data': response.data
        })
    return responses


def get_download_file_format(request):
    file_format = request.query_params.get('file_format', 'warc')
    supported_formats = ['warc', 'wacz']
    if file_format not in supported_formats:
        raise ValidationError({
            "file_format": f"The specified format is not supported. Options: {', '.join(supported_formats)}."
        })
    return file_format


def get_download_url(request, link, file_format='warc'):
    view_name = "archives_download"
    match file_format:
        case 'warc':
            if link.warc_size or link.wacz_size:
                return reverse_api_view(view_name, kwargs={'guid': link.guid}, request=request)
            return None
        case 'wacz':
            if link.wacz_size:
                base_url = reverse_api_view(view_name, kwargs={'guid': link.guid}, request=request)
                return f"{base_url}?file_format=wacz"
            return None
        case _:
            raise NotImplementedError("Unsupported file format.")

