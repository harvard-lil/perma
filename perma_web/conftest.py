import pytest
import boto3
from dataclasses import dataclass
import os
import subprocess
from django.conf import settings
from django.core.management import call_command
from django.urls import reverse


# patch Playwright's screenshot method so that we get full-page screenshots
# when functional tests fail, which is not presently configurable in pytest-playwright
# https://github.com/microsoft/playwright-pytest/blob/456f8286f09f132d2e21f6bf71f27465e71ba17a/pytest_playwright/pytest_playwright.py#L249
from playwright.sync_api import Page
_orig = Page.screenshot
def full_page_screenshot(*args, **kwargs):
    kwargs['full_page'] = True
    return _orig(*args, **kwargs)
Page.screenshot = full_page_screenshot


# Allow setup of live server test cases; see https://github.com/microsoft/playwright-python/issues/439
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


# shadow this fixture from  pytest_django_liveserver_ssl so that it doesn't request the admin client (which doesn't work with our fixture situation)
@pytest.fixture()
def live_server_ssl_clients_for_patch(client):
    return [client]


@pytest.fixture(scope="session")
def set_up_certs():
    certs = [
        ('mkcert ca root', f'{settings.PROJECT_ROOT}/rootCA.pem'),
        ('perma certs', f'{settings.PROJECT_ROOT}/perma-test.crt'),
        ('minio cert', '/tmp/minio_ssl/public.crt'),
        ('wacz-exhibitor cert', '/tmp/wacz-exhibitor_ssl/public.crt'),
    ]

    for cert in certs:
        completed = subprocess.run(
            f'certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n "{cert[0]}" -i {cert[1]}',
            shell=True,
            capture_output=True,
            text=True
        )
        if completed.returncode != 0:
            print(completed.stderr)
            raise Exception('Cert installation failed.')


@pytest.fixture(scope="session")
def live_server_ssl_cert(set_up_certs):
    return {
        'crt': f'{settings.PROJECT_ROOT}/perma-test.crt',
        'key': f'{settings.PROJECT_ROOT}/perma-test.key'
    }


def _load_json_fixtures():
    call_command('loaddata', *[
        'fixtures/users.json',
        'fixtures/api_keys.json',
        'fixtures/folders.json',
        'fixtures/archive.json',
        'fixtures/mirrors.json'
    ])


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        _load_json_fixtures()


@pytest.fixture(autouse=True, scope='function')
def _live_server_db_helper(request):
    """
    When using the live_server fixture, the DB is flushed between tests:
    load the fixtures for each test.

    See https://github.com/pytest-dev/pytest-django/blob/fba51531f067a985ec6b6be4aec9a2ed5766d69c/pytest_django/fixtures.py#L545
    and https://stackoverflow.com/questions/52561816/pytest-django-add-fixtures-to-live-server-fixture
    """
    if "live_server_ssl" not in request.fixturenames:
        return
    _load_json_fixtures()


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


URL_MAP = {
    'homepage': reverse('landing'),
    'login': reverse('user_management_limited_login'),
    'about': reverse('about'),
    'contact': reverse('contact'),
    'folders': reverse('create_link'),
}


class URLs:
    def __init__(self, base_url):
        for name, url in URL_MAP.items():
            setattr(self, name, base_url + url)


@pytest.fixture
def urls(transactional_db, live_server_ssl):
    return URLs(f'https://{settings.HOST}')


@dataclass
class User:
    username: str
    password: str


@pytest.fixture
def user() -> User:
    return User("functional_test_user@example.com", "pass")


# TODO: if this login fails, the fixture should error out,
# and it's weird that a fixture called "logged in user" returns a page object
@pytest.fixture
def logged_in_user(page, urls, user):
    """Actually log in the desired user"""
    page.goto(urls.login)
    username = page.locator('#id_username')
    username.focus()
    username.type(user.username)
    password = page.locator('#id_password')
    password.focus()
    password.type(user.password)
    page.locator("button.btn.login").click()
    return page


###              ###
### New Fixtures ###
###              ###

# As we modernize the test suite, we can start putting new fixtures here.
# The separation should make it easier to work out, going forward, what can be deleted.

import factory
from factory.django import DjangoModelFactory
import humps

from datetime import timezone as tz
from django.db.models import signals

from perma.models import LinkUser, Link, CaptureJob


### internal helpers ###

# functions used within this file to set up fixtures

def register_factory(cls):
    """
    Decorator to take a factory class and inject test fixtures. For example,
        @register_factory
        class UserFactory
    will inject the fixtures "user_factory" (equivalent to UserFactory) and "user" (equivalent to UserFactory()).
    This is basically the same as the @register decorator provided by the pytest_factoryboy package,
    but because it's simpler it seems to work better with RelatedFactory and SubFactory.
    """
    snake_case_name = humps.decamelize(cls.__name__)

    @pytest.fixture
    def factory_fixture(db):
        return cls

    @pytest.fixture
    def instance_fixture(db):
        return cls()

    globals()[snake_case_name] = factory_fixture
    globals()[snake_case_name.rsplit('_factory', 1)[0]] = instance_fixture

    return cls


### model factories ###

@register_factory
class LinkUserFactory(DjangoModelFactory):
    class Meta:
        model = LinkUser

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Sequence(lambda n: 'user%s@example.com' % n)
    is_active = True
    is_confirmed=True

    password = factory.PostGenerationMethodCall('set_password', 'pass')


@register_factory
class CaptureJobFactory(DjangoModelFactory):
    class Meta:
        model = CaptureJob
        exclude = ('create_link',)

    created_by = factory.SubFactory(LinkUserFactory)
    submitted_url = factory.Faker('url')

    create_link = True
    link = factory.Maybe(
        'create_link',
        yes_declaration=factory.RelatedFactory(
            'conftest.LinkFactory',
            factory_related_name='capture_job',
            create_pending_capture_job=False,
            created_by=factory.SelfAttribute('..created_by'),
            submitted_url=factory.SelfAttribute('..submitted_url'),
        ),
        no_declaration=None
    )


@register_factory
class InvalidCaptureJobFactory(CaptureJobFactory):
    submitted_url = 'not-a-valid-url'
    status = 'invalid'
    message = {'url': ['Not a valid URL.']}
    create_link = False


@register_factory
class PendingCaptureJobFactory(CaptureJobFactory):
    status = 'pending'


@register_factory
class InProgressCaptureJobFactory(PendingCaptureJobFactory):
    status = 'in_progress'
    capture_start_time = factory.Faker('future_datetime', end_date='+1m', tzinfo=tz.utc)
    step_count = factory.Faker('pyfloat', min_value=1, max_value=10)
    step_description = factory.Faker('text', max_nb_chars=15)


@register_factory
@factory.django.mute_signals(signals.pre_save)
class LinkFactory(DjangoModelFactory):
    class Meta:
        model = Link
        exclude = ('create_pending_capture_job', 'created_by')

    created_by = factory.SubFactory(LinkUserFactory)
    submitted_url = factory.Faker('url')

    create_pending_capture_job = True
    capture_job = factory.Maybe(
        'create_pending_capture_job',
        yes_declaration=factory.SubFactory(
            PendingCaptureJobFactory,
            created_by=factory.SelfAttribute('..created_by'),
            submitted_url=factory.SelfAttribute('..submitted_url'),
            create_link=False
        ),
        no_declaration=None
    )
