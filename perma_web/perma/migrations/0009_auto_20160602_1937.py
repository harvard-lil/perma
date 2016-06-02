# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0008_auto_20160602_1911'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicallinkuser',
            name='pending_registrar',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='perma.Registrar', null=True),
        ),
        migrations.AlterField(
            model_name='linkuser',
            name='pending_registrar',
            field=models.ForeignKey(related_name='pending_users', blank=True, to='perma.Registrar', null=True),
        ),
    ]
