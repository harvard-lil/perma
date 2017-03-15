# Views that only load when we are running tests:

from django.http import HttpResponse
from perma.utils import get_client_ip


def client_ip(request):
    return HttpResponse(get_client_ip(request))