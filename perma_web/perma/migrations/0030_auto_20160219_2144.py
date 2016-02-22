# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0029_auto_20160203_2024'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='asset',
            name='link',
        ),
        migrations.RemoveField(
            model_name='cdxline',
            name='asset',
        ),
        migrations.DeleteModel(
            name='Asset',
        ),
    ]
