# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0003_auto_20150407_1506'),
    ]

    operations = [
        migrations.RenameField(
            model_name='linkuser',
            old_name='vesting_org',
            new_name='vesting_org_old',
        ),
    ]
