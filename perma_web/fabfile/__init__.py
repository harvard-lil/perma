import sys
import os
from fabric.api import env

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perma.settings')
django.setup()
from django.conf import settings

# import sub-tasks
from . import dev, deploy
from .dev import run_django, test

# import Heroku subtasks (must come after django conf)
sys.path.append(os.path.join(settings.PROJECT_ROOT, '../services/'))
import heroku.fabfile as heroku

# optionally import fab_targets
try:
    from .fab_targets import *
except ImportError, e:
    if e.args[0] != 'No module named fab_targets':
        raise

### SETUP ###
env.use_ssh_config = True
env.REMOTE_DIR = '/srv/www/perma/perma_web'
env.VIRTUALENV_NAME = 'perma'
env.PYTHON_BIN = 'python'
env.DATABASE_BACKUP_DIR = '/perma/assets/db_backups' # If relative path, dir is relative to REMOTE_DIR. If None, no backup will be done.
env.CODE_BACKUP_DIR = '/perma/assets/code_backups' # If set, web code will be copied to this dir during deploy.
