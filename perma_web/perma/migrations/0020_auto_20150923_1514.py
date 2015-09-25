# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0019_auto_20150825_1833'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='registrar',
            options={'ordering': ['name']},
        ),
        migrations.AddField(
            model_name='organization',
            name='default_to_private',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='cdxline',
            name='urlkey',
            field=models.CharField(max_length=2100),
            preserve_default=True,
        ),
    ]
