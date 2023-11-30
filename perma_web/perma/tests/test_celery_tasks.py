from django.core import mail

from django.test import override_settings
from perma.celery_tasks import update_stats, send_js_errors
from perma.models import UncaughtError


@override_settings(CELERY_ALWAYS_EAGER=True)
def testUpdateStats(db):
    # this tests only that the task runs,
    # not anything about the task itself
    assert update_stats.delay()


def test_send_js_errors(db):
    response = send_js_errors()
    assert not response
    assert len(mail.outbox) == 0
    unruly_stack_trace = '[{"function": "getNextContents", "column": 6, "line": 304, "file": "static/bundles/create.js"}, {"function": "showFolderContents", "column": 4, "line": 335, "file": "static/bundles/create.js"}]'
    err = UncaughtError.objects.create(
        message="oh no!",
        current_url="perma.cc/about",
        stack=unruly_stack_trace)
    err.save()

    response = send_js_errors()
    assert response

    message = mail.outbox[0]
    message_parts = message.body.split('\n')
    assert 'URL: %s' % err.current_url in message_parts
    assert 'Message: %s' % err.message in message_parts
    assert 'Function: getNextContents' in message_parts
    assert 'File: static/bundles/create.js' in message_parts
    assert 'showFolderContents' not in message_parts
