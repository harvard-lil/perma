# Settings for the ECS tiers. The prod image selects this module by default
# (PERMA_SETTINGS_MODULE=settings_ecs in the Dockerfile) and every role -- web,
# beat, each worker -- boots from it.
#
# Everything tier-specific comes from one JSON document in the APP_CONFIG
# environment variable, which the ECS task definition injects from the
# `<tier>-perma-settings` Secrets Manager secret. This module reads it on
# import, so it cannot be imported at build time; settings_build exists for
# that. Nothing here is a value the Salt template hardcodes for both tiers;
# those stay literal below, as they were in repos/salt/perma-settings.
#
# APP_CONFIG keys. Every value is a string. Required unless marked optional.
#
#   TIER                         "staging" or "prod". Chooses the beat schedule,
#                                analytics, and the Sentry environment label.
#   ALLOWED_HOSTS                Comma-separated, e.g. "perma.cc,api.perma.cc".
#   SECRET_KEY                   Django's.
#   ADMINS                       Python literal, e.g. "[('Name', 'a@b.c')]".
#                                Also MANAGERS. Error emails go here.
#   DATABASE_NAME
#   DATABASE_USERNAME
#   DATABASE_PASSWORD
#   DATABASE_HOST                Postgres, reached over TLS with the RDS CA
#   DATABASE_PORT                bundle shipped in the image (see below).
#   DEFAULT_FROM_EMAIL           From: address for mail Perma sends.
#   SERVER_EMAIL                 From: address for error mail to ADMINS.
#   EMAIL_HOST                   SMTP relay (Mailgun on the Salt hosts).
#   EMAIL_HOST_USER
#   EMAIL_HOST_PASSWORD
#   HOST                         Public hostname, e.g. "perma.cc".
#   MEDIA_URL                    User-content URL prefix, as Salt's media_url.
#   PLAYBACK_HOST                Replay hostname, as Salt's playback_host.
#   INTERNET_ARCHIVE_COLLECTION
#   INTERNET_ARCHIVE_IDENTIFIER_PREFIX
#   INTERNET_ARCHIVE_ACCESS_KEY
#   INTERNET_ARCHIVE_SECRET_KEY
#   STORAGE_BUCKET               S3 bucket for WARCs (STORAGES["default"]).
#   WACZ_BUCKET                  S3 bucket for WACZs (STORAGES["secondary"]).
#   AWS_ACCESS_KEY_ID            Optional. Static S3 credentials, as the Salt
#   AWS_SECRET_ACCESS_KEY        hosts use. Omit both to use the task role.
#   CELERY_BROKER_URL            The existing broker (Redis, on ElastiCache).
#   CACHE_LOCATION               Redis URL for Django's cache.
#   STRIPE_PAYMENTS_APP_INTERNAL_URL   perma-payments, from inside the VPC.
#   STRIPE_PAYMENTS_APP_EXTERNAL_URL   perma-payments, as browsers reach it.
#   PAYMENTS_KEY_ID              PERMA_PAYMENTS_ENCRYPTION_KEYS["id"]
#   PAYMENTS_PERMA_SECRET_KEY    ...["perma_secret_key"]
#   PAYMENTS_PERMA_PUBLIC_KEY    ...["perma_public_key"]
#   PAYMENTS_PAYMENTS_PUBLIC_KEY ...["perma_payments_public_key"]
#   SCAN_URL                     filecheck's /scan/ endpoint.
#   SENTRY_DSN
#   SCOOP_API_URL
#   SCOOP_API_KEY
#   BETA_SCOOP_API_URL           Optional. Staging points these at the
#   BETA_SCOOP_API_KEY           staging Scoop API; prod leaves them unset.
#   STATIC_URL                   Optional. Where browsers fetch static files;
#                                default "/static/", served by WhiteNoise from
#                                the image. Set to the static bucket's URL
#                                (`https://static.<host>/static/`) once the
#                                deploy publishes there; see below.
#   CUSTOM_EMAILS_FOR_REGISTRAR  Optional. JSON object, registrar id =>
#                                {"subject", "opening", "closing"}; see below.
#   TRUSTED_PROXIES              Optional. JSON, the shape settings_common
#                                documents: a list of proxies, each a list of
#                                CIDRs. Default: the cloudflared sidecar on
#                                localhost, which is the only thing that can
#                                reach the web container.
#
# Other environment variables read here:
#
#   PERMA_VERSION                Short commit hash, stamped into the image at
#                                build time (Dockerfile ARG). Not in APP_CONFIG
#                                because it belongs to the image, not the tier.
#   PERMA_STATEMENT_TIMEOUT      Optional. Postgres statement_timeout for this
#                                process's connections, e.g. "60s". Set by
#                                gunicorn_config.py for web workers only.
import ast
import json
import os

