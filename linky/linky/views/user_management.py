import logging

from linky.forms import EditorRegForm

from django.http import  HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.core.context_processors import csrf
from django.contrib import auth

logger = logging.getLogger(__name__)

try:
    from linky.local_settings import *
except ImportError, e:
    logger.error('Unable to load local_settings.py:', e)


def process_register(request):
    """Register a new user"""
    c = {}
    c.update(csrf(request))

    if request.method == 'POST':

        reg_key = request.POST.get('reg_key', '')
                
        editor_reg_form = EditorRegForm(request.POST, prefix = "a")
        
        if editor_reg_form.is_valid():
            new_user = editor_reg_form.save()

            new_user.backend='django.contrib.auth.backends.ModelBackend'
            auth.login(request, new_user)
            
            return HttpResponseRedirect(reverse('landing'))
        
        else:
            c.update({'editor_reg_form': editor_reg_form,})
                      
            return render_to_response('registration/register.html', c)
    else:
        editor_reg_form = EditorRegForm(prefix = "a")
        
        c.update({'editor_reg_form': editor_reg_form,})
        return render_to_response("registration/register.html", c)