import os
from fabric.api import env

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perma.settings')
try:
    django.setup()
except Exception as e:
    print("WARNING: Can't configure Django. %s" % e)

# import sub-tasks
from . import dev, deploy, heroku  # noqa
from .dev import run_django, test  # noqa

# optionally import fab_targets
try:
    from .fab_targets import *
except ImportError as e:
    if e.args[0] != "No module named 'fabfile.fab_targets'":
        raise

### SETUP ###
env.use_ssh_config = True
env.REMOTE_DIR = '/srv/www/perma/perma_web'
env.VIRTUALENV_NAME = 'perma'
env.PYTHON_BIN = 'python'
env.DATABASE_BACKUP_DIR = '/perma/assets/db_backups' # If relative path, dir is relative to REMOTE_DIR. If None, no backup will be done.
env.CODE_BACKUP_DIR = '/perma/assets/code_backups' # If set, web code will be copied to this dir during deploy.