from .settings_prod import *  # noqa

config = json.loads(os.environ["APP_CONFIG"])

tier = config["TIER"]
if tier not in ("staging", "prod"):
    raise ValueError(f"APP_CONFIG TIER must be 'staging' or 'prod', not {tier!r}")

DEBUG = False

ALLOWED_HOSTS = config["ALLOWED_HOSTS"].split(",")
SECRET_KEY = config["SECRET_KEY"]

ADMINS = ast.literal_eval(config["ADMINS"])
MANAGERS = ADMINS

DATABASES["default"]["NAME"] = config["DATABASE_NAME"]  # noqa: F405
DATABASES["default"]["USER"] = config["DATABASE_USERNAME"]  # noqa: F405
DATABASES["default"]["PASSWORD"] = config["DATABASE_PASSWORD"]  # noqa: F405
DATABASES["default"]["HOST"] = config["DATABASE_HOST"]  # noqa: F405
DATABASES["default"]["PORT"] = int(config["DATABASE_PORT"])  # noqa: F405
DATABASES["default"]["OPTIONS"] = {  # noqa: F405
    "sslmode": "verify-full",
    # services/aws/global-bundle.pem, copied into the image beside perma_web.
    "sslrootcert": os.path.join(SERVICES_DIR, "aws", "global-bundle.pem"),  # noqa: F405
    "connect_timeout": 60,
}
# Set by gunicorn_config.py for the web server only; see there.
if "PERMA_STATEMENT_TIMEOUT" in os.environ:
    DATABASES["default"]["OPTIONS"]["options"] = f"-c statement_timeout={os.environ['PERMA_STATEMENT_TIMEOUT']}"  # noqa: F405

# Email
DEFAULT_FROM_EMAIL = config["DEFAULT_FROM_EMAIL"]
DEFAULT_REPLYTO_EMAIL = "lil@law.harvard.edu"
SERVER_EMAIL = config["SERVER_EMAIL"]
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config["EMAIL_HOST"]
EMAIL_HOST_USER = config["EMAIL_HOST_USER"]
EMAIL_HOST_PASSWORD = config["EMAIL_HOST_PASSWORD"]
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Hosts
HOST = config["HOST"]
MEDIA_URL = config["MEDIA_URL"]
PLAYBACK_HOST = config["PLAYBACK_HOST"]

# Internet Archive
INTERNET_ARCHIVE_MAX_UPLOAD_SIZE = 1024 * 1024 * 40
INTERNET_ARCHIVE_COLLECTION = config["INTERNET_ARCHIVE_COLLECTION"]
INTERNET_ARCHIVE_IDENTIFIER_PREFIX = config["INTERNET_ARCHIVE_IDENTIFIER_PREFIX"]
INTERNET_ARCHIVE_ACCESS_KEY = config["INTERNET_ARCHIVE_ACCESS_KEY"]
INTERNET_ARCHIVE_SECRET_KEY = config["INTERNET_ARCHIVE_SECRET_KEY"]

