# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0037_uncaughterror_resolved_by_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uncaughterror',
            name='user_id',
            field=models.CharField(max_length=767, null=True),
        ),
    ]
