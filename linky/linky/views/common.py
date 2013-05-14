from django.shortcuts import render_to_response, get_object_or_404

from linky.models import Link

def landing(request):
    """The landing page"""

    return render_to_response('landing.html', {'host': request.get_host()})
    
def single_linky(request, linky_id):
    """Given a Linky ID, serve it up """

    link = get_object_or_404(Link, hash_id=linky_id)

    created_datestamp = link.creation_time
    pretty_date = created_datestamp.strftime("%B %d, %Y %I:%M GMT")

    return render_to_response('single-linky.html', {'linky_id': link.hash_id, 'pretty_date': pretty_date, 'indexed_url': link.submitted_url})