from django.conf import settings
from django.template.loader import render_to_string

def analytics(request):
    """
    Returns analytics code.
    """
    if not settings.DEBUG:
      return { 'analytics_code': render_to_string("analytics.html", { 'google_analytics_key': settings.GOOGLE_ANALYTICS_KEY, 'google_analytics_domain': settings.GOOGLE_ANALYTICS_DOMAIN}), 'requested_host': request.get_host(), 'determined_host': settings.HOST }
    else:
      return { 'analytics_code': "Google Analytics would go here if we weren't in DEBUG", 'requested_host': request.get_host(), 'determined_host': request.get_host() }
      #return { 'analytics_code': render_to_string("analytics.html", { 'google_analytics_key': settings.GOOGLE_ANALYTICS_KEY, 'google_analytics_domain': settings.GOOGLE_ANALYTICS_DOMAIN }) }