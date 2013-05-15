from django.contrib import admin
from django.conf.urls.defaults import patterns, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth import views as auth_views


admin.autodiscover()

urlpatterns = patterns('linky.views',

    # Common Pages
    url(r'^$', 'common.landing', name='landing'),
    
    #API routes
    url(r'^api/linky/?$', 'api.linky_post', name='api_linky_post'),
    
    # Session/account management
    url(r'^password/change/$', auth_views.password_change, {'template_name': 'registration/password_change_form.html'}, name='auth_password_change'),
    url(r'^login/?$', auth_views.login, {'template_name': 'registration/login.html'}, name='auth_login'),
    url(r'^logout/?$', auth_views.logout, {'template_name': 'registration/logout.html'}, name='auth_logout'),
    url(r'^register/?$', 'user_management.process_register', name='process_register'),
    url(r'^password/change/?$', auth_views.password_change, {'template_name': 'registration/password_change_form.html'}, name='auth_password_change'),
    url(r'^password/change/done/?$', auth_views.password_change_done, {'template_name': 'registration/password_change_done.html'},   name='auth_password_change_done'),
    url(r'^password/reset/?$', auth_views.password_reset, {'template_name': 'registration/password_reset_form.html'}, name='auth_password_reset'),
    url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/?$', auth_views.password_reset_confirm, {'template_name': 'registration/password_reset_confirm.html'}, name='auth_password_reset_confirm'),
    url(r'^password/reset/complete/?$', auth_views.password_reset_complete, {'template_name': 'registration/password_reset_complete.html'}, name='auth_password_reset_complete'),
    url(r'^password/reset/done/?$', auth_views.password_reset_done, {'template_name': 'registration/password_reset_done.html'}, name='auth_password_reset_done'),
    
    # Our Linky ID catchall
    url(r'^(?P<linky_id>[a-zA-Z0-9]+)/?$', 'common.single_linky', name='single_linky'),    
    
)

urlpatterns += staticfiles_urlpatterns()