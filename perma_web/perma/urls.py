from django.contrib import admin
from django.conf.urls import patterns, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

from .views.common import DirectTemplateView


admin.autodiscover()

guid_pattern = r'(?P<guid>[a-zA-Z0-9\-]+)'

urlpatterns = patterns('perma.views',

    # Common Pages
    url(r'^$', DirectTemplateView.as_view(template_name='landing.html', extra_context={'this_page':'landing'}), name='landing'),
    url(r'^tools/?$', DirectTemplateView.as_view(template_name='tools.html'), name='tools'),
    url(r'^about/?$', DirectTemplateView.as_view(template_name='about.html'), name='about'),
    url(r'^additional-resources/?$', DirectTemplateView.as_view(template_name='additional-resources.html'), name='additional_resources'),
    url(r'^faq/?$', DirectTemplateView.as_view(template_name='faq.html'), name='faq'),
    url(r'^copyright-policy/?$', DirectTemplateView.as_view(template_name='copyright_policy.html'), name='copyright_policy'),
    url(r'^terms-of-service/?$', DirectTemplateView.as_view(template_name='terms_of_service.html'), name='terms_of_service'),
    url(r'^privacy-policy/?$', DirectTemplateView.as_view(template_name='privacy_policy.html'), name='privacy_policy'),
    url(r'^stats/?$', 'common.stats', name='global_stats'),
    url(r'^contingency-plan/?$', DirectTemplateView.as_view(template_name='contingency_plan.html'), name='contingency_plan'),

    #API routes
    url(r'^api/linky/urldump/?$', 'api.urldump', name='urldump'),
    url(r'^api/linky/urldump/(?P<since>\d{4}-\d{2}-\d{2})/?', 'api.urldump', name='urldump_with_since'),
    url(r'^api/render/%s/?$' % guid_pattern, 'common.single_link_main_server', name='single_link_main_server'),
    
    #Services
    url(r'^service/email-confirm/?$', 'service.email_confirm', name='service_email_confirm'),
    url(r'^service/receive-feedback/?$', 'service.receive_feedback', name='service_receive_feedback'),
    url(r'^service/link/status/%s?/?$' % guid_pattern, 'service.link_status', name='service_link_status'),
    url(r'^service/stats/users/?$', 'service.stats_users', name='service_stats_users'),
    url(r'^service/stats/links/?$', 'service.stats_links', name='service_stats_links'),
    url(r'^service/stats/darchive-links/?$', 'service.stats_darchive_links', name='service_stats_darchive_links'),
    url(r'^service/stats/storage/?$', 'service.stats_storage', name='service_stats_storage'),
    url(r'^service/stats/vesting-org/?$', 'service.stats_vesting_org', name='service_stats_vesting_org'),
    url(r'^service/stats/registrar/?$', 'service.stats_registrar', name='service_stats_registrar'),
    url(r'^service/bookmarklet-create/$', 'service.bookmarklet_create', name='service.bookmarklet_create'),
    
    # Session/account management
    url(r'^login/?$', 'user_management.limited_login', {'template_name': 'registration/login.html'}, name='user_management_limited_login'),
    url(r'^login/not-active/?$', 'user_management.not_active', name='user_management_not_active'),
    url(r'^login/account-is-deactivated/?$', 'user_management.account_is_deactivated', name='user_management_account_is_deactivated'),
    url(r'^logout/?$', 'user_management.logout', name='auth_logout'),
    url(r'^register/?$', 'user_management.process_register', name='process_register'),
    url(r'^register/confirm/(?P<code>\w+)/$', 'user_management.register_email_code_confirmation', name='confirm_register'),
    url(r'^register/password/(?P<code>\w+)/$', 'user_management.register_email_code_password', name='register_password'),
    url(r'^register/email/?$', 'user_management.register_email_instructions', name='register_email_instructions'),
    url(r'^password/change/?$', auth_views.password_change, {'template_name': 'registration/password_change_form.html'}, name='auth_password_change'),
    url(r'^password/change/done/?$', auth_views.password_change_done, {'template_name': 'registration/password_change_done.html'},   name='auth_password_change_done'),
    url(r'^password/reset/?$', auth_views.password_reset, {'template_name': 'registration/password_reset_form.html'}, name='auth_password_reset'),
    url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/?$', auth_views.password_reset_confirm, {'template_name': 'registration/password_reset_confirm.html'}, name='auth_password_reset_confirm'),
    url(r'^password/reset/complete/?$', auth_views.password_reset_complete, {'template_name': 'registration/password_reset_complete.html'}, name='auth_password_reset_complete'),
    url(r'^password/reset/done/?$', auth_views.password_reset_done, {'template_name': 'registration/password_reset_done.html'}, name='auth_password_reset_done'),
    url(r'^manage/account/?$', 'user_management.manage_account', name='user_management_manage_account'),
    
    # Link management
    url(r'^manage/?$', RedirectView.as_view(url='/manage/create/', permanent=False)),
    url(r'^manage/create/?$', 'link_management.create_link', name='create_link'),
    url(r'^manage/create/upload?$', 'link_management.upload_file', name='upload_link'),
    url(r'^manage/dark-archive/%s/?$' % guid_pattern, 'link_management.dark_archive_link', name='dark_archive_link'),
    url(r'^manage/vest/%s/?$' % guid_pattern, 'link_management.vest_link', name='vest_link'),
    url(r'^manage/created-links(?P<path>/.*)?$', 'link_management.created_links', name='created_links'),
    url(r'^manage/vested-links(?P<path>/.*)?$', 'link_management.vested_links', name='vested_links'),

    # user management
    url(r'^manage/registrars/?$', 'user_management.manage_registrar', name='user_management_manage_registrar'),
    url(r'^manage/registrars/(?P<registrar_id>[a-zA-Z0-9]+)/?$', 'user_management.manage_single_registrar', name='user_management_manage_single_registrar'),
    url(r'^manage/vesting-organizations/?$', 'user_management.manage_vesting_org', name='user_management_manage_vesting_org'),
    url(r'^manage/vesting-organizations/(?P<vesting_org_id>[a-zA-Z0-9]+)/?$', 'user_management.manage_single_vesting_org', name='user_management_manage_single_vesting_org'),
    url(r'^manage/registrar-members/?$', 'user_management.manage_registrar_member', name='user_management_manage_registrar_member'),
    url(r'^manage/registrar-members/(?P<user_id>[a-zA-Z0-9]+)/?$', 'user_management.manage_single_registrar_member', name='user_management_manage_single_registrar_member'),
    url(r'^manage/registrar-members/(?P<user_id>[a-zA-Z0-9]+)/delete/?$', 'user_management.manage_single_registrar_member_delete', name='user_management_manage_single_registrar_member_delete'),
    url(r'^manage/registrar-members/(?P<user_id>[a-zA-Z0-9]+)/reactivate/?$', 'user_management.manage_single_registrar_member_reactivate', name='user_management_manage_single_registrar_member_reactivate'),
    url(r'^manage/users/?$', 'user_management.manage_user', name='user_management_manage_user'),
    url(r'^manage/users/(?P<user_id>[a-zA-Z0-9]+)/?$', 'user_management.manage_single_user', name='user_management_manage_single_user'),
    url(r'^manage/users/(?P<user_id>[a-zA-Z0-9]+)/delete/?$', 'user_management.manage_single_user_delete', name='user_management_manage_single_user_delete'),
    url(r'^manage/users/(?P<user_id>[a-zA-Z0-9]+)/reactivate/?$', 'user_management.manage_single_user_reactivate', name='user_management_manage_single_user_reactivate'),
    url(r'^manage/vesting-managers/?$', 'user_management.manage_vesting_manager', name='user_management_manage_vesting_manager'),
    url(r'^manage/vesting-managers/(?P<user_id>[a-zA-Z0-9]+)/?$', 'user_management.manage_single_vesting_manager', name='user_management_manage_single_vesting_manager'),
    url(r'^manage/vesting-managers/(?P<user_id>[a-zA-Z0-9]+)/delete/?$', 'user_management.manage_single_vesting_manager_delete', name='user_management_manage_single_vesting_manager_delete'),
    url(r'^manage/vesting-managers/(?P<user_id>[a-zA-Z0-9]+)/reactivate/?$', 'user_management.manage_single_vesting_manager_reactivate', name='user_management_manage_single_vesting_manager_reactivate'),
    url(r'^manage/vesting-members/?$', 'user_management.manage_vesting_member', name='user_management_manage_vesting_member'),
    url(r'^manage/vesting-members/(?P<user_id>[a-zA-Z0-9]+)/?$', 'user_management.manage_single_vesting_member', name='user_management_manage_single_vesting_member'),
    url(r'^manage/vesting-members/(?P<user_id>[a-zA-Z0-9]+)/delete/?$', 'user_management.manage_single_vesting_member_delete', name='user_management_manage_single_vesting_member_delete'),
    url(r'^manage/vesting-members/(?P<user_id>[a-zA-Z0-9]+)/reactivate/?$', 'user_management.manage_single_vesting_member_reactivate', name='user_management_manage_single_vesting_member_reactivate'),
    url(r'^manage/users/(?P<user_id>[a-zA-Z0-9]+)/add-registrar/?$', 'user_management.user_add_registrar', name='user_management_user_add_registrar'),
    url(r'^manage/users/(?P<user_id>[a-zA-Z0-9]+)/add-vesting-org/?$', 'user_management.user_add_vesting_org', name='user_management_user_add_vesting_org'),
#    url(r'^manage/batch-convert/?$', 'user_management.batch_convert', name='user_management_batch_convert'),
#    url(r'^manage/export/?$', 'user_management.export', name='user_management_export'),
#    url(r'^manage/custom-domain/?$', 'user_management.custom_domain', name='user_management_custom_domain'),
#    url(r'^manage/users/?$', 'manage.users', name='manage_users'),
#    url(r'^manage/account/?$', 'manage.account', name='manage_account'),
#    url(r'^manage/activity/?$', 'manage.activity', name='manage_activity'),

    url(r'^cdx$', 'common.cdx', name='cdx'),

    # Our Perma ID catchall
    url(r'^%s/?$' % guid_pattern, 'common.single_linky', name='single_linky'),
    
)

urlpatterns += staticfiles_urlpatterns()
