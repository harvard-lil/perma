# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0005_auto_20150407_1552'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='linkuser',
            name='vesting_org_old',
        ),
    ]
