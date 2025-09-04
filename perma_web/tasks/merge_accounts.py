"""
Perma's email addresses used to be case-sensitive, so users could actually
have multiple accounts, with the same address capitalized differently.
We merged accounts using the below tasks, and made login etc. case-insensitive.
"""
from collections import defaultdict
import csv
from invoke import task
import itertools
from pathlib import Path
import re
import time

from django.utils import timezone

from perma.email import send_user_email
from perma.models import Link, LinkUser

import logging
logger = logging.getLogger(__name__)


TRANSFERRED_ORG_LINKS_CSV = 'merge_reports/transferred_org_links.csv'
TRANSFERRED_PERSONAL_LINKS_CSV = 'merge_reports/transferred_personal_links.csv'
MERGED_USERS_CSV = 'merge_reports/merged_users.csv'
RETAINED_USERS_CSV = 'merge_reports/retained_users.csv'


def initialize_csvs(reports_dir):
    p = Path(reports_dir)

    for filename in [TRANSFERRED_ORG_LINKS_CSV, TRANSFERRED_PERSONAL_LINKS_CSV, MERGED_USERS_CSV, RETAINED_USERS_CSV]:
        (p / filename).parent.mkdir(parents=True, exist_ok=True)

    with open(p / TRANSFERRED_ORG_LINKS_CSV, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter='|')
        writer.writerow(['guid', 'from user id', 'to user id', 'moved at'])

    with open(p / TRANSFERRED_PERSONAL_LINKS_CSV, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter='|')
        writer.writerow(['guid', 'from user id', 'from folder id', 'to user id', 'to folder id', 'moved at'])

    with open(p / MERGED_USERS_CSV, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter='|')
        writer.writerow([
            'user id',
            'original email',
            'changed to placeholder',
            'normalized email',
            'merged with user id',
            'org links transferred',
            'personal links transferred',
            'merged at'
        ])

    with open(p / RETAINED_USERS_CSV, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter='|')
        writer.writerow(['user id', 'original email', 'normalized email', 'merged with accounts', 'merged at'])


def merge_accounts(
        to_keep,
        to_delete,
        reports_dir,
        copy_memberships=True,
        transfer_links=False):

    p = Path(reports_dir)

    #
    # Make sure the 'kept' account belongs to the same registrar, or the same orgs, as the other accounts
    #
    if copy_memberships:
        try:
            to_keep.copy_memberships_from_users(itertools.chain([to_keep], to_delete))
        except AssertionError as e:
            logger.error(f"MERGING: Could not merge users {to_keep.id}, {', '.join([str(u.id) for u in to_delete])}: {str(e)}")
            return

    #
    # If we know we need to move links around, do so: first org links, then personal links.
    #
    updated_org_links = defaultdict(lambda: 0)
    updated_personal_links = defaultdict(lambda: 0)
    if transfer_links:
        # Find all links in org folders and change 'created_by' to the new ID.
        org_links = Link.objects.filter(created_by__in=to_delete, organization__isnull=False)
        with open(p / TRANSFERRED_ORG_LINKS_CSV, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter='|')
            for link in org_links:
                writer.writerow([link.guid, link.created_by_id, to_keep.id, timezone.now()])
                updated_org_links[link.created_by_id] += 1
        org_links.update(
            created_by=to_keep
        )

        # Then, move all the Personal Links into the target account's Personal Links folder,
        # in addition to setting 'created_by' to the new ID. We know from studying the accounts
        # in question that folder tree structure can be ignored.
        for user in to_delete:
            personal_links = Link.folders.through.objects.filter(link__in=user.created_links.all())
            with open(p / TRANSFERRED_PERSONAL_LINKS_CSV, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter='|')
                for lf in personal_links:
                    writer.writerow([lf.link_id, lf.link.created_by_id, lf.folder_id, to_keep.id, to_keep.root_folder_id, timezone.now()])
            updated_personal_links[user.id] += personal_links.update(folder_id=to_keep.root_folder_id)
            user.created_links.all().update(created_by_id=to_keep.id)

    #
    # Finally, soft-delete the redundant accounts...
    #
    with open(p / MERGED_USERS_CSV, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter='|')
        for user in to_delete:
            original_email, placeholder_email = user.soft_delete_after_merge_with_user(to_keep)
            writer.writerow([
                user.id,
                original_email,
                placeholder_email,
                original_email.lower(),
                to_keep.id,
                updated_org_links[user.id],
                updated_personal_links[user.id],
                timezone.now()
            ])

    #
    # ...and update our records.
    #
    merged_with = ', '.join([str(user.id) for user in to_delete])
    to_keep.prepend_to_notes(f"Merged with {merged_with}")
    if updated_org_links or updated_personal_links:
        to_keep.link_count = to_keep.created_links.count()
    to_keep.save(update_fields=['notes', 'link_count'])
    with open(p / RETAINED_USERS_CSV, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter='|')
        writer.writerow([
            to_keep.id,
            to_keep.email,
            to_keep.email.lower(),
            merged_with,
            timezone.now()
        ])


