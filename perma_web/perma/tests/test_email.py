from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.test import RequestFactory
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from perma.celery_tasks import send_user_email_from_bulk_addition
from perma.email import (
    STAFF_INVITED_CUSTOM_TEMPLATE,
    get_activation_email_context,
    registrar_users_plus_stats,
    send_staff_invited_new_user_email,
    send_signup_new_user_email,
    send_user_email_copy_admins,
)
from perma.models import LinkUser, Organization, Registrar


@pytest.fixture
def fixed_activation_token_time(monkeypatch):
    monkeypatch.setattr(
        default_token_generator,
        '_now',
        lambda: datetime(2026, 8, 29),
    )


def test_get_activation_email_context_with_request(
    link_user_factory, fixed_activation_token_time,
):
    user = link_user_factory()
    request = RequestFactory().get('/')
    context = get_activation_email_context(user, request=request)
    assert context['activation_expires'] == settings.PASSWORD_RESET_TIMEOUT
    expected_path = reverse(
        'password_reset_confirm',
        args=[
            urlsafe_base64_encode(force_bytes(user.pk)),
            default_token_generator.make_token(user),
        ],
    )
    assert context['activation_route'] == request.build_absolute_uri(expected_path)


def test_get_activation_email_context_with_host(
    link_user_factory, fixed_activation_token_time,
):
    user = link_user_factory()
    context = get_activation_email_context(user, host='https://perma.cc')
    assert context['activation_expires'] == settings.PASSWORD_RESET_TIMEOUT
    expected_path = reverse(
        'password_reset_confirm',
        args=[
            urlsafe_base64_encode(force_bytes(user.pk)),
            default_token_generator.make_token(user),
        ],
    )
    assert context['activation_route'] == f'https://perma.cc{expected_path}'


def test_get_activation_email_context_requires_request_or_host(link_user_factory):
    with pytest.raises(ValueError, match='request or host'):
        get_activation_email_context(link_user_factory())


def test_send_user_email_copy_admins(mailoutbox):
    send_user_email_copy_admins(
        "title",
        "from@example.com",
        ["to@example.com"],
        HttpRequest(),
        "email/default.txt",
        {"message": "test message"}
    )
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.from_email == settings.DEFAULT_FROM_EMAIL
    assert message.cc == [settings.DEFAULT_FROM_EMAIL, "from@example.com"]
    assert message.to == ["to@example.com"]
    assert message.reply_to == ["from@example.com"]


def test_registrar_users_plus_stats_specific_registrars(db):
    '''
        Returns data in the expected format.
    '''
    r_list = registrar_users_plus_stats(registrars=Registrar.objects.filter(email='library@university.edu'))
    assert isinstance(r_list, list)
    assert len(r_list) == 1
    assert r_list[0]['registrar_email'] == 'library@university.edu'


def test_send_signup_new_user_email_uses_default_template(link_user_factory, mailoutbox):
    user = link_user_factory()
    request = RequestFactory().get('/')
    send_signup_new_user_email(request, user)
    assert len(mailoutbox) == 1
    assert 'Thanks for signing up' in mailoutbox[0].body


@patch('perma.email.settings')
def test_send_staff_invited_new_user_email_without_registrar_uses_default(
    mock_settings, link_user_factory, mailoutbox,
):
    """Admin/regular staff invites omit registrar_id; CUSTOM_EMAILS_FOR_REGISTRAR is not read."""
    mock_settings.CUSTOM_EMAILS_FOR_REGISTRAR = MagicMock()
    user = link_user_factory()
    send_staff_invited_new_user_email(
        user,
        context={'requester_name': 'Staff Admin'},
        host='https://perma.cc',
    )
    mock_settings.CUSTOM_EMAILS_FOR_REGISTRAR.get.assert_not_called()
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == 'A Perma.cc account has been created for you'
    assert 'created for you by Staff Admin' in mailoutbox[0].body


