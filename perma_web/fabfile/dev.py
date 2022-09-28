import os
import subprocess
import signal
import sys

from django.conf import settings
from fabric.context_managers import shell_env
from fabric.decorators import task
from fabric.operations import local


@task(name='run')
def run_django(port="0.0.0.0:8000", cert_file='perma-test.crt', key_file='perma-test.key', debug_toolbar=''):
    """
        Run django test server on open port, so it's accessible outside Docker.

        Use runserver_plus for SSL.
    """
    commands = []

    if settings.CELERY_TASK_ALWAYS_EAGER:
        print("\nWarning! Batch Link creation will not work as expected:\n" +
              "to create new batches you should run with settings.CELERY_TASK_ALWAYS_EAGER = False\n")
    else:
        print("\nStarting background celery process.")
        commands.append("watchmedo auto-restart -d ./ -p '*.py' -R -- celery -A perma worker --loglevel=info -Q celery,background,ia -B -n w1@%h")

    if settings.PROXY_CAPTURES:
        print("\nStarting Tor service in the background.")
        commands.append('tor')

    # Only run the webpack background process in debug mode -- with debug False, dev server uses static assets,
    # and running webpack just messes up the webpack stats file.
    # Similarly, don't download fresh replayweb.page assets, to avoid confusion.
    if settings.DEBUG:
        commands.append('npm start')
        commands.append("watchmedo auto-restart -d ./perma/settings/ -p '*.py' -R -- fab dev.get_replay_assets")

    proc_list = [subprocess.Popen(command, shell=True, stdout=sys.stdout, stderr=sys.stderr) for command in commands]

    with shell_env(DEBUG_TOOLBAR=debug_toolbar):

        try:
            # use runserver_plus
            import django_extensions  # noqa
            if not os.path.exists(os.path.join(settings.PROJECT_ROOT, cert_file)) or not os.path.exists(os.path.join(settings.PROJECT_ROOT, key_file)):
                print("\nError! The required SSL cert and key files are missing. See developer.md for instructions on how to generate.")
                return
            options = f'--cert-file {cert_file} --key-file {key_file}'
            local(f"python manage.py runserver_plus {port} {options}")
        finally:
            for proc in proc_list:
                os.kill(proc.pid, signal.SIGKILL)


_default_tests = "functional_tests perma api lockss"


@task
def test(apps=_default_tests):
    """ Run perma tests. (For coverage, run `coverage report` after tests pass.) """
    test_python(apps)
    if apps == _default_tests:
        test_js()

@task
def test_python(apps=_default_tests):
    """ Run Python tests. """

    # In order to run functional_tests, we have to run collectstatic, since functional tests use DEBUG=False
    # For speed we use the default Django STATICFILES_STORAGE setting here, which also has to be set in settings_testing.py
    if "functional_tests" in apps:
        local("DJANGO__STATICFILES_STORAGE=django.contrib.staticfiles.storage.StaticFilesStorage python manage.py collectstatic --noinput")

    local(f"pytest {apps} --no-migrations --ds=perma.settings.deployments.settings_testing --cov --cov-config=setup.cfg --cov-report= ")

@task
def test_js():
    """ Run Javascript tests. """
    local("npm test")


@task(alias='pip-compile')
def pip_compile(args=''):
    import subprocess

    # run pip-compile
    # Use --allow-unsafe because pip --require-hashes needs all requirements to be pinned, including those like
    # setuptools that pip-compile leaves out by default.
    command = ['pip-compile', '--generate-hashes', '--allow-unsafe']+args.split()
    print("Calling %s" % " ".join(command))
    subprocess.check_call(command, env=dict(os.environ, CUSTOM_COMPILE_COMMAND='fab pip-compile'))


@task()
def get_replay_assets():
    import requests

    for asset in ['sw.js', 'ui.js', 'ruffle/ruffle.js']:
        dest = os.path.join(settings.PROJECT_ROOT, f'static/vendors/replay-web-page/{asset}')
        with open(dest, 'wb') as file:
            url = f'{settings.REPLAYWEBPAGE_SOURCE_URL}@{settings.REPLAYWEBPAGE_VERSION}/{asset}'
            print(f'Downloading {url} to {dest}')
            response = requests.get(url)
            file.write(response.content)


@task
def logs(log_dir=os.path.join(settings.PROJECT_ROOT, '../services/logs/')):
    """ Tail all logs. """
    local(f"tail -f {log_dir}/*")


