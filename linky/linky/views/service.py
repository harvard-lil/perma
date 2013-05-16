from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt

import smtplib
from email.mime.text import MIMEText


# TODO: If we're going to csrf exempt this, we should keep an eye on things
@csrf_exempt
def email_confirm(request):
    """A service that sends a linky message. This is temporary."""
    
    email_address = request.POST.get('email_address')
    linky_link = request.POST.get('linky_link')
    
    if not email_address and not linky_link:
        return HttpResponse(status=400)
    
    # TODO: we should obviously only send messages that we send.
    # lock this down.
    
    from_address = "lil@law.harvard.edu"
    to_address = email_address
    content = "%s \n\nThis linky is 4-eva" % linky_link

    msg = MIMEText(content)
    msg['Subject'] = "The Linky link you requested"
    msg['From'] = from_address
    msg['To'] = to_address

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(from_address, [to_address], msg.as_string())
    s.quit()

    response_object = {"sent": True}

    return HttpResponse(json.dumps(response_object), content_type="application/json", status=200)
