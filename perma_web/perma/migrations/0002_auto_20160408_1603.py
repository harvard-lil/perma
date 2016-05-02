# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0001_initial'),
    ]

    operations = [
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
    ]
