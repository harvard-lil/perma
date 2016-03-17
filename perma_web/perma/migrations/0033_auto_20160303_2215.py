# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0032_auto_20160226_1946'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicallink',
            name='uploaded_to_internet_archive',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='link',
            name='uploaded_to_internet_archive',
            field=models.BooleanField(default=False),
        ),
    ]
