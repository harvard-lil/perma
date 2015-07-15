# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0010_auto_20150618_1534'),
    ]

    operations = [
        migrations.AddField(
            model_name='linkuser',
            name='requested_account_note',
            field=models.CharField(max_length=45, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='linkuser',
            name='requested_account_type',
            field=models.CharField(max_length=45, blank=True),
            preserve_default=True,
        ),
    ]
