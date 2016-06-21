import os
import subprocess
import sys
from django.conf import settings
from fabric.context_managers import shell_env
from fabric.decorators import task
from fabric.operations import local


@task(name='run')
def run_django(port="0.0.0.0:8000"):
    """
        Run django test server on open port, so it's accessible outside Vagrant.
    """
    try:
        # use runserver_plus if installed
        import django_extensions  # noqa
        local("python manage.py runserver_plus %s --threaded" % port)
    except ImportError:
        local("python manage.py runserver %s" % port)


@task
def run_ssl(port="0.0.0.0:8000"):
    """
        Run django test server with SSL.
    """
    local("python manage.py runsslserver %s" % port)


@task
def test(apps="perma api functional_tests"):
    """
        Run perma tests. (For coverage, run `coverage report` after tests pass.)
    """
    excluded_files = [
        "*/migrations/*",
        "*/management/*",
        "*/tests/*",
        "fabfile/*",
        "functional_tests/*",
    ]
    local("coverage run --source='.' --omit='%s' manage.py test %s" % (",".join(excluded_files), apps))


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
        print "\n\nLaunching local live server. Be sure Sauce tunnel is running! (fab dev.sauce_tunnel)\n\n"

    with shell_env(**shell_envs):
        test("functional_tests "+test_flags)


@task
def sauce_tunnel():
    """
        Set up Sauce tunnel before running functional tests targeted at localhost.
    """
    if subprocess.call(['which','sc']) == 1: # error return code -- program not found
        sys.exit("Please check that the `sc` program is installed and in your path. To install: https://docs.saucelabs.com/reference/sauce-connect/")
    local("sc -u %s -k %s" % (settings.SAUCE_USERNAME, settings.SAUCE_ACCESS_KEY))


@task
def logs(log_dir=os.path.join(settings.PROJECT_ROOT, '../services/logs/')):
    """ Tail all logs. """
    local("tail -f %s/*" % log_dir)

@task
def jasmine():
    """
        Run frontend unit tests.
        Go to 0.0.0.0:8888 in your browser to see the output.
    """
    local("jasmine -o 0.0.0.0 -p 8888")

@task
def init_db():
    """
        Run syncdb, apply migrations, and import fixtures for new dev database.
    """
    local("python manage.py migrate")
    local("python manage.py migrate --database=perma-cdxline")
    local("python manage.py loaddata fixtures/sites.json fixtures/users.json fixtures/folders.json")
        
        
@task
def screenshots(base_url='http://perma.dev:8000'):
    import StringIO
    from PIL import Image
    from selenium import webdriver

    browser = webdriver.Firefox()
    browser.set_window_size(1300, 800)

    base_path = os.path.join(settings.PROJECT_ROOT, 'static/img/docs')

    def screenshot(upper_left_selector, lower_right_selector, output_path, upper_left_offset=(0,0), lower_right_offset=(0,0)):
        print "Capturing %s" % output_path

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
    import json
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

    json_results = json.dumps(all_results, default=lambda o: o.__dict__)

    with open('internet_archive_results.json', 'w+') as outfile:
        json.dump(json_results, outfile)
