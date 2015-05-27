# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def copy_vesting_org(apps, schema_editor):
    # Data migration. Copy all the foreign key values for linkuser/
    # vesting org to our new many to many field
    LinkUser = apps.get_model("perma", "LinkUser")
    for lu in LinkUser.objects.all():
    	if lu.vesting_org:
        	lu.vesting_org_new.add(lu.vesting_org)
        	lu.save()

class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0002_linkuser_vesting_org_new'),
    ]

    operations = [
    	migrations.RunPython(copy_vesting_org),
    ]
