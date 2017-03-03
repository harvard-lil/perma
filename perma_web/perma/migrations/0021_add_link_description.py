# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0020_auto_20170301_1614'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicallink',
            name='submitted_description',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='link',
            name='submitted_description',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]
