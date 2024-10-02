import itertools

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponseRedirect, Http404, HttpResponseForbidden
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.decorators.debug import sensitive_variables
from django.views.decorators.http import require_http_methods

from perma.email import send_admin_email
from perma.exceptions import PermaPaymentsCommunicationException
from perma.forms import UserUpdateProfileForm
from perma.models import ApiKey, Organization, UserOrganizationAffiliation
from perma.utils import get_form_data, prep_for_perma_payments, user_passes_test_or_403


@login_required
def settings_profile(request):
    """
    Settings profile, change name, change email, ...
    """
    if request.method == 'GET':
        # We want the user to see their raw email address
        request.user.email = request.user.raw_email

    form = UserUpdateProfileForm(get_form_data(request), prefix = "a", instance=request.user)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Profile saved!', extra_tags='safe')
            return HttpResponseRedirect(reverse('settings_profile'))

    return render(request, 'settings/settings-profile.html', {
        'this_page': 'settings_profile',
        'form': form,
    })

@login_required
def delete_account(request):
    """
    Generate or regenerate an API key for the user
    """
    if request.method == "POST":
        request.user.notes = f"Requested account deletion {timezone.now()}\n" + request.user.notes
        request.user.save()
        send_admin_email(
            "Perma.cc account deletion request",
            request.user.raw_email,
            request,
            "email/admin/deletion_request.txt",
            {
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "email": request.user.raw_email,
                "admin_url": request.build_absolute_uri(reverse('admin:perma_linkuser_change', args=(request.user.id,)))
            }
        )
    return HttpResponseRedirect(reverse('settings_profile'))


@login_required
def settings_password(request):
    """
    Settings change password ...
    """
    form = PasswordChangeForm(get_form_data(request))
    context = {
        'this_page': 'settings_password',
        'form': form,
    }
    return render(request, 'settings/settings-password.html', context)


@user_passes_test_or_403(lambda user: user.is_registrar_user() or user.is_organization_user or user.has_registrar_pending())
def settings_affiliations(request):
    """
    Settings view organizations, leave organizations ...
    """

    pending_registrar = request.user.pending_registrar
    if pending_registrar:
        messages.add_message(request, messages.INFO, "Thank you for requesting an account for your library. Perma.cc will review your request as soon as possible.")

    organizations = request.user.organizations.all().order_by('registrar')
    affiliations = UserOrganizationAffiliation.objects.filter(user=request.user)
    expires_lookup = {affiliation.organization_id: affiliation.expires_at for affiliation in affiliations}

    orgs_by_registrar = {
        registrar: [
            {'organization': org, 'expires_at': expires_lookup.get(org.id)}
            for org in orgs
        ]
        for registrar, orgs in itertools.groupby(organizations, lambda x: x.registrar)
    }

    return render(request, 'settings/settings-affiliations.html', {
        'this_page': 'settings_affiliations',
        'pending_registrar': pending_registrar,
        'orgs_by_registrar': orgs_by_registrar})


@user_passes_test_or_403(lambda user: user.is_staff or user.is_registrar_user() or user.is_organization_user)
def settings_organizations_change_privacy(request, org_id):
    try:
        org = Organization.objects.accessible_to(request.user).get(pk=org_id)
    except Organization.DoesNotExist:
        raise Http404
    context = {'this_page': 'settings', 'user': request.user, 'org': org}

    if request.method == 'POST':
        org.default_to_private = not org.default_to_private
        org.save()

        if request.user.is_registrar_user() or request.user.is_staff:
            return HttpResponseRedirect(reverse('user_management_manage_organization'))
        else:
            return HttpResponseRedirect(reverse('settings_affiliations'))

    return render(request, 'settings/settings-organizations-change-privacy.html', context)


@login_required
def settings_tools(request):
    """
    Settings tools ...
    """
    return render(request, 'settings/settings-tools.html', {'this_page': 'settings_tools'})


@sensitive_variables()
@user_passes_test_or_403(lambda user: user.can_view_usage_plan())
def settings_usage_plan(request):
    accounts = []
    purchase_history = {}
    try:
        if request.user.is_registrar_user() and not request.user.registrar.nonpaying:
            accounts.append(request.user.registrar.get_subscription_info(timezone.now()))
        if not request.user.nonpaying:
            accounts.append(request.user.get_subscription_info(timezone.now()))
            purchase_history = request.user.get_purchase_history()
    except PermaPaymentsCommunicationException:
        context = {
            'this_page': 'settings_usage_plan',
        }
        return render(request, 'settings/settings-usage-plan-unavailable.html', context)

    context = {
        'this_page': 'settings_usage_plan',
        'purchase_url': settings.PURCHASE_URL,
        'subscribe_url': settings.SUBSCRIBE_URL,
        'cancel_confirm_url': reverse('settings_subscription_cancel'),
        'update_url': reverse('settings_subscription_update'),
        'accounts': accounts,
        'purchase_history': purchase_history,
        'bonus_packages': request.user.get_bonus_packages()

    }
    return render(request, 'settings/settings-usage-plan.html', context)


@sensitive_variables()
@require_http_methods(["POST"])
@user_passes_test_or_403(lambda user: user.can_view_usage_plan())
def settings_subscription_cancel(request):
    account_type = request.POST.get('account_type', '')
    if account_type == 'Registrar':
        customer = request.user.registrar
    elif account_type == 'Individual':
        customer = request.user
    account = customer.get_subscription_info(timezone.now())
    if not account['subscription']:
        return HttpResponseForbidden()
    context = {
        'this_page': 'settings_subscription',
        'cancel_url': settings.CANCEL_URL,
        'customer': customer,
        'customer_type': account_type,
        'account': account,
        'data': prep_for_perma_payments({
            'customer_pk': customer.id,
            'customer_type': account_type,
            'timestamp': timezone.now().timestamp()
        }).decode('utf-8')
    }
    return render(request, 'settings/settings-subscription-cancel-confirm.html', context)


@sensitive_variables()
@require_http_methods(["POST"])
@user_passes_test_or_403(lambda user: user.can_view_usage_plan())
def settings_subscription_update(request):
    account_type = request.POST.get('account_type', '')
    if account_type == 'Registrar':
        customer = request.user.registrar
    elif account_type == 'Individual':
        customer = request.user
    account = customer.get_subscription_info(timezone.now())
    if not account['subscription']:
        return HttpResponseForbidden()
    context = {
        'this_page': 'settings_subscription',
        'update_url': settings.UPDATE_URL,
        'change_url': settings.CHANGE_URL,
        'customer': customer,
        'customer_type': account_type,
        'account': account,
        'update_encrypted_data': prep_for_perma_payments({
            'customer_pk': customer.id,
            'customer_type': account_type,
            'timestamp': timezone.now().timestamp()
        }).decode('utf-8')
    }
    return render(request, 'settings/settings-subscription-update.html', context)


@login_required
def api_key_create(request):
    """
    Generate or regenerate an API key for the user
    """

    if request.method == "POST":
        try:
            # Clear key so a new one is generated on save()
            request.user.api_key.key = None
            request.user.api_key.save()
        except ApiKey.DoesNotExist:
            ApiKey.objects.create(user=request.user)
        return HttpResponseRedirect(reverse('settings_tools'))
