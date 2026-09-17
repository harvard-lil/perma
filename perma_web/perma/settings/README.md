Perma Settings
==============

This entire settings module is imported by Django and ends up in django.conf.settings. The core logic is in settings/\_\_init\_\_.py.

Settings specific to this deployment should go in the settings/settings.py file, which is kept out of version control.

That file should in turn import one of the base settings files in settings/deployments/.

If there is no custom settings/settings.py, settings/\_\_init\_\_.py will instead import the base settings/deployments/settings_dev.py file.
This lets the code run by default in our Docker dev environment without any additional setup.

Alternatively, the `PERMA_SETTINGS_MODULE` environment variable names a module in
settings/deployments/ directly (for example `settings_ecs` or `settings_prod`), and
takes precedence over settings/settings.py. This is how the container image selects
its settings at runtime: the prod image sets `PERMA_SETTINGS_MODULE=settings_ecs`,
whose values come from the `APP_CONFIG` environment variable (see the comment block
at the top of settings_ecs.py); the image build runs collectstatic and
migration_manifest under `settings_build`, which needs no secrets. A name that does
not exist is an error rather than a fall-through to settings_dev.
