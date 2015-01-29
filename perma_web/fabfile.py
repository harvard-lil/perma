from functools import wraps
import shutil
import sys, os
from datetime import date
import tempfile
from django.utils.crypto import get_random_string
from fabric.api import *
import subprocess
from perma.models import Registrar, Link

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perma.settings')
from django.conf import settings


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


### GENERAL UTILITIES ###

def run(port="0.0.0.0:8000"):
    """
        Run django test server on open port, so it's accessible outside Vagrant.
    """
    try:
        # use runserver_plus if installed
        import django_extensions
        local("python manage.py runserver_plus %s --threaded" % port)
    except ImportError:
        local("python manage.py runserver %s" % port)

def run_ssl(port="0.0.0.0:8000"):
    """
        Run django test server with SSL.
    """
    local("python manage.py runsslserver %s" % port)
    return

def test(apps="perma mirroring api"):
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

def test_sauce(target_host="127.0.0.1:8000"):
    """
        Run Sauce browser tests. If target_host is localhost, first run sauce_tunnel.
    """
    os.environ.setdefault('SAUCE_USERNAME', settings.SAUCE_USERNAME)
    os.environ.setdefault('SAUCE_ACCESS_KEY', settings.SAUCE_ACCESS_KEY)

    local("HOST="+target_host+" " +
          "py.test " +
          "-n3 " +  # run 3 in parallel - max for free account
          "--boxed " +  # don't let crashes in single test kill whole process
          os.path.join(settings.PROJECT_ROOT, "../services/sauce/run_tests.py"))

def sauce_tunnel():
    """
        Set up Sauce tunnel before running test_sauce targeted at localhost.
    """
    if subprocess.call(['which','sc']) == 1: # error return code -- program not found
        sys.exit("Please check that the `sc` program is installed and in your path. To install: https://docs.saucelabs.com/reference/sauce-connect/")
    local("sc -u %s -k %s" % (settings.SAUCE_USERNAME, settings.SAUCE_ACCESS_KEY))


def logs(log_dir=os.path.join(settings.PROJECT_ROOT, '../services/logs/')):
    """ Tail all logs. """
    local("tail -f %s/*" % log_dir)

def init_dev_db():
    """
        Run syncdb, South migrate, and import fixtures for new dev database.
    """
    local("python manage.py syncdb --noinput")
    local("python manage.py migrate")
    local("python manage.py loaddata fixtures/sites.json fixtures/users.json fixtures/folders.json")

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
def deploy(branch='master'):
    """
        Full deployment: back up database, pull code, install requirements, sync db, run south migrations, collect static files, restart server.
    """
    backup_database()
    deploy_code(restart=False, branch=branch)
    pip_install()
    run("%s manage.py syncdb" % env.PYTHON_BIN)
    run("fab south_in")
    run("%s manage.py collectstatic --noinput --clear" % env.PYTHON_BIN)
    

@setup_remote
def deploy_code(restart=True, branch='master'):
    """
        Deploy code only. This is faster than the full deploy.
    """
    run('find . -name "*.pyc" -exec rm -rf {} \;')
    run("git pull origin %s" % branch)
    if restart:
          restart_server()
          
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
    
          
def pip_install():
      run("pip install -r requirements.txt")

@setup_remote
def restart_server():
    """
        Touch the wsgi file to restart the remote server (hopefully).
    """
    run("sudo stop celery; sudo start celery;")
    run("sudo stop celerybeat; sudo start celerybeat;")


@setup_remote
def stop_server():
    """
        Stop the services
    """
    run("sudo service gunicorn stop")
    run("sudo service celery stop")
    run("sudo service celerybeat stop")
    
    
@setup_remote
def start_server():
    """
        Start the services
    """
    run("sudo service gunicorn start")
    run("sudo service celery start")
    run("sudo service celerybeat start")

### DATABASE STUFF ###

@setup_remote
def backup_database():
    if env.DATABASE_BACKUP_DIR:
        run("fab local_backup_database:%s" % env.DATABASE_BACKUP_DIR)

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


### MIRRORING ###

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



def set_up_folders():
    """ One-time function for use during transition to shared folders. """
    from perma.models import VestingOrg, LinkUser, Folder, Link
    from django.db.models import F

    print "Making sure each registrar has a default vesting org"
    for registrar in Registrar.objects.filter(default_vesting_org=None):
        registrar.create_default_vesting_org()

    print "Making sure each link has a vesting org"
    for link in Link.objects.filter(vested=True, vesting_org=None).select_related():
        editor = link.vested_by_editor
        if editor.vesting_org:
            link.vesting_org = editor.vesting_org
        elif editor.registrar:
            link.vesting_org = editor.registrar.default_vesting_org
        else:
            link.vesting_org_id = settings.FALLBACK_VESTING_ORG_ID
        link.save()

    print "Making sure each user has a root dir (this will use My Links if it exists)"
    for user in LinkUser.objects.filter(root_folder=None):
        user.create_root_folder()

    print "Making sure each vesting org has a shared folder"
    for vesting_org in VestingOrg.objects.filter(shared_folder=None):
        vesting_org.create_shared_folder()

    # helpers for next section
    target_folder_cache = {}

    def get_vesting_org_subfolder(vesting_org, user):
        folder, created = Folder.objects.get_or_create(name=user.get_full_name(), parent=vesting_org.shared_folder)
        return folder

    def get_target_folder(user):
        if user in target_folder_cache:
            return target_folder_cache[user]
        default_vesting_org = user.get_default_vesting_org()
        if default_vesting_org:
            target_folder = get_vesting_org_subfolder(default_vesting_org, user)
        else:
            target_folder = user.root_folder
        target_folder_cache[user] = target_folder
        return target_folder

    print "Moving top-level folders to parent dirs"
    Folder.objects.all().update(owned_by=F('created_by'))
    for folder in Folder.objects.filter(parent=None, is_root_folder=False, is_shared_folder=False):
        folder.move_to_folder(get_target_folder(folder.created_by))

    print "Moving top-level links to parent dirs"
    for link in Link.objects.all():
        # make sure link creator has link in a folder
        if link.created_by and not link.folders.accessible_to(link.created_by).exists():
            link.folders.add(get_target_folder(link.created_by))

        # make sure link vester has link in a folder
        if link.vested and not link.folders.accessible_to(link.vested_by_editor).exists():
            target_folder = get_target_folder(link.vested_by_editor)
            if target_folder.vesting_org == link.vesting_org:
                link.folders.add(target_folder)
            else:
                link.folders.add(get_vesting_org_subfolder(link.vesting_org, link.vested_by_editor))


try:
    from fab_targets import *
except ImportError, e:
    if e.args[0] == 'No module named fab_targets':
        print "Warning: no fab_targets file found."
    else:
        raise
