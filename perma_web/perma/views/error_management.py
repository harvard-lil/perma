import logging
from django.utils import timezone

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

# from ..models import Link, Folder, Organization

# logger = logging.getLogger(__name__)
# valid_link_sorts = ['-creation_timestamp', 'creation_timestamp', 'submitted_title', '-submitted_title']



@login_required
# @user_passes_test(lambda user: user.is_staff)
def get_all(request):
    return render(request, 'errors/view.html')


def post_new(request):
    print "posting new error"
    data = request.POST
    created_at = timezone.now()
    error.error = UncaughtError.objects.create(created_at=created_at)
    error.save()

    error.current_url=data['current_url']
    error.user_agent=data['user_agent']
    error.error_stack=data['error_stack']
    error.error_name=data['error_name']
    error.error_message=data['error_message']
    error.error_custom_message=data['error_custom_message']
    error.save()

    response = HttpResponse()
    return response

    return
