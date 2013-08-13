from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse

from datetime import datetime
from urlparse import urlparse

from linky.models import Link
from linky.utils import base

def landing(request):
    """The landing page"""
    
    if request.user.id >= 0:
      linky_links = list(Link.objects.filter(created_by=request.user).order_by('-creation_timestamp'))
      
      for linky_link in linky_links:
        linky_link.id =  base.convert(linky_link.id, base.BASE10, base.BASE58)
        if linky_link.submitted_url.startswith('http://'):
          linky_link.submitted_url = linky_link.submitted_url[7:]
        elif linky_link.submitted_url.startswith('https://'):
          linky_link.submitted_url = linky_link.submitted_url[8:] 
        if len(linky_link.submitted_title) > 50:
          linky_link.submitted_title = linky_link.submitted_title[:50] + '...'
        if len(linky_link.submitted_url) > 79:
          linky_link.submitted_url = linky_link.submitted_url[:70] + '...'
    else:
      linky_links = list();
    
    context = {'host': request.get_host(), 'user': request.user, 'linky_links': linky_links, 'next': request.get_full_path()}
    context.update(csrf(request))

    return render_to_response('landing.html', context)
    
def single_linky(request, linky_id):
    """Given a Linky ID, serve it up. Vetting also takes place here. """

    int_id = base.convert(linky_id, base.BASE58, base.BASE10)

    if request.method == 'POST':
        # TODO: We're forced to use update here because we generate our hash on the model save. This whole thing
        # feels wrong. Evaluate.
        
        Link.objects.filter(id=int_id).update(vested = True, vested_by_editor = request.user, vested_timestamp = datetime.now())

        return HttpResponseRedirect('/%s/' % linky_id)
    else:

        link = get_object_or_404(Link, id=int_id)
        
        created_datestamp = link.creation_timestamp
        pretty_date = created_datestamp.strftime("%B %d, %Y %I:%M GMT")
    
        context = {'linky': link, 'pretty_date': pretty_date, 'user': request.user, 'next': request.get_full_path()}
    
        context.update(csrf(request))

    return render_to_response('single-linky.html', context)
    
def editor_home(request):
    """The the editor user's admin home """
    
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('auth_login'))


    linkys = Link.objects.filter(vested_by_editor=request.user).order_by('-vested_timestamp')
    linky_list = list(linkys)    

    for linky in linky_list:
        if linky.submitted_url[0:4] != 'http':
            linky.submitted_url = 'http://' + linky.submitted_url

    context = {'linky_list': linky_list, 'user': request.user, 'host': request.get_host()}

    return render_to_response('editor-list-view.html', context)