# Archive storage. With the two AWS_* keys absent, django-storages leaves the
# credentials to boto3's default chain, which on ECS is the task role.
STORAGES["default"]["OPTIONS"]["bucket_name"] = config["STORAGE_BUCKET"]  # noqa: F405
STORAGES["secondary"]["OPTIONS"]["bucket_name"] = config["WACZ_BUCKET"]  # noqa: F405
if "AWS_ACCESS_KEY_ID" in config:
    for _storage in ("default", "secondary"):
        STORAGES[_storage]["OPTIONS"]["access_key"] = config["AWS_ACCESS_KEY_ID"]  # noqa: F405
        STORAGES[_storage]["OPTIONS"]["secret_key"] = config["AWS_SECRET_ACCESS_KEY"]  # noqa: F405
    del _storage

# Celery. The broker is Redis. The tunables are the Salt template's, which
# took them from https://www.cloudamqp.com/docs/celery.html for a CloudAMQP
# broker; the heartbeat setting has no effect on Redis. Redis redelivers a
# message that is unacknowledged after the visibility timeout (Celery's
# default, one hour), which bounds how long an acks_late task may run or wait.
CELERY_BROKER_URL = config["CELERY_BROKER_URL"]
CELERY_BROKER_CONNECTION_TIMEOUT = 30
CELERY_BROKER_HEARTBEAT = None
CELERY_WORKER_SEND_TASK_EVENTS = False
CELERY_RESULT_BACKEND = None

# The beat schedule differs by tier, as it does in the Salt template: staging
# does not sync subscriptions or talk to the Internet Archive.
if tier == "prod":
    CELERY_BEAT_JOB_NAMES = [
        "run-next-capture",
        "sync_subscriptions_from_perma_payments",
        "cache_playback_status_for_new_links",
        "conditionally_queue_internet_archive_uploads_for_date_range",
        "confirm_files_uploaded_to_internet_archive",
        "confirm_files_deleted_from_internet_archive",
        "deactivate_expired_sponsored_users",
        "warn_expiring_sponsored_users",
        "remove_expired_organization_user_affiliations",
        "warn_expiring_organization_users",
    ]
else:
    CELERY_BEAT_JOB_NAMES = [
        "run-next-capture",
        "cache_playback_status_for_new_links",
        "deactivate_expired_sponsored_users",
        "warn_expiring_sponsored_users",
        "remove_expired_organization_user_affiliations",
        "warn_expiring_organization_users",
    ]

# Logging: stdout only, for CloudWatch. settings_prod's file handler names
# /var/log/perma/perma.log, which does not exist in a container.
LOGGING["formatters"]["standard"]["format"] = "%(asctime)s [%(levelname)s] thread %(thread)d %(filename)s %(lineno)d: %(message)s"  # noqa: F405
del LOGGING["handlers"]["file"]  # noqa: F405
for _logger in LOGGING["loggers"].values():  # noqa: F405
    if "file" in _logger.get("handlers", []):
        _logger["handlers"] = [h for h in _logger["handlers"] if h != "file"]
del _logger

CONTACT_REGISTRARS = True

# Proxy chain, see settings_common. Behind the cloudflared sidecar the only
# peer gunicorn ever sees is localhost; the client IP is the last entry Cloudflare
# appended to X-Forwarded-For. The Cloudflare edge IPs are not in the chain,
# unlike on the Salt hosts, where the edge connects to nginx over TCP.
if "TRUSTED_PROXIES" in config:
    TRUSTED_PROXIES = json.loads(config["TRUSTED_PROXIES"])
else:
    TRUSTED_PROXIES = [["127.0.0.1/32", "::1/128"]]

API_VERSION = 1

