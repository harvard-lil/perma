# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def set_archive_timestamps(apps, schema_editor):
    from perma.models import Link
    from django.conf import settings
    for link in Link.objects.filter(user_deleted=False):
        link.archive_timestamp = link.creation_timestamp + settings.ARCHIVE_DELAY
        link.save()

def reverse_archive_timestamps(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0021_link_is_private'),
    ]

    operations = [
        migrations.AddField(
            model_name='link',
            name='archive_timestamp',
            field=models.DateTimeField(help_text=b'Date after which this link is eligible to be copied by the mirror network.', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.RunPython(set_archive_timestamps, reverse_archive_timestamps),
    ]
