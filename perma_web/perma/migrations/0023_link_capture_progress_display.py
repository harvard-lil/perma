# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0022_link_archive_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='link',
            name='capture_progress_display',
            field=models.CharField(max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
    ]
