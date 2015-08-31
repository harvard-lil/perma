from django.conf import settings

from .models import LinkUser


### read only mode ###

# install signals to prevent database writes if settings.READ_ONLY_MODE is set

from django.contrib.sessions.models import Session
from django.db.models.signals import pre_save

from .utils import ReadOnlyException

write_whitelist = (
    (Session, None),
    (LinkUser, {'password'}),
    (LinkUser, {'last_login'}),
)

def read_only_mode(sender, instance, **kwargs):
    for whitelist_sender, whitelist_fields in write_whitelist:
        if whitelist_sender==sender and (whitelist_fields is None or whitelist_fields==kwargs['update_fields']):
            return
    raise ReadOnlyException("Read only mode enabled.")

if settings.READ_ONLY_MODE:
    pre_save.connect(read_only_mode)