@task
def init_db():
    """
        Apply migrations and import fixtures for new dev database.
    """
    local("python manage.py migrate")
    local("python manage.py loaddata fixtures/sites.json fixtures/users.json fixtures/folders.json")


@task
def build_week_stats():
    """
        A temporary helper to populate our weekly stats
    """
    from perma.models import Link, LinkUser, Organization, Registrar, WeekStats
    from datetime import timedelta
    from django.utils import timezone

    # regenerate all weekly stats
    WeekStats.objects.all().delete()

    oldest_link = Link.objects.earliest('creation_timestamp')

    # this is always the end date in our range, usually a saturday
    date_of_stats = oldest_link.creation_timestamp

    # this is the start date in our range, always a sunday
    start_date = date_of_stats

    links_this_week = 0
    users_this_week = 0
    orgs_this_week = 0
    registrars_this_week = 0

    while date_of_stats < timezone.now():
        links_this_week += Link.objects.filter(creation_timestamp__year=date_of_stats.year,
            creation_timestamp__month=date_of_stats.month, creation_timestamp__day=date_of_stats.day).count()

        users_this_week += LinkUser.objects.filter(date_joined__year=date_of_stats.year,
            date_joined__month=date_of_stats.month, date_joined__day=date_of_stats.day).count()

        orgs_this_week += Organization.objects.filter(date_created__year=date_of_stats.year,
            date_created__month=date_of_stats.month, date_created__day=date_of_stats.day).count()

        registrars_this_week += Registrar.objects.approved().filter(date_created__year=date_of_stats.year,
            date_created__month=date_of_stats.month, date_created__day=date_of_stats.day).count()

        # if this is a saturday, write our sums and reset our counts
        if date_of_stats.weekday() == 5:
            week_of_stats = WeekStats(start_date=start_date, end_date=date_of_stats, links_sum=links_this_week,
                users_sum=users_this_week, organizations_sum=orgs_this_week, registrars_sum=registrars_this_week)
            week_of_stats.save()

            links_this_week = 0
            users_this_week = 0
            orgs_this_week = 0
            registrars_this_week = 0

            start_date = date_of_stats + timedelta(days=1)

        date_of_stats += timedelta(days=1)

@task
def test_internet_archive():
    from datetime import timedelta
    from django.utils import timezone
    import internetarchive
    from perma.models import Link
    from django.template.defaultfilters import truncatechars

    start_date = timezone.now() - timedelta(days=3)
    end_date   = timezone.now() - timedelta(days=2)

    links = Link.objects.filter(internet_archive_upload_status="completed", creation_timestamp__range=(start_date, end_date))

    guid_results = dict()
    all_results = dict()

    c = {"s3":{"access":settings.INTERNET_ARCHIVE_ACCESS_KEY, "secret":settings.INTERNET_ARCHIVE_SECRET_KEY}}
    internetarchive.get_session(config=c)

    for link in links:
        identifier = settings.INTERNET_ARCHIVE_IDENTIFIER_PREFIX + link.guid
        item = internetarchive.get_item(identifier)
        warc_name = f"{link.guid}.warc.gz"

        try:
            fnames = [f.name for f in internetarchive.get_files(identifier, glob_pattern="*gz")]
            guid_results["uploaded_file"] = warc_name in fnames
            if settings.INTERNET_ARCHIVE_COLLECTION == 'test_collection':
                guid_results["collection"] = item.metadata["collection"] == settings.INTERNET_ARCHIVE_COLLECTION
            else:
                guid_results["collection"] = item.metadata["collection"][0] == settings.INTERNET_ARCHIVE_COLLECTION
            guid_results["title"] = item.metadata["title"] == f"{link.guid}: {truncatechars(link.submitted_title, 50)}"
            guid_results["mediatype"] = item.metadata["mediatype"]=="web"
            guid_results["description"] = item.metadata["description"]==f"Perma.cc archive of {link.submitted_url} created on {link.creation_timestamp}."
            guid_results["contributor"] = item.metadata["contributor"]=="Perma.cc"
            guid_results["submitted_url"] = item.metadata["submitted_url"]==link.submitted_url
            guid_results["perma_url"] = item.metadata["perma_url"]==f"http://{settings.HOST}/{link.guid}"
            guid_results["external-identifier"] = item.metadata["external-identifier"]==f"urn:X-perma:{link.guid}"
            if link.organization:
                guid_results["organization"] = item.metadata["sponsor"] == f"{link.organization} - {link.organization.registrar}"

        except Exception as e:
            guid_results["error"] = e
            pass

        all_results[link.guid] = guid_results

    print(all_results)

