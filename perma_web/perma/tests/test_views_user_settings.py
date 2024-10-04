from bs4 import BeautifulSoup

from django.urls import reverse
from django.conf import settings

from perma.exceptions import PermaPaymentsCommunicationException

from conftest import submit_form
from mock import patch, sentinel


#
# User's own settings
#

def test_user_can_change_own_settings(client, link_user):

    def get_name_and_email():
        response = client.get(reverse('settings_profile'), secure=True)
        assert response.status_code == 200

        soup = BeautifulSoup(response.content, 'html.parser')
        first_name = soup.find('input', {'id': 'id_a-first_name'}).get('value', None)
        last_name = soup.find('input', {'id': 'id_a-last_name'}).get('value', None)
        email = soup.find('input', {'id': 'id_a-email'}).get('value', None)

        return first_name, last_name, email

    client.force_login(link_user)

    # Name and email are present on page load
    first_name, last_name, email = get_name_and_email()
    assert first_name == link_user.first_name
    assert last_name == link_user.last_name
    assert email == link_user.email

    # We can submit the change form
    new_first, new_last, new_email = "Newfirst", "Newlast", "newemail@example.com"
    response = submit_form(
        client,
        'settings_profile',
        data={
            'a-first_name': new_first,
            'a-last_name': new_last,
            'a-email': new_email
        },
        follow=True
    )
    assert response.status_code == 200
    assert bytes('Profile saved!', 'utf-8') in response.content

    # New name and email are present on reload
    first_name, last_name, email = get_name_and_email()
    assert first_name == new_first
    assert last_name == new_last
    assert email == new_email


def test_user_can_request_deletion_once(client, link_user, mailoutbox):

    def get_profile():
        response = client.get(
            reverse('settings_profile'),
            secure=True
        )
        assert response.status_code == 200
        return response

    # Confirm this user hasn't yet requested a deletion
    assert 'Requested account deletion' not in link_user.notes

    # Confirm that the request form is present
    deletion_request_form_markup = f'<form method="post" action="{reverse("settings_delete_account")}"'.encode()
    client.force_login(link_user)
    assert deletion_request_form_markup in get_profile().content

    # Submit the form
    response = client.post(
        reverse('settings_delete_account'),
        secure=True,
        follow=True
    )
    assert response.status_code == 200
    assert b'Deletion Request Received' in response.content

    # Confirm the request was recorded
    link_user.refresh_from_db()
    assert 'Requested account deletion' in link_user.notes

    # Observe that the request form is no longer present
    assert deletion_request_form_markup not in get_profile().content

    # Check that admins were emailed about the request
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == 'Perma.cc account deletion request'


#
# Org Privacy
#

def toggle_org_privacy(client, org, success_url):
    url = reverse('settings_organizations_change_privacy', kwargs={'org_id': org.id})

    # Establish the status quo
    response = client.get(
        url,
        secure=True
    )
    assert response.status_code == 200
    assert b"Your Perma Links are currently <strong>Public</strong> by default." in response.content

    # Toggle policy
    submit_form(
        client,
        url=url,
        success_url=success_url
    )

    # Observe that the privacy notice has changed
    response = client.get(
        url,
        secure=True
    )
    assert b"Your Perma Links are currently <strong>Private</strong> by default." in response.content


def test_edit_org_privacy_org_user(client, org_user):

    client.force_login(org_user)
    org = org_user.organizations.first()
    toggle_org_privacy(client, org, reverse('settings_affiliations'))


def test_edit_org_privacy_registrar_user(client, registrar_user):

    client.force_login(registrar_user)
    org = registrar_user.registrar.organizations.first()
    toggle_org_privacy(client, org, reverse('user_management_manage_organization'))


def test_edit_org_privacy_admin_user(client, admin_user, organization):

    client.force_login(admin_user)
    toggle_org_privacy(client, organization, reverse('user_management_manage_organization'))


def test_edit_nonexistent_org_privacy_404s(client, admin_user):

    client.force_login(admin_user)
    url = reverse('settings_organizations_change_privacy', kwargs={'org_id': 0})

    # Establish the status quo
    response = client.get(
        url,
        secure=True
    )
    assert response.status_code == 404


#
# Subscriptions, Regular Users
#

