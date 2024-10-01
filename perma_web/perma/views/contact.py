from ratelimit.decorators import ratelimit
import uuid
from urllib.parse import urlencode

from django.conf import settings
from django.forms import widgets
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from perma.email import send_admin_email, send_user_email_copy_admins
from perma.forms import ContactForm, ReportForm, check_honeypot
from perma.models import Registrar
from perma.utils import ratelimit_ip_key

import logging

logger = logging.getLogger(__name__)


@ratelimit(rate=settings.CONTACT_DAY_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.CONTACT_HOUR_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.CONTACT_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def contact(request):
    """
    Our contact form page
    """
    def affiliation_string():
        affiliation_string = ''
        if request.user.is_authenticated:
            if request.user.registrar:
                affiliation_string += f"{request.user.registrar.name} (Registrar)"
            elif request.user.is_organization_user:
                affiliations = [f"{org.name} ({org.registrar.name})" for org in request.user.organizations.all().order_by('registrar')]
                if affiliations:
                    affiliation_string = ', '.join(affiliations)
            if request.user.is_sponsored_user():
                affiliations = [f"{sponsorship.registrar.name}" for sponsorship in request.user.sponsorships.all().order_by('registrar')]
                affiliation_string += ', '.join(affiliations)
        return affiliation_string

    def formatted_organization_list(registrar):
        organization_string = ''
        if request.user.is_organization_user:
            orgs = [org.name for org in request.user.organizations.filter(registrar=registrar)]
            org_count = len(orgs)
            if org_count > 2:
                organization_string = ", ".join(orgs[:-1]) + " and " + orgs[-1]
            elif org_count == 2:
                organization_string = f"{orgs[0]} and {orgs[1]}"
            elif org_count == 1:
                organization_string = orgs[0]
            else:
                # this should never happen, consider raising an exception
                organization_string = '(error retrieving organization list)'
        return organization_string

    def handle_registrar_fields(form):
        if request.user.is_supported_by_registrar():
            registrars = set()
            if request.user.is_organization_user:
                registrars.update(org.registrar for org in request.user.organizations.all())
            if request.user.is_sponsored_user:
                registrars.update(sponsorship.registrar for sponsorship in request.user.sponsorships.all())
            if len(registrars) > 1:
                form.fields['registrar'].choices = [(registrar.id, registrar.name) for registrar in registrars]
            if len(registrars) == 1:
                form.fields['registrar'].widget = widgets.HiddenInput()
                registrar = registrars.pop()
                form.fields['registrar'].initial = registrar.id
                form.fields['registrar'].choices = [(registrar.id, registrar.email)]
        else:
            del form.fields['registrar']
        return form

    if request.method == 'POST':

        if something_took_the_bait := check_honeypot(request, 'contact_thanks', check_js=True):
            return something_took_the_bait

        form = handle_registrar_fields(ContactForm(request.POST))

        if form.is_valid():
            # Assemble info for email
            from_address = form.cleaned_data['email']
            subject = f"[perma-contact] {form.cleaned_data['subject']} ({str(uuid.uuid4())})"
            context = {
                "message": form.cleaned_data['box2'],
                "from_address": from_address,
                "referer": form.cleaned_data['referer'],
                "affiliation_string": affiliation_string()
            }
            if request.user.is_supported_by_registrar():
                # Send to all active registar users for registrar and cc Perma
                reg_id = form.cleaned_data['registrar']
                context["organization_string"] = formatted_organization_list(registrar=reg_id)
                send_user_email_copy_admins(
                    subject,
                    from_address,
                    [user.raw_email for user in Registrar.objects.get(id=reg_id).active_registrar_users()],
                    request,
                    'email/registrar_contact.txt',
                    context
                )
                # redirect to a new URL:
                return HttpResponseRedirect(
                    reverse('contact_thanks') + "?{}".format(urlencode({'registrar': reg_id}))
                )
            else:
                # Send only to the admins
                send_admin_email(
                    subject,
                    from_address,
                    request,
                    'email/admin/contact.txt',
                    context
                )
                # redirect to a new URL:
                return HttpResponseRedirect(reverse('contact_thanks'))
        else:
            return render(request, 'contact.html', {'form': form})

    else:

        # Our contact form serves a couple of purposes
        # If we get a message parameter, we're getting a message from the create form
        # about a failed archive
        #
        # If we get a flagged parameter, we're getting the guid of an archive from the
        # Flag as inappropriate button on an archive page
        #
        # We likely want to clean up this contact for logic if we tack much else on

        subject = request.GET.get('subject', '')
        message = request.GET.get('message', '')

        upgrade = request.GET.get('upgrade', '')
        if upgrade == 'organization' :
            subject = 'Upgrade to Unlimited Account'
            message = "My organization is interested in a subscription to Perma.cc."
        else:
            # all other values of `upgrade` are disallowed
            upgrade = None

        form = handle_registrar_fields(
            ContactForm(
                initial={
                    'box2': message,
                    'subject': subject,
                    'referer': request.META.get('HTTP_REFERER', ''),
                    'email': getattr(request.user, 'email', '')
                }
            )
        )

        return render(request, 'contact.html', {'form': form, 'upgrade': upgrade})


def contact_thanks(request):
    """
    The page users are delivered at after submitting the contact form.
    """
    registrar = Registrar.objects.filter(pk=request.GET.get('registrar', '-1')).first()
    return render(request, 'contact-thanks.html', {'registrar': registrar})


@ratelimit(rate=settings.REPORT_DAY_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.REPORT_HOUR_LIMIT, block=True, key=ratelimit_ip_key)
@ratelimit(rate=settings.REPORT_MINUTE_LIMIT, block=True, key=ratelimit_ip_key)
def report(request):
    """
    Report inappropriate content.
    """
    def affiliation_string():
        affiliation_string = ''
        if request.user.is_authenticated:
            if request.user.registrar:
                affiliation_string = f"{request.user.registrar.name} (Registrar)"
            else:
                affiliations = [f"{org.name} ({org.registrar.name})" for org in request.user.organizations.all().order_by('registrar')]
                if affiliations:
                    affiliation_string = ', '.join(affiliations)
        return affiliation_string

    if request.method == 'POST':

        if something_took_the_bait := check_honeypot(request, 'contact_thanks', check_js=True):
            return something_took_the_bait

        form = ReportForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['guid']:
                from_address = form.cleaned_data['email']
                subject = f"[perma-contact] Reporting Inappropriate Content ({str(uuid.uuid4())})"
                context = {
                    "reason": form.cleaned_data['reason'],
                    "source": form.cleaned_data['source'],
                    "from_address": from_address,
                    "guid": form.cleaned_data['guid'],
                    "referer": form.cleaned_data['referer'],
                    "affiliation_string": affiliation_string()
                }
                send_admin_email(
                    subject,
                    from_address,
                    request,
                    'email/admin/report.txt',
                    context
                )
            return HttpResponseRedirect(reverse('contact_thanks'))
        else:
            return render(request, 'report.html', {
                'form': form,
                'guid': request.POST.get('guid', '')
            })

    else:
        guid = request.GET.get('guid', '')
        form = ReportForm(
                initial={
                    'guid': guid,
                    'referer': request.META.get('HTTP_REFERER', ''),
                    'email': getattr(request.user, 'email', '')
                }
        )
        return render(request, 'report.html', {
            'form': form,
            'guid': guid
        })
