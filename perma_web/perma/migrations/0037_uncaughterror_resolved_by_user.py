# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0036_auto_20160329_1547'),
    ]

    operations = [
        migrations.AddField(
            model_name='uncaughterror',
            name='resolved_by_user',
            field=models.CharField(max_length=767, null=True),
        ),
    ]
