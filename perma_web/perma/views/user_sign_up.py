import logging
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from ratelimit.decorators import ratelimit

from perma.email import send_admin_email, send_user_email, send_user_email_copy_admins
from perma.forms import (
    ApproveRegistrarForm,
    CreateUserFormWithCourt,
    CreateUserFormWithFirm,
    FirmRegistrarForm,
    FirmUsageForm,
    LibraryRegistrarForm,
    UserForm,
    check_honeypot,
)
from perma.models import LinkUser, Registrar
from perma.utils import (
    apply_pagination,
    apply_search_query,
    apply_sort_order,
    ratelimit_ip_key,
    user_passes_test_or_403,
)
from perma.views.common import valid_member_sorts

logger = logging.getLogger(__name__)


@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def sign_up_libraries(request):
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
            email_library_registrar_request(request, new_registrar)
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
        something_took_the_bait = check_honeypot(
            request, 'register_email_instructions', check_js=True
        )
        if something_took_the_bait:
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
        initial = {}
        if hasattr(request, 'user'):
            fields = ['first_name', 'last_name', 'email']
            initial = {field: getattr(request.user, field, None) for field in fields}
        form = CreateUserFormWithCourt(initial=initial, request=request)

    return render(request, "registration/sign-up-courts.html", {'form': form})


