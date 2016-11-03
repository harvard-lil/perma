import logging
from createsend import Subscriber, List
from collections import defaultdict

from django.conf import settings
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string

from .models import Registrar, LinkUser


logger = logging.getLogger(__name__)

###
### Send email
###

def send_user_email(to_address, template, context):
    email_text = render_to_string(template, context)
    title, email_text = email_text.split("\n\n", 1)
    title = title.split("TITLE: ")[-1]
    send_mail(
        title,
        email_text,
        settings.DEFAULT_FROM_EMAIL,
        [to_address],
        fail_silently=False
    )

def send_admin_email(title, from_address, request, template="email/default.txt", context={}, referer=''):
    """
        Send a message on behalf of a user to the admins.
        Use reply-to for the user address so we can use email services that require authenticated from addresses.
    """
    EmailMessage(
        title,
        render_to_string(template, context=context, request=request),
        settings.DEFAULT_FROM_EMAIL,
        [settings.DEFAULT_FROM_EMAIL],
        headers={'Reply-To': from_address}
    ).send(fail_silently=False)

###
### Collect user data, bundled for emails ###
###

def registrar_users_plus_stats(destination=None):
    '''
        Returns all active registrar users plus assorted metadata as
        a list of dicts. If destination=cm, info is formatted for
        ingest by Campaign Monitor.
    '''
    users = []
    registrars = Registrar.objects.all()
    for registrar in registrars:
        registrar_users = LinkUser.objects.filter(registrar = registrar.pk,
                                                  is_active = True,
                                                  is_confirmed = True)
        for user in registrar_users:
            users.append({ "first_name": user.first_name,
                           "last_name": user.last_name,
                           "email": user.email,
                           "registrar_email": registrar.email,
                           "registrar_name": registrar.name,
                           "total_links": registrar.link_count,
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
        return "{} {}".format(user["first_name"], user["last_name"])

    def format_registrar_users(registrar_users):
        string_list = ["{} {} ({})".format(user.first_name, user.last_name, user.email) for user in registrar_users]
        return "<br> ".join(string_list)

    formatted_users = []
    for user in users:
        formatted = {}
        formatted['Name'] = format_name(user)
        formatted['EmailAddress'] = user["email"]
        formatted['CustomFields'] = [
            {"Key": "RegistrarEmail", "Value":  user["registrar_email"]},
            {"Key": "RegistrarName", "Value": user["registrar_name"]},
            {"Key": "TotalLinks", "Value": user["total_links"]},
            {"Key": "RegistrarUsers", "Value": format_registrar_users(user['registrar_users'])}
        ]
        formatted_users.append(formatted)
    return formatted_users

def users_to_unsubscribe(cm_list_id, current_perma_user_emails):
    '''
        Returns a list of any email addresses marked as active in
        a given Campaign Monitor subscriber list, but not appearing in
        a passed-in list of currely active Perma user email addresses.
    '''
    def retrieve_subscribers(cm_list, page=1, page_size=1000, results = []):
        result = cm_list.active(page=page, page_size=page_size)
        if result.NumberOfPages <= 0:
            return results
        if result.PageNumber == result.NumberOfPages:
            results.extend(result.Results)
            return results
        else:
            results.extend(result.Results)
            return retrieve_subscribers(cm_list, page+1, page_size, results)

    cm_list = List(settings.CAMPAIGN_MONITOR_AUTH, cm_list_id)
    subscribers = retrieve_subscribers(cm_list)

    unsubscribers = []
    for subscriber in subscribers:
        if subscriber.EmailAddress not in current_perma_user_emails:
            unsubscribers.append(subscriber.EmailAddress)
    return unsubscribers

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
