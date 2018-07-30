import logging
from createsend import Subscriber, List
from collections import defaultdict

from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Registrar, LinkUser
from .utils import tz_datetime

logger = logging.getLogger(__name__)

###
### Send email
###

def send_user_email(to_address, template, context):
    email_text = render_to_string(template, context=context, using="AUTOESCAPE_OFF")
    title, email_text = email_text.split("\n\n", 1)
    title = title.split("TITLE: ")[-1]
    success_count = send_mail(
        title,
        email_text,
        settings.DEFAULT_FROM_EMAIL,
        [to_address],
        fail_silently=False
    )
    return success_count

# def send_mass_user_email(template, recipients):
    # '''
    #     Opens a single connection to the mail server and sends many emails.
    #     Pass in recipients as a list of tuples (email, context):
    #     [('recipient@example.com', {'first_name': 'Joe', 'last_name': 'Yacoboski' }), (), ...]
    # '''
    # to_send = []
    # for recipient in recipients:
    #     to_address, context = recipient
    #     email_text = render_to_string(template, context)
    #     title, email_text = email_text.split("\n\n", 1)
    #     title = title.split("TITLE: ")[-1]
    #     to_send.append(( title,
    #                      email_text,
    #                      settings.DEFAULT_FROM_EMAIL,
    #                      [to_address]))

    # success_count = send_mass_mail(tuple(to_send), fail_silently=False)
    # return success_count

def send_admin_email(title, from_address, request, template="email/default.txt", context={}):
    """
        Send a message on behalf of a user to the admins.
        Use reply-to for the user address so we can use email services that require authenticated from addresses.
    """
    EmailMessage(
        title,
        render_to_string(template, context=context, request=request, using="AUTOESCAPE_OFF"),
        settings.DEFAULT_FROM_EMAIL,
        [settings.DEFAULT_FROM_EMAIL],
        headers={'Reply-To': from_address}
    ).send(fail_silently=False)

def send_user_email_copy_admins(title, from_address, to_addresses, request, template="email/default.txt", context={}):
    """
        Send a message on behalf of a user to another user, cc'ing
        the sender and the Perma admins.
        Use reply-to for the user address so we can use email services that require authenticated from addresses.
    """
    EmailMessage(
        title,
        render_to_string(template, context=context, request=request, using="AUTOESCAPE_OFF"),
        settings.DEFAULT_FROM_EMAIL,
        to_addresses,
        cc=[settings.DEFAULT_FROM_EMAIL, from_address],
        reply_to=[from_address]
    ).send(fail_silently=False)

###
### Collect user data, bundled for emails ###
###

def registrar_users(registrars=None):
    '''
        Returns all active registrar users plus assorted metadata as
        a list of dicts.
    '''
    users = []
    if registrars is None:
        registrars = Registrar.objects.all()
    for registrar in registrars:
        registrar_users = LinkUser.objects.filter(registrar = registrar.pk,
                                                  is_active = True,
                                                  is_confirmed = True)
        for user in registrar_users:
            users.append({ "id": user.id,
                           "first_name": user.first_name,
                           "last_name": user.last_name,
                           "email": user.email,
                        })
    return users


def registrar_users_plus_stats(destination=None, registrars=None, year=None):
    '''
        Returns all active registrar users plus assorted metadata as
        a list of dicts. If destination=cm, info is formatted for
        ingest by Campaign Monitor. By default, uses stats from current
        calendar year.
    '''
    users = []
    if year is None:
        year = timezone.now().year
    start_time = tz_datetime(year, 1, 1)
    end_time = tz_datetime(year + 1, 1, 1)
    if registrars is None:
        registrars = Registrar.objects.all()
    for registrar in registrars:
        registrar_users = LinkUser.objects.filter(registrar = registrar.pk,
                                                  is_active = True,
                                                  is_confirmed = True)
        for user in registrar_users:
            users.append({ "first_name": user.first_name,
                           "last_name": user.last_name,
                           "email": user.email,
                           "registrar_id": registrar.id,
                           "registrar_email": registrar.email,
                           "registrar_name": registrar.name,
                           "total_links": registrar.link_count,
                           "year_links": registrar.link_count_in_time_period(start_time, end_time),
                           "most_active_org": registrar.most_active_org_in_time_period(start_time, end_time),
                           "registrar_users": registrar_users })
    if destination == 'cm':
        return format_for_cm_registrar_users(users)
    else:
        return users

###
### Interact with Campaign Monitor ###
###

