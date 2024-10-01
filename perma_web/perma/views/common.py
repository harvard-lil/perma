from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, NoReverseMatch
from django.views.generic import TemplateView

from perma.models import Link


class DirectTemplateView(TemplateView):
    extra_context = None

    def get_context_data(self, **kwargs):
        """ Override Django's TemplateView to allow passing in extra_context. """
        context = super(self.__class__, self).get_context_data(**kwargs)
        if self.extra_context is not None:
            for key, value in self.extra_context.items():
                if callable(value):
                    context[key] = value()
                else:
                    context[key] = value
        return context


def landing(request):
    """
    The landing page
    """
    if request.user.is_authenticated and request.get_host() not in request.META.get('HTTP_REFERER',''):
        return HttpResponseRedirect(reverse('create_link'))
    else:
        return render(request, 'landing.html', {
            'this_page': 'landing',
        })


def rate_limit(request, exception):
    """
    When a user hits a rate limit, send them here.
    """
    return render(request, "rate_limit.html")


def robots_txt(request):
    """
    robots.txt
    """
    from ..urls import urlpatterns

    disallowed_prefixes = ['_', 'archive-', 'api_key', 'errors', 'log', 'manage', 'password', 'register', 'service', 'settings', 'sign-up']
    allow = ['/$']
    # some urlpatterns do not have names
    names = [urlpattern.name for urlpattern in urlpatterns if urlpattern.name is not None]
    for name in names:
        # urlpatterns that take parameters can't be reversed
        try:
            url = reverse(name)
            disallowed = any(url[1:].startswith(prefix) for prefix in disallowed_prefixes)
            if not disallowed and url != '/':
                allow.append(url)
        except NoReverseMatch:
            pass
    disallow = list(Link.GUID_CHARACTER_SET) + disallowed_prefixes
    return render(request, 'robots.txt', {'allow': allow, 'disallow': disallow}, content_type='text/plain; charset=utf-8')
