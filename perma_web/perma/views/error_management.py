import collections
import json

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from perma.utils import user_passes_test_or_403

from ..models import UncaughtError


@user_passes_test_or_403(lambda user: user.is_staff)
def get_all(request):
    errors = UncaughtError.objects.filter(resolved=False).order_by('-created_at')[:40]
    return render(request, 'errors/view.html', {'errors': errors})

@user_passes_test_or_403(lambda user: user.is_staff)
def resolve(request):
    error = get_object_or_404(UncaughtError, pk=request.POST.get('error_id'))
    error.resolved = True
    error.resolved_by_user = request.user
    error.save()
    return HttpResponse(status=200)

@csrf_exempt
def post_new(request):
    try:
        body = json.loads(str(request.body,'utf-8'))
    except ValueError:
        body = ''
    e = {}
    context = {}
    if isinstance(body, collections.Mapping):
        e = body.get("errors", [{}])[0]
        context = body.get("context", {})
    error = UncaughtError(
        user_agent=context.get("userAgent"),
        current_url=context.get("url", request.META.get('HTTP_REFERER')),
        message=e.get("message"),
        stack=json.dumps(e.get("backtrace")),
        user=None if request.user.is_anonymous() else request.user)
    error.save()
    return HttpResponse(status=200)

def csrf_failure(request, reason="CSRF Failure."):
    '''
        Custom view for CSRF failures, required for proper rendering of
        our custom template.
    '''
    return render(request, '403_csrf.html')

def server_error(request):
    '''
        Custom view for 500 failures, required for proper rendering of
        our custom template.
    '''
    return render(request, '500.html')
