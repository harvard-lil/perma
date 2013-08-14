from django.contrib import admin
from django.conf.urls import patterns, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth import views as auth_views


admin.autodiscover()

urlpatterns = patterns('linky.views',

    # Common Pages
    url(r'^$', 'common.landing', name='landing'),
    url(r'^editor/?$', 'common.editor_home', name='editor_home'),
    url(r'^about/?$', 'common.about', name='about'),
    url(r'^faq/?$', 'common.faq', name='faq'),
    url(r'^contact/?$', 'common.contact', name='contact'),
    url(r'^terms-of-service/?$', 'common.terms_of_service', name='terms_of_service'),
    url(r'^privacy-policy/?$', 'common.privacy_policy', name='privacy_policy'),
    
    #API routes
    url(r'^api/linky/upload?$', 'api.upload_file', name='api_linky_upload'),
    url(r'^api/linky/?$', 'api.linky_post', name='api_linky_post'),
    
    #Services
    url(r'^service/email-confirm/?$', 'service.email_confirm', name='service_email_confirm'),
    
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
    
    # Manage/Linky Admin routes
    #url(r'^manage/?$', 'user_management.landing', name='user_management_landing'),
    url(r'^manage/?$', 'user_management.created_links', name='user_management_created_links'),
    url(r'^manage/registrars/?$', 'user_management.manage_registrar', name='user_management_manage_registrar'),
    url(r'^manage/registrars/(?P<registrar_id>[a-zA-Z0-9]+)/?$', 'user_management.manage_single_registrar', name='user_management_manage_single_registrar'),
    url(r'^manage/registrar-members/?$', 'user_management.manage_registrar_member', name='user_management_manage_registrar_member'),
    url(r'^manage/registrar-members/(?P<user_id>[a-zA-Z0-9]+)/?$', 'user_management.manage_single_registrar_member', name='user_management_manage_single_registrar_member'),
    url(r'^manage/registrar-members/(?P<user_id>[a-zA-Z0-9]+)/delete/?$', 'user_management.manage_single_registrar_member_delete', name='user_management_manage_single_registrar_member_delete'),
    url(r'^manage/journal-members/?$', 'user_management.manage_journal_member', name='user_management_manage_journal_member'),
    url(r'^manage/journal-members/(?P<user_id>[a-zA-Z0-9]+)/?$', 'user_management.manage_single_journal_member', name='user_management_manage_single_journal_member'),
    url(r'^manage/journal-members/(?P<user_id>[a-zA-Z0-9]+)/delete/?$', 'user_management.manage_single_journal_member_delete', name='user_management_manage_single_journal_member_delete'),
    url(r'^manage/created-links/?$', 'user_management.created_links', name='user_management_created_links'),
    url(r'^manage/vested-links/?$', 'user_management.vested_links', name='user_management_vested_links'),
    url(r'^manage/sponsoring-library/?$', 'user_management.sponsoring_library', name='user_management_sponsoring_library'),
    url(r'^manage/account/?$', 'user_management.manage_account', name='user_management_manage_account'),
    url(r'^manage/batch-convert/?$', 'user_management.batch_convert', name='user_management_batch_convert'),
    url(r'^manage/export/?$', 'user_management.export', name='user_management_export'),
    url(r'^manage/custom-domain/?$', 'user_management.custom_domain', name='user_management_custom_domain'),
#    url(r'^manage/users/?$', 'manage.users', name='manage_users'),
#    url(r'^manage/account/?$', 'manage.account', name='manage_account'),
#    url(r'^manage/activity/?$', 'manage.activity', name='manage_activity'),
    
    # Our Linky ID catchall
    url(r'^(?P<linky_guid>[a-zA-Z0-9]+)/?$', 'common.single_linky', name='single_linky'),    
    
)

urlpatterns += staticfiles_urlpatterns()
