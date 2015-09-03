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
        migrations.AlterField(
            model_name='cdxline',
            name='urlkey',
            field=models.URLField(max_length=2100, db_index=True),
            preserve_default=True,
        ),
    ]
