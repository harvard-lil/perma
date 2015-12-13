# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0026_historicallinkuser_historicalorganization_historicalregistrar'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stat',
            old_name='unvested_count',
            new_name='link_count',
        ),
        migrations.RemoveField(
            model_name='historicallink',
            name='vested',
        ),
        migrations.RemoveField(
            model_name='historicallink',
            name='vested_by_editor',
        ),
        migrations.RemoveField(
            model_name='historicallink',
            name='vested_timestamp',
        ),
        migrations.RemoveField(
            model_name='link',
            name='vested',
        ),
        migrations.RemoveField(
            model_name='link',
            name='vested_by_editor',
        ),
        migrations.RemoveField(
            model_name='link',
            name='vested_timestamp',
        ),
        migrations.RemoveField(
            model_name='stat',
            name='darchive_robots_count',
        ),
        migrations.RemoveField(
            model_name='stat',
            name='darchive_takedown_count',
        ),
        migrations.RemoveField(
            model_name='stat',
            name='vested_count',
        ),
    ]