def unmerge_accounts(from_user_id, reports_dir, log_to_file=None):
    p = Path(reports_dir)
    user = LinkUser.objects.get(id=from_user_id)
    if match := re.search(r"\n*Merged with (?P<user_ids>.+)", user.notes):
        user_ids = [int(uid) for uid in match.group('user_ids').split(', ')]
    else:
        logger.info(f"MERGING: Found no accounts to unmerge from user {from_user_id}.")
        return

    reversed_org_links = defaultdict(list)
    reversed_personal_links = defaultdict(list)

    # Find all transferred org links and change 'created_by' to the old ID.
    with open(p / TRANSFERRED_ORG_LINKS_CSV, 'r', newline='') as csvfile:
        csv_reader = csv.DictReader(csvfile, delimiter='|')
        to_reverse = []
        for row in csv_reader:
            if int(row['from user id']) in user_ids:
                guid = row['guid']
                original_creator = int(row['from user id'])
                link = Link.objects.get(guid=guid)
                link.created_by_id = original_creator
                to_reverse.append(link)
                reversed_org_links[original_creator].append(guid)
        Link.objects.bulk_update(to_reverse, ['created_by_id'])

    # Find all transferred personal links and move them back to their original folder,
    # in addition to setting 'created_by' to the original ID.
    with open(p / TRANSFERRED_PERSONAL_LINKS_CSV, 'r', newline='') as csvfile:
        csv_reader = csv.DictReader(csvfile, delimiter='|')
        lfs_to_reverse = []
        links_to_reverse = []
        for row in csv_reader:
            if int(row['from user id']) in user_ids:
                guid = row['guid']
                original_creator = int(row['from user id'])
                original_folder = int(row['from folder id'])
                lf = Link.folders.through.objects.select_related('link').get(link_id=guid)
                lf.folder_id = original_folder
                lf.link.created_by_id = original_creator
                lfs_to_reverse.append(lf)
                links_to_reverse.append(lf.link)
                reversed_personal_links[original_creator].append(guid)
        Link.folders.through.objects.bulk_update(lfs_to_reverse, ['folder_id'])
        Link.objects.bulk_update(links_to_reverse, ['created_by_id'])

    # Reverse the soft-deletions
    with open(p / MERGED_USERS_CSV, 'r', newline='') as csvfile:
        csv_reader = csv.DictReader(csvfile, delimiter='|')
        to_reverse = []
        from_users = set()

        for row in csv_reader:
            if int(row['user id']) in user_ids:
                original_email = row['original email']
                from_user_id = int(row['merged with user id'])

                user = LinkUser.objects.get(id=int(row['user id']))
                user.email = original_email
                user.is_active = user.is_confirmed
                user.link_count = int(row['org links transferred']) + int(row['personal links transferred'])

                if match := re.search(r"\n*Original registrar: (?P<registrar_id>\d+)", user.notes):
                    user.registrar_id = int(match.group('registrar_id'))
                    user.remove_line_from_notes('Original registrar')

                if match := re.search(r"\n*Original orgs: (?P<org_ids>.+)", user.notes):
                    orgs = [int(oid) for oid in match.group('org_ids').split(', ')]
                    user.organizations.add(*orgs)
                    user.remove_line_from_notes('Original orgs')

                user.prepend_to_notes(f'Previously merged with user { from_user_id }.')
                user.remove_line_from_notes('Original email')
                to_reverse.append(user)

                from_user = LinkUser.objects.get(id=from_user_id)
                from_user.prepend_to_notes(f"Extracted previously merged user { user.id }.")
                from_user.save(update_fields=['notes'])
                from_users.add(from_user)

        LinkUser.objects.bulk_update(to_reverse, ['email', 'is_active', 'link_count', 'registrar_id', 'notes'])
        for user in from_users:
            user.refresh_from_db()
            if match := re.search(r"\n*Added registrar during the merging of accounts", user.notes):
                user.registrar_id = None
                user.remove_line_from_notes('Added registrar')

            if match := re.search(r"\n*Added organizations.*: (?P<org_ids>.+)", user.notes):
                orgs = [int(oid) for oid in match.group('org_ids').split(', ')]
                user.organizations.remove(*orgs)
                user.remove_line_from_notes('Added organizations')

            user.link_count = user.created_links.count()
            user.save(update_fields=['link_count', 'registrar_id', 'notes'])

        # Report everything that was changed
        if log_to_file:
            with open(log_to_file, 'a', newline='') as file:
                file.write(f"## Unmerged accounts {user_ids} from user {from_user_id}\n")
                file.write(f"{''.join([str(u) for u in to_reverse])} from {from_users.pop()}\n\n")
                if reversed_org_links:
                    file.write("\tREVERSED ORG LINKS\n\n")
                    for original_creator_id, link_list in reversed_org_links.items():
                        file.write(f"\tRestored to user: {original_creator_id}\n")
                        file.write(f"\t{link_list}")
                        file.write("\n\n")
                if reversed_personal_links:
                    file.write("\tREVERSED PERSONAL LINKS\n\n")
                    for original_creator_id, link_list in reversed_personal_links.items():
                        file.write(f"\tRestored to user: {original_creator_id}\n")
                        file.write(f"\t{str(link_list)}")
                        file.write("\n\n")
        else:
            print(f"Unmerged accounts {user_ids} from user {from_user_id}")
            print(f"{to_reverse} from {from_users}")
            if reversed_org_links:
                print(f"Reversed org links {reversed_org_links}")
            if reversed_personal_links:
                print(f"Reversed personal links {reversed_personal_links}")
            print("")


