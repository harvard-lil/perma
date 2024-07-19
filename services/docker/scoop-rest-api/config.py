# This is the default config.py from the Scoop REST API as of 7/19/2024
# https://github.com/harvard-lil/perma-scoop-api/blob/ac4691f4716ac1481dcecdc87c2b2302406aa3c3/scoop_rest_api/config.py
# We use it to:
# - override the blocklist, to allow the capturing of docker-hosted pages in our test suite;
# - enable additional attachments

"""
`config` module: App-wide settings.
"""

import os

from celery.schedules import crontab
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

#
# Security settings
#
ACCESS_KEY_SALT = os.environ.get(
    "ACCESS_KEY_SALT", "$2b$12$rXmm9AWx82fxw9Jbs1PXI.zebeXu4Ydi1huwxyH5k9flyhccBBTxa"
).encode()
# Access key salt should be provided via an environment variable.
# Use bcrypt.gensalt() to generate one.

MAX_PENDING_CAPTURES = 300
""" Stop accepting new capture requests if there are over X captures in the queue. """

EXPOSE_SCOOP_LOGS = os.environ.get("EXPOSE_SCOOP_LOGS", "True") == "True"
""" If `True`, Scoop logs will be exposed at API level by capture_to_dict. Handle with care. """

EXPOSE_SCOOP_CAPTURE_SUMMARY = True
""" If `True`, Scoop's capture summary will be exposed at API level via capture_to_dict. Handle with care. """  # noqa

#
# Database settings
#
DATABASE_USERNAME = os.environ.get("DATABASE_USERNAME", "root")
""" (Postgres) Database username. Should be provided via an environment variable. """

DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "")
""" (Postgres) Database password. Should be provided via an environment variable. """

DATABASE_HOST = os.environ.get("DATABASE_HOST", "127.0.0.1")
""" (Postgres) Database host. Should be provided via an environment variable. """

DATABASE_PORT = int(os.environ.get("DATABASE_PORT", "5432"))
""" (Postgres) Database port. Should be provided via an environment variable. """

DATABASE_NAME = os.environ.get("DATABASE_NAME", "scoop_api")
""" (Postgres) Database name. Should be provided via an environment variable. """

DATABASE_CA_PATH = os.environ.get("DATABASE_CA_PATH", "")
""" If provided, will be used to connect to Postgres via SSL. """


#
# Path and artifact settings
#
TEMPORARY_STORAGE_EXPIRATION = os.environ.get("TEMPORARY_STORAGE_EXPIRATION", str(60 * 60 * 24))
""" How long should temporary files be stored for? (In seconds). Can be provided via an environment variable. """  # noqa

DEPLOYMENT_SENTINEL_PATH = "/tmp/deployment-pending"

#
# API-wide settings
#
API_DOMAIN = os.environ.get("API_DOMAIN", "http://localhost:5000")
""" Root URL of the API. """

API_STORAGE_URL = f"{API_DOMAIN}/storage"
""" URL for the storage folder. """

#
# Background processing options
#
PROCESSES = int(os.environ.get("PROCESSES", "6"))
""" How many tick commands (capture processing) should run in parallel."""

PROCESSES_PROXY_PORT = 9000
"""
    Default port for Scoop Proxy for a given process.
    Will be incremented by 1 for each new parallel process.
"""

#
# Scoop settings
#
BANNED_IP_RANGES = [
    "0.0.0.0/8",
    "10.0.0.0/8",
    "100.64.0.0/10",
    "127.0.0.0/8",
    "169.254.0.0/16",
    # "172.16.0.0/12",
    "192.0.0.0/29",
    "192.0.2.0/24",
    "192.88.99.0/24",
    # "192.168.0.0/16",
    "198.18.0.0/15",
    "198.51.100.0/24",
    "203.0.113.0/24",
    "224.0.0.0/4",
    "240.0.0.0/4",
    "255.255.255.255/32",
    "::/128",
    "::1/128",
    "::ffff:0:0/96",
    "100::/64",
    "64:ff9b::/96",
    "2001::/32",
    "2001:10::/28",
    "2001:db8::/32",
    "2002::/16",
    "fc00::/7",
    "fe80::/10",
    "ff00::/8",
]

