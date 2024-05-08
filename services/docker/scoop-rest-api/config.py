# This is the default config.py from the Scoop REST API as of 1/2/2024
# https://github.com/harvard-lil/perma-scoop-api/blob/86b757b15c1c91e0c5a99a74bf82dcedde9d780f/scoop_rest_api/config.py
# We only use it to override the blocklist, to allow the capturing of docker-hosted pages in our test suite.

"""
`config` module: App-wide settings.
"""
from dotenv import load_dotenv
import os
from playwright.sync_api import sync_playwright

load_dotenv()

#
# Security settings
#
ACCESS_KEY_SALT = b"$2b$12$rXmm9AWx82fxw9Jbs1PXI.zebeXu4Ydi1huwxyH5k9flyhccBBTxa"  # default / dev

# Access key salt should be provided via an environment variable.
# Use bcrypt.gensalt() to generate one.
if "ACCESS_KEY_SALT" in os.environ:
    ACCESS_KEY_SALT = os.environ["ACCESS_KEY_SALT"].encode()

MAX_PENDING_CAPTURES = 300
""" Stop accepting new capture requests if there are over X captures in the queue. """

EXPOSE_SCOOP_LOGS = True
""" If `True`, Scoop logs will be exposed at API level by capture_to_dict. Handle with care. """

EXPOSE_SCOOP_CAPTURE_SUMMARY = True
""" If `True`, Scoop's capture summary will be exposed at API level via capture_to_dict. Handle with care. """  # noqa

#
# Database settings
#
DATABASE_USERNAME = "root"
""" (MySQL) Database username. Should be provided via an environment variable. """

if "DATABASE_USERNAME" in os.environ:
    DATABASE_USERNAME = os.environ["DATABASE_USERNAME"]

DATABASE_PASSWORD = ""
""" (MySQL) Database password. Should be provided via an environment variable. """

if "DATABASE_PASSWORD" in os.environ:
    DATABASE_PASSWORD = os.environ["DATABASE_PASSWORD"]

DATABASE_HOST = "127.0.0.1"
""" (MySQL) Database host. Should be provided via an environment variable. """

if "DATABASE_HOST" in os.environ:
    DATABASE_HOST = os.environ["DATABASE_HOST"]

DATABASE_PORT = 3306
""" (MySQL) Database port. Should be provided via an environment variable. """

if "DATABASE_PORT" in os.environ:
    DATABASE_PORT = int(os.environ["DATABASE_PORT"])

DATABASE_NAME = "scoop_api"
""" (MySQL) Database name. Should be provided via an environment variable. """

if "DATABASE_NAME" in os.environ:
    DATABASE_NAME = os.environ["DATABASE_NAME"]

DATABASE_CA_PATH = ""
""" (MySQL) If provided, will be used to connect to MySQL via SSL. """

if "DATABASE_CA_PATH" in os.environ:
    DATABASE_CA_PATH = os.environ["DATABASE_CA_PATH"]


#
# Paths settings
#
TEMPORARY_STORAGE_PATH = "./storage"
""" Directory in which files will be (temporarily) stored. """

TEMPORARY_STORAGE_EXPIRATION = 60 * 60 * 24
""" How long should temporary files be stored for? (In seconds). Can be provided via an environment variable. """  # noqa

DEPLOYMENT_SENTINEL_PATH = "/tmp/deployment-pending"

#
# API-wide settings
#
API_DOMAIN = "http://localhost:5000"
""" Root URL of the API. """

if "API_DOMAIN" in os.environ:
    API_DOMAIN = os.environ["API_DOMAIN"]

API_STORAGE_URL = f"{API_DOMAIN}/storage"
""" URL for the storage folder. """

#
# Background processing options
#
PROCESSES = 6
""" How many tick commands (capture processing) should run in parallel."""

if "PROCESSES" in os.environ:
    PROCESSES = os.environ["PROCESSES"]

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
    "--dom-snapshot": "false",
    "--capture-video-as-attachment": "false",
    "--capture-certificates-as-attachment": "false",
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
    "--blocklist": f"/https?:\/\/localhost/,{','.join(BANNED_IP_RANGES)}",  # noqa
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
    VALIDATION_USER_AGENT = playwright.devices['Desktop Chrome']['user_agent']

VALIDATION_EXTRA_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "*",
    "Accept-Language": "*",
    "Connection": "keep-alive"
}
VALIDATION_TIMEOUT = 45
