# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0029_auto_20160203_2024'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalorganization',
            name='user_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicalorganization',
            name='user_deleted_timestamp',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='user_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='organization',
            name='user_deleted_timestamp',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='link',
            name='organization',
            field=models.ForeignKey(related_name='links', blank=True, to='perma.Organization', null=True),
        ),
    ]
