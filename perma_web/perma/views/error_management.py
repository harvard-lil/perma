import json
from django.utils import timezone

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse

from django.shortcuts import render

from ..models import UncaughtError

@login_required
@user_passes_test(lambda user: user.is_staff)
def get_all(request):
    errors = UncaughtError.objects.filter(resolved=False).order_by('-created_at')[:40]
    return render(request, 'errors/view.html', {'errors': errors})

@login_required
@user_passes_test(lambda user: user.is_staff)
def resolve(request):
    error_id = request.POST.get('error_id')
    try:
        error = UncaughtError.objects.get(id=error_id)
        error.resolved = True
        error.resolved_by_user = request.user
        error.save()
    except:
        pass
    return HttpResponse(status=200)

@csrf_exempt
def post_new(request):
    created_at = timezone.now()
    error = UncaughtError.objects.create(created_at=created_at)
    try:
        body = json.loads(request.body)

        e = body["errors"][0]
        context = body["context"]
        error.user_agent=context["userAgent"]
        error.current_url=body["context"]["url"]
        error.message=e["message"]
        error.stack=e["backtrace"]
        error.user = request.user
        error.save()
    except ValueError as e:
        pass
    return HttpResponse(status=200)
