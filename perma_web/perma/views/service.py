from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse

import smtplib, json, logging
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def email_confirm(request):
    """A service that sends a linky message. This is temporary."""
    
    email_address = request.POST.get('email_address')
    linky_link = request.POST.get('linky_link')
    
    if not email_address and not linky_link:
        return HttpResponse(status=400)
    
    from_address = "info@perma.cc"
    to_address = email_address
    content = "%s \n\n(This link is the Perma link)" % linky_link

    msg = MIMEText(content)
    msg['Subject'] = "The Perma link you requested"
    msg['From'] = from_address
    msg['To'] = to_address

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(from_address, [to_address], msg.as_string())
    s.quit()

    response_object = {"sent": True}

    return HttpResponse(json.dumps(response_object), content_type="application/json", status=200)

def receive_feedback(request):
    """
    Take feedback data and send it off in an email
    """
    
    submitted_url = request.POST.get('submitted_url')
    visited_page = request.POST.get('visited_page')
    feedback_text = request.POST.get('feedback_text')
    
    from_address = "lil@law.harvard.edu"
    to_address = request.POST.get('user_email')
    content = '''Visited page: %s
    Feedback text
    _______________________________________
    %s
    _______________________________________

''' % (visited_page, feedback_text)
    logger.debug(content)

    msg = MIMEText(content)
    msg['Subject'] = "New Perma feedback"
    msg['From'] = from_address
    msg['To'] = to_address
        
    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    #s.sendmail(from_address, [to_address], msg.as_string())
    s.quit()
        
    response_object = {'submitted': 'true', 'content': content}

    return HttpResponse(json.dumps(response_object), content_type="application/json", status=201)
