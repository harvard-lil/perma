# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0018_auto_20150820_1249'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrar',
            name='logo',
            field=models.ImageField(null=True, upload_to=b'registrar_logos', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='registrar',
            name='partner_display_name',
            field=models.CharField(help_text=b"Optional. Use this to override 'name' for the partner list.", max_length=400, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='registrar',
            name='show_partner_status',
            field=models.BooleanField(default=False, help_text=b'Whether to show this registrar in our list of partners.'),
            preserve_default=True,
        ),
    ]
