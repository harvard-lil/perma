from contextlib import contextmanager
from datetime import date
import os

from fabric.api import *

### HELPERS ###

def run_as_web_user(*args, **kwargs):
    kwargs.setdefault('user', 'perma')
    with cd(env.REMOTE_DIR):
        if env.VIRTUALENV_NAME:
            with prefix("workon "+env.VIRTUALENV_NAME):
                return sudo(*args, **kwargs)
        else:
            return sudo(*args, **kwargs)

### DEPLOYMENT ###

@task(default=True)
def deploy(skip_backup=False):
    """
        Full deployment: back up database, pull code, install requirements, sync db, run migrations, collect static files, restart server.
    """
    if not skip_backup:
        backup_database()
        backup_code()
    deploy_code(restart=False)
    pip_install()
    run_as_web_user("%s manage.py migrate" % env.PYTHON_BIN)
    run_as_web_user("%s manage.py collectstatic --noinput --clear" % env.PYTHON_BIN)
    restart_server()


@task
def deploy_code(restart=True):
    """
        Deploy code only. This is faster than the full deploy.
    """
    run_as_web_user("find . -name '*.pyc' -delete")
    git("pull")
    if restart:
        restart_server()


@task
def git(*args):
    """
        Run a remote git command. Example:  fab git:"pull foo bar"
    """
    run_as_web_user("git %s" % " ".join(args))

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
    local("git push upstream master:master")
    local("git checkout develop")


@task
def pip_install():
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

@task
def backup_database():
    if env.DATABASE_BACKUP_DIR:
        run_as_web_user("fab deploy.local_backup_database:%s" % env.DATABASE_BACKUP_DIR)

@task
def local_backup_database(backup_dir):
    # this is going to be triggered by calling fab on the remote server, so that LOCAL_DB_SETTINGS has the remote settings
    import tempfile
    from django.conf import settings

    LOCAL_DB_SETTINGS = settings.DATABASES['default']
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

@task
def backup_code():
    """ Create a .tar.gz of the perma_web folder and store in env.CODE_BACKUP_DIR. """
    if env.CODE_BACKUP_DIR:
        with cd(".."):
            out_file_path = os.path.join(env.CODE_BACKUP_DIR, "perma_web_%s.tar.gz" % date.today().isoformat())
            # || [[ $? -eq 1 ]] makes sure that we still consider an exit code of 1 (meaning files changed during tar) a success
            run_as_web_user("tar -cvzf %s perma_web || [[ $? -eq 1 ]]" % out_file_path)
