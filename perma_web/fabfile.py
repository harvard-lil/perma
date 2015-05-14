from functools import wraps
import shutil
import sys, os
from datetime import date
import tempfile
from django.utils.crypto import get_random_string
import django
from fabric.api import *
import subprocess

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perma.settings')
from django.conf import settings
django.setup()


### SETUP ###
env.REMOTE_DIR = None
env.VIRTUALENV_NAME = None
env.SETUP_PREFIXES = None # list of prefixes to run in setup_remote, e.g. [prefix('do stuff')]
env.PYTHON_BIN = 'python'
WSGI_FILE = 'perma/wsgi.py'
LOCAL_DB_SETTINGS = settings.DATABASES['default']
env.DATABASE_BACKUP_DIR = None # If relative path, dir is relative to REMOTE_DIR. If None, no backup will be done.


_already_setup = False
def setup_remote(f):
    """
        Decorator to make sure we're running things in the right remote directory,
        with the virtualenv set up.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        global _already_setup
        if not _already_setup:
            _already_setup = True
            def apply_withs(withs, target_func):
                if withs:
                    with withs[0]:
                        return apply_withs(withs[1:], target_func)
                return target_func()
            prefixes = [cd(env.REMOTE_DIR)]
            if env.VIRTUALENV_NAME:
                prefixes.append(prefix("workon "+env.VIRTUALENV_NAME))
            if env.SETUP_PREFIXES:
                prefixes += env.SETUP_PREFIXES
            return apply_withs(prefixes, lambda: f(*args, **kwargs))
        return f(*args, **kwargs)
    return wrapper

# def run_as_perma(*args, **kwargs):
#     """
#         Version of fabric's `run()` that sudoes into the `perma` user to run the command.
#     """
#     with _setenv({'shell': 'sudo -p "%s" su perma -c' % env.sudo_prompt}):
#         return run(*args, **kwargs)


### GENERAL UTILITIES ###

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
def runmirror():
    """
        Run parallel django main and mirror servers.
    """
    local("python manage.py runmirror")

