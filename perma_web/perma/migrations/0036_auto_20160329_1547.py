# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0035_auto_20160328_2238'),
    ]

    operations = [
        migrations.RenameField(
            model_name='uncaughterror',
            old_name='error_custom_message',
            new_name='custom_message',
        ),
        migrations.RenameField(
            model_name='uncaughterror',
            old_name='error_message',
            new_name='message',
        ),
        migrations.RenameField(
            model_name='uncaughterror',
            old_name='error_name',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='uncaughterror',
            old_name='error_stack',
            new_name='stack',
        ),
    ]
