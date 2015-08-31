# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import timedelta

from django.db import models, migrations

def set_archive_timestamps(apps, schema_editor):
    from perma.models import Link
    for link in Link.objects.filter(user_deleted=False):
        link.archive_timestamp = link.creation_timestamp + timedelta(days=1)
        link.save()

class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0020_auto_20150827_1736'),
    ]

    operations = [
        migrations.RunPython(set_archive_timestamps),
    ]
