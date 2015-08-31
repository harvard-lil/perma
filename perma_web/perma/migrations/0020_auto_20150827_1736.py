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
            model_name='link',
            name='archive_timestamp',
            field=models.DateTimeField(help_text=b'Date on which this link was published to the mirror network.', null=True, blank=True),
            preserve_default=True,
        ),
    ]
