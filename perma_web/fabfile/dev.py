import os
import subprocess
import sys
from django.conf import settings
from fabric.decorators import task
from fabric.operations import local


@task(name='run')
def run_django(port="0.0.0.0:8000"):
    """
        Run django test server on open port, so it's accessible outside Vagrant.
    """
    try:
        # use runserver_plus if installed
        import django_extensions
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
def init_db():
    """
        Run syncdb, apply migrations, and import fixtures for new dev database.
    """
    local("python manage.py migrate")
    local("python manage.py loaddata fixtures/sites.json fixtures/users.json fixtures/folders.json")

@task
def export_warcs(start_guid=''):
    from perma.models import Asset
    from django.core.files.storage import default_storage

    for asset in Asset.objects.filter(link_id__gte=start_guid).order_by('link_id').select_related('link'):
        print "Exporting %s" % start_guid
        if default_storage.exists(asset.link.warc_storage_file()):
            print "-- Already exported."
            continue
        asset.link.export_warc()
        print "-- Exported."