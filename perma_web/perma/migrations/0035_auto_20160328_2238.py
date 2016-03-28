# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0034_uncaughterror'),
    ]

    operations = [
        migrations.RenameField(
            model_name='uncaughterror',
            old_name='error_date',
            new_name='created_at',
        ),
        migrations.AlterField(
            model_name='uncaughterror',
            name='current_url',
            field=models.TextField(),
        ),
    ]
