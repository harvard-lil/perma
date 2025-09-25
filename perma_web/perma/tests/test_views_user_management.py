# -*- coding: utf-8 -*-

import csv
from datetime import timedelta
from io import StringIO
import json
import pytest

import re

from bs4 import BeautifulSoup
from django.urls import reverse

from perma.models import LinkUser, Organization, Registrar, UserOrganizationAffiliation
from perma.tests.utils import PermaTestCase

from conftest import submit_form, randomize_capitalization, GENESIS


###
### REGISTRAR A/E/D VIEWS ###
###

def test_admin_can_create_registrar(client, admin_user):
    client.force_login(admin_user)
    submit_form(
        client,
        'user_management_manage_registrar',
        data={
            'a-name':'test_views_registrar',
            'a-email':'test@test.com',
            'a-website':'http://test.com'
        },
        success_url=reverse('user_management_manage_registrar'),
        success_query=Registrar.objects.filter(name='test_views_registrar')
    )


def test_admin_can_update_registrar(client, admin_user, registrar):
    client.force_login(admin_user)
    submit_form(
        client,
        url=reverse('user_management_manage_single_registrar', args=[registrar.pk]),
        data={
            'a-name': 'new_name',
            'a-email': 'test@test.com2',
            'a-website': 'http://test.com'
        },
        success_url=reverse('user_management_manage_registrar'),
        success_query=Registrar.objects.filter(name='new_name')
    )


def test_registrar_can_update_registrar(client, registrar_user):
    client.force_login(registrar_user)
    submit_form(
        client,
        url=reverse('user_management_manage_single_registrar', args=[registrar_user.registrar.pk]),
        data={
            'a-name': 'new_name',
            'a-email': 'test@test.com2',
            'a-website': 'http://test.com'
        },
        success_url=reverse('settings_affiliations'),
        success_query=Registrar.objects.filter(name='new_name')
    )


def test_registrar_cannot_update_unrelated_registrar(client, registrar, registrar_user):
    assert registrar_user.registrar_id != registrar.id
    client.force_login(registrar_user)
    response = client.get(
        reverse('user_management_manage_single_registrar', args=[registrar.pk]),
        secure=True
    )
    assert response.status_code == 403


def test_admin_can_approve_pending_registrar(client, pending_registrar, admin_user):
    client.force_login(admin_user)
    submit_form(
        client,
        url=reverse('user_sign_up_approve_pending_registrar', args=[pending_registrar.pk]),
        data={'status':'approved', 'base_rate': '100.00'},
        success_query=Registrar.objects.filter(pk=pending_registrar.pk, status="approved").exists()
    )


def test_admin_can_deny_pending_registrar(client, pending_registrar, admin_user):
    client.force_login(admin_user)
    submit_form(
        client,
        url=reverse('user_sign_up_approve_pending_registrar', args=[pending_registrar.pk]),
        data={'status': 'denied', 'base_rate': '100.00'},
        success_query=Registrar.objects.filter(pk=pending_registrar.pk, status="denied").exists()
    )


###
### ORGANIZATION A/E/D VIEWS ###
###

def test_admin_can_create_organization(client, registrar, admin_user):
    client.force_login(admin_user)
    submit_form(
        client,
        'user_management_manage_organization',
        data={
            'a-name': 'new_name',
            'a-registrar': registrar.pk
        },
        success_url=reverse('user_management_manage_organization'),
        success_query=Organization.objects.filter(name='new_name')
    )


def test_registrar_can_create_organization(client, registrar_user):
    client.force_login(registrar_user)
    submit_form(
        client,
        'user_management_manage_organization',
        data={'a-name': 'new_name'},
        success_url=reverse('user_management_manage_organization'),
        success_query=Organization.objects.filter(name='new_name')
    )


def test_admin_can_update_organization(client, organization, admin_user):
    client.force_login(admin_user)
    submit_form(
        client,
        url=reverse('user_management_manage_single_organization', args=[organization.pk]),
        data={
            'a-name': 'new_name',
            'a-registrar': organization.registrar.pk
        },
        success_url=reverse('user_management_manage_organization'),
        success_query=Organization.objects.filter(name='new_name')
    )


def test_registrar_can_update_organization(client, registrar_user):
    org = registrar_user.registrar.organizations.first()
    client.force_login(registrar_user)
    submit_form(
        client,
        url=reverse('user_management_manage_single_organization', args=[org.pk]),
        data={'a-name': 'new_name'},
        success_url=reverse('user_management_manage_organization'),
        success_query=Organization.objects.filter(name='new_name')
    )


def test_org_user_can_update_organization(client, org_user):
    org = org_user.organizations.first()
    client.force_login(org_user)
    submit_form(
        client,
        url=reverse('user_management_manage_single_organization', args=[org.pk]),
        data={'a-name': 'new_name'},
        success_url=reverse('user_management_manage_organization'),
        success_query=Organization.objects.filter(name='new_name')
    )


def test_registrar_cannot_update_unrelated_organization(client, registrar_user, organization):
    client.force_login(registrar_user)
    response = client.get(
        reverse('user_management_manage_single_organization', args=[organization.pk]),
        secure=True
    )
    assert response.status_code == 403


def test_org_user_cannot_update_unrelated_organization(client, org_user, organization_factory):
    other_org = organization_factory()
    client.force_login(org_user)
    response = client.get(
        reverse('user_management_manage_single_organization', args=[other_org.pk]),
        secure=True
    )
    assert response.status_code == 403


def _delete_organization(client, user, org, expect="success"):
    url = reverse('user_management_manage_single_organization_delete', args=[org.pk])
    client.force_login(user)
    if expect == 'success':
        return submit_form(
            client,
            url=url,
            success_url=reverse('user_management_manage_organization'),
            success_query=Organization.objects.filter(user_deleted=True, pk=org.pk)
        )
    else:
        response = submit_form(
            client,
            url=url
        )
        assert response.status_code == expect
        return response


def test_admin_user_can_delete_organization_without_links(client, admin_user, organization):
    _delete_organization(client, admin_user, organization)
    _delete_organization(client, admin_user, organization, 404)


def test_registrar_user_cannot_delete_unrelated_organization(client, registrar_user, organization):
    _delete_organization(client, registrar_user, organization, 403)


def test_registrar_user_can_delete_organization_without_links(client, registrar_user):
    org = registrar_user.registrar.organizations.first()
    _delete_organization(client, registrar_user, org)
    _delete_organization(client, registrar_user, org, 404)


def test_org_user_cannot_delete_unrelated_organization(client, org_user, organization_factory):
    org = organization_factory()
    _delete_organization(client, org_user, org, 403)


def test_org_user_can_delete_organization_without_links(client, multi_registrar_org_user):
    # Use multi_registrar_org_user so that the user is still an org user, even after the org is deleted
    user = multi_registrar_org_user
    org = user.organizations.first()
    _delete_organization(client, user, org)
    _delete_organization(client, user, org, 404)


def test_even_admin_cannot_delete_organization_with_links(client, admin_user, organization_with_links):
    _delete_organization(client, admin_user, organization_with_links, 403)


###
### USER A/E/D VIEWS ###
###