def test_send_staff_invited_new_user_email_default_template(link_user_factory, registrar_factory, mailoutbox):
    user = link_user_factory()
    registrar = registrar_factory()
    request = RequestFactory().get('/')
    send_staff_invited_new_user_email(
        user,
        registrar_id=registrar.pk,
        context={'requester_name': 'Admin User', 'on_behalf_of': 'Test Org'},
        request=request,
    )
    assert len(mailoutbox) == 1
    assert 'created for you by Admin User' in mailoutbox[0].body
    assert 'on behalf of Test Org' in mailoutbox[0].body


def test_send_staff_invited_new_user_email_custom_template(
    link_user_factory, registrar_factory, mailoutbox, settings,
):
    user = link_user_factory()
    registrar = registrar_factory()
    settings.CUSTOM_EMAILS_FOR_REGISTRAR = {
        registrar.pk: {
            'template_file': STAFF_INVITED_CUSTOM_TEMPLATE,
            'subject': 'Custom Activation Subject',
            'opening': 'Custom opening from law firm.',
            'closing': 'Custom closing.',
        },
    }
    send_staff_invited_new_user_email(
        user,
        registrar_id=registrar.pk,
        host='https://perma.cc',
    )
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == 'Custom Activation Subject'
    assert 'Custom opening from law firm.' in message.body
    assert 'Custom closing.' in message.body
    assert 'https://perma.cc' in message.body


def test_send_user_email_from_bulk_addition_new_user_custom(
    link_user_factory, registrar_factory, mailoutbox, settings,
):
    user = link_user_factory()
    registrar = registrar_factory()
    settings.CUSTOM_EMAILS_FOR_REGISTRAR = {
        registrar.pk: {
            'subject': 'Bulk custom subject',
            'opening': 'Bulk custom opening.',
        },
    }
    send_user_email_from_bulk_addition(
        user.raw_email,
        {'requester_name': 'Staff'},
        host='https://perma.cc',
        is_new_user=True,
        registrar_id=registrar.pk,
    )
    assert mailoutbox[0].subject == 'Bulk custom subject'
    assert 'Bulk custom opening.' in mailoutbox[0].body


def test_send_staff_invited_new_user_email_custom_without_org(
    link_user_factory, registrar_factory, mailoutbox, settings,
):
    """Registrar-user invites have no organization; custom email still applies."""
    user = link_user_factory()
    registrar = registrar_factory()
    user.registrar = registrar
    user.save()
    settings.CUSTOM_EMAILS_FOR_REGISTRAR = {
        registrar.pk: {
            'subject': 'Registrar invite subject',
            'opening': 'Registrar invite opening.',
        },
    }
    send_staff_invited_new_user_email(
        user, registrar_id=registrar.pk, host='https://perma.cc',
    )
    assert mailoutbox[0].subject == 'Registrar invite subject'
    assert 'Registrar invite opening.' in mailoutbox[0].body


def test_registrar_users_plus_stats(db):
    '''
        Returns data in the expected format.
    '''
    r_list = registrar_users_plus_stats()
    assert isinstance(r_list, list)
    assert len(r_list) > 0
    for user in r_list:
        assert isinstance(user, dict)
        expected_keys = [ 'email',
                          'first_name',
                          'last_name',
                          'most_active_org',
                          'registrar_email',
                          'registrar_id',
                          'registrar_name',
                          'registrar_users',
                          'total_links',
                          'year_links' ]
        assert sorted(user.keys()) == expected_keys
        for key in ['email', 'first_name', 'last_name', 'registrar_email', 'registrar_name']:
            assert isinstance(user[key], str)
            assert user[key]
        perma_user = LinkUser.objects.get(email=user['email'])
        assert perma_user.registrar
        assert perma_user.is_active
        assert perma_user.is_confirmed
        assert isinstance(user['total_links'], int)
        assert isinstance(user['year_links'], int)
        assert isinstance(user['registrar_id'], int)
        assert isinstance(user['most_active_org'], (Organization, type(None)))
        assert isinstance(user['registrar_users'], QuerySet)
        assert len(user['registrar_users']) >= 1
        for user in user['registrar_users']:
            assert isinstance(user, LinkUser)
