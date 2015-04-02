# Settings to mix in for a mirror server.
# E.g., settings.py:
#  from deployments.settings_prod import *
#  from deployments.settings_mirror import *

MIRRORING_ENABLED = True
MIRROR_SERVER = True

CELERYBEAT_JOB_NAMES = ['mirror-integrity-check']