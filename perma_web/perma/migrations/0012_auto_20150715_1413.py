# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0011_auto_20150714_1531'),
    ]

    operations = [
        migrations.AlterField(
            model_name='linkuser',
            name='requested_account_note',
            field=models.CharField(max_length=45, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='linkuser',
            name='requested_account_type',
            field=models.CharField(max_length=45, null=True, blank=True),
            preserve_default=True,
        ),
    ]