def test_nonpaying_user_cannot_see_usage_plan_page(client, nonpaying_user):
    assert not nonpaying_user.can_view_usage_plan()
    client.force_login(nonpaying_user)
    response = client.get(
        reverse('settings_usage_plan'),
        secure=True
    )
    assert response.status_code == 403


def test_regular_user_can_see_usage_plan_page(client, link_user):
    assert link_user.can_view_usage_plan()
    client.force_login(link_user)
    response = client.get(
        reverse('settings_usage_plan'),
        secure=True
    )
    assert response.status_code == 200


def test_no_purchase_history_section_if_no_one_time_purchases(client, user_without_subscription_or_purchase_history):
    user = user_without_subscription_or_purchase_history

    client.force_login(user)
    response = client.get(reverse('settings_usage_plan'), secure=True)

    assert response.status_code == 200
    assert b'Purchase History' not in response.content



def test_purchase_history_present_if_one_time_purchases(client, user_without_subscription_with_purchase_history):
    user = user_without_subscription_with_purchase_history

    client.force_login(user)
    response = client.get(reverse('settings_usage_plan'), secure=True)

    assert b'Purchase History' in response.content
    assert b'10 Links' in response.content
    assert b'3 Links' in response.content
    assert b'13 Links' in response.content
    assert b'January 1, 1970' in response.content


@patch('perma.models.prep_for_perma_payments', autospec=True)
def test_subscribe_form_if_no_standing_subscription(prepped, client, user_without_subscription_or_purchase_history):
    user = user_without_subscription_or_purchase_history
    prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

    client.force_login(user)
    response = client.get(reverse('settings_usage_plan'), secure=True)

    assert b'Get More Personal Links' in  response.content
    assert b'Purchase a personal subscription' in response.content
    assert prepped.return_value in response.content

    individual_tier_count = len(settings.TIERS['Individual'])
    bonus_package_count = len(settings.BONUS_PACKAGES)
    assert response.content.count(b'<form class="purchase-form') == bonus_package_count
    assert response.content.count(b'<form class="upgrade-form') == individual_tier_count
    assert response.content.count(b'<input type="hidden" name="encrypted_data"') == individual_tier_count + bonus_package_count


def test_update_button_cancel_button_and_subscription_info_present_if_standing_subscription(client, user_with_monthly_subscription):
    user = user_with_monthly_subscription

    client.force_login(user)
    response = client.get(reverse('settings_usage_plan'), secure=True)

    assert b'Rate' in response.content
    assert b'Paid Through' in response.content
    assert b'Modify Subscription' in response.content
    assert b'Cancel Subscription' in response.content
    assert b'Your subscription is <span class="blue-text">current</span>' in response.content
    assert response.content.count(b'<input type="hidden" name="account_type"') == 2


def test_help_present_if_subscription_on_hold(client, user_with_on_hold_subscription):
    user = user_with_on_hold_subscription

    client.force_login(user)
    response = client.get(reverse('settings_usage_plan'), secure=True)

    assert b'problem with your credit card' in response.content


def test_cancellation_info_present_if_cancellation_requested(client, user_with_requested_cancellation):
    user = user_with_requested_cancellation

    client.force_login(user)
    response = client.get(reverse('settings_usage_plan'), secure=True)

    bonus_package_count = len(settings.BONUS_PACKAGES)
    assert b'Get More Personal Links' in response.content
    assert response.content.count(b'<input type="hidden" name="encrypted_data"') == bonus_package_count
    assert b'received the request to cancel' in response.content


@patch('perma.models.LinkUser.get_subscription', autospec=True)
def test_apology_page_displayed_if_perma_payments_is_down(get_subscription, client, link_user):
    get_subscription.side_effect = PermaPaymentsCommunicationException

    client.force_login(link_user)
    response = client.get(reverse('settings_usage_plan'), secure=True)
    assert b'is currently unavailable' in response.content
    assert b'<input type="hidden" name="encrypted_data"' not in response.content
    get_subscription.assert_called_once_with(link_user)


def test_unauthorized_user_cannot_see_cancellation_page(client, nonpaying_user):
    assert not nonpaying_user.can_view_usage_plan()
    client.force_login(nonpaying_user)
    response = client.post(
        reverse('settings_subscription_cancel'),
        secure=True
    )
    assert response.status_code == 403


def test_authorized_user_cant_use_get_for_cancellation_page(client, link_user):
    assert link_user.can_view_usage_plan()
    client.force_login(link_user)
    response = client.get(
        reverse('settings_subscription_cancel'),
        secure=True
    )
    assert response.status_code == 405