@task
def upload_all_to_internet_archive():
    from django.utils import timezone
    from perma.tasks import upload_to_internet_archive
    from perma.models import Link
    from datetime import timedelta
    from django.db.models import Q

    links = Link.objects.filter((Q(internet_archive_upload_status='not_started') |
                                Q(internet_archive_upload_status='failed') |
                                Q(internet_archive_upload_status='deleted', is_private=False)) &
                                Q(creation_timestamp__lte=timezone.now()-timedelta(days=1), is_private=False, is_unlisted=False)
                                ).order_by('creation_timestamp')

    for link in links:
        upload_to_internet_archive(link.guid)


@task
def count_pending_ia_links():
    """
    For use in monitoring the size of the queue.
    """
    from perma.models import Link

    count = Link.objects.visible_to_ia().filter(
        internet_archive_upload_status__in=['not_started', 'failed', 'upload_or_reupload_required', 'deleted']
    ).count()
    print(count)


@task
def count_links_without_cached_playback_status():
    """
    For use in monitoring the size of the queue.
    """
    from perma.models import Link

    count = Link.objects.permanent().filter(cached_can_play_back__isnull=True).count()
    print(count)


@task
def rebuild_folder_trees():
    from perma.models import Organization, LinkUser, Folder
    print("Checking for broken folder trees ...")

    for o in Organization.objects.all():
        if set(o.folders.all()) != set(o.shared_folder.get_descendants(include_self=True)):
            print(f"Tree corruption found for org: {o}")
            Folder._tree_manager.partial_rebuild(o.shared_folder.tree_id)

    for u in LinkUser.objects.all():
        if u.root_folder and set(u.folders.all()) != set(u.root_folder.get_descendants(include_self=True)):
            print(f"Tree corruption found for user: {u}")
            Folder._tree_manager.partial_rebuild(u.root_folder.tree_id)


@task
def ping_all_users(limit_to="", exclude="", batch_size="500"):
    '''
       Sends an email to all our current users. See templates/email/special.txt

       Arguments should be strings, with multiple values separated by semi-colons
       e.g. fab ping_all_users:limit_to="14;27;30",batch_size="1000"

       Limit filters are applied before exclude filters.
    '''
    import logging
    from tqdm import tqdm
    from perma.models import LinkUser
    from perma.email import send_user_email

    logger = logging.getLogger(__name__)

    logger.info("BEGIN: ping_all_users")

    # load desired Perma users
    if limit_to:
        users = LinkUser.objects.filter(id__in=limit_to.split(";"))
    else:
        users = LinkUser.objects.filter(is_confirmed=True, is_active=True)
    if exclude:
        users = users.exclude(id__in=exclude.split(";"))

    # exclude users we have already emailed
    already_emailed_path = '/tmp/perma_emailed_user_list'
    already_emailed = set()
    if os.path.exists(already_emailed_path):
        logging.info("Loading list of already-emailed users.")
        with open(already_emailed_path) as f:
            lines = f.read().splitlines()
            for line in lines:
                already_emailed.add(int(line))
    if already_emailed:
        users = users.exclude(id__in=already_emailed)

    # limit to our desired batch size
    not_yet_emailed = users.count()
    batch_size = int(batch_size)
    if not_yet_emailed > batch_size:
        logger.info(f"{not_yet_emailed} users to email: limiting to first {batch_size}")
        users = users[:batch_size]

    to_send_count = users.count()
    if not to_send_count:
        logger.info("No users to email.")
        return

    sent_count = 0
    failed_list = []
    logger.info(f"Begin emailing {to_send_count} users.")
    with open(already_emailed_path, 'a') as f:
        for user in tqdm(users):
            succeeded = send_user_email(user.email,
                                        'email/special.txt',
                                         {'user': user})
            if succeeded:
                sent_count += 1
                f.write(str(user.id)+"\n")
            else:
                failed_list.append(user.id)

    logger.info(f"Emailed {sent_count} users")
    if to_send_count != sent_count:
        if failed_list:
            msg = f"Some users were not emailed: {str(failed_list)}. Check log for fatal SMTP errors."
        else:
            msg = "Some users were not emailed. Check log for fatal SMTP errors."
        logger.error(msg)

    # offer to send another batch if there are any users left to email
    remaining_to_email = not_yet_emailed - sent_count
    if remaining_to_email:
        if input(f"\nSend another batch of size {batch_size}? [y/n]\n").lower() == 'y':
            ping_all_users(batch_size=str(batch_size))
        else:
            logger.info(f"Stopped with ~ {remaining_to_email} remaining users to email")
    else:
        logger.info("Done! Run me again, to catch anybody who signed up while this was running!")


