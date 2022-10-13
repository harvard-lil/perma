import os

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perma.settings')
try:
    django.setup()
except Exception as e:
    print(f"WARNING: Can't configure Django. {e}")

# import sub-tasks
from . import dev  # noqa
from .dev import run_django, test, pip_compile  # noqa
