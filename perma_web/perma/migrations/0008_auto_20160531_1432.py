# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def sum_existing_links(apps, schema_editor):
    # We're now caching link counts. Let's use this function
    # to sum existing links and save them to the model

    LinkUser = apps.get_model("perma", "LinkUser")
    Link = apps.get_model("perma", "Link")
    Organization = apps.get_model("perma", "Organization")
    Registrar = apps.get_model("perma", "Registrar")


    for regular_user in LinkUser.objects.all():
        link_count = Link.objects.filter(created_by=regular_user).count()
        regular_user.link_count = link_count
        regular_user.save()

	for org in Organization.objects.all():
		link_count = Link.objects.filter(organization=org).count()
		org.link_count = link_count
		org.save()

	for registrar in Registrar.objects.all():
		link_count = Link.objects.filter(organization__registrar=registrar).count()
		registrar.link_count = link_count
		registrar.save()

class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0007_auto_20160527_1625'),
    ]

    operations = [
    	migrations.RunPython(sum_existing_links),
    ]

