# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0028_auto_20151221_2145'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalregistrar',
            name='default_organization',
        ),
        migrations.RemoveField(
            model_name='registrar',
            name='default_organization',
        ),
    ]
