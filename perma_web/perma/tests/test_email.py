from django.conf import settings
from django.db.models.query import QuerySet
from django.http import HttpRequest

from perma.email import registrar_users_plus_stats, send_user_email_copy_admins
from perma.models import LinkUser, Organization, Registrar


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
