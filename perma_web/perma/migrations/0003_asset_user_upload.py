# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0002_cdxline'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='user_upload',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