@task
def ping_registrar_users(limit_to="", limit_by_tag="", exclude="", exclude_by_tag="", email="stats", year=""):
    '''
       Sends an email to our current registrar users. See templates/email/registrar_user_ping.txt

       Arguments should be strings, with multiple values separated by semi-colons
       e.g. fab ping_registrar_users:limit_to="14;27;30",exclude_by_tag="opted_out",email="special"

       Limit filters are applied before exclude filters.
    '''
    import json, logging
    from datetime import datetime
    from django.http import HttpRequest
    from perma.models import Registrar
    from perma.email import send_user_email, send_self_email, registrar_users, registrar_users_plus_stats

    logger = logging.getLogger(__name__)

    registrars = Registrar.objects.all()
    if limit_to:
        registrars = registrars.filter(id__in=limit_to.split(";"))
    if limit_by_tag:
        registrars = registrars.filter(tags__name__in=limit_by_tag.split(";")).distinct()
    if exclude:
        registrars = registrars.exclude(id__in=exclude.split(";"))
    if exclude_by_tag:
        registrars = registrars.exclude(tags__name__in=exclude_by_tag.split(";")).distinct()
    if year:
        year = int(year)
    else:
        year = datetime.now().year - 1

    if email == 'stats':
        template = 'email/registrar_user_ping.txt'
        users = registrar_users_plus_stats(registrars=registrars, year=year)
    elif email == 'special':
        # update special template as desired, to send one-off emails
        # update email.registrar_users if you need more context variables
        template = 'email/special.txt'
        users = registrar_users(registrars=registrars)
    else:
        NotImplementedError()

    logger.info("Begin emailing registrar users.")
    send_count = 0
    failed_list = []
    for user in users:
        context = {}
        context.update(user)
        context["year"] = year
        succeeded = send_user_email(user['email'],
                                    template,
                                     context)
        if succeeded:
            send_count += 1
        else:
            failed_list.append(user.id)

    # Another option is to use Django's send_mass_email.
    # It's unclear which would be more performant in real life.
    # send_count = send_mass_user_email('email/registrar_user_ping.txt',
    #                                   [(user['email'], user) for user in users])
    logger.info("Done emailing registrar users.")
    if len(users) != send_count:
        if failed_list:
            msg = f"Some registrar users were not emailed: {failed_list}. Check log for fatal SMTP errors."
        else:
            msg = "Some registrar users were not emailed. Check log for fatal SMTP errors."
        logger.error(msg)
        result = "incomplete"
    else:
        result = "ok"
    send_self_email("Registrar Users Emailed",
                     HttpRequest(),
                     'email/admin/pinged_registrar_users.txt',
                     {"users": users, "result": result})
    return json.dumps({"result": result, "send_count": send_count})


@task
def fix_ia_metadata():
    """
        One-off helper function, kept for example purposes. Update all existing IA uploads to remove `sponsor` metadata.
    """
    from django.conf import settings
    import internetarchive
    from perma.models import Link

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
def check_s3_hashes():
    """
        Confirm that files in primary (disk) storage are also in secondary (s3) storage.

        One-off helper function, kept for example purposes.
    """
    from django.core.files.storage import default_storage
    from tqdm import tqdm
    import hashlib

    local_cache_path = '/tmp/perma_local_file_list'
    remote_cache_path = '/tmp/perma_remote_file_list'
    remote_paths = {}

    if not os.path.exists(local_cache_path):
        print("Building local state ...")
        local_warc_path = os.path.join(settings.MEDIA_ROOT, settings.WARC_STORAGE_DIR)
        remove_char_count = len(settings.MEDIA_ROOT+1)
        with open(local_cache_path, 'w') as tmp_file:
            for root, subdirs, files in tqdm(os.walk(local_warc_path)):
                for f in files:
                    tmp_file.write(os.path.join(root, f)[remove_char_count:]+"\n")
    else:
        print(f"Using cached local state from {local_cache_path}")

    if not os.path.exists(remote_cache_path):
        print("Building remote state ...")
        remove_char_count = len(settings.SECONDARY_MEDIA_ROOT)
        with open(remote_cache_path, 'w') as tmp_file:
            for f in tqdm(default_storage.secondary_storage.bucket.list('generated/warcs/')):
                key = f.key[remove_char_count:]
                val = f.etag[1:-1]
                tmp_file.write(f"{key}\t{val}\n")
                remote_paths[key] = val
    else:
        print(f"Using cached remote state from {remote_cache_path}")
        for line in open(remote_cache_path):
            key, val = line[:-1].split("\t")
            remote_paths[key] = val

    print("Comparing local and remote ...")
    blocksize = 2 ** 20
    for local_path in tqdm(open(local_cache_path)):
        local_path = local_path[:-1]
        if local_path not in remote_paths:
            print("Missing from remote:", local_path)
            continue
        m = hashlib.md5()
        with open(os.path.join(settings.MEDIA_ROOT, local_path), "rb") as f:
            while True:
                buf = f.read(blocksize)
                if not buf:
                    break
                m.update(buf)
        if m.hexdigest() != remote_paths[local_path]:
            print(f"Hash mismatch! Local: {m.hexdigest()} Remote: {remote_paths[local_path]}")


