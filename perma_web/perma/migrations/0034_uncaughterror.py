# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0033_auto_20160303_2215'),
    ]

    operations = [
        migrations.CreateModel(
            name='UncaughtError',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('current_url', models.TextField()),
                ('user_agent', models.TextField()),
                ('stack', models.TextField()),
                ('name', models.TextField()),
                ('message', models.TextField()),
                ('custom_message', models.TextField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('resolved', models.BooleanField(default=False)),
                ('resolved_by_user', models.CharField(max_length=767, null=True)),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
    ]
