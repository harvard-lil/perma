from django.dispatch import receiver
from django.db.models import expressions
from simple_history import signals


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
