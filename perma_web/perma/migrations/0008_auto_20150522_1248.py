# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0007_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='asset',
            name='instapaper_hash',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='instapaper_id',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='instapaper_timestamp',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='text_capture',
        ),
        migrations.AddField(
            model_name='asset',
            name='user_upload',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='asset',
            name='user_upload_file_name',
            field=models.CharField(max_length=2100, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='linkuser',
            name='vesting_org',
            field=models.ManyToManyField(help_text=b'If set, this user is a vesting org member. This should not be set if registrar is set!', to='perma.VestingOrg', null=True, blank=True),
            preserve_default=True,
        ),
    ]
