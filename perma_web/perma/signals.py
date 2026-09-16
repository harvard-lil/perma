from django.dispatch import receiver
from django.db.models import expressions
from django.db.models.signals import pre_save
from simple_history import signals

from .models import Link, Registrar


@receiver(pre_save, sender=Link)
def update_link_count(sender, instance, **kwargs):
    """ update link counts when a link is saved or deleted """

    def decrement_organization_link_counts(link):
        """ minus one from user's organization and associated registrar """
        if link.organization:
            organization = link.organization
            registrar = organization.registrar

            if organization.link_count > 0:
                organization.link_count -= 1
                organization.save(update_fields=["link_count"])
            if registrar.link_count > 0:
                registrar.link_count -= 1
                registrar.save(update_fields=["link_count"])

    def increment_organization_link_counts(link):
        """ plus one to user's organization and associated registrar """
        if link.organization:
            organization = link.organization
            registrar = organization.registrar
            organization.link_count += 1
            organization.save(update_fields=["link_count"])
            registrar.link_count += 1
            registrar.save(update_fields=["link_count"])

    try:
        incoming_link = instance
        # include user deleted links, so we don't hit the new link signal when a link is deleted and later saved
        existing_link = sender.objects.all_with_deleted().get(pk=incoming_link.pk)
        if existing_link.user_deleted and incoming_link.user_deleted:
            return

        organization_changed = existing_link.organization != incoming_link.organization
        if organization_changed:
            decrement_organization_link_counts(existing_link)

        if incoming_link.user_deleted and not existing_link.user_deleted:
            if existing_link.created_by.link_count > 0:
                existing_link.created_by.link_count -= 1
                existing_link.created_by.save(update_fields=["link_count"])
            decrement_organization_link_counts(existing_link)
            Registrar.adjust_sponsored_link_count(existing_link._sponsored_by_id(), None)

        if incoming_link.organization and organization_changed:
            increment_organization_link_counts(incoming_link)

    except sender.DoesNotExist:
        # new link, let's add it to the user, org and registrar counts
        incoming_link.created_by.link_count += 1
        incoming_link.created_by.save(update_fields=["link_count"])
        increment_organization_link_counts(incoming_link)


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
