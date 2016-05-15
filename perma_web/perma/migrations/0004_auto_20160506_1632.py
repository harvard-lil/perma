# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0003_capturejob'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicallink',
            name='warc_size',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='link',
            name='warc_size',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
