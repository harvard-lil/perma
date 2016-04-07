from django.utils import timezone

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse

from django.shortcuts import get_object_or_404, render

from ..models import UncaughtError

@login_required
@user_passes_test(lambda user: user.is_staff)
def get_all(request):
    errors = UncaughtError.objects.filter(resolved=False).order_by('-created_at')
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

    error.current_url=request.POST.get('current_url')
    error.user_agent=request.POST.get('user_agent')
    error.stack=request.POST.get('stack')
    error.name=request.POST.get('name')
    error.message=request.POST.get('message')
    error.custom_message=request.POST.get('custom_message')

    try:
        error.user = request.user
    except ValueError as e:
        pass

    error.save()

    return HttpResponse(status=200)