@task
def check_storage(start_date=None):
    """
        Confirm that, for every link, there is a WARC in each storage, and that their hashes match.

        start_date is in the format YYYY-MM-DD

        Ground truth is the list of link objects: compare its list of warcs with those of each storage,
        and compare hashes when more than one such file is present.

        Derived from check_s3_hashes
    """
    from django.core.files.storage import default_storage
    from django.db.models import Q
    from perma.models import Link, Capture

    from datetime import date, datetime
    from dateutil.relativedelta import relativedelta
    import pytz
    import re

    # check the arg
    if not start_date:
        # use first archive date
        start_datetime = Link.objects.order_by('creation_timestamp')[0].creation_timestamp
    elif re.match(r'^\d\d\d\d-\d\d-\d\d$', start_date):
        start_datetime = pytz.utc.localize(datetime.strptime(start_date, "%Y-%m-%d"))
    else:
        print("Bad argument")
        return
    end_datetime = pytz.utc.localize(datetime.now())

    # The abstraction of multiple storages is an artifact of the
    # transition to S3 for storage; although it's conceivable that we'd
    # want multiple storages at some point again, there's no need right now
    # to diverge from the Django norm. The abstraction remains here as a
    # point of historical interest.
    storages = {'primary': {'storage': default_storage, 'lookup': {}}}

    # only use cache files when all are present: link cache, and one for each storage
    link_cache = '/tmp/perma_link_cache{0}.txt'.format("" if start_date is None else start_date)
    caches = [link_cache]
    for key in storages:
        caches.append('/tmp/perma_storage_cache_{0}{1}.txt'.format(key, "" if start_date is None else start_date))

    if not all(os.path.exists(p) for p in caches):
        print("Building link cache ...")
        with open(link_cache, 'w') as tmp_file:
            capture_filter = (Q(role="primary") & Q(status="success")) | (Q(role="screenshot") & Q(status="success"))
            # assemble list of links by year-month, as in lockss/views.titledb:
            start_month = date(year=start_datetime.year, month=start_datetime.month, day=1)
            today = date.today()
            while start_month <= today:
                for link in Link.objects.filter(
                        creation_timestamp__year=start_month.year,
                        creation_timestamp__month=start_month.month,
                        creation_timestamp__gte=start_datetime,
                        creation_timestamp__lt=end_datetime,
                        captures__in=Capture.objects.filter(capture_filter)
                ).distinct():
                    tmp_file.write(f"{link.warc_storage_file()}\n")
                    # this produces strings like u'warcs/0G/GO/XR/XG/0-GGOX-RXGQ.warc.gz'; make the storage paths match
                    # by chopping off the prefix, whether storage.location, ._root_path, or .base_location
                start_month += relativedelta(months=1)

        print("Building storage cache{0} ...".format("s" if len(storages) > 1 else ""))
        for key in storages:
            storage = storages[key]['storage']
            with open('/tmp/perma_storage_cache_{0}{1}.txt'.format(key, "" if start_date is None else start_date), 'w') as tmp_file:
                if hasattr(storage, 'bucket'):
                    # S3
                    for f in storage.bucket.list('generated/warcs/'):
                        if (not start_date) or (start_datetime <= pytz.utc.localize(datetime.strptime(f.last_modified, '%Y-%m-%dT%H:%M:%S.%fZ')) < end_datetime):
                            # here we chop off the prefix aka storage.location
                            path = f.key[(len(storage.location)):]
                            # etag is a string like u'"3ea8c903d9991d466ec437d1789379a6"', so we need to
                            # knock off the extra quotation marks
                            hash = f.etag[1:-1]
                            tmp_file.write(f"{path}\t{hash}\n")
                            storages[key]['lookup'][path] = hash
                else:
                    if hasattr(storage, '_root_path'):
                        # SFTP -- no longer in use, but leaving this here to show that different storages may have
                        # different bases
                        base = storage._root_path
                    else:
                        # local file storage -- are there other possibilities to consider?
                        base = storage.base_location
                    for f in storage.walk(os.path.join(base, 'warcs')):
                        # os.walk: "For each directory in the tree rooted at directory top (including top itself),
                        # it yields a 3-tuple (dirpath, dirnames, filenames)" -- so:
                        for filename in f[2]:
                            full_path = os.path.join(f[0], filename)
                            if (not start_date) or (start_datetime <= pytz.utc.localize(storage.modified_time(full_path)) < end_datetime):
                                # here we chop off the prefix, whether storage._root_path or storage.base_location
                                path = full_path[len(base):]
                                # note that etags are not always md5sums, but should be in these cases; we can rewrite
                                # or replace md5hash if necessary
                                hash = md5hash(full_path, storage)
                                tmp_file.write(f"{path}\t{hash}\n")
                                storages[key]['lookup'][path] = hash
    else:
        print("Reading storage caches ...")
        for key in storages:
            with open('/tmp/perma_storage_cache_{0}{1}.txt'.format(key, "" if start_date is None else start_date)) as f:
                for line in f:
                    path, hash = line[:-1].split("\t")
                    storages[key]['lookup'][path] = hash

    # now check ground truth against storage lookup tables
    print("Comparing link cache against storage caches ...")
    with open(link_cache) as f:
        for line in f:
            path = line[:-1]
            file_present = True
            for key in storages:
                if path not in storages[key]['lookup']:
                    print(f"{path} not in {key}")
                    file_present = False
            if file_present and len(storages) > 1:
                hashes = []
                for key in storages:
                    hashes.append(storages[key]['lookup'][path])
                # this looks funny (and is unnecessary here) but is faster than using set, per
                # http://stackoverflow.com/a/3844948/4074877
                if hashes.count(hashes[0]) != len(hashes):
                    print("Hash mismatch for {0}: {1}".format(path, str(zip(storages.keys(), hashes))))


