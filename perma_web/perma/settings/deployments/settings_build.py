# Settings for the management commands that run during the image build:
# collectstatic and migration_manifest. Both derive their output from
# INSTALLED_APPS, and nothing else here is consulted by either one.
#
# The deployment targets are unusable at build time: settings_ecs reads
# APP_CONFIG out of the environment on import, and that config is a runtime
# secret the builder does not hold. This module imports from settings_prod
# exactly as settings_ecs does, so INSTALLED_APPS is the same tuple --
# perma/tests/test_perma_settings_module.py asserts that the two agree, since
# the build's output is only correct for production insofar as they do.
#
# Selected per-command in the Dockerfile (PERMA_SETTINGS_MODULE=settings_build),
# not baked in: the image's default stays settings_ecs.
from .settings_prod import *  # noqa

DEBUG = False

# Django refuses to start with SECRET_KEY unset, and neither build command signs
# anything. This value is deliberately not a secret; a container that booted with
# these settings would be serving one it published on GitHub, so nothing selects
# this module except the RUN lines that produce the two build artifacts.
SECRET_KEY = "not-a-secret-this-module-only-runs-at-build-time"

# post_process_settings asserts these are set. Neither build command makes a
# request to the payments app.
STRIPE_PAYMENTS_APP_INTERNAL_URL = "http://payments.invalid"
STRIPE_PAYMENTS_APP_EXTERNAL_URL = "http://payments.invalid"

# settings_prod logs to /var/log/perma/perma.log, which does not exist in the
# image; logging.config would try to open it. Console only, as settings_ecs.
del LOGGING["handlers"]["file"]  # noqa: F821
for _logger in LOGGING["loggers"].values():  # noqa: F821
    if "file" in _logger.get("handlers", []):
        _logger["handlers"] = [h for h in _logger["handlers"] if h != "file"]
del _logger
