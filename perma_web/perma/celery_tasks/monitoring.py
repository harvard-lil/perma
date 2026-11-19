import socket

from celery.signals import task_failure
from django.core.mail import mail_admins


@task_failure.connect()
def celery_task_failure_email(**kwargs):
    """
    Celery 4.0 onward has no method to send emails on failed tasks
    so this event handler is intended to replace it. It reports truly failed
    tasks, such as those terminated after CELERY_TASK_TIME_LIMIT.
    From https://github.com/celery/celery/issues/3389
    """

    subject = "[Django][{queue_name}@{host}] Error: Task {sender.name} ({task_id}): {exception}".format(
        queue_name='celery',
        host=socket.gethostname(),
        **kwargs
    )

    message = """Task {sender.name} with id {task_id} raised exception:
{exception!r}


Task was called with args: {args} kwargs: {kwargs}.

The contents of the full traceback was:

{einfo}
    """.format(
        **kwargs
    )
    mail_admins(subject, message)
