import json
from django.utils import timezone

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse

from django.shortcuts import render, get_object_or_404

from ..models import UncaughtError

@login_required
@user_passes_test(lambda user: user.is_staff)
def get_all(request):
    errors = UncaughtError.objects.filter(resolved=False).order_by('-created_at')[:40]
    return render(request, 'errors/view.html', {'errors': errors})

@login_required
@user_passes_test(lambda user: user.is_staff)
def resolve(request):
    error = get_object_or_404(UncaughtError, pk=request.POST.get('error_id'))
    error.resolved = True
    error.resolved_by_user = request.user
    error.save()
    return HttpResponse(status=200)

@csrf_exempt
def post_new(request):
    created_at = timezone.now()
    error = UncaughtError.objects.create(created_at=created_at)

    try:
        body = json.loads(request.body)
        e = body["errors"][0]
        context = body["context"]
    except:
        e = {}
        context = {}

    error.user_agent=context.get("userAgent")
    error.current_url=context.get("url", request.META.get('HTTP_REFERER'))
    error.message=e.get("message")
    error.stack=e.get("backtrace")
    if not request.user.is_anonymous():
        error.user = request.user
    error.save()
    return HttpResponse(status=200)