@task
def test(apps="perma mirroring api functional_tests"):
    """
        Run perma tests. (For coverage, run `coverage report` after tests pass.)
    """
    excluded_files = [
        "perma/migrations/*",
        "*/tests/*",
        "fabfile.py",
        "mirroring/management/commands/runmirror.py"
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
def init_dev_db():
    """
        Run syncdb, apply migrations, and import fixtures for new dev database.
    """
    local("python manage.py syncdb --noinput")
    local("python manage.py migrate")
    local("python manage.py loaddata fixtures/sites.json fixtures/users.json fixtures/folders.json")

@task
def set_user_upload_field():
    """
        Temporary task to fix user_upload field.
    """
    from perma.models import Asset
    from django.db.models import Q
    from urlparse import urlparse

    first_change_date = '2014-04-10 13:22:44'  # last date when uploaded filenames still started with a slash
    second_change_date = '2014-10-27 18:43:26'  # date when non-uploaded PDFs started to set image_capture

    # user uploads up to first_change_date can be identified because
    # image_capture or pdf_capture will start with a slash
    Asset.objects.filter(link__creation_timestamp__lte=first_change_date).filter(
        Q(image_capture__startswith='/') | Q(pdf_capture__startswith='/')
    ).update(user_upload=True)

    # image uploads at any time can be identified because pdf_capture and warc_capture are null
    Asset.objects.filter(pdf_capture=None, warc_capture=None).exclude(image_capture=None).update(user_upload=True)

    # PDF uploads after second_change_date can be identified because
    # image_capture is null
    Asset.objects.filter(link__creation_timestamp__gte=second_change_date, image_capture=None).update(user_upload=True)

    # PDF uploads between first_change_date and second_change_date can be identified because
    # submitted_title is not the submitted_url domain
    for asset in Asset.objects.filter(link__creation_timestamp__gt=first_change_date, link__creation_timestamp__lt=second_change_date).exclude(pdf_capture=None).select_related('link'):
        if asset.link.submitted_title != urlparse(asset.link.submitted_url).netloc:
            asset.user_upload = True
            asset.save()

### DEPLOYMENT ###

@task
@setup_remote
def deploy(branch='master'):
    """
        Full deployment: back up database, pull code, install requirements, sync db, run migrations, collect static files, restart server.
    """
    backup_database()
    deploy_code(restart=False, branch=branch)
    pip_install()
    run("%s manage.py syncdb" % env.PYTHON_BIN)
    run("%s manage.py migrate" % env.PYTHON_BIN)
    run("%s manage.py collectstatic --noinput --clear" % env.PYTHON_BIN)
    

@task
@setup_remote
def deploy_code(restart=True, branch='master'):
    """
        Deploy code only. This is faster than the full deploy.
    """
    run('find . -name "*.pyc" -exec rm -rf {} \;')
    run("git pull origin %s" % branch)
    if restart:
          restart_server()
          
@task
def tag_new_release(tag):
    """
        Roll develop into master and tag it
    """
    local("git checkout master")
    local("git merge develop -m 'Tagging %s. Merging develop into master'" % tag)
    local("git tag -a %s -m '%s'" % (tag, tag))
    local("git push --tags")
    local("git push")
    local("git checkout develop")
    
          
@task
def pip_install():
      run("pip install -r requirements.txt")

@task
@setup_remote
def restart_server():
    """
        Touch the wsgi file to restart the remote server (hopefully).
    """
    run("sudo stop celery; sudo start celery;")
    run("sudo stop celerybeat; sudo start celerybeat;")


@task
@setup_remote
def stop_server():
    """
        Stop the services
    """
    run("sudo service gunicorn stop")
    run("sudo service celery stop")
    run("sudo service celerybeat stop")
    
    
@task
@setup_remote
def start_server():
    """
        Start the services
    """
    run("sudo service gunicorn start")
    run("sudo service celery start")
    run("sudo service celerybeat start")

### DATABASE STUFF ###

@task
@setup_remote
def backup_database():
    if env.DATABASE_BACKUP_DIR:
        run("fab local_backup_database:%s" % env.DATABASE_BACKUP_DIR)

@task
def local_backup_database(backup_dir):
    # WARNING: this is totally untested
    # this is going to be triggered by calling fab on the remote server, so that LOCAL_DB_SETTINGS has the remote settings
    import pexpect
    child = pexpect.spawn(r"""mysqldump --user={user} {database} | gzip > {backup_dir}/{date}.sql.gz""".format(
        user=LOCAL_DB_SETTINGS['USER'],
        database=LOCAL_DB_SETTINGS['NAME'],
        backup_dir=backup_dir,
        date=date.today().isoformat()
    ))
    child.expect('Enter password:')
    child.sendline(LOCAL_DB_SETTINGS['PASSWORD'])

@task
@setup_remote
def shell():
    """
        Handy way to drop into remote shell with Django stuff set up.
    """
    from fabric.context_managers import char_buffered
    with char_buffered(sys.stdin):
        open_shell("cd %s && workon %s" % (env.REMOTE_DIR, env.VIRTUALENV_NAME))


### MIRRORING ###

@task
def generate_keys():
    """
        Generate a keypair suitable for settings.py on the main server.
    """
    if '/vagrant/' in __file__:
        print "WARNING: This command does not run well under Vagrant, as it requires random entropy."
    import gnupg
    gpg = gnupg.GPG(gnupghome=settings.GPG_DIRECTORY)
    gpg_input = gpg.gen_key_input()  # use sensible defaults
    print "Generating keypair with this input: %s" % gpg_input
    key = gpg.gen_key(gpg_input)
    print "Copy these keys into settings.py on the main server, and into UPSTREAM_SERVER['public_key'] on the mirror servers:"
    print "\nGPG_PUBLIC_KEY = %s\nGPG_PRIVATE_KEY = %s" % (
        repr(gpg.export_keys(key.fingerprint)),  # public key
        repr(gpg.export_keys(key.fingerprint, True))  # private key
    )


### HEROKU ###

@task
def heroku_configure_app(app_name, s3_storage_bucket=None, s3_path='/'):
    """
        Set up a new Heroku Perma app.
    """
    def heroku(cmd, capture=False):
        return local("heroku %s --app %s" % (cmd, app_name), capture=capture)

    #heroku("apps:create %s" % app_name)
    existing_addons = heroku("addons", capture=True)
    for addon in ('cleardb', 'cloudamqp', 'rediscloud'):
        if addon not in existing_addons:
            heroku("addons:add %s" % addon)

    # Django config
    if not s3_storage_bucket:
        s3_storage_bucket = app_name
    s3_url = '//%s.s3.amazonaws.com%s' % (s3_storage_bucket, s3_path)

    django_config_vars = {
        'AWS_STORAGE_BUCKET_NAME':s3_storage_bucket,
        'HOST':'%s.herokuapp.com' % app_name,
        'MEDIA_ROOT':'/generated/',
        'MEDIA_URL':s3_url+'media/',
        'SECRET_KEY':get_random_string(50, 'abcdefghijklmnopqrstuvwxyz0123456789'),
        'STATIC_URL':s3_url+'static/',
    }
    heroku("config:set %s" % " ".join("DJANGO__%s=%s" % (key, val) for key, val in django_config_vars.items()))

    django_blank_vars = ('AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'GPG_PRIVATE_KEY', 'GPG_PUBLIC_KEY')
    heroku("config:set %s" % " ".join("DJANGO__%s=MISSING" % key for key in django_blank_vars))

    print "Heroku app setup completed. Remember to set the following config vars: %s" % (django_blank_vars,)

@task
def heroku_push(app_name='perma', project_dir=os.path.join(settings.PROJECT_ROOT, '..')):
    """
        Push code to Heroku.
    """
    # where we'll get files from to set up the heroku deployment
    heroku_files_dir = os.path.join(project_dir, "services", "heroku")

    # copy perma_web to a temp dir for deployment
    dest_dir = tempfile.mkdtemp()
    local("cp -r %s/* %s" % (os.path.join(project_dir, "perma_web"), dest_dir))

    with lcd(dest_dir):

        # set up heroku files
        local("cp -r %s ." % os.path.join(heroku_files_dir, "bin"))
        local("cp %s ." % os.path.join(heroku_files_dir, "Procfile"))
        local("cp %s perma/" % os.path.join(heroku_files_dir, "wsgi_heroku.py"))
        local("cp %s perma/settings/" % os.path.join(heroku_files_dir, "settings.py"))
        local("cat %s >> requirements.txt" % os.path.join(heroku_files_dir, "extra_requirements.txt"))

        # set up git
        local(r'sed "s/perma_web\/perma\/settings\/settings.py|perma_web\///g" %s/%s > %s' % (project_dir, '.gitignore', '.gitignore'))
        local("git init")
        local("git add -A")
        local("git commit -m 'heroku push `date`'")
        local("heroku git:remote -a %s" % app_name)

        # push to heroku
        local("git push --force heroku master")

    # delete temp dir
    shutil.rmtree(dest_dir)


try:
    from fab_targets import *
except ImportError, e:
    if e.args[0] == 'No module named fab_targets':
        print "Warning: no fab_targets file found."
    else:
        raise