@pytest.mark.parametrize(
    "view_name,form_field",
    [
        ('user', ''),
        ('registrar_user', 'a-registrar'),
        ('organization_user', 'a-organizations'),
        ('sponsored_user', 'a-sponsoring_registrars')
    ]
)
def test_admin_can_create_users(view_name, form_field, client, admin_user, registrar, user_data_factory):
    # Setup
    client.force_login(admin_user)
    user_data = user_data_factory()
    common_fields = {
        'a-first_name': user_data['first_name'],
        'a-last_name': user_data['last_name'],
        'a-address': user_data['email']
    }
    match view_name:
        case 'registrar_user':
            view_specific_fields = {form_field: registrar.id}
        case 'organization_user':
            view_specific_fields = {form_field: registrar.organizations.first().id}
        case 'sponsored_user':
            view_specific_fields = {form_field: registrar.id}
        case _:
            view_specific_fields = {}

    # Create the user
    submit_form(
        client,
        data={**common_fields, **view_specific_fields},
        view_name='user_management_' + view_name + '_add_user',
        success_url=reverse('user_management_manage_' + view_name),
        success_query=LinkUser.objects.filter(
            email=user_data['normalized_email'],
            raw_email=user_data['email']
        )
    )


def attempt_deletion(user_type, view_name, request, client, admin_user, deactivate=False):
    client.force_login(admin_user)
    user = request.getfixturevalue(user_type)
    if deactivate:
        assert user.is_active

    submit_form(
        client,
        url=reverse(
            'user_management_manage_single_' + view_name + '_delete',
            args=[user.id]
        ),
        success_url=reverse('user_management_manage_' + view_name)
    )

    if deactivate:
        user.refresh_from_db()
        assert not user.is_active
    else:
        with pytest.raises(LinkUser.DoesNotExist):
            user.refresh_from_db()


@pytest.mark.parametrize(
    "user_type, view_name",
    [
        ('link_user', 'user'),
        ('registrar_user', 'registrar_user'),
        ('org_user', 'organization_user'),
        ('sponsored_user', 'sponsored_user'),
    ]
)
def test_admin_can_deactivate_confirmed_users(user_type, view_name, request, client, admin_user):
    # If you attempt to delete a user where is_confirmed is True,
    # they are not deleted, they are deactivated
    attempt_deletion(user_type, view_name, request, client, admin_user, deactivate=True)


@pytest.mark.parametrize(
    "user_type, view_name",
    [
        ('unactivated_user', 'user'),
        ('unconfirmed_registrar_user', 'registrar_user'),
        ('unconfirmed_org_user', 'organization_user'),
        ('unconfirmed_sponsored_user', 'sponsored_user'),
    ]
)
def test_admin_can_delete_unconfirmed_users(user_type, view_name, request, client, admin_user):
    # If you attempt to delete a user where is_confirmed is False,
    # they are deleted
    attempt_deletion(user_type, view_name, request, client, admin_user)


@pytest.mark.parametrize(
    "user_type, view_name",
    [
        ('deactivated_user', 'user'),
        ('deactivated_registrar_user', 'registrar_user'),
        ('deactivated_org_user', 'organization_user'),
        ('deactivated_sponsored_user', 'sponsored_user'),
    ]
)
def test_admin_can_reactivate_deactivated_users(user_type, view_name, request, client, admin_user):
    client.force_login(admin_user)
    user = request.getfixturevalue(user_type)
    assert not user.is_active

    submit_form(
        client,
        url=reverse(
            'user_management_manage_single_' + view_name + '_reactivate',
            args=[user.id]
        ),
        success_url=reverse('user_management_manage_' + view_name)
    )

    user.refresh_from_db()
    assert user.is_active


###
### ADDING USERS TO ORGANIZATIONS ###
###

@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
def test_can_add_new_user_to_org(user_type, request, client, user_data):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")

    submit_form(
        client,
        url=f"{reverse('user_management_organization_user_add_user')}?email={user_data['email']}",
        data={
            "a-organizations": org.id,
            "a-first_name": user_data['first_name'],
            "a-last_name": user_data['last_name'],
            "a-address": user_data['email'],
        },
        success_url=reverse("user_management_manage_organization_user"),
        success_query=LinkUser.objects.filter(
            email=user_data['normalized_email'],
            raw_email=user_data['email'],
            organizations=org
        ).exists()
    )


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user"
    ]
)
def test_cannot_add_new_user_to_inaccessible_org(user_type, request, client, user_data, organization_factory):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    unrelated_org = organization_factory()

    submit_form(
        client,
        url=f"{reverse('user_management_organization_user_add_user')}?email={user_data['email']}",
        data={
            "a-organizations": unrelated_org.id,
            "a-first_name": user_data['first_name'],
            "a-last_name": user_data['last_name'],
            "a-address": user_data['email'],
        },
        error_keys=['organizations']
    )
    assert not LinkUser.objects.filter(email__iexact=user_data['email']).exists()


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
def test_can_add_existing_user_to_org(user_type, request, client, link_user):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")

    scrambled_email = randomize_capitalization(link_user.email)
    submit_form(
        client,
        url=f"{reverse('user_management_organization_user_add_user')}?email={scrambled_email}",
        data={
            "a-organizations": org.id
        },
        success_url=reverse("user_management_manage_organization_user"),
        success_query=link_user.organizations.filter(id=org.id)
    )


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user"
    ]
)
def test_cannot_add_existing_user_to_inaccessible_org(user_type, request, client, link_user, organization_factory):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    unrelated_org = organization_factory()

    scrambled_email = randomize_capitalization(link_user.email)
    submit_form(
        client,
        url=f"{reverse('user_management_organization_user_add_user')}?email={scrambled_email}",
        data={
            "a-organizations": unrelated_org.id
        },
        error_keys=['organizations']
    )
    assert not link_user.organizations.filter(id=unrelated_org.id).exists()


def test_cannot_add_admin_user_to_org(client, admin_user, organization):
    client.force_login(admin_user)

    scrambled_email = randomize_capitalization(admin_user.email)
    response = submit_form(
        client,
        url=f"{reverse('user_management_organization_user_add_user')}?email={scrambled_email}",
        data={
            "a-organizations": organization.id
        }
    )

    assert b"is an admin user" in response.content
    assert not admin_user.organizations.exists()


def test_cannot_add_registrar_user_to_org(client, admin_user, registrar_user):
    client.force_login(admin_user)
    org = registrar_user.registrar.organizations.first()

    scrambled_email = randomize_capitalization(registrar_user.email)
    response = submit_form(
        client,
        url=f"{reverse('user_management_organization_user_add_user')}?email={scrambled_email}",
        data={
            "a-organizations": org.id
        }
    )
    assert b"is already a registrar user"in response.content
    assert not registrar_user.organizations.exists()


###
### ADDING MULTIPLE ORG USERS VIA CSV
###


def test_multiple_org_user_form_populates_org_user_organization(
        client,
        org_user,
        organization_factory
):
    unrelated_org = organization_factory()
    assert not org_user.organizations.filter(id=unrelated_org.id).exists()
    client.force_login(org_user)

    response = client.get(
        reverse("user_management_organization_user_add_multiple_users"),
        secure=True
    )

    form = response.context["form"]
    assert list(form.fields['organizations'].queryset) == list(org_user.organizations.all())


def test_multiple_org_user_form_populates_registrar_user_organizations(
        client,
        registrar_with_five_orgs,
        organization_factory
):
    unrelated_org = organization_factory()
    assert not registrar_with_five_orgs.organizations.filter(id=unrelated_org.id).exists()
    user = registrar_with_five_orgs.users.get()
    client.force_login(user)

    response = client.get(
        reverse("user_management_organization_user_add_multiple_users"),
        secure=True
    )

    form = response.context["form"]
    assert list(
        form.fields['organizations'].queryset.order_by('name')
    ) == list(
        registrar_with_five_orgs.organizations.all().order_by('name')
    )


