import pytest
import boto3
from django.conf import settings
from django.core.management import call_command

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', *[
            'fixtures/users.json',
            'fixtures/api_keys.json',
            'fixtures/folders.json',
            'fixtures/archive.json',
            'fixtures/mirrors.json'
        ])

### non-model fixtures ###

@pytest.fixture(autouse=True, scope='function')
def cleanup_storage():
    """
    Empty the configured storage after each test, so that it's fresh each time.
    """
    yield
    storage = boto3.resource(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        verify=False
    ).Bucket(settings.AWS_STORAGE_BUCKET_NAME)
    storage.objects.delete()
