# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.core.exceptions import ObjectDoesNotExist


def rename_test_accounts(apps, schema_editor):
    # We're statndarding our test accounts to be *_user
    # and not *_member

    LinkUser = apps.get_model("perma", "LinkUser")

    try:
        lu = LinkUser.objects.get(email='test_admin_member@example.com')
        lu.email = 'test_admin_user@example.com'
        lu.last_name = 'User'
        lu.save()
    except ObjectDoesNotExist:
        pass

    try:
        lu = LinkUser.objects.get(email='test_registrar_member@example.com')
        lu.email = 'test_registrar_user@example.com'
        lu.last_name = 'User'
        lu.save()
    except ObjectDoesNotExist:
        pass

    try:
        lu = LinkUser.objects.get(email='test_org_user@example.com')
        lu.last_name = 'User'
        lu.save()
    except ObjectDoesNotExist:
        pass

    try:
        lu = LinkUser.objects.get(email='test_org_manager@example.com')
        lu.email = 'test_org_rando_user@example.com'
        lu.first_name = 'Org-Rando'
        lu.last_name = 'User'
        lu.save()
    except ObjectDoesNotExist:
        pass

    try:
        lu = LinkUser.objects.get(email='test_another_org_member@example.com')
        lu.email = 'test_another_org_user@example.com'
        lu.last_name = 'User'
        lu.save()
    except ObjectDoesNotExist:
        pass

    try:
        lu = LinkUser.objects.get(email='test_another_library_org_member@example.com')
        lu.email = 'test_another_library_org_user@example.com'
        lu.last_name = 'Organization-User'
        lu.save()
    except ObjectDoesNotExist:
        pass


    try:
        lu = LinkUser.objects.get(email='another_library_member@example.com')
        lu.email = 'another_library_user@example.com'
        lu.last_name = 'User'
        lu.save()
    except ObjectDoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0009_auto_20160602_1937'),
    ]

    operations = [
        migrations.RunPython(rename_test_accounts),
    ]
