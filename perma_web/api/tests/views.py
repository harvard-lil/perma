from django.http import HttpResponse


def redirect_to_file(request):
    # Use a plain HttpResponse to avoid all the built-in protections
    # Django has, attempting to prevent exactly this
    response = HttpResponse('We are up to no good.', status=301)
    response.url = response['Location'] = 'file:///etc/passwd'
    return response
