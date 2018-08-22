import os
import shutil
import subprocess
import signal
import sys
import tempfile

from django.conf import settings
from fabric.context_managers import shell_env
from fabric.decorators import task
from fabric.operations import local

from perma.tests.utils import reset_failed_test_files_folder


@task(name='run')
def run_django(port="0.0.0.0:8000"):
    """
        Run django test server on open port, so it's accessible outside Vagrant.
    """
    commands = []

    if settings.ENABLE_BATCH_LINKS and not settings.RUN_TASKS_ASYNC:
        print("\nWarning! Batch Link creation will not work as expected:\n" +
              "to create new batches you must run with settings.RUN_TASKS_ASYNC = True\n")

    if settings.RUN_TASKS_ASYNC:
        print("Starting background celery process. Warning: this has a documented memory leak, and developing with"
              " RUN_TASKS_ASYNC=False is usually easier unless you're specifically testing a Django-Celery interaction.")
        commands.append('celery -A perma worker --loglevel=info -B -n w1@%h')

    # Only run the webpack background process in debug mode -- with debug False, dev server uses static assets,
    # and running webpack just messes up the webpack stats file.
    if settings.DEBUG:
        commands.append('npm start')

    proc_list = [subprocess.Popen(command, shell=True, stdout=sys.stdout, stderr=sys.stderr) for command in commands]

    try:
        try:
            # use runserver_plus if installed
            import django_extensions  # noqa
            # use --reloader-type stat because:
            #  (1) we have to have watchdog installed for pywb, which causes runserver_plus to attempt to use it as the reloader, which depends on inotify, but
            #  (2) we are using a Vagrant NFS mount, which does not support inotify
            # see https://github.com/django-extensions/django-extensions/pull/1041
            local("python manage.py runserver_plus %s --threaded --reloader-type stat" % port)
        except ImportError:
            local("python manage.py runserver %s" % port)
    finally:
        for proc in proc_list:
            os.kill(proc.pid, signal.SIGKILL)


_default_tests = "functional_tests perma api lockss"

@task
def test(apps=_default_tests):
    """ Run perma tests. (For coverage, run `coverage report` after tests pass.) """
    reset_failed_test_files_folder()
    test_python(apps)
    if apps == _default_tests:
        test_js()

@task
def test_python(apps=_default_tests, travis=False):
    """ Run Python tests. """

    # .pyc files can contain filepaths; this permits easy switching
    # between a Vagrant- and Docker-based dev environment
    local("find . -name '*.pyc' -delete")

    # In order to run functional_tests, we have to run collectstatic, since functional tests use DEBUG=False
    # For speed we use the default Django STATICFILES_STORAGE setting here, which also has to be set in settings_testing.py
    if "functional_tests" in apps and not os.environ.get('SERVER_URL'):
        local("DJANGO__STATICFILES_STORAGE=django.contrib.staticfiles.storage.StaticFilesStorage python manage.py collectstatic --noinput")

    # temporarily set MEDIA_ROOT to a tmp directory, in a way that lets us clean up after ourselves
    tmp = tempfile.mkdtemp()
    try:
        shell_envs = {
            'DJANGO__MEDIA_ROOT': os.path.join(tmp, '') #join ensures path ends in /
        }
        with shell_env(**shell_envs):
            # NB: all arguments to Fabric tasks are interpreted as strings
            if travis == 'True':
                local("pytest %s --no-migrations --ds=perma.settings --cov --cov-report= " % (apps))
            else:
                local("pytest %s --no-migrations --ds=perma.settings.deployments.settings_testing --cov --cov-report= " % (apps))
    finally:
        # clean up after ourselves
        shutil.rmtree(tmp)


@task
def test_js():
    """ Run Javascript tests. """
    local("npm test")

