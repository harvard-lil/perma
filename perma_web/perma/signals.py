from django.dispatch import receiver
from django.db.models import expressions
from django.db.models.signals import pre_save
from simple_history import signals

from .models import Link


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


@receiver(
    signals.pre_create_historical_record, dispatch_uid="simple_history_refresh"
)
def remove_f_expressions(sender, instance, history_instance, **kwargs) -> None:  # noqa
    """
    Work around for F expressions not working with django-simple-history.
    https://github.com/jazzband/django-simple-history/pull/413/files
    From https://stackoverflow.com/a/62369328
    """

    f_expression_fields = []

    for field in history_instance._meta.fields:  # noqa
        field_value = getattr(history_instance, field.name)
        if isinstance(field_value, expressions.BaseExpression):
            f_expression_fields.append(field.name)

    if f_expression_fields:
        instance.refresh_from_db()
        for field_name in f_expression_fields:
            field_value = getattr(instance, field_name)
            setattr(history_instance, field_name, field_value)
