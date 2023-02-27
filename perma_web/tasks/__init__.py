import os

import django

from invoke import Collection


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perma.settings')
try:
    django.setup()
except Exception as e:
    print(f"WARNING: Can't configure Django. {e}")

# import sub-tasks
from .dev import run, test, pip_compile
from . import dev

ns = Collection()
ns.add_task(run)
ns.add_task(test)
ns.add_task(pip_compile)
ns.add_collection(dev)