@task
def test_sauce(server_url=None, test_flags=''):
    """
        Run functional_tests through Sauce rather than local phantomjs.
    """
    shell_envs = {
        'DJANGO_LIVE_TEST_SERVER_ADDRESS': "0.0.0.0:8000",  # tell Django to make the live test server visible outside vagrant (this is unrelated to server_url)
        'DJANGO__USE_SAUCE': "True"
    }
    if server_url:
        shell_envs['SERVER_URL'] = server_url
    else:
        print("\n\nLaunching local live server. Be sure Sauce tunnel is running! (fab dev.sauce_tunnel)\n\n")

    with shell_env(**shell_envs):
        test("functional_tests "+test_flags)


@task
def sauce_tunnel():
    """
        Set up Sauce tunnel before running functional tests targeted at localhost.
    """
    if subprocess.call(['which','sc']) == 1: # error return code -- program not found
        sys.exit("Please check that the `sc` program is installed and in your path. To install: https://wiki.saucelabs.com/display/DOCS/Sauce+Connect+Proxy")
    local("sc -u %s -k %s" % (settings.SAUCE_USERNAME, settings.SAUCE_ACCESS_KEY))


@task
def logs(log_dir=os.path.join(settings.PROJECT_ROOT, '../services/logs/')):
    """ Tail all logs. """
    local("tail -f %s/*" % log_dir)


@task
def create_db(host='db', user='root', password='password'):
    local("mysql -h {} -u{} -p{} -e 'create database perma character set utf8;'".format(host, user, password))
    local("mysql -h {} -u{} -p{} -e 'create database perma_cdxline character set utf8;'".format(host, user, password))


@task
def init_db():
    """
        Run syncdb, apply migrations, and import fixtures for new dev database.
    """
    local("python manage.py migrate")
    local("python manage.py migrate --database=perma-cdxline")
    local("python manage.py loaddata fixtures/sites.json fixtures/users.json fixtures/folders.json")


