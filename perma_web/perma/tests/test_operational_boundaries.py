from unittest.mock import patch
from uuid import uuid4

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.core.cache import cache
from django_redis import get_redis_connection

from perma.celery import app
from perma.settings.utils.post_processing import post_process_settings
from perma.storage_backends import S3MediaStorage


def test_celery_registers_tasks_and_preserves_json_routing():
    import perma.celery_tasks  # noqa: F401

    assert 'perma.celery_tasks.convert_warc_to_wacz' in app.tasks
    assert app.conf.task_always_eager is True
    assert app.conf.task_serializer == 'json'
    assert app.conf.accept_content == ['json']
    assert app.conf.task_routes['perma.celery_tasks.convert_warc_to_wacz'] == {
        'queue': 'wacz-conversion'
    }


def test_testing_cache_preserves_ttl_and_pipeline_response_bytes():
    cache_key = f'phase3-cache-{uuid4()}'
    pipeline_key = f'phase3-pipeline-{uuid4()}'

    try:
        cache.set(cache_key, 'value', timeout=30)
        assert cache.get(cache_key) == 'value'
        assert 0 < cache.ttl(cache_key) <= 30

        pipeline = get_redis_connection('default').pipeline()
        pipeline.set(pipeline_key, 'value')
        pipeline.get(pipeline_key)
        assert pipeline.execute() == [True, b'value']
    finally:
        cache.delete_many([cache_key, pipeline_key])


def test_s3_storage_keeps_gzip_archives_browser_decodable():
    assert S3MediaStorage().get_object_parameters('archive.warc.gz') == {
        'ContentType': 'application/gzip',
        'ContentEncoding': '',
    }


@pytest.mark.uses_storage
def test_s3_storage_uploads_to_local_minio_with_required_checksums_only():
    storage = storages['default']
    object_name = f'phase3-storage-{uuid4()}'

    try:
        storage.save(object_name, ContentFile(b'payload'))
        assert storage.size(object_name) == 7
        assert storage.client_config.signature_version == 's3v4'
        assert storage.client_config.request_checksum_calculation == 'when_required'
    finally:
        storage.delete(object_name)


def test_sentry_initialization_uses_only_the_configured_values():
    settings = {
        'USE_SENTRY': True,
        'SENTRY_ENVIRONMENT': 'test',
        'SENTRY_DSN': 'https://public@example.invalid/1',
        'SENTRY_TRACES_SAMPLE_RATE': 0.25,
        'SENTRY_SEND_DEFAULT_PII': False,
        'SECRET_KEY': 'test-secret',
        'STRIPE_PAYMENTS_APP_EXTERNAL_URL': 'https://payments.example.invalid',
        'STRIPE_PAYMENTS_APP_INTERNAL_URL': 'https://payments-internal.example.invalid',
    }

    with patch('sentry_sdk.init') as sentry_init:
        post_process_settings(settings)

    assert sentry_init.call_args.kwargs == {
        'environment': 'test',
        'dsn': 'https://public@example.invalid/1',
        'integrations': sentry_init.call_args.kwargs['integrations'],
        'enable_tracing': True,
        'traces_sample_rate': 0.25,
        'send_default_pii': False,
    }
    assert {integration.__class__.__name__ for integration in sentry_init.call_args.kwargs['integrations']} == {
        'CeleryIntegration',
        'DjangoIntegration',
    }
