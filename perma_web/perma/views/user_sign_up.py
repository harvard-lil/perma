import logging
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.db.models.manager import BaseManager
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from ratelimit.decorators import ratelimit

from perma.email import send_admin_email, send_user_email
from perma.forms import (
    CreateUserFormWithCourt,
    CreateUserFormWithFirm,
    FirmOrganizationForm,
    FirmUsageForm,
    LibraryRegistrarForm,
    UserForm,
    check_honeypot,
)
from perma.models import (
    LinkUser,
    Registrar,
)
from perma.utils import (
    ratelimit_ip_key,
    user_passes_test_or_403,
)

logger = logging.getLogger(__name__)


@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def libraries(request):
    """
    Info for libraries, allow them to request accounts
    """
    if request.method == 'POST':

        if something_took_the_bait := check_honeypot(request, 'register_library_instructions', 'a-telephone', check_js=True):
            return something_took_the_bait

        registrar_form = LibraryRegistrarForm(request.POST, request.FILES, prefix ="b")
        if request.user.is_authenticated:
            user_form = None
        else:
            user_form = UserForm(request.POST, prefix = "a")
            user_form.fields['email'].label = "Your email"
        user_email = request.POST.get('a-e-address', '').lower()
        try:
            target_user = LinkUser.objects.get(email=user_email)
        except LinkUser.DoesNotExist:
            target_user = None
        if target_user:
            messages.add_message(request, messages.INFO, "You already have a Perma account, please sign in to request an account for your library.")
            request.session['request_data'] = registrar_form.data
            return HttpResponseRedirect('/login?next=/libraries/')

        # test if both form objects that comprise the signup form are valid
        if user_form:
            form_is_valid = user_form.is_valid() and registrar_form.is_valid()
        else:
            form_is_valid = registrar_form.is_valid()
        if form_is_valid:
            new_registrar = registrar_form.save()
            email_registrar_request(request, new_registrar)
            if user_form:
                new_user = user_form.save(commit=False)
                new_user.pending_registrar = new_registrar
                new_user.save()
                email_pending_registrar_user(request, new_user)
                return HttpResponseRedirect(reverse('register_library_instructions'))
            else:
                request.user.pending_registrar = new_registrar
                request.user.save()
                return HttpResponseRedirect(reverse('settings_affiliations'))
    else:
        request_data = request.session.get('request_data','')
        user_form = None
        if not request.user.is_authenticated:
            user_form = UserForm(prefix="a")
            user_form.fields['email'].label = "Your email"
        if request_data:
            registrar_form = LibraryRegistrarForm(request_data, prefix="b")
        else:
            registrar_form = LibraryRegistrarForm(prefix="b")

    return render(request, "registration/sign-up-libraries.html",
        {'user_form':user_form, 'registrar_form':registrar_form})

@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def sign_up(request):
    """
    Register a new user
    """
    if request.method == 'POST':

        if something_took_the_bait := check_honeypot(request, 'register_email_instructions', check_js=True):
            return something_took_the_bait

        form = UserForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            email_new_user(request, new_user)
            return HttpResponseRedirect(reverse('register_email_instructions'))
    else:
        form = UserForm()

    return render(request, "registration/sign-up.html", {'form': form})


@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def sign_up_courts(request):
    """
    Register a new court user
    """
    if request.method == 'POST':

        if something_took_the_bait := check_honeypot(request, 'register_email_instructions', check_js=True):
            return something_took_the_bait

        form = CreateUserFormWithCourt(request.POST)
        submitted_email = request.POST.get('e-address', '').lower()

        try:
            target_user = LinkUser.objects.get(email=submitted_email)
        except LinkUser.DoesNotExist:
            target_user = None

        if target_user:
            requested_account_note = request.POST.get('requested_account_note', None)
            target_user.requested_account_type = 'court'
            target_user.requested_account_note = requested_account_note
            target_user.save()
            email_court_request(request, target_user)
            return HttpResponseRedirect(reverse('court_request_response'))

        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.requested_account_type = 'court'
            create_account = request.POST.get('create_account', None)
            if create_account:
                new_user.save()
                email_new_user(request, new_user)
                email_court_request(request, new_user)
                messages.add_message(request, messages.INFO, "We will shortly follow up with more information about how Perma.cc could work in your court.")
                return HttpResponseRedirect(reverse('register_email_instructions'))
            else:
                email_court_request(request, new_user)
                return HttpResponseRedirect(reverse('court_request_response'))

    else:
        form = CreateUserFormWithCourt()

    return render(request, "registration/sign-up-courts.html", {'form': form})


