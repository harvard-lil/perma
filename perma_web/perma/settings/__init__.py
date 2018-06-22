# This is the base module that will be imported by Django.

# Try to import the custom settings.py file, which will in turn import one of the deployment targets.
# If it doesn't exist we assume this is a vanilla development environment and import .deployments.settings_dev.
try:
    from .settings import *
except ImportError as e:
    if e.message=='No module named settings':
        from .deployments.settings_dev import *
    else:
        raise

# After we've imported one of the deployment targets, we'll override the settings based on any
# DJANGO__SETTING_NAME environment variables. This is handy for deploying to Heroku, Travis, etc.
from .utils.environmental_settings import import_environmental_settings
import_environmental_settings(globals())

# Finally we'll apply some post-processing logic to the settings we've ended up with.
from .utils.post_processing import post_process_settings
post_process_settings(globals())