def merge_users_with_only_unconfirmed_accounts(user_list, reports_dir):
    """
    Sync all the registrars/orgs to the most recently created and delete the others.
    """
    user_list.sort(key=lambda u: u.id, reverse=True)
    to_keep, *to_delete = user_list
    merge_accounts(to_keep, to_delete, reports_dir)


def merge_users_with_only_one_confirmed_account(user_list, reports_dir):
    """
    Sync all the registrars/orgs to the confirmed one and delete the other ones.
    """
    user_list.sort(key=lambda u: u.is_confirmed, reverse=True)
    to_keep, *to_delete = user_list
    merge_accounts(to_keep, to_delete, reports_dir)


def merge_users_with_multiple_confirmed_accounts_but_no_links(user_list, reports_dir):
    """
    Select the account they have logged into most recently, or if they
    have never logged in, the most recently created confirmed account.
    Then sync all the registrars/orgs to it and delete the other ones.
    """
    to_keep = None
    to_delete = []

    if any(u.last_login for u in user_list):
        for user in user_list:
            if user.last_login:
                if to_keep:
                    if to_keep.last_login < user.last_login:
                        to_delete.append(to_keep)
                        to_keep = user
                    else:
                        to_delete.append(user)
                else:
                    to_keep = user
            else:
                to_delete.append(user)
    else:
        for user in user_list:
            if user.is_confirmed:
                if to_keep:
                    if to_keep.id < user.id:
                        to_delete.append(to_keep)
                        to_keep = user
                    else:
                        to_delete.append(user)
                else:
                    to_keep = user
            else:
                to_delete.append(user)

    merge_accounts(to_keep, to_delete, reports_dir)


