# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0033_auto_20160303_2215'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cdxline',
            name='link',
        ),
        migrations.AddField(
            model_name='cdxline',
            name='is_private',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='cdxline',
            name='is_unlisted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='cdxline',
            name='link_id',
            field=models.CharField(max_length=2100, null=True),
        ),
    ]
