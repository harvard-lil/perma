# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0033_auto_20160303_2215'),
    ]

    operations = [
        migrations.CreateModel(
            name='UncaughtError',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('current_url', models.CharField(max_length=2100)),
                ('user_agent', models.TextField()),
                ('error_stack', models.TextField()),
                ('error_name', models.TextField()),
                ('error_message', models.TextField()),
                ('error_custom_message', models.TextField()),
                ('user_id', models.CharField(max_length=767)),
                ('error_date', models.DateTimeField()),
                ('resolved', models.BooleanField(default=False)),
            ],
        ),
    ]