def format_for_cm_registrar_users(users):
    '''
        Given a list of dictionaries describing active Perma
        registrar users, returns the list, formatted for ingest
        by Campaign Monitor.
    '''
    def format_name(user):
        return u"{} {}".format(user["first_name"], user["last_name"])

    def format_registrar_users(registrar_users):
        string_list = [u"{} {} ({})".format(user.first_name, user.last_name, user.email) for user in registrar_users]
        return u"<br> ".join(string_list)

    formatted_users = []
    for user in users:
        if user["most_active_org"]:
            most_active_org_text = user["most_active_org"].name
        else:
            most_active_org_text = u"(none)"
        formatted = {}
        formatted['Name'] = format_name(user)
        formatted['EmailAddress'] = user["email"]
        formatted['CustomFields'] = [
            {"Key": "RegistrarId", "Value":  str(user["registrar_id"])},
            {"Key": "RegistrarEmail", "Value":  user["registrar_email"]},
            {"Key": "RegistrarName", "Value": user["registrar_name"]},
            {"Key": "TotalLinks", "Value": str(user["total_links"])},
            {"Key": "YearLinks", "Value": str(user["year_links"])},
            {"Key": "MostActiveOrg", "Value": most_active_org_text},
            {"Key": "RegistrarUsers", "Value": format_registrar_users(user['registrar_users'])}
        ]
        formatted_users.append(formatted)
    return formatted_users

def users_to_unsubscribe(cm_list_id, current_perma_user_emails):
    '''
        Returns a list of any email addresses marked as active in
        a given Campaign Monitor subscriber list, but not appearing in
        a passed-in iterable of currely active Perma user email addresses.
    '''
    page = 0
    to_unsubscribe = []
    current_users = set(current_perma_user_emails)
    cm_list = List(settings.CAMPAIGN_MONITOR_AUTH, cm_list_id)
    while True:
        page += 1
        result = cm_list.active(page=page, page_size=1000)
        if result.NumberOfPages <= 0:
            return []
        for subscriber in result.Results:
                if subscriber.EmailAddress not in current_users:
                    to_unsubscribe.append(subscriber.EmailAddress)
        if result.PageNumber == result.NumberOfPages:
            return to_unsubscribe

def add_and_update_cm_subscribers(list_id, subscribers):
    '''
       Adds new people to a Campaign Monitor list, and updates fields of
       existing subscribers. (If a field is ommited, its value remains
       unchanged.)
    '''
    logger.info("Adding new and updating existing.")
    subscriber = Subscriber(settings.CAMPAIGN_MONITOR_AUTH)
    import_result = subscriber.import_subscribers(list_id, subscribers, False)
    logger.info("Added new and updated existing.")

    report = {
        "new_subscribers": import_result.TotalNewSubscribers,
        "existing_subscribers": import_result.TotalExistingSubscribers,
        "duplicates_in_import_list": import_result.DuplicateEmailsInSubmission,
        "uniques_in_import_list": import_result.TotalUniqueEmailsSubmitted
    }

    if len(import_result.FailureDetails):
        errors = defaultdict(list)
        for error in import_result.FailureDetails:
            errors["{} ({})".format(error.Message, error.Code)].append(error.EmailAddress)
        report["errors"] = errors

    return report

def unsubscribe_cm_subscribers(list_id, emails):
    '''
       Unsubscribes all passed-in email addresses from a specified
       Campaign Monitor list.
    '''
    logger.info("Begin unsubscribing people from list {}".format(list_id))
    unsubscribed = []
    for email in emails:
        subscriber = Subscriber(settings.CAMPAIGN_MONITOR_AUTH, list_id, email)
        subscriber.unsubscribe()
        unsubscribed.append(email)
    logger.info("Done unsubscribing people from list {}".format(list_id))
    return unsubscribed

def sync_cm_list(list_id, subscribers):
    '''
        Given a Campaign Monitor list id and a properly-formatted list
        of subscribers, adds new subscribers, updates fields of existing
        subscribers, and unsubscribes any users not present in the
        passed-in list.
    '''
    logger.info("Begin syncing users to Campaign Monitor.")
    reports = {}
    reports['import'] = add_and_update_cm_subscribers(list_id, subscribers)
    unsubscribers = users_to_unsubscribe(list_id, [subscriber['EmailAddress'] for subscriber in subscribers])
    if unsubscribers:
        reports['unsubscribe'] = unsubscribe_cm_subscribers(list_id, unsubscribers)
    logger.info("Done syncing users to Campaign Monitor.")
    return reports
