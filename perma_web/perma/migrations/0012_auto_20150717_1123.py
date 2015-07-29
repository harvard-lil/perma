# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0011_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='asset',
            name='integrity_check_succeeded',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='last_integrity_check',
        ),
    ]
