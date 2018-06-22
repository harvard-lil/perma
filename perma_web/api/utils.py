import unicodedata
import imghdr
from collections import OrderedDict, Mapping
from functools import wraps
import json

from django.http import Http404
from django.urls import resolve, reverse
from django.urls.exceptions import NoReverseMatch
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
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
                class SpoofResponse(object):
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
