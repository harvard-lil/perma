from axes.models import AccessAttempt
import datetime
from time import sleep

from django.core import mail
from django.test.utils import override_settings
from django.urls import reverse

from perma.models import LinkUser

from conftest import TEST_USER_PASSWORD, randomize_capitalization, submit_form


def attempt_login(perma_client, username, password, expect_success=True):
    assert '_auth_user_id' not in perma_client.session

    response = perma_client.post(reverse('user_management_limited_login'),
                                 {'username': username,
                                  'password': password})
    if expect_success:
        assert response.status_code == 302
        assert 'login' not in response['Location']
        assert '_auth_user_id' in perma_client.session
    else:
        assert '_auth_user_id' not in perma_client.session
    return response

def test_login(perma_client, link_user):
    """
    Test the login form
    We should get redirected to the create page
    """
    # Login through our form and make sure we get redirected to our create page,
    # no matter how the email address is capitalized
    assert LinkUser.objects.filter(email__iexact=link_user.email).count() == 1

    attempt_login(perma_client, link_user.email, TEST_USER_PASSWORD)
    perma_client.logout()
    attempt_login(perma_client, link_user.email.upper(), TEST_USER_PASSWORD)
    perma_client.logout()
    attempt_login(perma_client, link_user.email.title(), TEST_USER_PASSWORD)
    perma_client.logout()
    attempt_login(perma_client, randomize_capitalization(link_user.email), TEST_USER_PASSWORD)

def test_deactived_user_login(perma_client, deactivated_user):
    submit_form(perma_client, 'user_management_limited_login',
                    data = {'username': deactivated_user.email,
                            'password': TEST_USER_PASSWORD},
                    success_url=reverse('user_management_account_is_deactivated'))
    assert '_auth_user_id' not in perma_client.session

def test_unactived_user_login(perma_client, unactivated_user):
    submit_form(perma_client, 'user_management_limited_login',
                        data = {'username': unactivated_user.email,
                                'password': 'pass'},
                        success_url=reverse('user_management_not_active'))
    assert '_auth_user_id' not in perma_client.session

def test_logout(perma_client, link_user):
    """
    Test our logout link
    """

    # Login with our client and logout with our view
    attempt_login(perma_client, link_user.email, TEST_USER_PASSWORD)
    assert '_auth_user_id' in perma_client.session
    perma_client.get(reverse('logout'))
    submit_form(perma_client, 'logout')
    assert '_auth_user_id' not in perma_client.session

def test_password_change(perma_client, link_user):
    """
    Let's make sure we can login and change our password
    """

    attempt_login(perma_client, link_user.email, TEST_USER_PASSWORD)
    assert '_auth_user_id' in perma_client.session

    perma_client.post(reverse('password_change'),
        {'old_password':TEST_USER_PASSWORD, 'new_password1':'Changed-password1',
        'new_password2':'Changed-password1'})

    perma_client.logout()

    # Try to login with our old password
    attempt_login(perma_client, link_user.email, TEST_USER_PASSWORD, expect_success=False)
    assert '_auth_user_id' not in perma_client.session

    perma_client.logout()

    # Try to login with our new password
    attempt_login(perma_client, link_user.email, 'Changed-password1')
    assert '_auth_user_id' in perma_client.session

@override_settings(AXES_FAILURE_LIMIT=2)
def test_locked_out_after_limit(perma_client, link_user):
    response = attempt_login(perma_client, link_user.email, 'wrongpass', expect_success=False)
    assert response.status_code == 200
    assert 'class="field-error"' in str(response.content)

    response = attempt_login(perma_client, link_user.email, 'wrongpass', expect_success=False)
    assert response.status_code == 403
    assert 'Too Many Attempts' in str(response.content)

    response = attempt_login(perma_client, link_user.email, 'Anewpass1', expect_success=False)
    assert response.status_code == 403
    assert 'Too Many Attempts' in str(response.content)
    assert '_auth_user_id' not in perma_client.session

@override_settings(AXES_FAILURE_LIMIT=1)
@override_settings(AXES_COOLOFF_TIME=datetime.timedelta(seconds=2))
def test_lockout_expires_after_cooloff(perma_client, link_user):
    response = attempt_login(perma_client, link_user.email, 'wrongpass', expect_success=False)
    assert response.status_code == 403
    assert 'Too Many Attempts' in str(response.content)
    sleep(2)
    attempt_login(perma_client, link_user.email,TEST_USER_PASSWORD)
    assert '_auth_user_id' in perma_client.session


@override_settings(AXES_FAILURE_LIMIT=2)
def test_login_attempts_reset(perma_client, link_user):
    # lock the user out
    attempt_login(perma_client, link_user.email, 'wrongpass', expect_success=False)
    response = attempt_login(perma_client, link_user.email, 'wrongpass', expect_success=False)
    assert response.status_code == 403
    assert 'Too Many Attempts' in str(response.content)
    assert 'Reset my password' in str(response.content)
    aa = AccessAttempt.objects.get(username=link_user.email)
    assert aa.failures_since_start == 2

    # get the reset password email/link
    perma_client.post(reverse('password_reset'), {"email": link_user.email})
    message = mail.outbox[0]
    reset_url = next(line for line in message.body.rstrip().split("\n") if line.startswith('http'))

    # go through with the reset
    response = perma_client.get(reset_url, follow=True)
    post_url = response.redirect_chain[0][0]
    response = perma_client.post(post_url, {'new_password1': 'Anewpass1', 'new_password2': 'Anewpass1'}, follow=True, secure=True)
    assert 'Your password has been set' in str(response.content)
    assert not AccessAttempt.objects.filter(username=link_user.email).exists()

    # verify you get the normal form errors, not the lockout page,
    # if you fail again
    response = attempt_login(perma_client, link_user.email, 'wrongpass', expect_success=False)
    assert response.status_code == 200
    assert 'class="field-error"' in str(response.content)

    # verify you CAN login with the new password
    attempt_login(perma_client, link_user.email, 'Anewpass1')