@task
def screenshots(base_url='http://perma.test:8000'):
    import StringIO
    from PIL import Image
    from selenium import webdriver

    browser = webdriver.Firefox()
    browser.set_window_size(1300, 800)

    base_path = os.path.join(settings.PROJECT_ROOT, 'static/img/docs')

    def screenshot(upper_left_selector, lower_right_selector, output_path, upper_left_offset=(0,0), lower_right_offset=(0,0)):
        print("Capturing %s" % output_path)

        upper_left_el = browser.find_element_by_css_selector(upper_left_selector)
        lower_right_el = browser.find_element_by_css_selector(lower_right_selector)

        upper_left_loc = upper_left_el.location
        lower_right_loc = lower_right_el.location
        lower_right_size = lower_right_el.size

        im = Image.open(StringIO.StringIO(browser.get_screenshot_as_png()))
        im = im.crop((
            upper_left_loc['x']+upper_left_offset[0],
            upper_left_loc['y']+upper_left_offset[1],
            lower_right_loc['x'] + lower_right_size['width'] + lower_right_offset[0],
            lower_right_loc['y'] + lower_right_size['height'] + lower_right_offset[1]
        ))
        im.save(os.path.join(base_path, output_path))

    # home page
    browser.get(base_url)
    screenshot('header', '#landing-introduction', 'screenshot_home.png')

    # login screen
    browser.get(base_url+'/login')
    screenshot('header', '#main-content', 'screenshot_create_account.png')

    # logged in user - drop-down menu
    browser.find_element_by_css_selector('#id_username').send_keys('test_user@example.com')
    browser.find_element_by_css_selector('#id_password').send_keys('pass')
    browser.find_element_by_css_selector("button.btn.login").click()
    browser.find_element_by_css_selector("a.navbar-link").click()
    screenshot('header', 'ul.dropdown-menu', 'screenshot_dropdown.png', lower_right_offset=(15,15))

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
        warc_name = "%s.warc.gz" % link.guid

        try:
            fnames = [f.name for f in internetarchive.get_files(identifier, glob_pattern="*gz")]
            guid_results["uploaded_file"] = warc_name in fnames
            if settings.INTERNET_ARCHIVE_COLLECTION == 'test_collection':
                guid_results["collection"] = item.metadata["collection"] == settings.INTERNET_ARCHIVE_COLLECTION
            else:
                guid_results["collection"] = item.metadata["collection"][0] == settings.INTERNET_ARCHIVE_COLLECTION
            guid_results["title"] = item.metadata["title"] == "%s: %s" % (link.guid, truncatechars(link.submitted_title, 50))
            guid_results["mediatype"] = item.metadata["mediatype"]=="web"
            guid_results["description"] = item.metadata["description"]=="Perma.cc archive of %s created on %s." % (link.submitted_url, link.creation_timestamp,)
            guid_results["contributor"] = item.metadata["contributor"]=="Perma.cc"
            guid_results["submitted_url"] = item.metadata["submitted_url"]==link.submitted_url
            guid_results["perma_url"] = item.metadata["perma_url"]=="http://%s/%s" % (settings.HOST, link.guid)
            guid_results["external-identifier"] = item.metadata["external-identifier"]=="urn:X-perma:%s" % link.guid
            if link.organization:
                guid_results["organization"] = item.metadata["sponsor"] == "%s - %s" % (link.organization, link.organization.registrar)

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
def regenerate_urlkeys(urlkey_prefix='file'):
    """
        Rewrite CDXLine urlkeys using the current version of the surt library.
    """

    from perma.models import CDXLine
    from surt import surt

    target_cdxlines = CDXLine.objects.all()
    if urlkey_prefix:
        target_cdxlines = target_cdxlines.filter(urlkey__startswith=urlkey_prefix)

    for i, cdxline in enumerate(target_cdxlines):
        if not (i%1000):
            print("%s records done -- next is %s." % (i, cdxline.link_id))
        new_surt = surt(cdxline.parsed['url'])
        if new_surt != cdxline.urlkey:
            try:
                cdxline.raw = cdxline.raw.replace(cdxline.urlkey, new_surt, 1)
            except UnicodeDecodeError:
                print("Skipping unicode for %s" % cdxline.link_id)
                continue
            cdxline.urlkey = new_surt
            cdxline.save()

@task
def rebuild_folder_trees():
    from perma.models import Organization, LinkUser, Folder
    print("Checking for broken folder trees ...")

    for o in Organization.objects.all():
        if set(o.folders.all()) != set(o.shared_folder.get_descendants(include_self=True)):
            print("Tree corruption found for org: %s" % o)
            Folder._tree_manager.partial_rebuild(o.shared_folder.tree_id)

    for u in LinkUser.objects.all():
        if u.root_folder and set(u.folders.all()) != set(u.root_folder.get_descendants(include_self=True)):
            print("Tree corruption found for user: %s" % u)
            Folder._tree_manager.partial_rebuild(u.root_folder.tree_id)


@task
def test_playbacks(guid_list_file=None, min_guid=None, created_by=None):
    """
        Test all primary captures and report any that throw errors when playing back in pywb.
    """
    from perma.models import Capture
    import traceback
    import types
    from warc_server.app import application

    # monkey patch the pywb application to raise all exceptions instead of catching them
    def handle_exception(self, env, exc, print_trace):
        raise exc
    application.handle_exception = types.MethodType(handle_exception, application)

    # either check links by guid, one per line in the supplied file ...
    if guid_list_file:
        def capture_iterator():
            for guid in open(guid_list_file):
                if guid.strip():
                    capture = Capture.objects.select_related('link').get(link_id=guid.strip(), role='primary')
                    # in rechecks, skip deleted links
                    if capture.link.user_deleted:
                        continue
                    yield capture
        captures = capture_iterator()

    # ... or just check everything.
    else:
        captures = Capture.objects.filter(role='primary', status='success', link__user_deleted=False).select_related('link')
        if min_guid:
            captures = captures.filter(link_id__gt=min_guid)
        if created_by:
            captures = captures.filter(link__created_by_id=created_by)

    # check each playback
    for capture in captures:
        try:
            replay_response = capture.link.replay_url(capture.url, wsgi_application=application)
        except RuntimeError as e:
            if 'does not support redirect to external targets' in e.args:
                # skip these for now -- relative redirects will be fixed in Werkzeug 0.12
                continue
            raise
        except Exception as e:
            print("%s\t%s\tEXCEPTION\t" % (capture.link_id, capture.link.creation_timestamp), e.args)
            traceback.print_exc()
            continue

        if 'Link' not in replay_response.headers:
            print("%s\t%s\tWARNING\t%s" % (capture.link_id, capture.link.creation_timestamp, "Link header not found"))
            continue

        print("%s\t%s\tOK" % (capture.link_id, capture.link.creation_timestamp))