def md5hash(path, storage):
    """
    helper function to calculate MD5 hash of a file

    """
    import hashlib

    blocksize = 2 ** 20
    m = hashlib.md5()
    with storage.open(path) as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
        return m.hexdigest()


@task
def update_cloudflare_cache():
    """ Update Cloudflare IP lists. """
    import requests
    for ip_filename in ('ips-v4', 'ips-v6'):
        with open(os.path.join(settings.CLOUDFLARE_DIR, ip_filename), 'w') as ip_file:
            ip_file.write(requests.get(f'https://www.cloudflare.com/{ip_filename}').text)


@task
def test_db_connection(connection):
    """
    Open a database connection.
    Use this task repeatedly, possibly with different database connection settings,
    e.g. in order to flush out a transient SSL connection problem, something like:
    while [ 1 ] ; do date ; fab dev.test_db_connection:some-connection ; sleep 1 ; done
    """
    from django.db import connections
    print(f"Attempting connection to {connection} ...")
    cursor = connections[connection].cursor()
    print("Succeeded.")
    cursor.close()


@task
def populate_link_surt_column(batch_size="500", model='Link'):
    import logging
    from tqdm import tqdm
    import surt
    from perma.models import Link, HistoricalLink

    logger = logging.getLogger(__name__)

    logger.info("BEGIN: populate_link_surt_column")

    models = {'Link': Link, 'HistoricalLink': HistoricalLink}
    links = models[model].objects.filter(submitted_url_surt__isnull=True)

    # limit to our desired batch size
    not_populated = links.count()
    batch_size = int(batch_size)
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
def populate_folder_cached_path(batch_size="500"):
    import logging
    from tqdm import tqdm
    from perma.models import Folder

    logger = logging.getLogger(__name__)

    logger.info("BEGIN: populate_folder_cached_path")

    folders = Folder.objects.filter(cached_path__isnull=True)

    # limit to our desired batch size
    not_populated = folders.count()
    batch_size = int(batch_size)
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
