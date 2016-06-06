from django.conf import settings
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from django.db.models.signals import pre_save

from .models import LinkUser, Link
from .utils import ReadOnlyException


### read only mode ###

# install signals to prevent database writes if settings.READ_ONLY_MODE is set
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

@receiver(pre_save, sender=Link)
def update_link_count(sender, instance, **kwargs):
    try:
        # get an existing link
        loaded_link = sender.objects.get(pk=instance.pk)

        def decrement_link_count(loaded_link):
            # minus one from user's organization and related registar
            if loaded_link.organization:
                if  loaded_link.organization.link_count > 0:
                    loaded_link.organization.link_count -= 1
                    loaded_link.organization.save()

                if loaded_link.organization.registrar.link_count > 0:
                    loaded_link.organization.registrar.link_count -= 1
                    loaded_link.organization.registrar.save()

        # subtract from org and registrar if org has changed
        if loaded_link.organization != instance.organization:
            decrement_link_count(loaded_link)

        # if the link was deleted
        if instance.user_deleted and loaded_link.user_deleted != instance.user_deleted:
            # minus one from user's link count
            if loaded_link.created_by.link_count > 0:
                loaded_link.created_by.link_count -= 1
                loaded_link.created_by.save()

            decrement_link_count(loaded_link)    

        # if org changed or we have a new link with an associated org, increment
        if instance.organization and loaded_link.organization != instance.organization:
            instance.organization.link_count += 1
            instance.organization.save()
            instance.organization.registrar.link_count += 1
            instance.organization.registrar.save()

    except sender.DoesNotExist:
        # new link. let's add it to the user's sum
        instance.created_by.link_count += 1
        instance.created_by.save()

        if instance.organization:
            instance.organization.link_count += 1
            instance.organization.save()
            instance.organization.registrar.link_count += 1
            instance.organization.registrar.save()