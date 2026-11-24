"""
Celery tasks grouped by area/theme. Import tasks from their submodule,
for example: 'from perma.celery_tasks.capture import run_next_capture'.
"""
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from . import capture, internet_archive, link_maintenance, monitoring, user_management # noqa: F401, E402
