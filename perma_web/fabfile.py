from functools import wraps
import shutil
import sys, os
from datetime import date
import tempfile
from django.utils.crypto import get_random_string
from fabric.api import *

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perma.settings')
from django.conf import settings


### SETUP ###

env.REMOTE_DIR = None
env.VIRTUALENV_NAME = 'perma'
WSGI_FILE = 'perma/wsgi.py'
LOCAL_DB_SETTINGS = settings.DATABASES['default']
DATABASE_BACKUP_DIR = 'database_backups' # If relative path, dir is relative to REMOTE_DIR. If None, no backup will be done.

try:
    from fab_targets import *
except ImportError:
    print "Warning: no fab_targets file found."

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
            with cd(env.REMOTE_DIR), prefix("workon "+env.VIRTUALENV_NAME):
                return f(*args, **kwargs)
        return f(*args, **kwargs)
    return wrapper


### GENERAL UTILITIES ###

def run(port="0.0.0.0:8000"):
    """
        Run django test server on open port, so it's accessible outside Vagrant.
    """
    local("python manage.py runserver %s" % port)

def test():
    """
        Run perma tests. (For coverage, run `coverage report` after tests pass.)
    """
    local("coverage run --source='.' --omit='lib/*,perma/migrations/*,*/tests/*' manage.py test perma")

def logs(log_dir=os.path.join(settings.PROJECT_ROOT, '../services/logs/')):
    """ Tail all logs. """
    local("tail -f %s/*" % log_dir)

def init_dev_db():
    """
        Run syncdb, South migrate, and import fixtures for new dev database.
    """
    local("python manage.py syncdb --noinput")
    local("python manage.py migrate")
    local("python manage.py loaddata fixtures/users.json fixtures/groups.json")

def south_out(app="perma"):
    """
        Migrate schema changes out of models.py to migration files.
    """
    local("python manage.py schemamigration %s --auto" % app)

def south_in(*args):
    """
        Migrate schema changes from migration files into db. For single app, do fab south_in:app_name
    """
    local("python manage.py migrate %s" % (" ".join(args)))


### DEPLOYMENT ###

@setup_remote
def deploy():
    """
        Full deployment: back up database, pull code, install requirements, sync db, run south migrations, collect static files, restart server.
    """
    backup_database()
    deploy_code(restart=False)
    run("pip install -r requirements.txt")
    run("python manage.py syncdb")
    run("fab south_in")
    run("python manage.py collectstatic --noinput --clear")
    run("touch "+WSGI_FILE) # restart server

@setup_remote
def deploy_code(restart=True):
    """
        Deploy code only. This is faster than the full deploy.
    """
    run("git pull origin master")
    if restart:
          restart_server()

@setup_remote
def restart_server():
    """
        Touch the wsgi file to restart the remote server (hopefully).
    """
    run("touch " + WSGI_FILE)
    # TODO: not sure if one or both of these is useful
    # sudo('service livesite restart')
    # sudo('service nginx restart')


### DATABASE STUFF ###

@setup_remote
def backup_database():
    if DATABASE_BACKUP_DIR:
        run("fab local_backup_database:%s" % DATABASE_BACKUP_DIR)

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

@setup_remote
def shell():
    """
        Handy way to drop into remote shell with Django stuff set up.
    """
    from fabric.context_managers import char_buffered
    with char_buffered(sys.stdin):
        open_shell("cd %s && workon %s" % (env.REMOTE_DIR, env.VIRTUALENV_NAME))


### HEROKU ###

def heroku_create_app(app_name):
    """
        Set up a new Heroku Perma app.
    """
    local("heroku apps:create %s" % app_name)
    local("heroku config:set SECRET_KEY=%s" % get_random_string(50, 'abcdefghijklmnopqrstuvwxyz0123456789'))
    local("heroku config:add BUILDPACK_URL=git://github.com/jcushman/heroku-buildpack-python.git")
    local("heroku addons:add cleardb:ignite")

def heroku_push(project_dir=os.path.join(settings.PROJECT_ROOT, '..')):
    """
        Push code to Heroku.
    """
    # where we'll get files from to set up the heroku deployment
    heroku_files_dir = os.path.join(project_dir, "services", "heroku")

    # copy perma_web to a temp dir for deployment
    dest_dir = tempfile.mkdtemp()
    print "Creating Heroku build at %s" % dest_dir
    local("cp -r %s/* %s" % (os.path.join(project_dir, "perma_web"), dest_dir))

    with lcd(dest_dir):

        # set up heroku files
        local("cp -r %s ." % os.path.join(heroku_files_dir, "bin"))
        local("cp %s ." % os.path.join(heroku_files_dir, "Procfile"))
        local("cp %s perma/" % os.path.join(heroku_files_dir, "wsgi_heroku.py"))
        local("cp %s perma/settings/__init__.py" % os.path.join(heroku_files_dir, "settings.py"))

        # set up git
        for git_file in ('.gitmodules', '.gitignore'):
            local(r'sed "s/perma_web\///g" %s/%s > %s' % (project_dir, git_file, git_file))
        local("git init")
        local("rm -r lib/cdx_writer")
        local("rm -r lib/warc-tools")
        local("git init")
        local("git submodule add https://github.com/jcushman/CDX-Writer.git lib/cdx_writer")
        local("git submodule add https://github.com/jcushman/warc-tools.git lib/warc-tools")
        local("git commit -a -m 'heroku push `date`'")
        local("heroku git:remote -a perma")

        # push to heroku
        local("git push --force heroku master")

    # delete temp dir
    shutil.rmtree(dest_dir)