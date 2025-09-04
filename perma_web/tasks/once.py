"""
One-time tasks, to fix anomalies or follow up after changes to the database.
"""
import internetarchive
from invoke import task
import surt
from tqdm import tqdm

from django.conf import settings
from django.db import connections
from django.db.models import Count

from perma.models import Folder, Link, LinkUser, Organization, CaptureJob

import logging
logger = logging.getLogger(__name__)


@task
def test_db_connection(ctx, connection):
    """
    Open a database connection.
    Use this task repeatedly, possibly with different database connection settings,
    e.g. in order to flush out a transient SSL connection problem, something like:
    while [ 1 ] ; do date ; invoke dev.test-db-connection "some-connection" ; sleep 1 ; done
    """
    print(f"Attempting connection to {connection} ...")
    cursor = connections[connection].cursor()
    print("Succeeded.")
    cursor.close()


@task
def delete_redundant_personal_links_folders(ctx, dry_run=False):
    """
    Clean up users with two top-level Personal Links folders, due to an as-yet-undiagnosed timing issue.
    """
    duplicated_folders = Folder.objects.filter(
        name='Personal Links',
        parent__isnull=True
    ).values(
        'owned_by_id'
    ).annotate(
        owner_count=Count('owned_by_id')
    ).filter(
        owner_count__gt=1
    )

    users_with_duplicate_folders = LinkUser.objects.filter(
        id__in=duplicated_folders.values_list('owned_by_id', flat=True)
    )

    skipped = 0
    fixed_up = 0
    mangled = 0

    for user in users_with_duplicate_folders:

        folders = user.folders.filter(name='Personal Links')

        try:
            assert len(folders) == 2
            assert user.root_folder_id in [folder.id for folder in folders]
            [redundant] = filter(lambda f: f.id != user.root_folder_id, folders)
            assert redundant.is_empty()
        except AssertionError:
            print(f"Skipping user {user.id}: their situation isn't accounted for. Please investigate.")
            skipped = skipped + 1
            continue

        if dry_run:
            print(f"Would delete {redundant.id} and retain {user.root_folder_id} for user {user.id}.")
            fixed_up = fixed_up + 1
        else:
            print(f"Deleting {redundant.id} and retaining {user.root_folder_id} for user {user.id}.")
            deleted = redundant.delete()
            try:
                assert deleted[0] == 1
                fixed_up = fixed_up + 1
            except AssertionError:
                print(f"We deleted more things than we intended to, for user {user.id}...: {deleted}")
                mangled = mangled + 1

    if dry_run:
        print("\nDRY RUN:")
    print(f"\nFixed up: {fixed_up}")
    print(f"Skipped: {skipped}")
    print(f"Mangled: {mangled}\n")


@task
def delete_redundant_org_folders(ctx, dry_run=False):
    """
    Clean up orgs with two top-level shared folders, due to an as-yet-undiagnosed timing issue.
    """
    duplicated_folders = Folder.objects.filter(
        is_shared_folder=True
    ).order_by().values(
        'organization_id'
    ).annotate(
        org_count=Count('organization_id')
    ).filter(
        org_count__gt=1
    )

    orgs_with_duplicate_folders = Organization.objects.all_with_deleted().filter(
        id__in=duplicated_folders.values_list('organization_id', flat=True)
    )

    skipped = 0
    fixed_up = 0
    mangled = 0

    for org in orgs_with_duplicate_folders:

        folders = org.folders.filter(name=org.name)

        try:
            assert len(folders) == 2
            assert org.shared_folder_id in [folder.id for folder in folders]
            [redundant] = filter(lambda f: f.id != org.shared_folder_id, folders)
            assert redundant.is_empty()
        except AssertionError:
            print(f"Skipping org {org.id}: its situation isn't accounted for. Please investigate.")
            skipped = skipped + 1
            continue

        if dry_run:
            print(f"Would delete {redundant.id} and retain {org.shared_folder_id} for org {org.id}.")
            fixed_up = fixed_up + 1
        else:
            print(f"Deleting {redundant.id} and retaining {org.shared_folder_id} for org {org.id}.")
            deleted = redundant.delete()
            try:
                assert deleted[0] == 1
                fixed_up = fixed_up + 1
            except AssertionError:
                print(f"We deleted more things than we intended to, for org {org.id}...: {deleted}")
                mangled = mangled + 1

    if dry_run:
        print("\nDRY RUN:")
    print(f"\nFixed up: {fixed_up}")
    print(f"Skipped: {skipped}")
    print(f"Mangled: {mangled}\n")