SCOOP_CLI_OPTIONS = {
    "--log-level": "info",
    # "--signing-url": "https://authsign.lil.tools/sign",
    # "--signing-token": "",
    "--screenshot": "true",
    "--pdf-snapshot": "false",
    "--dom-snapshot": "true",
    "--capture-video-as-attachment": "true",
    "--capture-certificates-as-attachment": "true",
    "--provenance-summary": "true",
    "--attachments-bypass-limits": "true",
    "--capture-timeout": 45 * 1000,
    "--load-timeout": 20 * 1000,
    "--network-idle-timeout": 20 * 1000,
    "--behaviors-timeout": 15 * 1000,
    "--capture-video-as-attachment-timeout": 20 * 1000,
    "--capture-certificates-as-attachment-timeout": 10 * 1000,
    "--capture-window-x": 1600,
    "--capture-window-y": 900,
    "--max-capture-size": int(200 * 1024 * 1024),
    "--auto-scroll": "true",
    "--auto-play-media": "true",
    "--grab-secondary-resources": "true",
    "--run-site-specific-behaviors": "true",
    "--headless": "false",  # Note: `xvfb-run --auto-servernum --` prefix may be needed if false.
    # "--user-agent-suffix": "",
    "--blocklist": rf"/https?:\/\/localhost/,{','.join(BANNED_IP_RANGES)}",
    "--public-ip-resolver-endpoint": "https://icanhazip.com",
}
"""
    Options passed to the Scoop CLI during capture.
    See https://github.com/harvard-lil/scoop for details.

    Options which cannot be set at config level are listed here:
    - utils.config_check.EXCLUDED_SCOOP_CLI_OPTIONS
"""

SCOOP_TIMEOUT_FUSE = 35
""" Number of seconds to wait before "killing" a Scoop progress after capture timeout. """


#
# Validation settings
#
with sync_playwright() as playwright:
    VALIDATION_USER_AGENT = playwright.devices["Desktop Chrome"]["user_agent"]

VALIDATION_EXTRA_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "*",
    "Accept-Language": "*",
    "Connection": "keep-alive",
}
VALIDATION_TIMEOUT = int(os.environ.get("VALIDATION_TIMEOUT", "45"))


#
# Celery settings
#
CELERY_SETTINGS = {
    "broker_url": os.environ.get("BROKER_URL", "redis://scoop-redis:6379/0"),
    "result_backend": os.environ.get("RESULT_BACKEND", "redis://scoop-redis:6379/1"),
    "accept_content": ["json"],
    "result_serializer": "json",
    "task_serializer": "json",
    # If a task is running longer than five minutes, ask it to shut down
    "task_soft_time_limit": 300,
    # If a task is running longer than seven minutes, kill it
    "task_time_limit": 420,
    "task_always_eager": False,
    "task_routes": {
        "scoop_rest_api.tasks.start_capture_process": {"queue": "main"},
    },
    "beat_schedule": {
        "run-next-capture": {
            "task": "scoop_rest_api.tasks.start_capture_process",
            "schedule": crontab(minute="*"),
        }
    },
}
ENABLE_CELERY_BACKEND = os.environ.get("ENABLE_CELERY_BACKEND", "False") == "True"
if "CELERYBEAT_TASKS" in os.environ:
    CELERYBEAT_TASKS = os.environ["CELERYBEAT_TASKS"].split(",")
else:
    CELERYBEAT_TASKS = ["run-next-capture"]

#
# Command for wrapping Scoop, e.g. firejail
#
SCOOP_PREFIX = os.environ.get("SCOOP_PREFIX", "")
