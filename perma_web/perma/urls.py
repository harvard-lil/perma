from django.conf import settings
from django.conf.urls import patterns, url
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

from .views.common import DirectTemplateView


guid_pattern = r'(?P<guid>[a-zA-Z0-9\-]+)'

urlpatterns = patterns('perma.views',

    # Common Pages
    url(r'^$', 'common.landing', name='landing'),
    url(r'^tools/?$', DirectTemplateView.as_view(template_name='tools.html'), name='tools'),
    url(r'^about/?$', 'common.about', name='about'),
    url(r'^additional-resources/?$', DirectTemplateView.as_view(template_name='additional-resources.html'), name='additional_resources'),
    url(r'^copyright-policy/?$', DirectTemplateView.as_view(template_name='copyright_policy.html'), name='copyright_policy'),
    url(r'^terms-of-service/?$', DirectTemplateView.as_view(template_name='terms_of_service.html'), name='terms_of_service'),
    url(r'^privacy-policy/?$', DirectTemplateView.as_view(template_name='privacy_policy.html'), name='privacy_policy'),
    url(r'^stats/?$', 'common.stats', name='global_stats'),
    url(r'^contingency-plan/?$', DirectTemplateView.as_view(template_name='contingency_plan.html'), name='contingency_plan'),
    url(r'^contact/?$', 'common.contact', name='contact'),
    url(r'^contact/thanks/?$', DirectTemplateView.as_view(template_name='contact-thanks.html'), name='contact_thanks'),
#   url(r'^is500/?$', DirectTemplateView.as_view(template_name='500.html'), name='is500'),
#	url(r'^is404/?$', DirectTemplateView.as_view(template_name='404.html'), name='is404'),
	url(r'^landing-new/?$', DirectTemplateView.as_view(template_name='landing-new.html'), name='landing-new'),
   
    #Docs 
    url(r'^docs/?$', DirectTemplateView.as_view(template_name='docs/index.html'), name='docs'),
    url(r'^docs/perma-link-creation/?$', DirectTemplateView.as_view(template_name='docs/perma-link-creation.html'), name='docs_perma_link_creation'),
    url(r'^docs/perma-link-vesting/?$', DirectTemplateView.as_view(template_name='docs/perma-link-vesting.html'), name='docs_perma_link_vesting'),
    url(r'^docs/perma-archive/?$', DirectTemplateView.as_view(template_name='docs/perma-archive.html'), name='docs_perma_archive'),
    url(r'^docs/libraries/?$', DirectTemplateView.as_view(template_name='docs/libraries.html'), name='docs_libraries'),
    url(r'^docs/perma-dark-archive/?$', DirectTemplateView.as_view(template_name='docs/perma-dark-archive.html'), name='docs_perma_dark_archive'),
    url(r'^docs/copyright/?$', DirectTemplateView.as_view(template_name='docs/copyright.html'), name='docs_copyright'),
    url(r'^docs/getting-started/?$', DirectTemplateView.as_view(template_name='docs/getting-started.html'), name='docs_getting-started'),
    url(r'^docs/mirrors/?$', DirectTemplateView.as_view(template_name='docs/mirrors.html'), name='docs_mirrors'),
    url(r'^docs/robustness/?$', DirectTemplateView.as_view(template_name='docs/robustness.html'), name='docs_robustness'),
    url(r'^docs/perma-user-roles/?$', DirectTemplateView.as_view(template_name='docs/perma-user-roles.html'), name='docs_perma_user_roles'),
    url(r'^docs/faq/?$', 'common.faq', name='docs_faq'),
    url(r'^docs/organizations/?$', DirectTemplateView.as_view(template_name='docs/organizations.html'), name='docs_organizations'),
    
    #Developer docs
    url(r'^docs/developer/?$', DirectTemplateView.as_view(template_name='docs/developer/index.html'), name='dev_docs'),
    url(r'^docs/developer/public/?$', DirectTemplateView.as_view(template_name='docs/developer/public.html'), name='docs_developer_public'),
    url(r'^docs/developer/user-profile/?$', DirectTemplateView.as_view(template_name='docs/developer/user-profile.html'), name='docs_developer_user_profile'),
    url(r'^docs/developer/archives/?$', DirectTemplateView.as_view(template_name='docs/developer/archives.html'), name='docs_developer_archives'),
    url(r'^docs/developer/folders/?$', DirectTemplateView.as_view(template_name='docs/developer/folders.html'), name='docs_developer_folders'),

    #API routes
    url(r'^api/linky/urldump/?$', 'api.urldump', name='urldump'),
    url(r'^api/linky/urldump/(?P<since>\d{4}-\d{2}-\d{2})/?', 'api.urldump', name='urldump_with_since'),
    
    #Services
    url(r'^service/email-confirm/?$', 'service.email_confirm', name='service_email_confirm'),
    url(r'^service/receive-feedback/?$', 'service.receive_feedback', name='service_receive_feedback'),
    url(r'^service/stats/users/?$', 'service.stats_users', name='service_stats_users'),
    url(r'^service/stats/links/?$', 'service.stats_links', name='service_stats_links'),
    url(r'^service/stats/darchive-links/?$', 'service.stats_darchive_links', name='service_stats_darchive_links'),
    url(r'^service/stats/storage/?$', 'service.stats_storage', name='service_stats_storage'),
    url(r'^service/stats/org/?$', 'service.stats_org', name='service_stats_org'),
    url(r'^service/stats/registrar/?$', 'service.stats_registrar', name='service_stats_registrar'),
    url(r'^service/bookmarklet-create/$', 'service.bookmarklet_create', name='service.bookmarklet_create'),
    url(r'^service/image-wrapper/%s?/?$' % guid_pattern, 'service.image_wrapper', name='service_image_wrapper'),
    url(r'^service/thumbnail/%s/thumbnail.png$' % guid_pattern, 'service.get_thumbnail', name='service_get_thumbnail'),

    # Session/account management
    url(r'^login/?$', 'user_management.limited_login', {'template_name': 'registration/login.html'}, name='user_management_limited_login'),
    url(r'^login/not-active/?$', 'user_management.not_active', name='user_management_not_active'),
    url(r'^login/account-is-deactivated/?$', 'user_management.account_is_deactivated', name='user_management_account_is_deactivated'),
    url(r'^logout/?$', 'user_management.logout', name='logout'),
    url(r'^register/?$', RedirectView.as_view(url='/sign-up/', permanent=True)),

    url(r'^sign-up/?$', 'user_management.sign_up', name='sign_up'),
    url(r'^sign-up/courts/?$', 'user_management.sign_up_courts', name='sign_up_courts'),
    url(r'^sign-up/faculty/?$', 'user_management.sign_up_faculty', name='sign_up_faculty'),
    url(r'^sign-up/journals/?$', 'user_management.sign_up_journals', name='sign_up_journals'),
    url(r'^libraries/?$', 'user_management.libraries', name='libraries'),
    #url(r'^register/confirm/(?P<code>\w+)/$', 'user_management.register_email_code_confirmation', name='confirm_register'),
    url(r'^register/password/(?P<code>\w+)/$', 'user_management.register_email_code_password', name='register_password'),
    url(r'^register/email/?$', 'user_management.register_email_instructions', name='register_email_instructions'),
    url(r'^register/library/?$', 'user_management.register_library_instructions', name='register_library_instructions'),
    url(r'^register/court/?$', 'user_management.court_request_response', name='court_request_response'),
    url(r'^password/change/?$', auth_views.password_change, {'template_name': 'registration/password_change_form.html'}, name='password_change'),
    url(r'^password/change/done/?$', auth_views.password_change_done, {'template_name': 'registration/password_change_done.html'},   name='password_change_done'),
    url(r'^password/reset/?$', auth_views.password_reset, {'template_name': 'registration/password_reset_form.html'}, name='password_reset'),
    url(r'^password/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', auth_views.password_reset_confirm, {'template_name': 'registration/password_reset_confirm.html'}, name='password_reset_confirm'),
    url(r'^password/reset/complete/?$', auth_views.password_reset_complete, {'template_name': 'registration/password_reset_complete.html'}, name='password_reset_complete'),
    url(r'^password/reset/done/?$', auth_views.password_reset_done, {'template_name': 'registration/password_reset_done.html'}, name='password_reset_done'),
    url(r'^api_key/create/?$', 'user_management.api_key_create', name='api_key_create'),

    # Settings
    url(r'^settings/profile/?$', 'user_management.settings_profile', name='user_management_settings_profile'),
    url(r'^settings/password/?$', 'user_management.settings_password', name='user_management_settings_password'),
    url(r'^settings/organizations/?$', 'user_management.settings_organizations', name='user_management_settings_organizations'),
    url(r'^settings/organizations-change-privacy/(?P<org_id>[a-zA-Z0-9]+)/', 'user_management.settings_organizations_change_privacy', name='user_management_settings_organizations_change_privacy'),
    url(r'^settings/tools/?$', 'user_management.settings_tools', name='user_management_settings_tools'),

    # Link management
    url(r'^manage/?$', RedirectView.as_view(url='/manage/create/', permanent=False)),
    url(r'^manage/create/?$', 'link_management.create_link', name='create_link'),
    url(r'^manage/create/(?P<org_id>[a-zA-Z0-9]+)/?$', 'link_management.create_link_with_org', name='create_link_with_org'),
    url(r'^manage/delete-link/%s/?$' % guid_pattern, 'link_management.user_delete_link', name='user_delete_link'),
    url(r'^manage/links/folder/(?P<folder_id>.+?)/?$', 'link_management.folder_contents', name='folder_contents'),
    url(r'^manage/links(?P<path>/.*)?$', RedirectView.as_view(url='/manage/create/', permanent=False), name='link_browser'), # we used to serve an important page here. No longer. Redirect in case anyone has this bookmakred.

    # user management
    url(r'^manage/registrars/?$', 'user_management.manage_registrar', name='user_management_manage_registrar'),
    url(r'^manage/registrars/(?P<registrar_id>[a-zA-Z0-9]+)/?$', 'user_management.manage_single_registrar', name='user_management_manage_single_registrar'),
    url(r'^manage/registrars/approve/(?P<registrar_id>[a-zA-Z0-9]+)/?$', 'user_management.approve_pending_registrar', name='user_management_approve_pending_registrar'),
    url(r'^manage/organizations/?$', 'user_management.manage_organization', name='user_management_manage_organization'),
    url(r'^manage/organizations/(?P<org_id>[a-zA-Z0-9]+)/?$', 'user_management.manage_single_organization', name='user_management_manage_single_organization'),
    url(r'^manage/organization/(?P<org_id>[a-zA-Z0-9]+)/delete/?$', 'user_management.manage_single_organization_delete', name='user_management_manage_single_organization_delete'),
    url(r'^manage/registry-users/add-user/?$', 'user_management.registry_user_add_user', name='user_management_registry_user_add_user'),
    url(r'^manage/registry-users/?$', 'user_management.manage_registry_user', name='user_management_manage_registry_user'),
    url(r'^manage/registry-user/(?P<user_id>[a-zA-Z0-9]+)/delete/?$', 'user_management.manage_single_registry_user_delete', name='user_management_manage_single_registry_user_delete'),
    url(r'^manage/registry-users/(?P<user_id>[a-zA-Z0-9]+)/remove/?$', 'user_management.manage_single_registry_user_remove', name='user_management_manage_single_registry_user_remove'),
    url(r'^manage/registrar-users/?$', 'user_management.manage_registrar_user', name='user_management_manage_registrar_user'),
    url(r'^manage/registrar-users/(?P<user_id>[a-zA-Z0-9]+)/?$', 'user_management.manage_single_registrar_user', name='user_management_manage_single_registrar_user'),
    url(r'^manage/registrar-user/(?P<user_id>[a-zA-Z0-9]+)/delete/?$', 'user_management.manage_single_registrar_user_delete', name='user_management_manage_single_registrar_user_delete'),
    url(r'^manage/registrar-users/(?P<user_id>[a-zA-Z0-9]+)/reactivate/?$', 'user_management.manage_single_registrar_user_reactivate', name='user_management_manage_single_registrar_user_reactivate'),
    url(r'^manage/registrar-users/add-user/?$', 'user_management.registrar_user_add_user', name='user_management_registrar_user_add_user'),
    url(r'^manage/registrar-users/(?P<user_id>[a-zA-Z0-9]+)/remove/?$', 'user_management.manage_single_registrar_user_remove', name='user_management_manage_single_registrar_user_remove'),
    url(r'^manage/users/?$', 'user_management.manage_user', name='user_management_manage_user'),
    url(r'^manage/users/(?P<user_id>[a-zA-Z0-9]+)/?$', 'user_management.manage_single_user', name='user_management_manage_single_user'),
    url(r'^manage/users/(?P<user_id>[a-zA-Z0-9]+)/delete/?$', 'user_management.manage_single_user_delete', name='user_management_manage_single_user_delete'),
    url(r'^manage/users/(?P<user_id>[a-zA-Z0-9]+)/reactivate/?$', 'user_management.manage_single_user_reactivate', name='user_management_manage_single_user_reactivate'),
    url(r'^manage/organization-users/?$', 'user_management.manage_organization_user', name='user_management_manage_organization_user'),
    url(r'^manage/organization-users/(?P<user_id>[a-zA-Z0-9]+)/?$', 'user_management.manage_single_organization_user', name='user_management_manage_single_organization_user'),
    url(r'^manage/organization-users/(?P<user_id>[a-zA-Z0-9]+)/delete/?$', 'user_management.manage_single_organization_user_delete', name='user_management_manage_single_organization_user_delete'),
    url(r'^manage/organization-users/(?P<user_id>[a-zA-Z0-9]+)/reactivate/?$', 'user_management.manage_single_organization_user_reactivate', name='user_management_manage_single_organization_user_reactivate'),
    url(r'^manage/organization-users/(?P<user_id>[a-zA-Z0-9]+)/remove/?$', 'user_management.manage_single_organization_user_remove', name='user_management_manage_single_organization_user_remove'),
    url(r'^manage/users/(?P<user_id>[a-zA-Z0-9]+)/add-registrar/?$', 'user_management.user_add_registrar', name='user_management_user_add_registrar'),
    url(r'^manage/organization-users/add-user/?$', 'user_management.organization_user_add_user', name='user_management_organization_user_add_user'),
    url(r'^manage/account/leave-organization/(?P<org_id>[a-zA-Z0-9]+)/?$', 'user_management.organization_user_leave_organization', name='user_management_organization_user_leave_organization'),
#    url(r'^manage/users/?$', 'manage.users', name='manage_users'),
#    url(r'^manage/activity/?$', 'manage.activity', name='manage_activity'),

    # Our Perma ID catchall
    url(r'^%s/?$' % r'(?P<guid>[^\./]+)', 'common.single_linky', name='single_linky'),

)

# debug-only serving of media assets
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'perma.views.common.server_error_404'
handler500 = 'perma.views.common.server_error_500'