@patch('perma.views.user_settings.prep_for_perma_payments', autospec=True)
def test_authorized_user_cancellation_confirm_form(prepped, client, user_with_monthly_subscription):
    user = user_with_monthly_subscription
    prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

    client.force_login(user)
    response = client.post(
        reverse('settings_subscription_cancel'),
        secure=True,
        data={'account_type':'Individual'}
    )

    assert b'<input type="hidden" name="encrypted_data"' in response.content
    assert prepped.return_value in response.content
    assert b'Are you sure you want to cancel' in response.content


def test_update_page_if_no_standing_subscription(client, user_without_subscription_or_purchase_history):
    user = user_without_subscription_or_purchase_history

    client.force_login(user)
    response = client.post(
        reverse('settings_subscription_update'),
        secure=True,
        data={'account_type':'Individual'}
    )
    assert response.status_code == 403


@patch('perma.views.user_settings.prep_for_perma_payments', autospec=True)
@patch('perma.models.prep_for_perma_payments', autospec=True)
def test_update_page_if_standing_subscription(model_prepped, view_prepped, client, user_with_monthly_subscription):
    user = user_with_monthly_subscription
    model_prepped.return_value = bytes(str(sentinel.model_prepped), 'utf-8')
    view_prepped.return_value = bytes(str(sentinel.view_prepped), 'utf-8')

    client.force_login(user)
    response = client.post(
        reverse('settings_subscription_update'),
        secure=True,
        data={'account_type':'Individual'}
    )

    # Should be able to up/downgrade to all monthly individual tiers, except the current tier
    available_tiers = len([tier for tier in settings.TIERS['Individual'] if tier['period'] == 'monthly']) - 1

    assert b'Update Credit Card Information' in response.content
    assert response.content.count(b'<input type="hidden" name="encrypted_data"') == 1
    assert b'Change Plan' in response.content
    assert b'Cancel Scheduled Downgrade' not in response.content
    assert response.content.count(b'<input required type="radio" name="encrypted_data"') == available_tiers
    assert response.content.count(model_prepped.return_value) == available_tiers
    assert response.content.count(view_prepped.return_value) == 1


@patch('perma.views.user_settings.prep_for_perma_payments', autospec=True)
@patch('perma.models.prep_for_perma_payments', autospec=True)
def test_update_page_if_downgrade_scheduled(model_prepped, view_prepped, client, user_with_scheduled_downgrade):
    user = user_with_scheduled_downgrade
    model_prepped.return_value = bytes(str(sentinel.model_prepped), 'utf-8')
    view_prepped.return_value = bytes(str(sentinel.view_prepped), 'utf-8')

    client.force_login(user)
    response = client.post(
        reverse('settings_subscription_update'),
        secure=True,
        data={'account_type':'Individual'}
    )

    assert b'Update Credit Card Information' in response.content
    assert b'Cancel Scheduled Downgrade' in response.content
    assert response.content.count(b'<input type="hidden" name="encrypted_data"') == 2
    assert b'<input required type="radio" name="encrypted_data"' not in response.content
    assert response.content.count(model_prepped.return_value) == 1
    assert response.content.count(view_prepped.return_value) == 1


@patch('perma.views.user_settings.prep_for_perma_payments', autospec=True)
def test_update_page_if_subscription_on_hold(prepped, client, user_with_on_hold_subscription):
    user = user_with_on_hold_subscription
    prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

    client.force_login(user)
    response = client.post(
        reverse('settings_subscription_update'),
        secure=True,
        data={'account_type':'Individual'}
    )

    assert b'Update Credit Card Information' in response.content
    assert response.content.count(b'<input type="hidden" name="encrypted_data"') == 1
    assert response.content.count(prepped.return_value) == 1
    assert b'Change Plan' not in response.content


@patch('perma.views.user_settings.prep_for_perma_payments', autospec=True)
def test_update_page_if_cancellation_requested(prepped, client, user_with_requested_cancellation):
    user = user_with_requested_cancellation
    prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

    client.force_login(user)
    response = client.post(
        reverse('settings_subscription_update'),
        secure=True,
        data={'account_type':'Individual'}
    )

    assert b'Update Credit Card Information' in response.content
    assert response.content.count(b'<input type="hidden" name="encrypted_data"') == 1
    assert response.content.count(prepped.return_value) == 1
    assert b'Change Plan' not in response.content