@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def sign_up_firm(request):
    """
    Register a new law firm user
    """
    if request.method == 'POST':

        if something_took_the_bait := check_honeypot(request, 'register_email_instructions', check_js=True):
            return something_took_the_bait

        user_form = CreateUserFormWithFirm(request.POST)
        user_email = request.POST.get('e-address', '').lower()

        try:
            existing_user = LinkUser.objects.get(email=user_email)
        except LinkUser.DoesNotExist:
            existing_user = None

        # If user email in form matches an existing user in database, update user record to include
        # organization name under `LinkUser.requested_account_note` field
        if existing_user is not None:
            organization_name = request.POST.get('name', None)
            existing_user.requested_account_type = 'firm'
            existing_user.requested_account_note = organization_name
            existing_user.save()
            email_firm_request(request, existing_user)
            return HttpResponseRedirect(reverse('firm_request_response'))

        # Otherwise, validate the user form, create a new user account (if requested), and email a
        # firm request to Perma administrators
        elif user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.requested_account_type = 'firm'
            create_account = request.POST.get('create_account', None)
            if create_account:
                new_user.save()
                email_new_user(request, new_user)
                email_firm_request(request, new_user)
                messages.add_message(
                    request,
                    messages.INFO,
                    'We will shortly follow up with more information about how Perma.cc could work in your organization.',
                )
                return HttpResponseRedirect(reverse('register_email_instructions'))
            else:
                email_firm_request(request, new_user)
                return HttpResponseRedirect(reverse('firm_request_response'))

        else:
            organization_form = FirmOrganizationForm()
            usage_form = FirmUsageForm()

    else:
        user_form = CreateUserFormWithFirm()
        organization_form = FirmOrganizationForm()
        usage_form = FirmUsageForm()

    return render(
        request,
        'registration/sign-up-firms.html',
        {
            'user_form': user_form,
            'organization_form': organization_form,
            'usage_form': usage_form,
        },
    )


@user_passes_test_or_403(lambda user: user.is_staff)
def approve_pending_registrar(request, registrar_id):
    """Perma admins can approve account requests from libraries"""

    target_registrar = get_object_or_404(Registrar, id=registrar_id)
    target_registrar_user = target_registrar.pending_users.first()

    if request.method == 'POST':
        with transaction.atomic():
            new_status = request.POST.get('status')
            if new_status in ['approved', 'denied']:
                target_registrar.status = new_status
                target_registrar.save()

                if new_status == 'approved':
                    target_registrar_user.registrar = target_registrar
                    target_registrar_user.pending_registrar = None
                    target_registrar_user.save()
                    email_approved_registrar_user(request, target_registrar_user)

                    messages.add_message(
                        request,
                        messages.SUCCESS,
                        f'<h4>Registrar approved!</h4> <strong>{target_registrar_user.email}</strong> will receive a notification email with further instructions.',
                        extra_tags='safe',
                    )
                else:
                    messages.add_message(
                        request,
                        messages.SUCCESS,
                        f'Registrar request for <strong>{target_registrar}</strong> denied. Please inform {target_registrar_user.email} if appropriate.',
                        extra_tags='safe',
                    )

        return HttpResponseRedirect(reverse('user_management_manage_registrar'))

    return render(
        request,
        'user_management/approve_pending_registrar.html',
        {
            'target_registrar': target_registrar,
            'target_registrar_user': target_registrar_user,
            'this_page': 'users_registrars',
        },
    )


def register_email_instructions(request):
    """
    After the user has registered, give the instructions for confirming
    """
    return render(request, 'registration/check_email.html')


def register_library_instructions(request):
    """
    After the user requested a library account, give instructions
    """
    return render(request, 'registration/check_email_library.html')


def court_request_response(request):
    """
    After the user has requested info about a court account
    """
    return render(request, 'registration/court_request.html')


def firm_request_response(request):
    """
    After the user has requested info about a firm account
    """
    return render(request, 'registration/firm_request.html')


