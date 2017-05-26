from datetime import date
import os
from fabric.api import *
from django.conf import settings

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
    maintenance_mode_on()
    if not skip_backup:
        backup_database()
        backup_code()
    deploy_code(restart=False)
    pip_install()
    run_as_web_user("%s manage.py migrate" % env.PYTHON_BIN)
    run_as_web_user("%s manage.py migrate --database=perma-cdxline" % env.PYTHON_BIN)
    run_as_web_user("%s manage.py collectstatic --noinput --clear" % env.PYTHON_BIN)
    restart_server()
    maintenance_mode_off()
    notify_opbeat()

@task
def notify_opbeat():
    """
        Tell opbeat that deploy has completed.
        Via https://opbeat.com/docs/articles/get-started-with-release-tracking/
    """
    if settings.USE_OPBEAT:
        run_as_web_user("""
            curl https://opbeat.com/api/v1/organizations/{ORGANIZATION_ID}/apps/{APP_ID}/releases/
                -H "Authorization: Bearer {SECRET_TOKEN}"
                -d rev=`git log -n 1 --pretty=format:%H`
                -d branch=`git rev-parse --abbrev-ref HEAD`
                -d status=completed
            """.format(**settings.OPBEAT).replace("\n", ""))

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
def tag_new_release(tag=None):
    """
        Roll stage into master and tag it.
    """
    local("git fetch upstream")

    # figure out tag based on previous tags
    if not tag:
        last_release = max(int(tag.split('.')[1]) for tag in local("git tag", capture=True).split("\n") if tag.startswith("v0."))
        this_release = raw_input("Enter release number (default %s): " % (last_release+1))
        if not this_release:
            this_release = last_release+1
        tag = "v0.%s" % this_release

    current_branch = local("git rev-parse --abbrev-ref HEAD", capture=True)
    try:
        # check out upstream/master
        local("git checkout upstream/master")

        # merge upstream/stage and push changes to master
        local("git merge upstream/stage -m 'Tagging %s. Merging stage into master'" % tag)
        local("git push upstream HEAD:master")

        # tag release and push tag
        local("git tag -a %s -m '%s'" % (tag, tag))
        local("git push upstream --tags")

    finally:
        # switch back to the branch you were on
        local("git checkout %s" % current_branch)


@task
def release_to_stage():
    """
        Roll develop into stage.
    """
    # re-create stage from develop and force push
    local("git fetch upstream")
    local("git branch -f stage upstream/develop")
    local("git push upstream stage -f")


@task
def pip_install():
    run_as_web_user("pip-sync")

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
def maintenance_mode_on():
    """
        Enable maintenance mode.

        (Nginx sees maintenance_on.html and routes all requests to that file.)
    """
    run_as_web_user("cp static/maintenance/maintenance.html static/maintenance/maintenance_on.html ")

@task
def maintenance_mode_off():
    """
        Disable maintenance mode.
    """
    run_as_web_user("rm static/maintenance/maintenance_on.html ")

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
    local("mysqldump --defaults-extra-file=%s -h%s --ignore-table=perma.perma_cdxline %s | gzip > %s" % (
        temp_password_file.name,
        LOCAL_DB_SETTINGS['HOST'],
        LOCAL_DB_SETTINGS['NAME'],
        out_file_path
    ))

@task
def backup_code():
    """ Create a .tar.gz of the perma_web folder and store in env.CODE_BACKUP_DIR. """
    if env.CODE_BACKUP_DIR:
        out_file_path = os.path.join(env.CODE_BACKUP_DIR, "perma_web_%s.tar.gz" % date.today().isoformat())
        # || [[ $? -eq 1 ]] makes sure that we still consider an exit code of 1 (meaning files changed during tar) a success
        run_as_web_user("cd .. && tar -cvzf %s perma_web || [[ $? -eq 1 ]]" % out_file_path)

@task
def bulk_sync_cdxline_flags(primary_defaults_file, cdxline_defaults_file):
    """ This task will be required when migrating the database to RDS. """
    print("Creating perma_link table on cdxline server ...")
    local("mysqldump --defaults-extra-file='%s' --tables perma_link --no-create-info perma | mysql --defaults-extra-file='%s' perma_cdxline" % (primary_defaults_file, cdxline_defaults_file))
    print("Updating cdxline table ...")
    local("mysql --defaults-extra-file='%s' 'update perma_cdxline as c, perma_link as l set c.is_private=l.is_private, c.is_unlisted=l.unlisted where c.link_id=l.guid; drop table perma_link;'" % (cdxline_defaults_file,))
    print("Done.")
