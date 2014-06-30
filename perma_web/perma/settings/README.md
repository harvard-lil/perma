Perma Settings
==============

This entire settings module is imported by Django and ends up in django.conf.settings. The core logic is in settings/\_\_init\_\_.py.

Settings specific to this deployment should go in the settings/settings.py file, which is kept out of version control.

That file should in turn import one of the base settings files in settings/deployments/.

If there is no custom settings/settings.py, settings/\_\_init\_\_.py will instead import the base settings/deployments/settings_dev.py file.
This lets the code run by default in our Vagrant dev environment without any additional setup.