def suggest_registrars(user: LinkUser, limit: int = 5) -> BaseManager[Registrar]:
    """Suggest potential registrars for a user based on email domain.

    This queries the database for registrars whose website matches the
    base domain from the user's email address. For example, if the
    user's email is `username@law.harvard.edu`, this will suggest
    registrars whose domains end with `harvard.edu`.
    """
    _, email_domain = user.email.split('@')
    base_domain = '.'.join(email_domain.rsplit('.', 2)[-2:])
    pattern = f'^https?://([a-zA-Z0-9\\-\\.]+\\.)?{re.escape(base_domain)}(/.*)?$'
    registrars = (
        Registrar.objects.exclude(status='pending')
        .filter(website__iregex=pattern)
        .order_by('-link_count', 'name')[:limit]
    )
    return registrars


def email_new_user(request, user, template='email/new_user.txt', context=None):
    """
    Send email to newly created accounts
    """
    # This uses the forgot-password flow; logic is borrowed from auth_forms.PasswordResetForm.save()
    activation_route = request.build_absolute_uri(reverse('password_reset_confirm', args=[
        urlsafe_base64_encode(force_bytes(user.pk)),
        default_token_generator.make_token(user),
    ]))

    # Include context variables
    template_is_default = template == 'email/new_user.txt'
    context = context if context is not None else {}
    context.update(
        {
            'activation_expires': settings.PASSWORD_RESET_TIMEOUT,
            'activation_route': activation_route,
            'request': request,
            # Only query DB if we're using the default template; otherwise there's no need
            'suggested_registrars': suggest_registrars(user) if template_is_default else [],
        }
    )

    send_user_email(
        user.raw_email,
        template,
        context
    )


def email_pending_registrar_user(request, user):
    """
    Send email to newly created accounts for folks requesting library accounts
    """
    email_new_user(request, user, template='email/pending_registrar.txt')


def email_registrar_request(request, pending_registrar):
    """
    Send email to Perma.cc admins when a library requests an account
    """
    host = request.get_host()
    try:
        email = request.user.raw_email
    except AttributeError:
        # User did not have an account
        email = request.POST.get('a-e-address')

    send_admin_email(
        "Perma.cc new library registrar account request",
        email,
        request,
        'email/admin/registrar_request.txt',
        {
            "name": pending_registrar.name,
            "email": pending_registrar.email,
            "requested_by_email": email,
            "host": host,
            "confirmation_route": reverse('user_sign_up_approve_pending_registrar', args=[pending_registrar.id])
        }
    )


def email_approved_registrar_user(request, user):
    """
    Send email to newly approved registrar accounts for folks requesting library accounts
    """
    host = request.get_host()
    send_user_email(
        user.raw_email,
        "email/library_approved.txt",
        {
            "host": host,
            "account_route": reverse('user_management_manage_organization')
        }
    )


def email_court_request(request, user):
    """
    Send email to Perma.cc admins when a court requests an account
    """
    try:
        target_user = LinkUser.objects.get(email=user.email)
    except LinkUser.DoesNotExist:
        target_user = None
    send_admin_email(
        "Perma.cc new library court account information request",
        user.raw_email,
        request,
        "email/admin/court_request.txt",
        {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "court_name": user.requested_account_note,
            "has_account": target_user,
            "email": user.raw_email
        }
    )


def email_firm_request(request: HttpRequest, user: LinkUser):
    """
    Send email to Perma.cc admins when a firm requests an account
    """
    organization_form = FirmOrganizationForm(request.POST)
    usage_form = FirmUsageForm(request.POST)
    user_form = CreateUserFormWithFirm(request.POST)

    # Validate form values; this should rarely or never arise in practice, but the `cleaned_data`
    # attribute is only populated after checking
    if organization_form.errors or usage_form.errors:
        return HttpResponseBadRequest('Form data contains validation errors')

    try:
        existing_user = LinkUser.objects.get(email=user_form.data['e-address'].casefold())
    except LinkUser.DoesNotExist:
        existing_user = None

    send_admin_email(
        'Perma.cc new law firm account information request',
        user.raw_email,
        request,
        'email/admin/firm_request.txt',
        {
            'existing_user': existing_user,
            'organization_form': organization_form,
            'usage_form': usage_form,
            'user_form': user_form,
        },
    )


def email_premium_request(request, user):
    """
    Send email to Perma.cc admins when a user requests a premium account
    """
    send_admin_email(
        "Perma.cc premium account request",
        user.raw_email,
        request,
        "email/admin/premium_request.txt",
        {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.raw_email
        }
    )