@task
def fix_ia_metadata(ctx):
    """
        One-off helper function, kept for example purposes. Update all existing IA uploads to remove `sponsor` metadata.
    """
    for link in Link.objects.filter(internet_archive_upload_status='completed').order_by('guid').values('guid'):
        result = 'success'
        identifier = settings.INTERNET_ARCHIVE_IDENTIFIER_PREFIX + link['guid']
        try:
            item = internetarchive.get_item(identifier)
            if item.exists and item.metadata.get('sponsor'):
                item.modify_metadata({"sponsor": "REMOVE_TAG"},
                                     access_key=settings.INTERNET_ARCHIVE_ACCESS_KEY,
                                     secret_key=settings.INTERNET_ARCHIVE_SECRET_KEY)
        except Exception as e:
            result = str(e)
        print(f"{link['guid']}\t{result}")


@task
def populate_link_surt_column(ctx, batch_size=500, model='Link'):
    logger.info("BEGIN: populate_link_surt_column")

    models = {'Link': Link}
    links = models[model].objects.filter(submitted_url_surt__isnull=True)

    # limit to our desired batch size
    not_populated = links.count()
    if not_populated > batch_size:
        logger.info(f"{not_populated} links to update: limiting to first {batch_size}")
        links = links[:batch_size]

    to_update = links.count()
    if not to_update:
        logger.info("No links to update.")
        return

    for link in tqdm(links):
        link.submitted_url_surt = surt.surt(link.submitted_url)
        link.save()

    # offer to send another batch if there are any links left to update
    remaining_to_update = not_populated - to_update
    if remaining_to_update:
        if input(f"\nSend another batch of size {batch_size}? [y/n]\n").lower() == 'y':
            populate_link_surt_column(batch_size=str(batch_size), model=model)
        else:
            logger.info(f"Stopped with ~ {remaining_to_update} remaining {model}s to update")
    else:
        logger.info(f"No more {model}s left to update!")


@task
def populate_folder_cached_path(ctx, batch_size=500):
    logger.info("BEGIN: populate_folder_cached_path")

    folders = Folder.objects.filter(cached_path__isnull=True)

    # limit to our desired batch size
    not_populated = folders.count()
    if not_populated > batch_size:
        logger.info(f"{not_populated} folders to update: limiting to first {batch_size}")
        folders = folders[:batch_size]

    to_update = folders.count()
    if not to_update:
        logger.info("No folders to update.")
        return

    for folder in tqdm(folders):
        folder.cached_path = folder.get_path()
        folder.save()

    # offer to send another batch if there are any links left to update
    remaining_to_update = not_populated - to_update
    if remaining_to_update:
        if input(f"\nSend another batch of size {batch_size}? [y/n]\n").lower() == 'y':
            populate_folder_cached_path(batch_size=str(batch_size))
        else:
            logger.info(f"Stopped with ~ {remaining_to_update} remaining folders to update")
    else:
        logger.info("No more folders left to update!")


@task
def clear_successful_scoop_logs(ctx, batch_size=500):
    logger.info("BEGIN: clear_successful_scoop_logs")
    capture_job_ids = CaptureJob.objects.filter(
        scoop_job_id__isnull=False
    ).exclude(
        status="failed"
    ).values_list('id', flat=True)

    capture_job_ids = list(capture_job_ids)
    logger.info(f"Found {len(capture_job_ids)} capture jobs to update.")

    for i in tqdm(range(0, len(capture_job_ids), batch_size)):
        batch = capture_job_ids[i:i + batch_size]
        CaptureJob.objects.filter(id__in=batch).update(scoop_logs=None)

    logger.info("END: clear_successful_scoop_logs")