@ratelimit(rate=settings.REGISTER_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def sign_up_firms(request: HttpRequest):
    """Display the sign-up page for submitting a firm/other org request."""
    if request.method == 'POST':
        something_took_the_bait = check_honeypot(
            request, 'register_email_instructions', honey_pot_fieldname='a-telephone', check_js=True
        )
        if something_took_the_bait:
            return something_took_the_bait

        user_email = request.POST.get('a-e-address', '').lower()
        user_form = CreateUserFormWithFirm(request.POST, prefix='a')
        registrar_form = FirmRegistrarForm(request.POST)
        usage_form = FirmUsageForm(request.POST)

        try:
            existing_user = LinkUser.objects.get(email=user_email)
        except LinkUser.DoesNotExist:
            existing_user = None

        # If user email in form matches an existing user in database, update user record to include
        # organization name under `LinkUser.requested_account_note` field
        if existing_user is not None and registrar_form.is_valid():
            new_registrar: Registrar = registrar_form.save()
            new_registrar.nonpaying = False
            new_registrar.save()
            existing_user.requested_account_type = 'firm'
            existing_user.requested_account_note = registrar_form.cleaned_data['name']
            existing_user.pending_registrar = new_registrar
            existing_user.save()

            email_firm_request(request, new_registrar)
            return HttpResponseRedirect(reverse('firm_request_response'))

        # Otherwise, validate the user form, create a new user account (if requested), and email a
        # firm request to Perma administrators
        elif user_form.is_valid() and registrar_form.is_valid():
            new_registrar: Registrar = registrar_form.save()
            new_registrar.nonpaying = False
            new_registrar.save()
            new_user: LinkUser = user_form.save(commit=False)
            new_user.requested_account_type = 'firm'
            new_user.requested_account_note = registrar_form.cleaned_data['name']
            create_account = request.POST.get('create_account', None)
            if create_account:
                new_user.save()
                email_firm_request(request, new_registrar)
                if user_form.cleaned_data['registrar_user_candidate'] is True:
                    email_pending_registrar_user(request, new_user)
                else:
                    email_new_user(request, new_user)
                messages.add_message(
                    request,
                    messages.INFO,
                    'We will shortly follow up with more information about how Perma.cc could work in your organization.',
                )
                return HttpResponseRedirect(reverse('register_email_instructions'))
            else:
                email_firm_request(request, new_registrar)
                return HttpResponseRedirect(reverse('firm_request_response'))

    else:
        initial = {}
        if hasattr(request, 'user'):
            fields = ['first_name', 'last_name', 'email']
            initial = {field: getattr(request.user, field, None) for field in fields}
        user_form = CreateUserFormWithFirm(initial=initial, prefix='a', request=request)
        registrar_form = FirmRegistrarForm()
        usage_form = FirmUsageForm()

    return render(
        request,
        'registration/sign-up-firms.html',
        {
            'user_form': user_form,
            'registrar_form': registrar_form,
            'usage_form': usage_form,
        },
    )


@user_passes_test_or_403(lambda user: user.is_staff)
def approve_pending_registrar(request: HttpRequest, registrar_id: int):
    """A view enabling admins to approve or deny a pending registrar."""
    target_registrar = get_object_or_404(Registrar, id=registrar_id)
    target_registrar_user = target_registrar.pending_users.first() or target_registrar.users.first()

    if request.method == 'POST':
        form = ApproveRegistrarForm(request.POST, target_registrar)
        if not form.is_valid():
            return render(
                request,
                'user_management/approve_pending_registrar.html',
                {
                    'target_registrar': target_registrar,
                    'target_registrar_user': target_registrar_user,
                    'approve_registrar_form': form,
                    'this_page': 'users_registrars',
                },
            )

        with transaction.atomic():
            registrar_user_email = form.cleaned_data.get('registrar_user', None)
            if registrar_user_email and not target_registrar_user:
                target_registrar_user = LinkUser.objects.get(email=registrar_user_email.lower())
                target_registrar_user.pending_registrar = target_registrar
                target_registrar_user.save()
                return HttpResponseRedirect(
                    reverse('user_sign_up_approve_pending_registrar', args=[target_registrar.id])
                )

            new_status = form.cleaned_data['status']
            if new_status in ['approved', 'denied']:
                target_registrar.status = new_status
                if form.cleaned_data['base_rate'] is not None and new_status == 'approved':
                    target_registrar.base_rate = form.cleaned_data['base_rate']
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

    # GET request
    form = ApproveRegistrarForm(request.GET, registrar=target_registrar)

    # Handle user search query, if supplied
    search_query = request.GET.get('q', '').strip()
    if search_query and not target_registrar_user:
        users = LinkUser.objects.distinct().filter(
            is_confirmed=True,
            is_active=True,
            is_staff=False,
            registrar=None,
            pending_registrar=None,
            organizations=None,
            # Note: while it's technically possible for a sponsored user to become a registrar
            # user for another registrar, we exclude sponsored users here to avoid confusion
            sponsoring_registrars=None,
        )
        users, sort = apply_sort_order(request, users, valid_member_sorts)
        users, _ = apply_search_query(request, users, ['email', 'first_name', 'last_name'])
        users = apply_pagination(request, users)

        return render(
            request,
            'user_management/approve_pending_registrar.html',
            {
                'target_registrar': target_registrar,
                'target_registrar_user': target_registrar_user,
                'approve_registrar_form': form,
                'search_query': search_query,
                'sort': sort,
                'users': users,
                'this_page': 'users_registrars',
            },
        )

    return render(
        request,
        'user_management/approve_pending_registrar.html',
        {
            'target_registrar': target_registrar,
            'target_registrar_user': target_registrar_user,
            'approve_registrar_form': form,
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


def suggest_registrars(user: LinkUser, limit: int = 5) -> QuerySet[Registrar]:
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
        Registrar.objects.filter(status='approved')
        .filter(website__iregex=pattern)
        .order_by('-link_count', 'name')[:limit]
    )
    return registrars


def email_new_user(request, user, template='email/new_user.txt', context=None):
    """
    Send email to newly created accounts
    """
    # This uses the forgot-password flow; logic is borrowed from auth_forms.PasswordResetForm.save()
    activation_route = request.build_absolute_uri(
        reverse(
            'password_reset_confirm',
            args=[
                urlsafe_base64_encode(force_bytes(user.pk)),
                default_token_generator.make_token(user),
            ],
        )
    )

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

    send_user_email(user.raw_email, template, context)


def email_pending_registrar_user(request: HttpRequest, user: LinkUser):
    """Send email to a newly created user whose registrar is pending."""
    email_new_user(request, user, template='email/pending_registrar.txt')


def email_library_registrar_request(request: HttpRequest, pending_registrar: Registrar):
    """Send email to admins when a registrar account is requested."""
    host = request.get_host()
    try:
        email = request.user.raw_email
    except AttributeError:
        # User did not have an account
        email = request.POST.get('a-e-address')

    send_admin_email(
        'Perma.cc new library registrar account request',
        email,
        request,
        'email/admin/registrar_request.txt',
        {
            'name': pending_registrar.name,
            'email': pending_registrar.email,
            'requested_by_email': email,
            'host': host,
            'confirmation_route': reverse(
                'user_sign_up_approve_pending_registrar', args=[pending_registrar.id]
            ),
        },
    )


def email_approved_registrar_user(request, user):
    """
    Send email to newly approved registrar accounts for folks requesting accounts
    """
    host = request.get_host()
    send_user_email(
        user.raw_email,
        'email/registrar_approved.txt',
        {'host': host, 'account_route': reverse('user_management_manage_organization')},
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


def email_firm_request(request: HttpRequest, registrar: Registrar):
    """Send email to admins when a paid registrar account is requested."""
    usage_form = FirmUsageForm(request.POST)
    user_form = CreateUserFormWithFirm(request.POST, prefix='a')

    # Validate form values; this should rarely or never arise in practice, but the `cleaned_data`
    # attribute is only populated after checking
    if usage_form.errors:
        return HttpResponseBadRequest('Form data contains validation errors')
    user_name = ' '.join(
        [user_form.data.get('a-first_name', ''), user_form.data.get('a-last_name', '')]
    ).strip()
    user_email = user_form.data['a-e-address'].lower()

    try:
        existing_user = LinkUser.objects.get(email=user_email)
    except LinkUser.DoesNotExist:
        existing_user = None

    context = {
        'existing_user': existing_user,
        'user_email': user_email,
        'user_name': user_name,
        'usage_form': usage_form,
        'registrar': registrar,
        'host': request.get_host(),
        'confirmation_route': reverse(
            'user_sign_up_approve_pending_registrar', args=[registrar.id]
        ),
    }
    send_user_email_copy_admins(
        title='Perma.cc new paid registrar account request',
        from_address=settings.DEFAULT_FROM_EMAIL,
        to_addresses=[user_email],
        request=request,
        template='email/admin/firm_request.txt',
        context=context,
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