# Subscriptions, Registrar Users

@patch('perma.models.prep_for_perma_payments', autospec=True)
def test_registrar_user_nonpaying_registrar(prepped, client, registrar_user_from_nonpaying_registrar):
    user = registrar_user_from_nonpaying_registrar
    prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

    client.force_login(user)
    response = client.get(
        reverse('settings_usage_plan'),
        secure=True
    )

    # Individual tiers should be available; no registrar section should be present

    individual_tier_count = len(settings.TIERS['Individual'])
    bonus_package_count = len(settings.BONUS_PACKAGES)
    assert b'Get More Personal Links' in response.content
    assert b'Purchase a personal subscription' in response.content
    assert f'Purchase a subscription for {user.registrar.name}'.encode() not in response.content
    assert response.content.count(b'<form class="purchase-form') == bonus_package_count
    assert response.content.count(b'<form class="upgrade-form') == individual_tier_count
    assert response.content.count(b'<input type="hidden" name="encrypted_data"') == individual_tier_count + bonus_package_count
    assert response.content.count(prepped.return_value) == individual_tier_count + bonus_package_count


@patch('perma.models.prep_for_perma_payments', autospec=True)
def test_paying_registrar_user_sees_both_subscribe_forms(prepped, client, registrar_user_from_paying_registrar_without_subscription):
    user = registrar_user_from_paying_registrar_without_subscription
    prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

    client.force_login(user)
    response = client.get(
        reverse('settings_usage_plan'),
        secure=True
    )

    # all tiers should be offered, both individual and registrar-level
    tier_count = len(settings.TIERS['Individual']) + len(settings.TIERS['Registrar'])
    bonus_package_count = len(settings.BONUS_PACKAGES)
    assert b'Get More Personal Links' in response.content
    assert b'Purchase a personal subscription' in response.content
    assert f'Purchase a subscription for {user.registrar.name}'.encode() in response.content
    assert response.content.count(b'<form class="purchase-form') == bonus_package_count
    assert response.content.count(b'<form class="upgrade-form') == tier_count
    assert response.content.count(b'<input type="hidden" name="encrypted_data"') == tier_count + bonus_package_count
    assert response.content.count(prepped.return_value) == tier_count + bonus_package_count


@patch('perma.models.prep_for_perma_payments', autospec=True)
def test_paying_registrar_user_sees_subscriptions_independently(prepped, client, registrar_user_from_registrar_with_monthly_subscription):
    user = registrar_user_from_registrar_with_monthly_subscription
    prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

    client.force_login(user)
    response = client.get(
        reverse('settings_usage_plan'),
        secure=True
    )

    # Individual tiers should be available; the registrar's subscription should be present

    individual_tier_count = len(settings.TIERS['Individual'])
    bonus_package_count = len(settings.BONUS_PACKAGES)
    assert b'Get More Personal Links' in response.content
    assert b'Purchase a personal subscription' in response.content
    assert b'Purchase a subscription for Test Firm' not in response.content
    assert response.content.count(b'<form class="purchase-form') == bonus_package_count
    assert response.content.count(b'<form class="upgrade-form') == individual_tier_count
    assert response.content.count(b'<input type="hidden" name="encrypted_data"') == individual_tier_count + bonus_package_count
    assert response.content.count(prepped.return_value) == individual_tier_count + bonus_package_count

    assert b'Rate' in response.content
    assert b'Paid Through' in response.content
    assert b'Modify Subscription' in response.content
    assert response.content.count(b'<input type="hidden" name="account_type"') == 2
    assert b'Cancel Subscription' in response.content


@patch('perma.views.user_settings.prep_for_perma_payments', autospec=True)
def test_paying_registrar_user_personal_cancellation_confirm_form(prepped, client, registrar_user_from_paying_registrar_with_personal_subscription):
    user = registrar_user_from_paying_registrar_with_personal_subscription
    prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

    client.force_login(user)
    response = client.post(
        reverse('settings_subscription_cancel'),
        secure=True,
        data={'account_type':'Individual'}
    )

    assert b'<input type="hidden" name="encrypted_data"' in response.content
    assert prepped.return_value in response.content
    assert b'Are you sure you want to cancel' in response.content
    assert user.registrar.name.encode() not in response.content
    assert b'personal' in response.content