def test_multiple_org_user_form_populates_admin_user_organizations(
        client,
        admin_user,
        organization_factory
):
    client.force_login(admin_user)
    for _ in range(5):
        organization_factory()

    response = client.get(
        reverse("user_management_organization_user_add_multiple_users"),
        secure=True
    )

    form = response.context["form"]
    assert list(
        form.fields['organizations'].queryset.order_by('name')
    ) == list(
        Organization.objects.all().order_by('name')
    )


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
def test_multiple_org_user_form_invalid_if_wrong_extension(
        user_type,
        request,
        client,
        tsv
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")

    response = submit_form(
        client,
        url = reverse("user_management_organization_user_add_multiple_users"),
        data = {
            "a-organizations": org.id,
            "a-indefinite_affiliation": True,
            "a-csv_file": tsv
        },
        error_keys=['csv_file']
    )
    assert b"The file must be a CSV" in response.content


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
def test_multiple_org_user_form_invalid_if_unreadable_file(
        user_type,
        request,
        client,
        utf16_csv
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")

    response = submit_form(
        client,
        url = reverse("user_management_organization_user_add_multiple_users"),
        data = {
            "a-organizations": org.id,
            "a-indefinite_affiliation": True,
            "a-csv_file": utf16_csv
        },
        error_keys=['csv_file']
    )
    assert b"CSV file must be encoded with UTF-8" in response.content


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
@pytest.mark.parametrize(
    "skip_headers",
    [
        "all",
        "first_name",
        "last_name",
        "email"
    ]
)
def test_multiple_org_user_form_invalid_if_headers_absent(
        user_type,
        skip_headers,
        request,
        client,
        org_user_csv_missing_headers
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    csv = org_user_csv_missing_headers(skip_headers=skip_headers)

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")

    response = submit_form(
        client,
        url = reverse("user_management_organization_user_add_multiple_users"),
        data = {
            "a-organizations": org.id,
            "a-indefinite_affiliation": True,
            "a-csv_file": csv
        },
        error_keys=['csv_file']
    )
    assert b"CSV file must contain a header row with first_name, last_name and email columns." in response.content


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
def test_multiple_org_user_form_invalid_if_no_rows(
        user_type,
        request,
        client,
        org_user_csv_missing_data
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    csv = org_user_csv_missing_data(skip_fields='all')

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")

    response = submit_form(
        client,
        url = reverse("user_management_organization_user_add_multiple_users"),
        data = {
            "a-organizations": org.id,
            "a-indefinite_affiliation": True,
            "a-csv_file": csv
        },
        error_keys=['csv_file']
    )
    assert b"CSV file must contain at least one user" in response.content


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
def test_multiple_org_user_form_invalid_if_any_email_absent(
        user_type,
        request,
        client,
        org_user_csv_missing_data
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    csv = org_user_csv_missing_data(skip_fields='email')

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")

    response = submit_form(
        client,
        url = reverse("user_management_organization_user_add_multiple_users"),
        data = {
            "a-organizations": org.id,
            "a-indefinite_affiliation": True,
            "a-csv_file": csv
        },
        error_keys=["csv_file"]
    )
    assert b"Each row in the CSV file must contain email." in response.content


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
def test_multiple_org_user_form_invalid_if_any_email_invalid(
        user_type,
        request,
        client,
        org_user_csv_invalid_email
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    csv = org_user_csv_invalid_email

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")

    response = submit_form(
        client,
        url = reverse("user_management_organization_user_add_multiple_users"),
        data = {
            "a-organizations": org.id,
            "a-indefinite_affiliation": True,
            "a-csv_file": csv
        },
        error_keys=['csv_file']
    )
    assert b"CSV file contains invalid email address" in response.content


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user"
    ]
)
def test_multiple_org_user_form_disallows_unrelated_organization(
        user_type,
        request,
        client,
        org_user_csv_complete,
        organization_factory
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    csv = org_user_csv_complete
    unrelated_org = organization_factory()

    response = submit_form(
        client,
        url = reverse("user_management_organization_user_add_multiple_users"),
        data = {
            "a-organizations": unrelated_org.id,
            "a-indefinite_affiliation": True,
            "a-csv_file": csv
        },
        error_keys=['organizations']
    )
    assert b"That choice is not one of the available choices." in response.content


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
def test_multiple_org_user_form_creates_without_names(
        user_type,
        request,
        client,
        org_user_csv_missing_data
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    csv = org_user_csv_missing_data(skip_fields='first_name,last_name')

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")

    response = submit_form(
        client,
        url = reverse("user_management_organization_user_add_multiple_users"),
        data = {
            "a-organizations": org.id,
            "a-indefinite_affiliation": True,
            "a-csv_file": csv
        },
        error_keys=None
    )

    form = response.context["form"]
    created_user_ids = [user.id for user in form.created_users.values()]
    assert len(created_user_ids) == 10
    assert UserOrganizationAffiliation.objects.filter(
        user_id__in=created_user_ids,
        user__first_name='',
        user__last_name=''
    ).count() == 1
    assert UserOrganizationAffiliation.objects.filter(
        user_id__in=created_user_ids
    ).count() == 10


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
def test_multiple_org_user_form_creates_with_names(
        user_type,
        request,
        client,
        org_user_csv_complete
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    csv = org_user_csv_complete

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")

    response = submit_form(
        client,
        url = reverse("user_management_organization_user_add_multiple_users"),
        data = {
            "a-organizations": org.id,
            "a-indefinite_affiliation": True,
            "a-csv_file": csv
        },
        error_keys=None
    )

    form = response.context["form"]
    created_user_ids = [user.id for user in form.created_users.values()]
    assert len(created_user_ids) == 10
    assert not UserOrganizationAffiliation.objects.filter(
        user_id__in=created_user_ids,
        user__first_name='',
        user__last_name=''
    ).exists()
    assert UserOrganizationAffiliation.objects.filter(
        user_id__in=created_user_ids
    ).count() == 10


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
def test_multiple_org_user_form_updates_expiry_date(
        user_type,
        request,
        client,
        org_user_csv_existing_org_users
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")

    csv = org_user_csv_existing_org_users(org)
    affiliations = UserOrganizationAffiliation.objects.filter(
        user__in=org.users.exclude(id=user.id)
    )
    user_count = affiliations.count()
    assert all(affiliation.expires_at is None for affiliation in affiliations.all())

    response = submit_form(
        client,
        url = reverse("user_management_organization_user_add_multiple_users"),
        data = {
            "a-organizations": org.id,
            "a-indefinite_affiliation": True,
            "a-csv_file": csv,
            "a-expires_at": GENESIS
        },
        error_keys=None
    )

    form = response.context["form"]
    updated_user_ids = [user.id for user in form.updated_users.values()]
    assert len(updated_user_ids) == user_count
    assert all(affiliation.expires_at == GENESIS for affiliation in affiliations.all())


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
def test_multiple_org_user_form_upgrades_regular_users(
        user_type,
        request,
        client,
        org_user_csv_existing_regular_users
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    csv = org_user_csv_existing_regular_users

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")

    assert not UserOrganizationAffiliation.objects.filter(
        user__in=org.users.exclude(id=user.id)
    ).exists()

    response = submit_form(
        client,
        url = reverse("user_management_organization_user_add_multiple_users"),
        data = {
            "a-organizations": org.id,
            "a-indefinite_affiliation": True,
            "a-csv_file": csv
        },
        error_keys=None
    )

    form = response.context["form"]
    updated_user_ids = [user.id for user in form.updated_users.values()]
    assert len(updated_user_ids) == 10
    assert UserOrganizationAffiliation.objects.filter(
        user__in=org.users.exclude(id=user.id)
    ).count() == 10


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
def test_multiple_org_user_form_rejects_admins_and_registrars(
        user_type,
        request,
        client,
        org_user_csv_admin_and_registrar
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    csv = org_user_csv_admin_and_registrar

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")

    response = submit_form(
        client,
        url = reverse("user_management_organization_user_add_multiple_users"),
        data = {
            "a-organizations": org.id,
            "a-indefinite_affiliation": True,
            "a-csv_file": csv
        },
        error_keys=None
    )

    form = response.context["form"]
    assert len(form.updated_users) == 0
    assert len(form.ineligible_users) == 2
    for email in form.ineligible_users:
        ineligible_user = LinkUser.objects.get(email=email)
        assert not ineligible_user.organizations.exists()


###
### REMOVING USERS FROM ORGANIZATIONS ###
###

@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
def test_can_visit_org_user_edit_page(user_type, request, client, link_user):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")
    link_user.organizations.set([org])

    response = client.get(
        reverse('user_management_manage_single_organization_user', args=[link_user.id]),
        secure=True
    )
    assert response.status_code == 200


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
    ]
)
def test_cannot_visit_unrelated_org_user_edit_page(user_type, request, client, org_user_factory):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    unrelated_org_user = org_user_factory()

    response = client.get(
        reverse('user_management_manage_single_organization_user', args=[unrelated_org_user.id]),
        secure=True
    )
    assert response.status_code == 403


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
def test_can_remove_user_from_organization(user_type, request, client, link_user):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")
    link_user.organizations.set([org])

    assert link_user.organizations.filter(id=org.id).exists()
    submit_form(
        client,
        url=reverse('user_management_manage_single_organization_user_remove', args=[link_user.id]),
        data={'affiliation': link_user.userorganizationaffiliation_set.first().id},
        success_url=reverse('user_management_manage_organization_user')
    )
    assert not link_user.organizations.filter(id=org.id).exists()


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
    ]
)
def test_cannot_remove_user_from_unrelated_organization(user_type, request, client, org_user_factory):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    unrelated_org_user = org_user_factory()

    submit_form(
        client,
        url=reverse('user_management_manage_single_organization_user_remove', args=[unrelated_org_user.id]),
        data={'affiliation': unrelated_org_user.userorganizationaffiliation_set.first().id},
        require_status_code=404
    )


def test_can_remove_self_from_organization(client, org_user):
    client.force_login(org_user)
    submit_form(
        client,
        url=reverse('user_management_manage_single_organization_user_remove', args=[org_user.id]),
        data={'affiliation': org_user.userorganizationaffiliation_set.first().id},
        success_url=reverse('create_link')
    )
    assert not org_user.organizations.exists()


### MODIFYING ORG USER AFFILIATION EXPIRATION DATES ###

def test_admin_user_can_modify_expiration_of_org_user(client, admin_user, org_user_with_expiring_affiliation):
    client.force_login(admin_user)
    org_user = org_user_with_expiring_affiliation
    affiliation = org_user.userorganizationaffiliation_set.first()
    assert affiliation.expires_at
    submit_form(
        client,
        url=reverse('user_management_manage_single_organization_user_expiration_date', args=[org_user.id, affiliation.organization.id]),
        data={'expires_at': ''},
        success_url=reverse('user_management_manage_single_organization_user', args=[org_user.id])
    )
    affiliation.refresh_from_db()
    assert affiliation.expires_at is None


def test_registrar_user_can_modify_expiration_of_org_user(client, org_user_with_expiring_affiliation):

    org_user = org_user_with_expiring_affiliation
    affiliation = org_user.userorganizationaffiliation_set.first()
    org = affiliation.organization
    registrar_user = org.registrar.users.first()

    assert affiliation.expires_at == GENESIS
    client.force_login(registrar_user)
    submit_form(
        client,
        url=reverse('user_management_manage_single_organization_user_expiration_date', args=[org_user.id, org.id]),
        data={'expires_at': GENESIS + timedelta(days=1)},
        success_url=reverse('user_management_manage_single_organization_user', args=[org_user.id])
    )
    affiliation.refresh_from_db()
    assert affiliation.expires_at == GENESIS + timedelta(days=1)


def test_registrar_user_cannot_modify_expiration_of_unrelated_org_user(client, registrar_user, org_user_with_expiring_affiliation):

    org_user = org_user_with_expiring_affiliation
    affiliation = org_user.userorganizationaffiliation_set.first()
    org = affiliation.organization
    registrar_users = org.registrar.users.all()

    assert affiliation.expires_at == GENESIS
    assert registrar_users
    assert registrar_user not in registrar_users
    client.force_login(registrar_user)
    submit_form(
        client,
        url=reverse('user_management_manage_single_organization_user_expiration_date', args=[org_user.id, org.id]),
        data={'expires_at': ''},
        require_status_code=404
    )
    affiliation.refresh_from_db()
    assert affiliation.expires_at == GENESIS


###
### ADDING SPONSORED USERS
###

def check_sponsorship_is_set_up_correctly(sponsored_user):
    sponsorship = sponsored_user.sponsorships.first()
    sponsored_folder = sponsorship.folders.get()
    assert sponsorship.status == 'active'
    assert sponsored_folder.parent == sponsored_user.sponsored_root_folder
    assert not sponsored_folder.read_only


@pytest.mark.parametrize(
    "user_type",
    [
        "registrar_user",
        "admin_user"
    ]
)
def test_can_add_new_sponsored_user_to_registrar(user_type, request, client, user_data):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "registrar_user":
            registrar = user.registrar
        case "admin_user":
            registrar = request.getfixturevalue("registrar")

    submit_form(
        client,
        url=f"{reverse('user_management_sponsored_user_add_user')}?email={user_data['email']}",
        data={
            "a-sponsoring_registrars": registrar.id,
            "a-first_name": user_data['first_name'],
            "a-last_name": user_data['last_name'],
            "a-address": user_data['email'],
        },
        success_url=reverse("user_management_manage_sponsored_user"),
    )

    sponsored_user = LinkUser.objects.get(
        email=user_data["normalized_email"],
        raw_email=user_data["email"],
        sponsoring_registrars=registrar
    )
    check_sponsorship_is_set_up_correctly(sponsored_user)


def test_cannot_add_sponsored_user_to_inaccessible_registrar(client, user_data, registrar_user, registrar_factory):
    client.force_login(registrar_user)
    unrelated_registrar = registrar_factory()

    submit_form(
        client,
        url=f"{reverse('user_management_sponsored_user_add_user')}?email={user_data['email']}",
        data={
            "a-sponsoring_registrars": unrelated_registrar.id,
            "a-first_name": user_data['first_name'],
            "a-last_name": user_data['last_name'],
            "a-address": user_data['email'],
        },
        error_keys=['sponsoring_registrars']
    )
    assert not LinkUser.objects.filter(email__iexact=user_data['email'])


@pytest.mark.parametrize(
    "user_type",
    [
        "registrar_user",
        "admin_user"
    ]
)
def test_can_add_sponsorship_to_existing_user(user_type, request, client, link_user):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "registrar_user":
            registrar = user.registrar
        case "admin_user":
            registrar = request.getfixturevalue("registrar")

    scrambled_email = randomize_capitalization(link_user.email)
    submit_form(
        client,
        url=f"{reverse('user_management_sponsored_user_add_user')}?email={scrambled_email}",
        data={'a-sponsoring_registrars': registrar.id},
        success_url=reverse('user_management_manage_sponsored_user'),
        success_query=link_user.sponsorships.filter(registrar=registrar)
    )

    link_user.refresh_from_db()
    check_sponsorship_is_set_up_correctly(link_user)


def test_registrar_user_cannot_add_sponsorship_for_other_registrar_to_existing_user(client, registrar_user, registrar_factory, link_user):
    client.force_login(registrar_user)
    unrelated_registrar = registrar_factory()

    scrambled_email = randomize_capitalization(link_user.email)
    submit_form(
        client,
        url=f"{reverse('user_management_sponsored_user_add_user')}?email={scrambled_email}",
        data={
            "a-sponsoring_registrars": unrelated_registrar.id,
        },
        error_keys=['sponsoring_registrars']
    )
    assert not link_user.sponsorships.filter(registrar=unrelated_registrar).exists()


def test_cannot_create_duplicative_sponsorships(client, admin_user, sponsored_user):
    client.force_login(admin_user)

    scrambled_email = randomize_capitalization(sponsored_user.email)
    response = submit_form(
        client,
        url=f"{reverse('user_management_sponsored_user_add_user')}?email={scrambled_email}",
        data={'a-sponsoring_registrars': sponsored_user.sponsorships.first().registrar.id}
    )
    assert b"Select a valid choice. That choice is not one of the available choices" in response.content


###
### TOGGLING SPONSORSHIP STATUS ###
###

@pytest.mark.parametrize(
    "user_type",
    [
        "registrar_user",
        "admin_user"
    ]
)
def test_can_deactivate_sponsorship(user_type, request, client, sponsored_user):
    sponsorship = sponsored_user.sponsorships.get()
    match user_type:
        case "registrar_user":
            user = sponsorship.registrar.users.first()
        case "admin_user":
            user = request.getfixturevalue("admin_user")
    client.force_login(user)

    submit_form(
        client,
        url=reverse('user_management_manage_single_sponsored_user_remove', args= [sponsored_user.id, sponsorship.registrar.id]),
        success_url=reverse('user_management_manage_single_sponsored_user', args=[sponsored_user.id])
    )
    sponsorship.refresh_from_db()
    assert sponsorship.status == 'inactive'
    assert all(folder.read_only for folder in sponsorship.folders)


@pytest.mark.parametrize(
    "user_type",
    [
        "registrar_user",
        "admin_user"
    ]
)
def test_can_reactivate_sponsorship(user_type, request, client, inactive_sponsored_user):
    sponsorship = inactive_sponsored_user.sponsorships.get()
    match user_type:
        case "registrar_user":
            user = sponsorship.registrar.users.first()
        case "admin_user":
            user = request.getfixturevalue("admin_user")
    client.force_login(user)

    submit_form(
        client,
        url=reverse('user_management_manage_single_sponsored_user_readd', args= [inactive_sponsored_user.id, sponsorship.registrar.id]),
        success_url=reverse('user_management_manage_single_sponsored_user', args=[inactive_sponsored_user.id])
    )
    sponsorship.refresh_from_db()
    assert sponsorship.status == 'active'
    assert all(not folder.read_only for folder in sponsorship.folders)


def test_registrar_user_cannot_deactivate_active_sponsorship_for_other_registrar(client, sponsored_user, registrar_user):
    sponsorship = sponsored_user.sponsorships.get()
    assert sponsorship.registrar != registrar_user.registrar
    client.force_login(registrar_user)

    submit_form(
        client,
        url=reverse('user_management_manage_single_sponsored_user_remove', args= [sponsored_user.id, sponsorship.registrar.id]),
        require_status_code=404
    )
    sponsorship.refresh_from_db()
    assert sponsorship.status == 'active'


def test_registrar_user_cannot_reactivate_inactive_sponsorship_for_other_registrar(client, inactive_sponsored_user, registrar_user):
    sponsorship = inactive_sponsored_user.sponsorships.get()
    assert sponsorship.registrar != registrar_user.registrar
    client.force_login(registrar_user)

    submit_form(
        client,
        url=reverse('user_management_manage_single_sponsored_user_readd', args= [inactive_sponsored_user.id, sponsorship.registrar.id]),
        require_status_code=404
    )
    sponsorship.refresh_from_db()
    assert sponsorship.status == 'inactive'


### MODIFYING SPONSORSHIP EXPIRATION DATES ###

def test_admin_user_can_modify_expiration_of_sponsored_user(client, admin_user, sponsored_user_with_expiring_affiliation):
    sponsored_user = sponsored_user_with_expiring_affiliation
    sponsorship = sponsored_user.sponsorships.first()
    registrar = sponsorship.registrar
    assert sponsorship.expires_at

    client.force_login(admin_user)
    submit_form(
        client,
        url=reverse('user_management_manage_single_sponsored_user_expiration_date', args=[sponsored_user.id, registrar.id]),
        data={'expires_at': ''},
        success_url=reverse('user_management_manage_single_sponsored_user', args=[sponsored_user.id]),
    )
    sponsorship.refresh_from_db()
    assert sponsorship.expires_at is None

def test_registrar_user_can_modify_expiration_of_sponsored_user(client, sponsored_user_with_expiring_affiliation):
    sponsored_user = sponsored_user_with_expiring_affiliation
    sponsorship = sponsored_user.sponsorships.first()
    registrar = sponsorship.registrar
    registrar_user = registrar.users.first()
    assert sponsorship.expires_at == GENESIS

    client.force_login(registrar_user)
    submit_form(
        client,
        url=reverse('user_management_manage_single_sponsored_user_expiration_date', args=[sponsored_user.id, registrar.id]),
        data={'expires_at': GENESIS + timedelta(days=1)},
        success_url=reverse('user_management_manage_single_sponsored_user', args=[sponsored_user.id]),
    )
    sponsorship.refresh_from_db()
    assert sponsorship.expires_at == GENESIS + timedelta(days=1)


def test_registrar_user_cannot_modify_expiration_of_unrelated_sponsored_user(client, registrar_user, sponsored_user_with_expiring_affiliation):
    sponsored_user = sponsored_user_with_expiring_affiliation
    sponsorship = sponsored_user.sponsorships.first()
    registrar = sponsorship.registrar

    assert sponsorship.expires_at == GENESIS
    assert registrar_user not in registrar.users.all()
    client.force_login(registrar_user)
    submit_form(
        client,
        url=reverse('user_management_manage_single_sponsored_user_expiration_date', args=[sponsored_user.id, registrar.id]),
        data={'expires_at': GENESIS + timedelta(days=1)},
        require_status_code=404,
    )
    sponsorship.refresh_from_db()
    assert sponsorship.expires_at == GENESIS


###
### ADDING REGISTRAR USERS ###
###

@pytest.mark.parametrize(
    "user_type",
    [
        "registrar_user",
        "admin_user"
    ]
)
def test_can_add_new_user_to_registrar(user_type, request, client, user_data):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "registrar_user":
            registrar = user.registrar
        case "admin_user":
            registrar = request.getfixturevalue("registrar")

    submit_form(
        client,
        url=f"{reverse('user_management_registrar_user_add_user')}?email={user_data['email']}",
        data={
            "a-registrar": registrar.id,
            "a-first_name": user_data['first_name'],
            "a-last_name": user_data['last_name'],
            "a-address": user_data['email'],
        },
        success_url=reverse("user_management_manage_registrar_user"),
        success_query=LinkUser.objects.filter(
              email=user_data['normalized_email'],
              raw_email=user_data['email'],
              registrar=registrar
        )
    )


def test_cannot_add_new_user_to_inaccessible_registrar(client, registrar_user, user_data, registrar_factory):
    client.force_login(registrar_user)
    unrelated_registrar = registrar_factory()

    submit_form(
        client,
        url=f"{reverse('user_management_registrar_user_add_user')}?email={user_data['email']}",
        data={
            "a-registrar": unrelated_registrar.id,
            "a-first_name": user_data['first_name'],
            "a-last_name": user_data['last_name'],
            "a-address": user_data['email'],
        },
        error_keys=['registrar']
    )
    assert not LinkUser.objects.filter(email__iexact=user_data['email'])


@pytest.mark.parametrize(
    "user_type",
    [
        "registrar_user",
        "admin_user"
    ]
)
def test_can_add_existing_user_to_registrar(user_type, request, client, link_user):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "registrar_user":
            registrar = user.registrar
        case "admin_user":
            registrar = request.getfixturevalue("registrar")

    scrambled_email = randomize_capitalization(link_user.email)
    submit_form(
        client,
        url=f"{reverse('user_management_registrar_user_add_user')}?email={scrambled_email}",
        data={
            "a-registrar": registrar.id
        },
        success_url=reverse("user_management_manage_registrar_user"),
    )

    link_user.refresh_from_db()
    assert link_user.registrar == registrar


def test_cannot_add_existing_user_to_inaccessible_registrar(client, registrar_user, registrar_factory, link_user):
    client.force_login(registrar_user)
    unrelated_registrar = registrar_factory()

    scrambled_email = randomize_capitalization(link_user.email)
    submit_form(
        client,
        url=f"{reverse('user_management_registrar_user_add_user')}?email={scrambled_email}",
        data={
            "a-registrar": unrelated_registrar.id,
        },
        error_keys=['registrar']
    )

    link_user.refresh_from_db()
    assert not link_user.registrar


@pytest.mark.parametrize(
    "user_type",
    [
        "registrar_user",
        "admin_user"
    ]
)
def test_cannot_readd_user_to_registrar(user_type, request, client, registrar_user):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "registrar_user":
            registrar = user.registrar
        case "admin_user":
            registrar = registrar_user.registrar

    response = submit_form(
        client,
        url=f"{reverse('user_management_registrar_user_add_user')}?email={registrar_user.email}",
        data={
            "a-registrar": registrar.id
        }
    )

    assert b"already a registrar user" in response.content


def test_registrar_user_cannot_change_registrar_users_registrar(client, registrar_user, registrar_user_factory):
    unrelated_registrar_user = registrar_user_factory()
    client.force_login(registrar_user)

    response = submit_form(
        client,
        url=f"{reverse('user_management_registrar_user_add_user')}?email={unrelated_registrar_user.email}",
        data={
            "a-registrar": registrar_user.registrar.id
        }
    )

    unrelated_registrar_user.refresh_from_db()
    assert b"is already a member" in response.content
    assert registrar_user.registrar != unrelated_registrar_user.registrar


def test_admin_user_can_change_registrar_users_registrar(client, admin_user, registrar_user, registrar_factory):
    unrelated_registrar = registrar_factory()
    client.force_login(admin_user)

    submit_form(
        client,
        url=f"{reverse('user_management_registrar_user_add_user')}?email={registrar_user.email}",
        data={
            "a-registrar": unrelated_registrar.id
        },
        success_url=reverse("user_management_manage_registrar_user"),
    )

    registrar_user.refresh_from_db()
    assert registrar_user.registrar == unrelated_registrar


@pytest.mark.parametrize(
    "user_type",
    [
        "registrar_user",
        "admin_user"
    ]
)
def test_can_upgrade_org_user_to_registrar(user_type, request, client, link_user):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "registrar_user":
            registrar = user.registrar
        case "admin_user":
            registrar = request.getfixturevalue("registrar")
    link_user.organizations.set([registrar.organizations.get()])
    assert link_user.is_organization_user

    submit_form(
        client,
        url=f"{reverse('user_management_registrar_user_add_user')}?email={link_user.email}",
        data={
            "a-registrar": registrar.id
        },
        success_url=reverse("user_management_manage_registrar_user")
    )

    link_user.refresh_from_db()
    assert link_user.registrar == registrar
    assert not link_user.organizations.exists()


def test_registrar_user_cannot_upgrade_unrelated_org_user_to_registrar(client, registrar_user, org_user):
    client.force_login(registrar_user)

    response = submit_form(
        client,
        url=f"{reverse('user_management_registrar_user_add_user')}?email={org_user.email}",
        data={
            "a-registrar": registrar_user.registrar.id
        }
    )

    assert b"belongs to organizations that are not controlled by your registrar" in response.content
    org_user.refresh_from_db()
    assert not org_user.registrar
    assert org_user.organizations.exists()


@pytest.mark.parametrize(
    "user_type",
    [
        "registrar_user",
        "admin_user"
    ]
)
def test_cannot_upgrade_multi_registrar_org_user_to_registrar(user_type, request, client, link_user, organization_factory):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "registrar_user":
            registrar = user.registrar
        case "admin_user":
            registrar = request.getfixturevalue("registrar")

    unrelated_org = organization_factory()
    link_user.organizations.set([registrar.organizations.get(), unrelated_org])
    assert link_user.organizations.count() == 2

    response = submit_form(
        client,
        url=f"{reverse('user_management_registrar_user_add_user')}?email={link_user.email}",
        data={
            "a-registrar": registrar.id
        }
    )

    assert b"You cannot make them a registrar" in response.content
    link_user.refresh_from_db()
    assert not link_user.registrar
    assert link_user.organizations.count() == 2


@pytest.mark.parametrize(
    "user_type",
    [
        "registrar_user",
        "admin_user"
    ]
)
def test_cannot_add_admin_user_to_registrar(user_type, request, client, admin_user_factory):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    admin_user = admin_user_factory()

    match user_type:
        case "registrar_user":
            registrar = user.registrar
        case "admin_user":
            registrar = request.getfixturevalue("registrar")

    response = submit_form(
        client,
        url=f"{reverse('user_management_registrar_user_add_user')}?email={admin_user.email}",
        data={
            "a-registrar": registrar.id
        }
    )

    assert b"is an admin user" in response.content
    admin_user.refresh_from_db()
    assert not admin_user.registrar
    assert admin_user.is_staff


###
### REMOVING REGISTRAR USERS ###
###

@pytest.mark.parametrize(
    "user_type",
    [
        "registrar_user",
        "admin_user"
    ]
)
def test_can_remove_user_from_registrar(user_type, request, client, link_user):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "registrar_user":
            registrar = user.registrar
        case "admin_user":
            registrar = request.getfixturevalue("registrar")
    link_user.registrar = registrar
    link_user.save()
    link_user.refresh_from_db()
    assert link_user.is_registrar_user()

    submit_form(
        client,
        url=reverse('user_management_manage_single_registrar_user_remove', args=[link_user.id]),
        success_url=reverse('user_management_manage_registrar_user')
    )

    link_user.refresh_from_db()
    assert not link_user.is_registrar_user()


def test_registrar_cannot_remove_unrelated_user_from_registrar(client, registrar_user_factory):
    registrar_user = registrar_user_factory()
    unrelated_registrar_user = registrar_user_factory()
    client.force_login(registrar_user)

    submit_form(
        client,
        url=reverse('user_management_manage_single_registrar_user_remove', args=[unrelated_registrar_user.id]),
        require_status_code=404
    )


def test_can_remove_self_from_registrar(client, registrar_user):
    client.force_login(registrar_user)

    submit_form(
        client,
        url=reverse('user_management_manage_single_registrar_user_remove', args=[registrar_user.id]),
        success_url=reverse('create_link')
    )

    registrar_user.refresh_from_db()
    assert not registrar_user.is_registrar_user()


###
### ADDING ADMINS ###
###

def test_admin_user_can_add_new_user_as_admin(client, admin_user, user_data):
    client.force_login(admin_user)

    submit_form(
        client,
        'user_management_admin_user_add_user',
        data={
            'a-first_name': user_data['first_name'],
            'a-last_name': user_data['last_name'],
            'a-address': user_data['email']
        },
        success_url=reverse('user_management_manage_admin_user'),
        success_query=LinkUser.objects.filter(
            email=user_data['normalized_email'],
            raw_email=user_data['email'],
            is_staff=True
        )
    )


def test_admin_user_can_add_existing_user_as_admin(client, admin_user, link_user):
    client.force_login(admin_user)

    submit_form(
        client,
        url=f"{reverse('user_management_admin_user_add_user')}?email={randomize_capitalization(link_user.email)}",
        success_url=reverse('user_management_manage_admin_user'),
        success_query=LinkUser.objects.filter(id=link_user.id, is_staff=True)
    )


### DEMOTING ADMINS ###

def test_can_remove_admin_privileges(client, admin_user_factory):
    admin_user = admin_user_factory()
    another_admin_user = admin_user_factory()
    assert another_admin_user.is_staff

    client.force_login(admin_user)
    submit_form(
        client,
        url=reverse('user_management_manage_single_admin_user_remove', args=[another_admin_user.id]),
        success_url=reverse('user_management_manage_admin_user')
    )

    another_admin_user.refresh_from_db()
    assert not another_admin_user.is_staff


def test_can_remove_own_admin_privileges(client, admin_user):
    assert admin_user.is_staff
    client.force_login(admin_user)
    submit_form(
        client,
        url=reverse('user_management_manage_single_admin_user_remove', args=[admin_user.id]),
        success_url=reverse('create_link')
    )

    admin_user.refresh_from_db()
    assert not admin_user.is_staff


###
### EXPORT USER LISTS
###


@pytest.mark.parametrize(
    "export_format,mime_type",
    [
        ('csv', 'text/csv'),
        ('json', 'application/json')
    ]
)
def test_org_export_user_list(export_format, mime_type, client, org_with_five_users):
    """Export all users in a single org"""

    # Log in as one of the org's users
    user = org_with_five_users.users.order_by('?').first()
    client.force_login(user)

    # Get the export output
    url = reverse(
        'user_management_manage_single_organization_export_user_list',
        args=[org_with_five_users.id]
    )
    response = client.get(
        url,
        data={'format': export_format},
        secure=True
    )
    assert response.status_code == 200
    assert response.headers['Content-Type'] == mime_type

    # Parse the output
    match export_format:
        case 'csv':
            csv_file = StringIO(response.content.decode('utf8'))
            reader = csv.DictReader(csv_file)
        case 'json':
            reader = json.loads(response.content)

    # Validate the output against the expected results
    reader_record_count = 0
    for record in reader:
        assert record['organization_name'] == org_with_five_users.name
        reader_record_count += 1
    assert reader_record_count == 5


@pytest.mark.parametrize(
    "export_format,mime_type",
    [
        ('csv', 'text/csv'),
        ('json', 'application/json')
    ]
)
def test_organization_user_export_user_list(flush_db, export_format, mime_type, client, admin_user, org_user_list):
    """Export all org users accessible to given user"""
    # Log in as an admin, to see the full list
    client.force_login(admin_user)

    # Get the export output
    response = client.get(
        reverse('user_management_manage_organization_user_export_user_list'),
        data={'format': export_format},
        secure=True
    )
    assert response.status_code == 200
    assert response.headers['Content-Type'] == mime_type

    # Parse the output
    match export_format:
        case 'csv':
            csv_file = StringIO(response.content.decode('utf8'))
            reader = csv.DictReader(csv_file)
        case 'json':
            reader = json.loads(response.content)

    # Validate the output against expected results
    for index, record in enumerate(reader):
        expected_email, expected_organization_name = org_user_list[index]
        assert record['email'] == expected_email
        assert record['organization_name'] == expected_organization_name
    assert index + 1 == len(org_user_list)


@pytest.mark.parametrize(
    "export_format,mime_type",
    [
        ('csv', 'text/csv'),
        ('json', 'application/json')
    ]
)
def test_sponsored_user_export_user_list(flush_db, export_format, mime_type, client, admin_user, sponsored_user_list):
    """Export all sponsored users accessible to given user"""
    # Log in as an admin, to see the full list
    client.force_login(admin_user)

    # Get the export output
    response = client.get(
        reverse('user_management_manage_sponsored_user_export_user_list'),
        data={'format': export_format},
        secure=True
    )
    assert response.status_code == 200
    assert response.headers['Content-Type'] == mime_type

    # Parse the output
    match export_format:
        case 'csv':
            csv_file = StringIO(response.content.decode('utf8'))
            reader = csv.DictReader(csv_file)
        case 'json':
            reader = json.loads(response.content)

    # Validate the output against expected results
    for index, record in enumerate(reader):
        expected_email, expected_sponsorship_status = sponsored_user_list[index]
        assert record['email'] == expected_email
        assert record['sponsorship_status'] == expected_sponsorship_status
    assert index + 1 == len(sponsored_user_list)


###
### RESENDING ACTIVATION EMAILS ###
###

def resend_should_succeed(client, target_user, mailoutbox):
    client.get(
        reverse(
            'user_management_resend_activation', args=[target_user.id]
        ),
        secure=True
    )

    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.subject == "A Perma.cc account has been created for you"
    assert message.recipients() == [target_user.raw_email]


def resend_should_fail(client, target_user, mailoutbox):
    response = client.get(
        reverse(
            'user_management_resend_activation', args=[target_user.id]
        ),
        secure=True
    )
    assert response.status_code == 403
    assert len(mailoutbox) == 0


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user",
        "admin_user"
    ]
)
def test_can_resend_activation_email_to_org_user(
    user_type,
    request,
    client,
    unactivated_user,
    mailoutbox
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "org_user":
            org = user.organizations.first()
        case "registrar_user":
            org = user.registrar.organizations.first()
        case "admin_user":
            org = request.getfixturevalue("organization")
    target_user = unactivated_user
    target_user.organizations.set([org])

    resend_should_succeed(client, target_user, mailoutbox)


@pytest.mark.parametrize(
    "user_type",
    [
        "org_user",
        "registrar_user"
    ]
)
def test_cannot_resend_activation_email_to_unrelated_org_user(
    user_type,
    request,
    client,
    unconfirmed_org_user_factory,
    mailoutbox
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    target_user = unconfirmed_org_user_factory()

    resend_should_fail(client, target_user, mailoutbox)


@pytest.mark.parametrize(
    "user_type",
    [
        "registrar_user",
        "admin_user"
    ]
)
def test_can_resend_activation_email_to_registrar_user(
    user_type,
    request,
    client,
    unactivated_user,
    mailoutbox
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)

    match user_type:
        case "registrar_user":
            registrar = user.registrar
        case "admin_user":
            registrar = request.getfixturevalue("registrar")
    target_user = unactivated_user
    target_user.registrar = registrar
    target_user.save()

    resend_should_succeed(client, target_user, mailoutbox)


def test_cannot_resend_activation_email_to_unrelated_registrar_user(
    client,
    registrar_user,
    unconfirmed_registrar_user_factory,
    mailoutbox
):
    client.force_login(registrar_user)
    target_user = unconfirmed_registrar_user_factory()

    resend_should_fail(client, target_user, mailoutbox)


def test_org_user_cannot_resend_activation_email_to_registrar_user(
    client,
    org_user,
    unconfirmed_registrar_user_factory,
    mailoutbox
):
    client.force_login(org_user)
    target_user = unconfirmed_registrar_user_factory(
        registrar=org_user.organizations.first().registrar
    )
    resend_should_fail(client, target_user, mailoutbox)


@pytest.mark.parametrize(
    "user_type",
    [
        "registrar_user",
        "org_user"
    ]
)
def test_cannot_resend_activation_email_to_regular_user(
    user_type,
    request,
    client,
    unactivated_user,
    mailoutbox
):
    user = request.getfixturevalue(user_type)
    client.force_login(user)
    target_user = unactivated_user

    resend_should_fail(client, target_user, mailoutbox)


def test_can_resend_activation_email_to_regular_user(
    client,
    admin_user,
    unactivated_user,
    mailoutbox
):
    client.force_login(admin_user)
    target_user = unactivated_user
    resend_should_succeed(client, target_user, mailoutbox)


class UserManagementViewsTestCase(PermaTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin_user = LinkUser.objects.get(pk=1)


    ### REGISTRAR A/E/D VIEWS ###

    def test_registrar_list_filters(self):
        # test assumptions: two registrars, one pending, one approved
        response = self.get('user_management_manage_registrar',
                             user=self.admin_user).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 4 registrars", count)
        self.assertEqual(response.count(b'needs approval'), 1)

        # get just approved registrars
        response = self.get('user_management_manage_registrar',
                             user=self.admin_user,
                             request_kwargs={'data':{'status':'approved'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 registrars", count)
        self.assertEqual(response.count(b'needs approval'), 0)

        # get just pending registrars
        response = self.get('user_management_manage_registrar',
                             user=self.admin_user,
                             request_kwargs={'data': {'status': 'pending'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 registrar", count)
        self.assertEqual(response.count(b'needs approval'), 1)

    def test_registrar_user_list_filters(self):
        # test assumptions: five users
        # - one deactivated
        # - one unactivated
        # - one from Test Library, three from Another Library, one from Test Firm
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 5 users", count)
        self.assertEqual(response.count(b'deactivated account'), 1)
        self.assertEqual(response.count(b'User must activate account'), 1)
        # registrar name appears by each user, and once in the filter dropdown
        self.assertEqual(response.count(b'Test Library'), 2)
        self.assertEqual(response.count(b'Another Library'), 4)
        self.assertEqual(response.count(b'Test Firm'), 2)

        # filter by registrar
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 1}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 2}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 users", count)
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 4}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)


        # filter by status
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'status': 'active'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 users", count)
        self.assertEqual(response.count(b'deactivated account'), 0)
        self.assertEqual(response.count(b'User must activate account'), 0)
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'status': 'deactivated'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        self.assertEqual(response.count(b'deactivated account'), 1)
        self.assertEqual(response.count(b'User must activate account'), 0)
        response = self.get('user_management_manage_registrar_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'status': 'unactivated'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        self.assertEqual(response.count(b'deactivated account'), 0)
        self.assertEqual(response.count(b'User must activate account'), 1)


    ### ORGANIZATION A/E/D VIEWS ###

    def test_organization_list_filters(self):
        # test assumptions: six orgs, three for Test Library and one for Another Library, two for Test Firm
        response = self.get('user_management_manage_organization',
                             user=self.admin_user).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 6 organizations", count)
        # registrar name appears by each org, once in the filter dropdown, once in the "add an org" markup
        self.assertEqual(response.count(b'Test Library'), 3 + 2)
        self.assertEqual(response.count(b'Test Firm'), 2 + 2)
        # 'Another Library' needs special handling because the fixture's org is
        # named 'Another Library's journal'. The "string" search finds the instance
        # by the org and the instance in the filter dropdown, but not the <option> in the "add an org" markup
        self.assertEqual(len(soup.find_all(string=re.compile(r"Another Library(?!')"))), 1 + 1)

        # get orgs for a single registrar
        response = self.get('user_management_manage_organization',
                             user=self.admin_user,
                             request_kwargs={'data': {'registrar': 1}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 organizations", count)
        response = self.get('user_management_manage_organization',
                             user=self.admin_user,
                             request_kwargs={'data': {'registrar': 2}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 organization", count)

    def test_org_user_list_filters(self):
        # test assumptions: seven users
        # - three from Test Journal
        # - one from Another Journal
        # - three from A Third Journal
        # - three from Another Library's Journal
        # - one from Some Case
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 7 users", count)
        # registrar name appears by each user, and once in the filter dropdown
        self.assertEqual(response.count(b'Test Journal'), 3 + 1)
        self.assertEqual(response.count(b'Another Journal'), 1 + 1)
        self.assertEqual(response.count(b"A Third Journal"), 3 + 1)
        self.assertEqual(response.count(b"Another Library&#x27;s Journal"), 3 + 1)
        self.assertEqual(response.count(b"Some Case"), 1 + 1)

        # filter by org
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'org': 1}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 users", count)
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'org': 2}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'org': 3}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 users", count)
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'org': 4}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 users", count)
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'org': 5}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)

        # filter by registrar
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 1}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 5 users", count)
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 2}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 3 users", count)
        response = self.get('user_management_manage_organization_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 4}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)

        # status filter tested in test_registrar_user_list_filters


    def test_sponsored_user_list_filters(self):
        # test assumptions: four users, with five sponsorships between them
        # - two users with active sponsorships, two users with inactive sponsorships
        # - two sponsored by Test Library, two from Another Library, one from A Third Library
        response = self.get('user_management_manage_sponsored_user',
                             user=self.admin_user).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 4 users", count)
        self.assertEqual(response.count(b'(inactive sponsorship)'), 2)
        # registrar name appears by each user, and once in the filter dropdown
        self.assertEqual(response.count(b'Test Library'), 3)
        self.assertEqual(response.count(b'Another Library'), 3)
        self.assertEqual(response.count(b'A Third Library'), 2)

        # filter by registrar
        response = self.get('user_management_manage_sponsored_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 1}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 2 users", count)
        response = self.get('user_management_manage_sponsored_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 2}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 2 users", count)
        response = self.get('user_management_manage_sponsored_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'registrar': 3}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)

        # filter by sponsorship status
        response = self.get('user_management_manage_sponsored_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'sponsorship_status': 'active'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 2 users", count)
        response = self.get('user_management_manage_sponsored_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'sponsorship_status': 'inactive'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 2 users", count)

        # user status filter tested in test_registrar_user_list_filters


    ### USER A/E/D VIEWS ###

    def test_user_list_filters(self):
        # test assumptions: nine users
        # - one aspiring court user, faculty user, journal user
        response = self.get('user_management_manage_user',
                             user=self.admin_user).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 9 users", count)
        self.assertEqual(response.count(b'Interested in a court account'), 1)
        self.assertEqual(response.count(b'Interested in a journal account'), 1)
        self.assertEqual(response.count(b'Interested in a faculty account'), 1)

        # filter by requested_account_type ("upgrade")
        response = self.get('user_management_manage_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'upgrade': 'court'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        self.assertEqual(response.count(b'Interested in a court account'), 1)
        self.assertEqual(response.count(b'Interested in a journal account'), 0)
        self.assertEqual(response.count(b'Interested in a faculty account'), 0)
        response = self.get('user_management_manage_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'upgrade': 'journal'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        self.assertEqual(response.count(b'Interested in a court account'), 0)
        self.assertEqual(response.count(b'Interested in a journal account'), 1)
        self.assertEqual(response.count(b'Interested in a faculty account'), 0)
        response = self.get('user_management_manage_user',
                             user=self.admin_user,
                             request_kwargs={'data':{'upgrade': 'faculty'}}).content
        soup = BeautifulSoup(response, 'html.parser')
        count = soup.select('.sort-filter-count')[0].text
        self.assertEqual("Found: 1 user", count)
        self.assertEqual(response.count(b'Interested in a court account'), 0)
        self.assertEqual(response.count(b'Interested in a journal account'), 0)
        self.assertEqual(response.count(b'Interested in a faculty account'), 1)

        # status filter tested in test_registrar_user_list_filters
