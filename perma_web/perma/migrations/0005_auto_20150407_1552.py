# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0004_auto_20150407_1548'),
    ]

    operations = [
        migrations.RenameField(
            model_name='linkuser',
            old_name='vesting_org_new',
            new_name='vesting_org',
        ),
    ]
