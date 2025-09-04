import os

import django

from invoke import Collection


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perma.settings')
try:
    django.setup()
except Exception as e:
    print(f"WARNING: Can't configure Django. {e}")

# import sub-tasks
from .dev import run, pip_compile
from . import dev

# Special tasks
from . import once
from . import wacz_conversion
from . import check_storage
from . import merge_accounts

ns = Collection()
ns.add_task(run)
ns.add_task(pip_compile)
ns.add_collection(dev)
ns.add_collection(once)
ns.add_collection(wacz_conversion)
ns.add_collection(check_storage)
ns.add_collection(merge_accounts)