def merge_users_with_only_one_account_with_links(user_list, reports_dir):
    """
    If the account with the links is the one they have logged into most recently, keep that one:
    sync registrars/orgs and then delete the other ones.

    If the account with the links is not the one they have logged into most recently,
    move the links to the most recently logged into account, sync the registrars/orgs,
    and then delete the others.
    """
    [account_with_links] = filter(lambda u: u.link_count, user_list)
    most_recently_logged_into_account = account_with_links
    for user in user_list:
        if user.last_login and user.last_login > most_recently_logged_into_account.last_login:
            most_recently_logged_into_account = user

    if account_with_links == most_recently_logged_into_account:
        to_keep = account_with_links
        to_delete = list(filter(lambda u: u is not to_keep, user_list))
        merge_accounts(to_keep, to_delete, reports_dir)
    else:
        to_keep = most_recently_logged_into_account
        to_delete = list(filter(lambda u: u is not to_keep, user_list))
        merge_accounts(to_keep, to_delete, reports_dir, transfer_links=True)


def merge_users_with_multiple_accounts_with_links(user_list, reports_dir):
    """
    Move all links into the account with the most recent login,
    sync registrars/orgs and then delete the other ones.
    """
    to_keep = None
    to_delete = []
    for user in user_list:
        if user.last_login:
            if to_keep:
                if to_keep.last_login < user.last_login:
                    to_delete.append(to_keep)
                    to_keep = user
                else:
                    to_delete.append(user)
            else:
                to_keep = user
        else:
            to_delete.append(user)
    merge_accounts(to_keep, to_delete, reports_dir, transfer_links=True)


DUPLICATIVE_USER_SQL = '''
  SELECT
    perma_linkuser.id,
    perma_linkuser.email,
    perma_linkuser.is_active,
    perma_linkuser.is_confirmed,
    perma_linkuser.link_count,
    perma_linkuser.registrar_id,
    STRING_AGG (DISTINCT perma_linkuser_organizations.organization_id::TEXT, ',') organization_ids,
    perma_linkuser.cached_subscription_status
  FROM
    perma_linkuser
    LEFT OUTER JOIN perma_linkuser_organizations ON (
      perma_linkuser.id = perma_linkuser_organizations.linkuser_id
    )
  WHERE
    LOWER(perma_linkuser.email) in (
      SELECT
        LOWER(perma_linkuser.email)
      FROM
        perma_linkuser
      GROUP BY
        LOWER(perma_linkuser.email)
      HAVING
        COUNT(*) > 1
    )
  GROUP BY
    perma_linkuser.id;
'''


def get_and_categorize_duplicative_users():
    duplicative_users = LinkUser.objects.raw(DUPLICATIVE_USER_SQL)
    grouped_duplicative_users = defaultdict(list)

    count = 0
    for user in duplicative_users:
        count += 1
        grouped_duplicative_users[user.email.lower()].append(user)
    logger.info(f"MERGING: Found {count} addresses, for {len(grouped_duplicative_users)} users.")

    any_paid_history = set()
    registrar_and_org_mix = set()
    none_confirmed = set()
    only_one_confirmed = set()

    multiple_confirmed = defaultdict(list)
    multiple_confirmed_none_with_links = set()
    multiple_confirmed_only_one_with_links = set()
    multiple_confirmed_several_with_links = set()

    #
    # Identify any groups of users that are not safe to merge
    #
    for normalized_email, user_group in grouped_duplicative_users.items():

        registrar = False
        orgs = False
        for user in user_group:
            purchase_history = user.get_purchase_history()
            has_purchase_history = bool(purchase_history['purchases']) if purchase_history else False
            if user.cached_subscription_status or has_purchase_history:
                any_paid_history.add(normalized_email)
            if user.registrar_id:
                registrar = True
            if user.organization_ids:
                orgs = True
        if registrar and orgs:
            registrar_and_org_mix.add(normalized_email)

    exclude_group = any_paid_history | registrar_and_org_mix
    logger.warning(f"MERGING: Found {len(any_paid_history)} users who have purchased subscriptions or bonus links.")
    logger.warning(f"MERGING: Found {len(registrar_and_org_mix)} users who have accounts associated with both registrars and orgs.")

    #
    # Organize remaining users by how many accounts associated with their email address have been confirmed.
    #
    for normalized_email, user_group in grouped_duplicative_users.items():
        if normalized_email not in exclude_group:
            confirmed = []
            for user in user_group:
                if user.is_confirmed:
                    confirmed.append(user.id)
            if not confirmed:
                none_confirmed.add(normalized_email)
            elif len(confirmed) == 1:
                only_one_confirmed.add(normalized_email)
            else:
                multiple_confirmed[normalized_email] = user_group

    logger.info(f"MERGING: Found {len(none_confirmed)} users with no confirmed accounts.")
    logger.info(f"MERGING: Found {len(only_one_confirmed)} users with only one confirmed account.")

    #
    # Organize with multiple confirmed accounts by how many of them have links.
    #
    for normalized_email, user_group in multiple_confirmed.items():
        has_links = []
        for user in user_group:
            if user.link_count > 0:
                has_links.append(user.id)
        if not has_links:
            multiple_confirmed_none_with_links.add(normalized_email)
        elif len(has_links) == 1:
            multiple_confirmed_only_one_with_links.add(normalized_email)
        else:
            multiple_confirmed_several_with_links.add(normalized_email)

    logger.info(f"MERGING: Found {len(multiple_confirmed_none_with_links)} users with multiple confirmed accounts, but no links.")
    logger.info(f"MERGING: Found {len(multiple_confirmed_only_one_with_links)} users that have multiple confirmed accounts but only one account with links.")
    logger.info(f"MERGING: Found {len(multiple_confirmed_several_with_links)} users that have multiple accounts with links.")

    return {
        'none_confirmed': none_confirmed,
        'only_one_confirmed': only_one_confirmed,
        'multiple_confirmed_none_with_links': multiple_confirmed_none_with_links,
        'multiple_confirmed_only_one_with_links': multiple_confirmed_only_one_with_links,
        'multiple_confirmed_several_with_links': multiple_confirmed_several_with_links
    }


