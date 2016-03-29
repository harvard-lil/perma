# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0038_auto_20160329_1858'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uncaughterror',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='uncaughterror',
            name='user_id',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