# Perma Payments
PERMA_PAYMENTS_ENCRYPTION_KEYS = {
    "id": config["PAYMENTS_KEY_ID"],
    "perma_secret_key": config["PAYMENTS_PERMA_SECRET_KEY"],
    "perma_public_key": config["PAYMENTS_PERMA_PUBLIC_KEY"],
    "perma_payments_public_key": config["PAYMENTS_PAYMENTS_PUBLIC_KEY"],
}
PERMA_PAYMENTS_TIMESTAMP_MAX_AGE_SECONDS = 120
STRIPE_PAYMENTS_APP_INTERNAL_URL = config["STRIPE_PAYMENTS_APP_INTERNAL_URL"]
STRIPE_PAYMENTS_APP_EXTERNAL_URL = config["STRIPE_PAYMENTS_APP_EXTERNAL_URL"]

# Cache
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config["CACHE_LOCATION"],
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,  # since this is just a cache, we don't want to show errors if redis is offline for some reason
        },
    }
}

# The deploy pauses capture intake with `manage.py deployment_sentinel set`,
# which stores a flag in this cache: it is the only signal shared between the
# web and worker containers (settings.DEPLOYMENT_SENTINEL, the file, is
# per-container here and only ever a fallback). With IGNORE_EXCEPTIONS above,
# a Redis outage makes the flag unreadable rather than raising; this setting
# makes perma.utils.deployment_pending treat that as pending (logged at ERROR),
# so an outage during a deploy cannot let captures through mid-migration. The
# cost is that an outage outside a deploy also pauses intake until Redis is
# back; the every-minute run-next-capture beat job resumes it.
DEPLOYMENT_SENTINEL_CACHE_REQUIRED = True

# Static files. The deploy publishes the image's collected static tree to the
# static bucket under `<static hostname>/static/`, so the value here is that
# hostname plus the "/static/" path. The path matters: WhiteNoise serves from
# STATIC_ROOT at urlparse(STATIC_URL).path, so with the path kept at /static/
# the copies in the image still answer /static/... requests (anything cached
# or rendered before the switch), and the middleware stays useful as the
# fallback. Absent key: "/static/" from settings_common, i.e. everything
# served by WhiteNoise from the image, as on the Salt hosts.
# collectstatic runs under settings_build, which does not read this.
STATIC_URL = config.get("STATIC_URL") or STATIC_URL  # noqa: F405

MAX_ARCHIVE_FILE_SIZE = 1024 * 1024 * 200  # 200 MB

# Upload scanning
SCAN_UPLOADS = True
SCAN_URL = config["SCAN_URL"]

# Sentry
USE_SENTRY = True
SENTRY_DSN = config["SENTRY_DSN"]
SENTRY_ENVIRONMENT = tier
SENTRY_TRACES_SAMPLE_RATE = 0.00005

# Scoop
SCOOP_API_KEY = config["SCOOP_API_KEY"]
SCOOP_API_URL = config["SCOOP_API_URL"]
SCOOP_API_USERAGENT = "Perma capture worker 20240110"
BETA_SCOOP_API_URL = config.get("BETA_SCOOP_API_URL")
BETA_SCOOP_API_KEY = config.get("BETA_SCOOP_API_KEY")

# JS_WACZ_DIR is not overridden: settings_common derives it from PROJECT_ROOT,
# which in the image is /perma/perma_web, giving /perma/services/js-wacz --
# where the Dockerfile installs it.

USE_ANALYTICS = tier == "prod"

PERMA_VERSION = os.environ.get("PERMA_VERSION", "unknown")

# turn this down from the default of 600/m to deal with a bot, 2025-03-19
REGISTER_MINUTE_LIMIT = "6/m"

# Registrar-specific invitation text, keyed by registrar id. It names
# customers, so it lives in the settings document rather than in this public
# repository: a JSON object in the optional CUSTOM_EMAILS_FOR_REGISTRAR key,
# shaped like the example in settings_common. JSON object keys are strings;
# registrar ids are integers.
CUSTOM_EMAILS_FOR_REGISTRAR = {
    int(registrar_id): text
    for registrar_id, text in json.loads(config.get("CUSTOM_EMAILS_FOR_REGISTRAR", "{}")).items()
}
