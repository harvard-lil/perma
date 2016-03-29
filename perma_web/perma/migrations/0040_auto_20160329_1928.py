# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0039_auto_20160329_1927'),
    ]

    operations = [
        migrations.RenameField(
            model_name='uncaughterror',
            old_name='user_id',
            new_name='user',
        ),
    ]
