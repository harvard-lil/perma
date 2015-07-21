from contextlib import contextmanager
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
env.VIRTUALENV_NAME = 'perma'
env.PYTHON_BIN = 'python'
WSGI_FILE = 'perma/wsgi.py'
LOCAL_DB_SETTINGS = settings.DATABASES['default']
env.DATABASE_BACKUP_DIR = None # If relative path, dir is relative to REMOTE_DIR. If None, no backup will be done.


@contextmanager
def web_root():
    with cd(env.REMOTE_DIR):
        if env.VIRTUALENV_NAME:
            with prefix("workon "+env.VIRTUALENV_NAME):
                yield
        else:
            yield

def run_as_web_user(*args, **kwargs):
    kwargs.setdefault('user', 'perma')
    return sudo(*args, **kwargs)


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
def test(apps="perma api functional_tests"):
    """
        Run perma tests. (For coverage, run `coverage report` after tests pass.)
    """
    excluded_files = [
        "perma/migrations/*",
        "*/tests/*",
        "fabfile.py",
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


### DEPLOYMENT ###

@task
def deploy(branch='master'):
    """
        Full deployment: back up database, pull code, install requirements, sync db, run migrations, collect static files, restart server.
    """
    backup_database()
    deploy_code(restart=False, branch=branch)
    pip_install()
    with web_root():
        run_as_web_user("%s manage.py syncdb" % env.PYTHON_BIN)
        run_as_web_user("%s manage.py migrate" % env.PYTHON_BIN)
        run_as_web_user("%s manage.py collectstatic --noinput --clear" % env.PYTHON_BIN)
    restart_server()


@task
def deploy_code(restart=True, branch='master'):
    """
        Deploy code only. This is faster than the full deploy.
    """
    with web_root():
        run_as_web_user('find . -name "*.pyc" -exec rm -rf {} \;')
        run_as_web_user("git pull origin %s" % branch)
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
    with web_root():
        run_as_web_user("pip install -r requirements.txt")

@task
def restart_server():
    stop_server()
    start_server()


@task
def stop_server():
    """
        Stop the services
    """
    sudo("stop celery", shell=False)
    
    
@task
def start_server():
    """
        Start the services
    """
    sudo("start celery", shell=False)

### DATABASE STUFF ###

@task
def backup_database():
    if env.DATABASE_BACKUP_DIR:
        with web_root():
            run_as_web_user("fab local_backup_database:%s" % env.DATABASE_BACKUP_DIR)

@task
def local_backup_database(backup_dir):
    # this is going to be triggered by calling fab on the remote server, so that LOCAL_DB_SETTINGS has the remote settings
    import tempfile
    out_file_path = os.path.join(backup_dir, "%s.sql.gz" % date.today().isoformat())
    temp_password_file = tempfile.NamedTemporaryFile()
    temp_password_file.write("[client]\nuser=%s\npassword=%s\n" % (LOCAL_DB_SETTINGS['USER'], LOCAL_DB_SETTINGS['PASSWORD']))
    temp_password_file.flush()
    local("mysqldump --defaults-extra-file=%s -h%s %s | gzip > %s" % (
        temp_password_file.name,
        LOCAL_DB_SETTINGS['HOST'],
        LOCAL_DB_SETTINGS['NAME'],
        out_file_path
    ))


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