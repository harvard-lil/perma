# Run locally using Heroku settings and config files.

import os

## Load Heroku settings.
from .settings_heroku import *


## Overrides to adapt to running locally.
heroku_dir = os.path.join(PROJECT_ROOT, "../services/heroku")
try:
    DATABASES['default']['OPTIONS']['ssl']['ca'] = os.path.join(heroku_dir, 'amazon-rds-combined-ca-bundle.pem')
except KeyError:
    pass  # not using RDS

