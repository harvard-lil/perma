import logging
from django.utils import timezone

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from django.shortcuts import get_object_or_404, render

from ..models import UncaughtError

# logger = logging.getLogger(__name__)
# valid_link_sorts = ['-creation_timestamp', 'creation_timestamp', 'submitted_title', '-submitted_title']

@login_required
@user_passes_test(lambda user: user.is_staff)
def get_all(request):
    errors = UncaughtError.objects.filter(resolved=False).all().order_by('-created_at')
    return render(request, 'errors/view.html', {'errors': errors})

@login_required
@user_passes_test(lambda user: user.is_staff)
def resolve(request):
    error_id = request.POST['error_id']
    error = UncaughtError.objects.get(id=error_id)
    error.resolved = True
    error.resolved_by_user = request.user.id
    error.save()

    return HttpResponse("ok")

def post_new(request):
    data = request.POST
    created_at = timezone.now()
    error = UncaughtError.objects.create(created_at=created_at)

    error.current_url=data['current_url']
    error.user_agent=data['user_agent']
    error.stack=data['stack']
    error.name=data['name']
    error.message=data['message']
    error.custom_message=data['custom_message']
    error.user_id=request.user.id
    error.save()

    response = HttpResponse(status=200)
    return response
