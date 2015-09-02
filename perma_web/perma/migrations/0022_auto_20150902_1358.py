# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0021_auto_20150827_1816'),
    ]

    operations = [
        migrations.AlterField(
            model_name='link',
            name='archive_timestamp',
            field=models.DateTimeField(help_text=b'Date after which this link is eligible to be copied by the mirror network.', null=True, blank=True),
            preserve_default=True,
        ),
    ]
