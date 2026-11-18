from datetime import timedelta

from celery import shared_task

from django.utils import timezone

from perma.email import send_staff_invited_new_user_email, send_user_email
from perma.exceptions import PermaPaymentsCommunicationException
from perma.models import LinkUser, Sponsorship, UserOrganizationAffiliation

import logging
logger = logging.getLogger('celery.django')


def email_expiring_user(user, template, context):
    """
    Sends email to user notifying about affiliation expiry
    """
    send_user_email(
        user.raw_email,
        template,
        context
    )


@shared_task(name='perma.celery_tasks.deactivate_expired_sponsored_users')
def deactivate_expired_sponsored_users(expiration_date=None):
    """
    Deactivates registrar sponsored users whose affiliation expired
    """
    if not expiration_date:
        expiration_date = timezone.now().date()

    expired_sponsorships = Sponsorship.objects.filter(status="active", expires_at__lt=expiration_date)
    updated = expired_sponsorships.update(status="inactive", status_changed=timezone.now())

    if updated:
        logger.info(f"Deactivated {updated} sponsorships that expired on {expiration_date}.")
    else:
        logger.info(f"Found no sponsorships that expired on {expiration_date}.")


@shared_task(name='perma.celery_tasks.remove_expired_organization_user_affiliations')
def remove_expired_organization_user_affiliations(expiration_date=None):
    """
    Removes affiliation of organization users whose affiliation expired
    """
    if not expiration_date:
        expiration_date = timezone.now().date()

    deleted_affiliations = UserOrganizationAffiliation.objects.filter(expires_at__lt=expiration_date).delete()

    if deleted_affiliations[0] > 0:
        logger.info(f"Removed {deleted_affiliations[0]} organization user affiliations that expired on {expiration_date}.")
    else:
        logger.info(f"Found no organization user affiliations that expired on {expiration_date}.")


@shared_task(name='perma.celery_tasks.warn_expiring_sponsored_users')
def warn_expiring_sponsored_users(warning_days=None):
    """
    Notifies registrar sponsored users whose affiliation is expiring
    """
    if not warning_days:
        warning_days = [7, 15, 30]

    todays_date = timezone.now().date()
    max_notification_date = todays_date + timedelta(days=max(warning_days))
    expiring_sponsorships = (
        Sponsorship.objects.filter(status="active", expires_at__lte=max_notification_date)
        .select_related('user')
        .select_related('registrar')
    )

    if not expiring_sponsorships:
        return

    for sponsorship in expiring_sponsorships:
        expiration_date = sponsorship.expires_at.date()
        for day in warning_days:
            warning_date = todays_date + timedelta(days=day)
            if expiration_date == warning_date:
                context = {
                    "registrar_name": sponsorship.registrar.name,
                    "registrar_email": sponsorship.registrar.email,
                    "expiration_days": day,
                    "expiration_date": expiration_date + timedelta(days=1)
                }
                try:
                    email_expiring_user(sponsorship.user, "email/sponsored_user_expiry_notification.txt", context)
                except Exception:
                    logger.exception(f"Error emailing user {sponsorship.id}")
                break


@shared_task(name='perma.celery_tasks.warn_expiring_organization_users')
def warn_expiring_organization_users(warning_days=None):
    """
    Notifies users whose affiliation with an organization is expiring
    """
    if not warning_days:
        warning_days = [7, 15, 30]

    todays_date = timezone.now().date()
    max_notification_date = todays_date + timedelta(days=max(warning_days))
    expired_organization_users = UserOrganizationAffiliation.objects.filter(expires_at__lt=max_notification_date)

    if not expired_organization_users:
        return

    for affiliation in expired_organization_users:
        expiration_date = affiliation.expires_at.date()
        for day in warning_days:
            warning_date = todays_date + timedelta(days=day)
            if expiration_date == warning_date:
                context = {
                    "organization_name": affiliation.organization.name,
                    "registrar_name": affiliation.organization.registrar.name,
                    "registrar_email": affiliation.organization.registrar.email,
                    "expiration_days": day,
                    "expiration_date": expiration_date + timedelta(days=1)
                }
                try:
                    email_expiring_user(affiliation.user, "email/organization_user_expiry_notification.txt", context)
                except Exception:
                    logger.exception(f"Error emailing user {affiliation.user_id}")
                break


@shared_task(name='perma.celery_tasks.send_user_email_from_bulk_addition')
def send_user_email_from_bulk_addition(
    user_email,
    context,
    template=None,
    host=None,
    is_new_user=False,
    *,
    registrar_id: int,
):
    """
    Handles sending emails to users created/updated via the bulk org user addition form.
    """
    if is_new_user:
        user = LinkUser.objects.get(raw_email=user_email)
        send_staff_invited_new_user_email(
            user, registrar_id=registrar_id, context=context, host=host,
        )
    else:
        send_user_email(user_email, template, context)


@shared_task(name='perma.celery_tasks.sync_subscriptions_from_perma_payments')
def sync_subscriptions_from_perma_payments():
    """
    Perma only learns about changes to a customer's record in Perma
    Payments when the user transacts with Perma. For admin convenience,
    refresh Perma's records on demand.
    """
    customers = LinkUser.objects.filter(in_trial=False)
    for customer in customers:
        try:
            customer.get_subscription()
        except PermaPaymentsCommunicationException:
            # This gets logged inside get_subscription; don't duplicate logging here
            pass
