from bs4 import BeautifulSoup
from urllib.parse import urlencode

from django.core import mail
from django.test import override_settings
from django.urls import reverse

from conftest import submit_form
import pytest

###
###   Does the contact form render as expected?
###

def test_contact_blank_when_logged_out(client):
    '''
        Check correct fields are blank for logged out user
    '''
    response = client.get(
        reverse('contact'),
        secure=True
    )
    soup = BeautifulSoup(response.content, 'html.parser')
    inputs = soup.select('input')
    assert len(inputs) == 4
    for input in inputs:
        assert input['name'] in ['csrfmiddlewaretoken', 'referer', 'email', 'subject']
        if input['name'] == 'csrfmiddlewaretoken':
            assert input.get('value', '')
        else:
            assert not input.get('value', '')
    textareas = soup.select('textarea')
    assert len(textareas) == 2
    for textarea in textareas:
        assert textarea['name'] in ['telephone', 'box2']
        assert textarea.text.strip() == ""


def test_contact_blank_regular(client, link_user):
    '''
        Check correct fields are blank for regular user
    '''
    client.force_login(link_user)
    response = client.get(
        reverse('contact'),
        secure=True
    )
    soup = BeautifulSoup(response.content, 'html.parser')
    inputs = soup.select('input')
    # Two csrf inputs: one by logout button, one in this form
    assert len(inputs) == 4 + 1
    for input in inputs:
        assert input['name'] in['csrfmiddlewaretoken', 'referer', 'email', 'subject']
        if input['name'] in ['csrfmiddlewaretoken', 'email']:
            assert input.get('value', '')
        else:
            assert not input.get('value', '')
    textareas = soup.select('textarea')
    assert len(textareas) == 2
    for textarea in textareas:
        assert textarea['name'] in ['telephone', 'box2']
        assert textarea.text.strip() == ""


def test_contact_blank_registrar(client, registrar_user):
    '''
        Check correct fields are blank for registrar user
    '''
    client.force_login(registrar_user)
    response = client.get(
        reverse('contact'),
        secure=True
    )
    soup = BeautifulSoup(response.content, 'html.parser')
    inputs = soup.select('input')
    # Two csrf inputs: one by logout button, one in this form
    assert len(inputs) == 4 + 1
    for input in inputs:
        assert input['name'] in ['csrfmiddlewaretoken', 'referer', 'email', 'subject']
        if input['name'] in ['csrfmiddlewaretoken', 'email']:
            assert input.get('value', '')
        else:
            assert not input.get('value', '')
    textareas = soup.select('textarea')
    assert len(textareas) == 2
    for textarea in textareas:
        assert textarea['name'] in ['telephone', 'box2']
        assert textarea.text.strip() == ""


def test_contact_blank_single_reg_org_user(client, org_user):
    '''
        Check correct fields are blank for a single-registrar org user
    '''
    client.force_login(org_user)
    response = client.get(
        reverse('contact'),
        secure=True
    )
    soup = BeautifulSoup(response.content, 'html.parser')
    inputs = soup.select('input')
    # Two csrf inputs: one by logout button, one in this form
    assert len(inputs) == 5 + 1
    for input in inputs:
        assert input['name'] in ['csrfmiddlewaretoken', 'referer', 'email', 'subject', 'registrar']
        if input['name'] in ['csrfmiddlewaretoken', 'email', 'registrar']:
            assert input.get('value', '')
        else:
            assert not input.get('value', '')
    textareas = soup.select('textarea')
    assert len(textareas) == 2
    for textarea in textareas:
        assert textarea['name'] in ['telephone', 'box2']
        assert textarea.text.strip() == ""


def test_contact_blank_multi_reg_org_user(client, multi_registrar_org_user):
    '''
        Check correct fields are blank for a multi-registrar org user
    '''
    client.force_login(multi_registrar_org_user)
    response = client.get(
        reverse('contact'),
        secure=True
    )
    soup = BeautifulSoup(response.content, 'html.parser')
    inputs = soup.select('input')
    # Two csrf inputs: one by logout button, one in this form
    assert len(inputs) == 4 + 1
    for input in inputs:
        assert input['name'] in ['csrfmiddlewaretoken', 'referer', 'email', 'subject']
        if input['name'] in ['csrfmiddlewaretoken', 'email']:
            assert input.get('value', '')
        else:
            assert not input.get('value', '')
    textareas = soup.select('textarea')
    assert len(textareas) == 2
    for textarea in textareas:
        assert textarea['name'] in ['telephone', 'box2']
        assert textarea.text.strip() == ""
    selects = soup.select('select')
    assert len(selects) == 1
    for select in selects:
        assert select['name'] in ['registrar']
        assert len(select.find_all("option")) >= 2


