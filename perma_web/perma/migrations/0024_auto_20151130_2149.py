# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations, connection


def migrate_private(apps, schema_editor):
    cursor = connection.cursor()
    cursor.execute("update perma_link set is_private = dark_archived || dark_archived_robots_txt_blocked, private_reason=case when dark_archived then 'user' when dark_archived_robots_txt_blocked then 'policy' else private_reason end;")


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0023_auto_20151021_1840'),
    ]

    operations = [
        migrations.AddField(
            model_name='link',
            name='is_unlisted',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='link',
            name='private_reason',
            field=models.CharField(blank=True, max_length=10, null=True, choices=[(b'policy', b'Robots.txt or meta tag'), (b'user', b'At user direction'), (b'takedown', b'At request of content owner')]),
            preserve_default=True,
        ),
        migrations.RunPython(migrate_private),
        migrations.RemoveField(
            model_name='link',
            name='dark_archived',
        ),
        migrations.RemoveField(
            model_name='link',
            name='dark_archived_by',
        ),
        migrations.RemoveField(
            model_name='link',
            name='dark_archived_robots_txt_blocked',
        ),
    ]