@patch('perma.views.user_settings.prep_for_perma_payments', autospec=True)
def test_paying_registrar_user_institutional_cancellation_confirm_form(prepped, client, registrar_user_from_registrar_with_monthly_subscription):
    user = registrar_user_from_registrar_with_monthly_subscription
    prepped.return_value = bytes(str(sentinel.prepped), 'utf-8')

    client.force_login(user)
    response = client.post(
        reverse('settings_subscription_cancel'),
        secure=True,
        data={'account_type':'Registrar'}
    )

    assert b'<input type="hidden" name="encrypted_data"' in response.content
    assert prepped.return_value in response.content
    assert b'Are you sure you want to cancel' in response.content
    assert user.registrar.name.encode() in response.content
    assert b'Personal' not in response.content


def test_paying_registrar_user_personal_update_form(client, registrar_user_from_paying_registrar_with_personal_subscription):
    user = registrar_user_from_paying_registrar_with_personal_subscription

    client.force_login(user)
    response = client.post(
        reverse('settings_subscription_update'),
        secure=True,
        data={'account_type':'Individual'}
    )

    assert user.registrar.name.encode() not in response.content
    assert b'Personal' in response.content


def test_paying_registrar_user_institutional_update_form(client, registrar_user_from_registrar_with_monthly_subscription):
    user = registrar_user_from_registrar_with_monthly_subscription

    client.force_login(user)
    response = client.post(
        reverse('settings_subscription_update'),
        secure=True,
        data={'account_type':'Registrar'}
    )

    assert user.registrar.name.encode() in response.content
    assert b'Personal' not in response.content


#
# Tools
#

def test_api_key(client, link_user):

    def get_api_key():
        response = client.get(reverse('settings_tools'), secure=True)
        assert response.status_code == 200
        soup = BeautifulSoup(response.content, 'html.parser')
        api_key_input = soup.find('input', {'id': 'id_api_key'})
        if api_key_input:
            key = api_key_input.get('value', None)
        else:
            key = None
        return key


    def create_api_key():
        submit_form(
            client,
            'api_key_create',
            success_url=reverse('settings_tools')
        )

    client.force_login(link_user)

    # No API key is present at first
    key = get_api_key()
    assert not key

    # We can generate one
    create_api_key()
    first_key = get_api_key()
    assert first_key

    # We can generate a new one
    create_api_key()
    second_key = get_api_key()
    assert second_key
    assert first_key != second_key


#
# Affiliations: Does the expected information show up on the affiliations page?
#

def get_afffilation_markup_for_user(client, user):
    client.force_login(user)
    response = client.get(reverse('settings_affiliations'), secure=True)
    return response, BeautifulSoup(response.content, 'html.parser')


def test_affiliations_org_user(client, multi_registrar_org_user):
    registrar_names = [org.registrar.name for org in multi_registrar_org_user.organizations.all()]
    org_names = [org.name for org in multi_registrar_org_user.organizations.all()]

    _, soup = get_afffilation_markup_for_user(client, multi_registrar_org_user)

    registrars = soup.select('h4 a')
    assert len(registrars) == 2
    for registrar in registrars:
        assert registrar.text.strip() in registrar_names

    orgs = soup.select('.settings-block p')
    assert len(orgs) == 2
    for org in orgs:
        assert org.text.strip() in org_names


def test_affiliations_registrar_user(client, registrar_user):
    _, soup = get_afffilation_markup_for_user(client, registrar_user)

    [registrar] = soup.select('h4')
    assert registrar.text.strip() == registrar_user.registrar.name

    registrar_settings = soup.select('dt')
    assert len(registrar_settings) == 2
    for setting in registrar_settings:
        assert setting.text.strip() in ["Website", "Email"]


def test_affiliations_pending_registrar_user(client, pending_registrar_user):
    response, soup = get_afffilation_markup_for_user(client, pending_registrar_user)

    assert b'Pending Registrar'in response.content
    assert b'Thank you for requesting an account for your library. Perma.cc will review your request as soon as possible.' in response.content

    [registrar] = soup.select('.sponsor-name')
    assert registrar.text.strip() == pending_registrar_user.pending_registrar.name

    registrar_settings = soup.select('dt')
    assert len(registrar_settings) == 2
    for setting in registrar_settings:
        assert setting.text.strip() in ["Website", "Email"]