@pytest.mark.parametrize(
    "user",
    [
        None,
        "link_user",
        "org_user",
        "multi_registrar_org_user",
        "registrar_user"

    ]
)
def test_contact_params_regular(user, client, email_details, request):
    '''
        Check subject line, message, read in from GET params
    '''
    query_params = {
        'message': email_details["message_text"],
        'subject': email_details["custom_subject"]
    }

    if user:
        client.force_login(request.getfixturevalue(user))

    response = client.get(
        reverse('contact') + f'?{urlencode(query_params)}',
        secure=True,

    )
    soup = BeautifulSoup(response.content, 'html.parser')
    subject_field = soup.find('input', {'name': 'subject'})
    assert subject_field.get('value', '') == email_details["custom_subject"]
    message_field = soup.find('textarea', {'name': 'box2'})
    assert message_field.text.strip() == email_details["message_text"]


###
###   Does the contact form submit as expected?
###


@override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
def test_contact_standard_submit_fail(client):
    '''
        Blank submission should fail and, for most users, request
        email address and message.
        We should get the contact page back.
    '''
    response = submit_form(
        client,
        'contact',
        data = { 'email': '',
              'box2': '' },
        error_keys = ['email', 'box2']
    )
    assert response.request['PATH_INFO'] == reverse('contact')


@override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
def test_contact_org_user_submit_fail(client, org_user):
    '''
        Org users are special. Blank submission should fail
        and request email address, message, and registrar.
        We should get the contact page back.
    '''
    client.force_login(org_user)
    response = submit_form(
        client,
        'contact',
        data = { 'email': '', 'box2': '' },
        error_keys = ['email', 'box2', 'registrar']
    )
    assert response.request['PATH_INFO'] == reverse('contact')


@override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
def test_contact_standard_submit_required(client, email_details):
    '''
        All fields, including custom subject and referer
    '''
    submit_form(
        client,
        'contact',
        data = { 'email': email_details["from_email"],
               'box2': email_details["message_text"],
               'subject': email_details["custom_subject"],
               'referer': email_details["refering_page"] },
        success_url=reverse('contact_thanks')
    )

    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert email_details["message_text"] in message.body
    assert "Referring Page: " + email_details["refering_page"] in message.body
    assert "Affiliations: (none)" in message.body
    assert "Logged in: false" in message.body
    assert message.subject.startswith(email_details["subject_prefix"] + email_details["custom_subject"])
    assert message.from_email == email_details["our_address"]
    assert message.recipients() == [email_details["our_address"]]
    assert message.extra_headers == {'Reply-To': email_details["from_email"]}


@override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
def test_contact_standard_submit_required_with_spam_catcher(client, email_details):
    '''
        All fields, including custom subject and referer
    '''
    submit_form(
        client,
        'contact',
        data = { 'email': email_details["from_email"],
               'telephone': "I'm a bot",
               'box2': email_details["message_text"],
               'subject': email_details["custom_subject"],
               'referer': email_details["refering_page"] },
        success_url=reverse('contact_thanks')
    )
    assert len(mail.outbox) == 0


@override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
def test_contact_standard_submit_no_optional(client, email_details):
    '''
        All fields except custom subject and referer
    '''
    submit_form(
        client,
        'contact',
        data = { 'email': email_details["from_email"],
               'box2': email_details["message_text"] },
        success_url=reverse('contact_thanks')
    )
    len(mail.outbox) == 1
    message = mail.outbox[0]
    assert email_details["message_text"] in message.body
    assert "Referring Page: " in message.body
    assert "Affiliations: (none)" in message.body
    assert "Logged in: false" in message.body
    assert message.subject.startswith(email_details["subject_prefix"] + 'New message from Perma contact form')
    assert message.from_email, email_details["our_address"]
    assert message.recipients() == [email_details["our_address"]]
    assert message.extra_headers == {'Reply-To': email_details["from_email"]}


@override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
def test_contact_org_user_submit_invalid(client, org_user, email_details):
    '''
        Org users get extra fields. Registrar must be a valid choice.
        We should get the contact page back.
    '''
    client.force_login(org_user)
    response =submit_form(
        client,
        'contact',
        data = { 'email': email_details["from_email"],
              'box2': email_details["message_text"],
              'registrar': 'not_a_licit_registrar_id'},
        error_keys = ['registrar']
    )
    assert response.request['PATH_INFO'] == reverse('contact')


