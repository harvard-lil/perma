# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0009_auto_20160602_1937'),
    ]

    operations = [
        migrations.AlterField(
            model_name='weekstats',
            name='end_date',
            field=models.DateTimeField(null=True),
        ),
    ]
