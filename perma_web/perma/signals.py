from django.dispatch import receiver
from django.db.models import F, expressions
from django.db.models.signals import pre_save
from simple_history import signals

from .models import Link, LinkUser, Organization, Registrar


@receiver(pre_save, sender=Link)
def update_link_count(sender, instance, **kwargs):
    """ update link counts when a link is saved or deleted """

    def decrement_organization_link_counts(link):
        """ minus one from user's organization and associated registrar """
        if link.organization_id:
            Organization.objects.filter(pk=link.organization_id, link_count__gt=0).update(link_count=F('link_count') - 1)
            Registrar.objects.filter(pk=link.organization.registrar_id, link_count__gt=0).update(link_count=F('link_count') - 1)

    def increment_organization_link_counts(link):
        """ plus one to user's organization and associated registrar """
        if link.organization_id:
            Organization.objects.filter(pk=link.organization_id).update(link_count=F('link_count') + 1)
            Registrar.objects.filter(pk=link.organization.registrar_id).update(link_count=F('link_count') + 1)

    try:
        incoming_link = instance
        # include user deleted links, so we don't hit the new link signal when a link is deleted and later saved
        existing_link = sender.objects.all_with_deleted().get(pk=incoming_link.pk)
        if existing_link.user_deleted and incoming_link.user_deleted:
            return

        organization_changed = existing_link.organization_id != incoming_link.organization_id
        if organization_changed:
            decrement_organization_link_counts(existing_link)

        if incoming_link.user_deleted and not existing_link.user_deleted:
            LinkUser.objects.filter(pk=existing_link.created_by_id, link_count__gt=0).update(link_count=F('link_count') - 1)
            decrement_organization_link_counts(existing_link)
            Registrar.adjust_sponsored_link_count(existing_link._sponsored_by_id(), None)

        if incoming_link.organization_id and organization_changed:
            increment_organization_link_counts(incoming_link)

    except sender.DoesNotExist:
        # new link, let's add it to the user, org and registrar counts
        LinkUser.objects.filter(pk=incoming_link.created_by_id).update(link_count=F('link_count') + 1)
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