@task
def read_playback_tests(*filepaths):
    """
        Aggregate files from the test_playbacks() task and report count for each type of error.
    """
    from collections import defaultdict
    errs = defaultdict(list)
    prefixes = [
        "'ascii' codec can't encode character",
        "No Captures found for:",
        "'ascii' codec can't decode byte",
        "Self Redirect:",
        "No such file or directory:",
        "u'",
        "Skipping Already Failed",
        "cdx format"
    ]
    for filepath in filepaths:
        for line in open(filepath):
            parts = line.strip().split("\t", 2)
            if len(parts) < 3:
                continue
            key = parts[2]
            for prefix in prefixes:
                if prefix in key:
                    key = prefix
                    break
            errs[key].append(parts)

    err_count = 0
    for err_type, sub_errs in errs.iteritems():
        err_count += len(sub_errs)
        print("%s: %s" % (err_type, len(sub_errs)))
    print("Total:", err_count)

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
    from perma.email import send_user_email, send_admin_email, registrar_users, registrar_users_plus_stats

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
            msg = "Some registrar users were not emailed: {}. Check log for fatal SMTP errors.".format(str(failed_list))
        else:
            msg = "Some registrar users were not emailed. Check log for fatal SMTP errors."
        logger.error(msg)
        result = "incomplete"
    else:
        result = "ok"
    send_admin_email("Registrar Users Emailed",
                     settings.DEFAULT_FROM_EMAIL,
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
        print("%s\t%s" % (link['guid'], result))


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
        print("Using cached local state from %s" % local_cache_path)

    if not os.path.exists(remote_cache_path):
        print("Building remote state ...")
        remove_char_count = len(settings.SECONDARY_MEDIA_ROOT)
        with open(remote_cache_path, 'w') as tmp_file:
            for f in tqdm(default_storage.secondary_storage.bucket.list('generated/warcs/')):
                key = f.key[remove_char_count:]
                val = f.etag[1:-1]
                tmp_file.write("%s\t%s\n" % (key, val))
                remote_paths[key] = val
    else:
        print("Using cached remote state from %s" % remote_cache_path)
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
            print("Hash mismatch! Local: %s Remote: %s" % (m.hexdigest(), remote_paths[local_path]))


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
                    tmp_file.write("{0}\n".format(link.warc_storage_file()))
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
                            tmp_file.write("{0}\t{1}\n".format(path, hash))
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
                                tmp_file.write("{0}\t{1}\n".format(path, hash))
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
                    print("{0} not in {1}".format(path, key))
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
            ip_file.write(requests.get('https://www.cloudflare.com/%s' % ip_filename).text)


@task
def test_db_connection(connection):
    """
    Open a database connection.
    Use this task repeatedly, possibly with different database connection settings,
    e.g. in order to flush out a transient SSL connection problem, something like:
    while [ 1 ] ; do date ; fab dev.test_db_connection:some-connection ; sleep 1 ; done
    """
    from django.db import connections
    print("Attempting connection to %s ..." % connection)
    cursor = connections[connection].cursor()
    print("Succeeded.")
    cursor.close()
