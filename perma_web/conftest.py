import pytest
import boto3
from dataclasses import dataclass
import os
from random import choice
import subprocess
from waffle import get_waffle_flag_model

from django.conf import settings
from django.core.management import call_command
from django.core.serializers.json import DjangoJSONEncoder
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


# patch django-liveserver-ssl to be compatible with changes made to the LiveTestServer in Django 4.2
# https://github.com/django/django/commit/823a9e6bac38d38f7b0347497b833eec732bd384
from pytest_django_liveserver_ssl.live_server_ssl_helper import HTTPSLiveServerThread, SecureHTTPServer, WSGIRequestHandler
def _create_server(self, connections_override=None):
    return SecureHTTPServer(
        (self.host, self.port),
        WSGIRequestHandler,
        allow_reuse_address=False,
        connections_override=connections_override,
        certificate=self.certificate_file,
        key=self.key_file,
    )
HTTPSLiveServerThread._create_server = _create_server


@pytest.fixture(scope="session")
def set_up_certs():
    certs = [
        ('mkcert ca root', f'{settings.PROJECT_ROOT}/rootCA.pem'),
        ('perma certs', f'{settings.PROJECT_ROOT}/perma-test.crt'),
        ('minio cert', '/tmp/minio_ssl/public.crt')
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
        'fixtures/archive.json'
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
    for storage_option in ['default', 'secondary']:
        storage = boto3.resource(
            's3',
            endpoint_url=settings.STORAGES[storage_option]["OPTIONS"]["endpoint_url"],
            aws_access_key_id=settings.STORAGES[storage_option]["OPTIONS"]["access_key"],
            aws_secret_access_key=settings.STORAGES[storage_option]["OPTIONS"]["secret_key"],
            verify=False
        ).Bucket(settings.STORAGES[storage_option]["OPTIONS"]["bucket_name"])
        storage.objects.delete()


URL_MAP = {
    'homepage': reverse('landing'),
    'login': reverse('user_management_limited_login'),
    'about': reverse('about'),
    'contact': reverse('contact'),
    'folders': reverse('create_link'),
    'bookmarklet': reverse('service_bookmarklet_create'),
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


@pytest.fixture
def wacz_user() -> User:
    """For this user, the 'wacz-playback' flag is True"""
    u = LinkUser.objects.get(email="wacz_functional_test_user@example.com")
    flag, _created = get_waffle_flag_model().objects.get_or_create(name="wacz-playback")
    flag.users.add(u.id)
    return User(u.email, "pass")


@pytest.fixture
def log_in_user(urls):
    """A utility to log in the desired user"""
    # TODO: if this login fails, the fixture should error out
    def f(page, user):
        page.goto(urls.login)
        username = page.locator('#id_username')
        username.focus()
        username.type(user.username)
        password = page.locator('#id_password')
        password.focus()
        password.type(user.password)
        page.locator("button.btn.login").click()
    return f


###              ###
### New Fixtures ###
###              ###

# As we modernize the test suite, we can start putting new fixtures here.
# The separation should make it easier to work out, going forward, what can be deleted.

import factory
from factory.django import DjangoModelFactory, Password
import humps

from decimal import Decimal
from datetime import datetime, timezone as tz
from dateutil.relativedelta import relativedelta
from django.utils import timezone

from perma.models import Registrar, Organization, LinkUser, Link, CaptureJob, Capture, Sponsorship, Folder
from perma.utils import pp_date_from_post


GENESIS = datetime.fromtimestamp(0).replace(tzinfo=tz.utc)
# this gives us a variable that we can use unhashed in tests
TEST_USER_PASSWORD = 'pass'

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

###
### Model Factories ###
###

@register_factory
class RegistrarFactory(DjangoModelFactory):
    class Meta:
        model = Registrar

    name = factory.Faker('company')
    email = factory.Faker('company_email')
    website = factory.Faker('url')

    # Default to "approved" in the fixtures for convenience
    status = 'approved'

    organizations = factory.RelatedFactoryList(
        'conftest.OrganizationFactory',
        size=1,
        factory_related_name='registrar'
    )


@register_factory
class PendingRegistrarFactory(RegistrarFactory):
    status = 'pending'


@register_factory
class DeniedRegistrarFactory(RegistrarFactory):
    status = 'denied'


@register_factory
class NonpayingRegistrarFactory(RegistrarFactory):
    pass


@register_factory
class PayingRegistrarFactory(RegistrarFactory):
    nonpaying = False
    cached_subscription_status = "Sentinel Status"
    cached_paid_through = GENESIS
    base_rate = Decimal(100.00)
    in_trial = False


@register_factory
class PayingLimitedRegistrarFactory(PayingRegistrarFactory):
    unlimited = False


@register_factory
class OrganizationFactory(DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Faker('company')
    registrar = factory.SubFactory(RegistrarFactory)


@register_factory
class LinkUserFactory(DjangoModelFactory):
    class Meta:
        model = LinkUser

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Sequence(lambda n: 'user%s@example.com' % n)

    # Default to confirmed and active in the fixtures for convenience
    is_active = True
    is_confirmed = True

    password = Password(TEST_USER_PASSWORD)


@register_factory
class DeactivatedUserFactory(LinkUserFactory):
    is_active = False


@register_factory
class UnactivatedUserFactory(LinkUserFactory):
    is_active = False
    is_confirmed = False


@register_factory
class RegistrarUserFactory(LinkUserFactory):
    registrar = factory.SubFactory(RegistrarFactory)


# SponsorshipFactory has to come after RegistrarUserFactory and LinkUserFactory,
# and before SponsoredUserFactory
@register_factory
class SponsorshipFactory(DjangoModelFactory):
    class Meta:
        model = Sponsorship

    user = factory.SubFactory(LinkUserFactory)
    registrar = factory.SubFactory(RegistrarFactory)
    created_by = factory.SubFactory(
        RegistrarUserFactory,
        registrar=factory.SelfAttribute('..registrar')
    )


@register_factory
class SponsoredUserFactory(LinkUserFactory):

    sponsorships = factory.RelatedFactoryList(
        SponsorshipFactory,
        size=1,
        factory_related_name='user'
    )


@register_factory
class NonpayingUserFactory(LinkUserFactory):
    nonpaying = True


@register_factory
class PayingUserFactory(LinkUserFactory):
    nonpaying = False
    cached_subscription_status = "Sentinel Status"
    cached_paid_through = GENESIS
    cached_subscription_rate = Decimal(0.01)
    base_rate = Decimal(100.00)
    in_trial = False


@register_factory
class CaptureJobFactory(DjangoModelFactory):
    class Meta:
        model = CaptureJob
        exclude = ('create_link', 'link_can_play_back')
        skip_postgeneration_save=True

    created_by = factory.SubFactory(LinkUserFactory)
    submitted_url = factory.Faker('url')

    create_link = True
    link_can_play_back = None
    link = factory.Maybe(
        'create_link',
        yes_declaration=factory.RelatedFactory(
            'conftest.LinkFactory',
            factory_related_name='capture_job',
            created_by=factory.SelfAttribute('..created_by'),
            submitted_url=factory.SelfAttribute('..submitted_url'),
            cached_can_play_back=factory.SelfAttribute('..link_can_play_back'),
            warc_size=factory.Maybe(
                'cached_can_play_back',
                yes_declaration=factory.Faker('random_int'),
                no_declaration=None
            )
        ),
        no_declaration=None
    )
    # Required to update CaptureJob.link_id from None, after the Link is generated
    _ = factory.PostGenerationMethodCall("save")


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
class CompletedCaptureJobFactory(InProgressCaptureJobFactory):
    status = 'completed'
    capture_start_time = factory.Faker('past_datetime', tzinfo=tz.utc)
    capture_end_time = factory.LazyAttribute(lambda o: o.capture_start_time + relativedelta(minutes=1))
    link_can_play_back = True


@register_factory
class LinkFactory(DjangoModelFactory):
    class Meta:
        model = Link

    created_by = factory.SubFactory(LinkUserFactory)
    submitted_url = factory.Faker('url')
    cached_can_play_back = None


@register_factory
class CaptureFactory(DjangoModelFactory):
    class Meta:
        model = Capture


@register_factory
class PrimaryCaptureFactory(CaptureFactory):
    role = 'primary'
    status = 'success'
    record_type = 'response'
    content_type = 'text/html'


@register_factory
class ScreenshotCaptureFactory(CaptureFactory):
    role = 'screenshot'
    status = 'success'
    record_type = 'response'
    content_type = 'image/png'

    url = "file:///screenshot.png"


@register_factory
class FolderFactory(DjangoModelFactory):
    class Meta:
        model = Folder


@register_factory
class SponsoredFolderFactory(FolderFactory):
    sponsored_by = factory.SubFactory(RegistrarFactory)

#
# Fixtures
#

# For working with users

@pytest.fixture
def perma_client():
    """
    A version of the Django test client that allows us to specify a user login for a particular request with an
    `as_user` parameter, like `client.get(url, as_user=user).
    """
    from django.test.client import Client

    session_key = settings.SESSION_COOKIE_NAME

    class UserClient(Client):
        def generic(self, *args, **kwargs):
            as_user = kwargs.pop("as_user", None)
            kwargs['secure'] = True

            if as_user:
                # If as_user is provided, store the current value of the session cookie, call force_login, and then
                # reset the current value after the request is over.
                previous_session = self.cookies.get(session_key)
                self.force_login(as_user)
                try:
                    return super().generic(*args, **kwargs)
                finally:
                    if previous_session:
                        self.cookies[session_key] = previous_session
                    else:
                        self.cookies.pop(session_key)
            else:
                return super().generic(*args, **kwargs)

    return UserClient()


@pytest.fixture
def admin_user(link_user_factory):
    return link_user_factory(is_staff=True)


@pytest.fixture
def org_user_factory(link_user, organization):
    def f(orgs=None):
        if orgs:
            link_user.organizations.set(orgs)
        else:
            link_user.organizations.add(organization)
        return link_user
    return f


@pytest.fixture
def org_user(org_user_factory):
    return org_user_factory()

@pytest.fixture
def multi_registrar_org_user(org_user_factory, organization_factory):
    first = organization_factory()
    second = organization_factory()
    assert first.registrar != second.registrar
    return org_user_factory(orgs=[first, second])


### For testing customer interactions

@pytest.fixture
def customers(paying_registrar_factory, paying_user_factory):
    return [
        paying_registrar_factory(),
        paying_user_factory()
    ]


@pytest.fixture
def noncustomers(nonpaying_registrar_factory, nonpaying_user_factory):
    return [
        nonpaying_registrar_factory(),
        nonpaying_user_factory()
    ]


@pytest.fixture
def user_with_links(link_user, link_factory):
    # a user with 6 personal links, made at intervals
    today = timezone.now()
    earlier_this_month = today.replace(day=1)
    within_the_last_year = today - relativedelta(months=6)
    over_a_year_ago = today - relativedelta(years=1, days=2)
    three_years_ago = today - relativedelta(years=3)

    link_factory(creation_timestamp=today, created_by=link_user)
    link_factory(creation_timestamp=earlier_this_month, created_by=link_user)
    link_factory(creation_timestamp=within_the_last_year, created_by=link_user)
    link_factory(creation_timestamp=over_a_year_ago, created_by=link_user)
    link_factory(creation_timestamp=three_years_ago, created_by=link_user)

    return link_user


@pytest.fixture
def user_with_links_this_month_before_the_15th(link_user, link_factory):
    # for use in testing mid-month link count limits
    link_factory(creation_timestamp=timezone.now().replace(day=1), created_by=link_user)
    link_factory(creation_timestamp=timezone.now().replace(day=2), created_by=link_user)
    link_factory(creation_timestamp=timezone.now().replace(day=3), created_by=link_user)
    link_factory(creation_timestamp=timezone.now().replace(day=4), created_by=link_user)
    link_factory(creation_timestamp=timezone.now().replace(day=14), created_by=link_user)

    return link_user


@pytest.fixture
def complex_user_with_bonus_link(link_user_factory, folder_factory,
                                 organization, registrar, sponsorship_factory, link_factory):
    user = link_user_factory(link_limit=2, bonus_links=0)
    user.organizations.add(organization)
    registrar_user = RegistrarUserFactory(registrar=registrar)
    sponsorship_factory(registrar=registrar, user=user, created_by=registrar_user)
    folder_factory(parent=user.top_level_folders()[0], name='Subfolder')
    bonus_link = link_factory(created_by=user, bonus_link=True)
    user.refresh_from_db()
    return user, bonus_link


@pytest.fixture
def active_cancelled_subscription():
    return {
        'status': "Canceled",
        'paid_through': timezone.now() + relativedelta(years=1)
    }


@pytest.fixture
def expired_cancelled_subscription():
    return {
        'status': "Canceled",
        'paid_through': timezone.now() + relativedelta(years=-1)
    }


@pytest.fixture
def spoof_pp_response_wrong_pk():
    def f(customer):
        data = {
            "customer_pk": "not_the_pk",
            "customer_type": customer.customer_type
        }
        assert customer.pk != data['customer_pk']
        return data
    return f


@pytest.fixture
def spoof_pp_response_wrong_type():
    def f(customer):
        data = {
            "customer_pk": customer.pk,
            "customer_type": "not_the_type"
        }
        assert customer.customer_type != data['customer_type']
        return data
    return f


@pytest.fixture
def spoof_pp_response_no_subscription():
    def f(customer):
        return {
            "customer_pk": customer.pk,
            "customer_type": customer.customer_type,
            "subscription": None,
            "purchases": []
        }
    return f


@pytest.fixture
def spoof_pp_response_no_subscription_two_purchases():
    def f(customer):
        return {
            "customer_pk": customer.pk,
            "customer_type": customer.customer_type,
            "subscription": None,
            "purchases": [{
                "id": 1,
                "link_quantity": "10"
            },{
                "id": 2,
                "link_quantity": "50"
            }]
        }
    return f


@pytest.fixture
def spoof_pp_response_subscription():
    def f(customer):
        return {
            "customer_pk": customer.pk,
            "customer_type": customer.customer_type,
            "subscription": {
                "status": "Sentinel Status",
                "rate": "9999.99",
                "frequency": "sample",
                "paid_through": "1970-01-21T00:00:00.000000Z",
                "link_limit_effective_timestamp": "1970-01-21T00:00:00.000000Z",
                "link_limit": "unlimited",
                "reference_number": "PERMA-1237-6200"
            },
            "purchases": []
        }
    return f


@pytest.fixture
def spoof_pp_response_subscription_with_pending_change():
    def f(customer):
        response = {
            "customer_pk": customer.pk,
            "customer_type": customer.customer_type,
            "subscription": {
                "status": "Sentinel Status",
                "rate": "9999.99",
                "frequency": "sample",
                "paid_through": "9999-01-21T00:00:00.000000Z",
                "link_limit_effective_timestamp": "9999-01-21T00:00:00.000000Z",
                "link_limit": "unlimited",
                "reference_number": "PERMA-1237-6201"
            },
            "purchases": []
        }
        assert pp_date_from_post(response['subscription']['link_limit_effective_timestamp']), timezone.now()
        return response
    return f


### For working with links ###

@pytest.fixture
def complete_link_factory(completed_capture_job_factory, primary_capture_factory, screenshot_capture_factory):
    def f(link_kwargs=None, primary_capture=True, screenshot_capture=True):
        if link_kwargs:
            link = completed_capture_job_factory(**{
                f"link__{k}": v
                for k, v in link_kwargs.items()
            }).link
        else:
            link = completed_capture_job_factory().link

        if primary_capture:
            primary_capture_factory(link=link, url=link.submitted_url)
        if screenshot_capture:
            screenshot_capture_factory(link=link)

        return link
    return f


@pytest.fixture
def complete_link(complete_link_factory):
    return complete_link_factory()


@pytest.fixture
def complete_link_without_capture_job(complete_link):
    complete_link.capture_job.delete()
    try:
        complete_link.capture_job
    except CaptureJob.DoesNotExist:
        pass
    return complete_link


@pytest.fixture
def deleted_link(complete_link_factory):
    link = complete_link_factory({
        "cached_can_play_back": False
    })
    link.safe_delete()
    link.save()
    return link


@pytest.fixture
def deleted_capture_job(deleted_link):
    # Capture Jobs are marked as 'deleted' if a user deletes that GUID
    # before the capture job is finished
    job = deleted_link.capture_job
    job.status = 'deleted'
    job.save()
    return job


@pytest.fixture
def failed_capture_job(in_progress_capture_job):
    in_progress_capture_job.mark_failed("Something went wrong.")
    return in_progress_capture_job


@pytest.fixture
def memento_link_set(link_factory):
    domain="wikipedia.org"
    url = f"https://{domain}"

    today = timezone.now()
    a_few_days_ago = today - relativedelta(days=5)
    within_the_last_year = today - relativedelta(months=6)
    over_a_year_ago = today - relativedelta(years=1, days=2)
    three_years_ago = today - relativedelta(years=3)

    links = [
        link_factory(
            creation_timestamp=time,
            submitted_url=url,
            cached_can_play_back=True,
        ) for time in [today, a_few_days_ago, within_the_last_year, over_a_year_ago, three_years_ago]
    ]

    return {
        "domain": domain,
        "url": url,
        "links": [
            {
                "guid": link.guid,
                #
                "timestamp": link.creation_timestamp
            } for link in reversed(links)
        ]
    }


### For testing email ###

@pytest.fixture
def email_details():
    return {
        "from_email": 'example@example.com',
        "custom_subject": 'Just some subject here',
        "message_text": 'Just some message here.',
        "referring_page": 'http://elsewhere.com',
        "our_address": settings.DEFAULT_FROM_EMAIL,
        "subject_prefix": '[perma-contact] ',
        "flag": "zzzz-zzzz",
        "flag_message": "http://perma.cc/zzzz-zzzz contains material that is inappropriate.",
        "flag_subject": "Reporting Inappropriate Content"
    }


### For testing utils ###

@pytest.fixture
def spoof_perma_payments_post():
    data = {
        'encrypted_data': {"timestamp": 1504884268.560902, "desired_field": "desired_field"},
    }
    assert 'encrypted_data' in data
    assert 'timestamp' in data['encrypted_data']
    assert 'desired_field' in data['encrypted_data']
    return data


@pytest.fixture
def one_two_three_dict():
    data = {
        'one': 'one',
        'two': 'two',
        'three': 'three'
    }
    assert 'one' in data
    assert 'two' in data
    assert 'three' in data
    assert 'four' not in data
    return data


#
# Helpers
#

def randomize_capitalization(s):
    return ''.join(choice((str.upper, str.lower))(c) for c in s)

def json_serialize_datetime(dt):
    return DjangoJSONEncoder().encode(dt).strip('"')

def submit_form(client,
                view_name,
                data={},
                success_url=None,
                success_query=None,
                form_keys=['form'],  # name of form objects in RequestContext returned with response
                error_keys=[],  # keys that must appear in form error list
                *args, **kwargs):
    """
        Post to a view.
        success_url = url form should forward to after success
        success_query = query that should return one object if form worked
    """

    if success_query:
        assert success_query.count() != 1
    kwargs['require_status_code'] = None
    resp = client.post(
        reverse(view_name),
        data,
        *args,
        secure=True,
        **kwargs
    )

    def form_errors():
        errors = {}
        try:
            for form in form_keys:
                errors.update(resp.context[form]._errors)
        except (TypeError, KeyError):
            pass
        return errors

    if success_url:
        assert resp.status_code == 302, "Form failed to forward to success url. Status: %s. Content: %s. Errors: %s." % (resp.status_code, resp.content, form_errors())
        assert resp['Location'].endswith(success_url) is True, "Form failed to forward to %s. Instead forwarded to: %s." % (success_url, resp['Location'])

    if success_query:
        assert success_query.count() == 1

    if error_keys:
        keys = set(form_errors().keys())
        assert set(error_keys) == keys, "Error keys don't match expectations. Expected: %s. Found: %s" % (set(error_keys), keys)

    return resp
