from functools import wraps
import sys
from datetime import date
from fabric.api import *
from django.conf import settings


### SETUP STUFF ###

REMOTE_DIR = None
VIRTUALENV_NAME = 'perma'
WSGI_FILE = 'perma/wsgi.py'
LOCAL_DB_SETTINGS = settings.DATABASES['default']
DATABASE_BACKUP_DIR = 'database_backups' # If relative path, dir is relative to REMOTE_DIR. If None, no backup will be done.

try:
    from .fab_targets import *
except ImportError:
    print "\n\nDid you create a fab_targets.py file?\n"
    raise

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
            with cd(REMOTE_DIR), prefix("workon "+VIRTUALENV_NAME):
                return f(*args, **kwargs)
        return f(*args, **kwargs)
    return wrapper


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


### UTILITIES ###

@setup_remote
def shell():
    """
        Handy way to drop into remote shell with Django stuff set up.
    """
    from fabric.context_managers import char_buffered
    with char_buffered(sys.stdin):
        open_shell("cd %s && workon %s" % (REMOTE_DIR, VIRTUALENV_NAME))
