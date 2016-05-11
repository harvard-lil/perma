# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0002_auto_20160408_1603'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicallinkuser',
            name='email',
            field=models.EmailField(db_index=True, max_length=255, verbose_name=b'email address', error_messages={b'unique': 'A user with that email address already exists.'}),
        ),
        migrations.AlterField(
            model_name='historicallinkuser',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='linkuser',
            name='email',
            field=models.EmailField(db_index=True, unique=True, max_length=255, verbose_name=b'email address', error_messages={b'unique': 'A user with that email address already exists.'}),
        ),
        migrations.AlterField(
            model_name='linkuser',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