@override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
def test_contact_org_user_submit(client, multi_registrar_org_user, email_details):
    '''
        Should be sent to registrar users.
    '''
    target_registrar = multi_registrar_org_user.organizations.first().registrar
    registrar_users = target_registrar.active_registrar_users()

    success = reverse('contact_thanks') + "?{}".format(urlencode({'registrar': target_registrar.id}))

    client.force_login(multi_registrar_org_user)
    submit_form(
        client,
        'contact',
        data = { 'email': email_details["from_email"],
               'box2': email_details["message_text"],
               'registrar': target_registrar.id },
        success_url=success
    )
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert email_details["message_text"] in message.body
    assert "Logged in: true" in message.body
    assert message.from_email == email_details["our_address"]
    assert message.to == [user.email for user in registrar_users]
    assert message.cc == [email_details["our_address"], email_details["from_email"]]
    assert message.reply_to == [email_details["from_email"]]


@override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
def test_contact_org_user_affiliation_string(client, multi_registrar_org_user, email_details):
    '''
        Verify org affiliations are printed correctly
    '''
    client.force_login(multi_registrar_org_user)
    submit_form(
        client,
        'contact',
        data = { 'email': email_details["from_email"],
               'box2': email_details["message_text"],
               'registrar': multi_registrar_org_user.organizations.first().registrar.id },
    )
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    for org in multi_registrar_org_user.organizations.all():
        assert f"{org.name} ({org.registrar.name})" in message.body
    assert "Logged in: true" in message.body


@override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
def test_contact_reg_user_affiliation_string(client, registrar_user, email_details):
    '''
        Verify registrar affiliations are printed correctly
    '''
    client.force_login(registrar_user)
    submit_form(
        client,
        'contact',
        data = { 'email': email_details["from_email"],
                 'box2': email_details["message_text"] },
    )
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert f"Affiliations: {registrar_user.registrar.name} (Registrar)" in message.body
    assert "Logged in: true" in message.body


@override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
def test_contact_sponsored_user_affiliation_string(client, sponsored_user, email_details):
    '''
        Verify registrar affiliations are printed correctly
    '''
    registrar = sponsored_user.sponsorships.first().registrar
    client.force_login(sponsored_user)
    submit_form(
        client,
        'contact',
        data = {'email': email_details["from_email"],
                'box2': email_details["message_text"],
                'registrar': registrar.id },
    )
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert f"Affiliations: {registrar.name}" in message.body
    assert "Logged in: true" in message.body


#
# Report form, as a bot
#

def test_report_with_no_guid_renders(client):
    response = client.get(
        reverse('report'),
        secure=True
    )
    assert b"Report Inappropriate Content"in response.content


@override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
def test_report_empty_post(client):
    submit_form(
        client,
        'report',
        data = {},
        error_keys = [
            'reason',
            'source',
            'email'
        ]
    )


@override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
def test_report_post_with_spam_catcher1(client):
    submit_form(
        client,
        'report',
        data = {
            'reason': "",
            'source': "",
            'email': "",
            'telephone': "I'm a bot",
            'guid': "AAAA-AAAA"
        },
        success_url=reverse('contact_thanks')
    )
    assert len(mail.outbox) == 0


@override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
def test_report_post_with_spam_catcher2(client):
    submit_form(
        client,
        'report',
        data = {
            'reason': 'Graphic or Dangerous Content',
            'source': 'Somewhere online',
            'email': 'me@me.com',
        },
        success_url=reverse('contact_thanks')
    )
    assert len(mail.outbox) == 0

#
# Report form, as a person
#

@override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
def test_report_post_with_basic_fields(client):
    submit_form(
        client,
        'report',
        data = {
            'reason': 'Graphic or Dangerous Content',
            'source': 'Somewhere online',
            'email': 'me@me.com',
            'guid': 'some-string-that-could-be-a-guid'
        },
        success_url=reverse('contact_thanks')
    )
    [message] = mail.outbox
    assert f"https://testserver{ reverse('admin:perma_link_changelist') }?guid=some-string-that-could-be-a-guid" in message.body
    assert 'Graphic or Dangerous Content' in message.body
    assert 'Somewhere online' in message.body
    assert 'me@me.com' in message.body
    assert 'some-string-that-could-be-a-guid' in message.body
    assert "Logged in: false" in message.body


@override_settings(REQUIRE_JS_FORM_SUBMISSIONS=False)
def test_report_email_prepopulated_for_logged_in_user(client, link_user):
    client.force_login(link_user)
    response = client.get(
        reverse('report'),
        secure=True
    )
    soup = BeautifulSoup(response.content, 'html.parser')
    [email] = soup.select('input[name="email"]')
    assert email['value'] == link_user.email