@task
def merge_duplicative_accounts(ctx, reports_dir='.'):
    soup = time.time()

    emails_by_category = get_and_categorize_duplicative_users()

    initialize_csvs(reports_dir)

    def merge_category(category, merge_func):
        start = time.time()
        for normalized_email in emails_by_category[category]:
            users = LinkUser.objects.filter(email__iexact=normalized_email)
            merge_func(list(users), reports_dir)
        end = time.time()
        logger.info(f"MERGING: Merged {category} in {end - start} seconds.")

    merge_category('none_confirmed', merge_users_with_only_unconfirmed_accounts)
    merge_category('only_one_confirmed', merge_users_with_only_one_confirmed_account)
    merge_category('multiple_confirmed_none_with_links', merge_users_with_multiple_confirmed_accounts_but_no_links)
    merge_category('multiple_confirmed_only_one_with_links', merge_users_with_only_one_account_with_links)
    merge_category('multiple_confirmed_several_with_links', merge_users_with_multiple_accounts_with_links)

    nuts = time.time()
    logger.info(f"MERGING: Merged all duplicative accounts in {nuts - soup} seconds.")


@task
def unmerge_duplicative_accounts(ctx, log_to_file=None, reports_dir='.'):
    p = Path(reports_dir)
    with open(p / RETAINED_USERS_CSV, 'r', newline='') as csvfile:
        csv_reader = csv.DictReader(csvfile, delimiter='|')
        for row in csv_reader:
            unmerge_accounts(row['user id'], reports_dir, log_to_file)


@task
def assert_no_duplicative_accounts(ctx):
    duplicative_users = LinkUser.objects.raw(DUPLICATIVE_USER_SQL)
    assert not len(duplicative_users), ", ".join(str(user.id) for user in duplicative_users)


@task
def email_retained_users(ctx, reports_dir='.'):
    p = Path(reports_dir)

    sent_count = 0
    failed_list = []

    logger.info("Begin emailing users.")
    with open(p / RETAINED_USERS_CSV, 'r', newline='') as csvfile:
        csv_reader = csv.DictReader(csvfile, delimiter='|')
        for row in csv_reader:
            raw_email = row['original email']
            succeeded = send_user_email(raw_email,'email/merged.txt',{})
            if succeeded:
                sent_count += 1
            else:
                failed_list.append(row['user id'])

    logger.info(f"Emailed {sent_count} users")
    if failed_list:
        logger.warning(f"Some users were not emailed: {str(failed_list)}. Check log for fatal SMTP errors.")
