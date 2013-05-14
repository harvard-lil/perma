from django.shortcuts import render_to_response

def landing(request):
    """The landing page"""

    return render_to_response('landing.html')