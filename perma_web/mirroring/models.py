from django.conf import settings
from django.core import serializers
from django.core.files.storage import default_storage
from django.db import models
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.db import transaction
from django.dispatch import receiver

from perma.models import LinkUser
from perma.storage_backends import file_saved
from perma.utils import run_task


class FakeLinkUser(LinkUser):
    """
        This is a fake user for use on mirror servers.
        It will be created from a serialized user object put in a cookie by the upstream server.
    """

    class Meta:
        proxy = True

    def is_authenticated(self):
        return True

    def save(self, *args, **kwargs):
        raise NotImplementedError("FakeLinkUser should never be saved.")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("FakeLinkUser should never be deleted.")


class UpdateQueue(models.Model):
    action = models.CharField(max_length=10, default='update', choices=(('update','update'),('delete','delete')))
    json = models.TextField()
    sent = models.BooleanField(default=False)

    @classmethod
    def init_from_instance(self, instance, **kwargs):
        return UpdateQueue(json=serializers.serialize("json", [instance], fields=instance.mirror_fields), **kwargs)

    class Meta:
        ordering = ['pk']

    @classmethod
    @transaction.atomic
    def import_updates(cls, updates):
        """
            Import a list of updates.
            Each update should be a dict with keys {'pk', 'json', 'action'}.
        """
        # first save updates to our downstream copy of the UpdateQueue
        model_updates = []
        for update in updates:
            print "IMPORTING", update['json']
            UpdateQueue(**update).save()
            decoded_instance = serializers.deserialize("json", update['json']).next().object

            # Keep track of the actual instances we need to save, but don't save them yet --
            # we don't want to run updates that are just going to be superceded by the following update
            # (which happens frequently with common database access patterns).
            last_instance = model_updates[-1] if model_updates else None
            this_instance = {'action':update['action'], 'instance':decoded_instance}
            if last_instance and type(last_instance['instance']) == type(decoded_instance) and last_instance['instance'].pk == decoded_instance.pk:
                # this instance is the same as the last one -- overwrite the last one
                model_updates[-1] = this_instance
            else:
                # this instance is different from the last one -- append
                model_updates.append(this_instance)

        # actually apply all updates
        for update in model_updates:
            if update['action'] == 'update':
                update['instance'].save()
            elif update['action'] == 'delete':
                update['instance'].delete()


### this is in models for now because it's annoying to put it in signals.py and resolve circular imports with models.py
### in Django 1.8 we can avoid that issue by putting this in signals.py and importing it from ready()
### https://docs.djangoproject.com/en/dev/topics/signals/

if settings.DOWNSTREAM_SERVERS:
    def queue_update(instance, action='update'):
        # Only send model classes with a mirror_fields setting.
        # Set _no_downstream_update on individual instances to disable sending of trivial updates.
        if not hasattr(instance, 'mirror_fields') or getattr(instance, '_no_downstream_update', False):
            return

        from .tasks import send_updates
        update = UpdateQueue.init_from_instance(instance=instance, action=action)
        update.save()
        print "MAIN: Created %s %s; queueing send." % (action, update.pk)
        run_task(send_updates, options={'countdown': 2})

    # add all useful database updates to UpdateQueue
    @receiver(post_save)
    def model_update(sender, instance, **kwargs):
        queue_update(instance)

    @receiver(post_delete)
    def model_delete(sender, instance, **kwargs):
        queue_update(instance)

    @receiver(m2m_changed)
    def model_m2m_changed(sender, instance, **kwargs):
        queue_update(instance)

    @receiver(file_saved)
    def broadcast_file_update(sender, **kwargs):
        print "Got save message", sender, kwargs
        if kwargs['instance'] == default_storage._wrapped:
            from .tasks import trigger_media_sync

            print "Saving."
            run_task(trigger_media_sync, paths=[kwargs['path']])