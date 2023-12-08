from django.http import HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import render

def csrf_failure(request, reason="CSRF Failure."):
    '''
        Custom view for CSRF failures, required for proper rendering of
        our custom template.
    '''
    return HttpResponseForbidden(render(request, '403_csrf.html'))

def server_error(request):
    '''
        Custom view for 500 failures, required for proper rendering of
        our custom template.
        https://github.com/django/django/blob/master/django/views/defaults.py#L97
    '''
    return HttpResponseServerError(render(request, '500.html'))
