# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0020_auto_20150923_1514'),
    ]

    operations = [
        migrations.AddField(
            model_name='link',
            name='is_private',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
