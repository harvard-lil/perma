# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def set_registrar_status(apps, schema_editor):
    Registrar = apps.get_model('perma', 'Registrar')
    Registrar.objects.filter(is_approved=True).update(status='approved')
    Registrar.objects.filter(is_approved=False).update(status='pending')
    HistoricalRegistrar = apps.get_model('perma','HistoricalRegistrar')
    HistoricalRegistrar.objects.filter(is_approved=True).update(status='approved')
    HistoricalRegistrar.objects.filter(is_approved=False).update(status='pending')

class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0007_auto_20160527_1625'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalregistrar',
            name='status',
            field=models.CharField(default=b'pending', max_length=20, choices=[(b'pending', b'pending'), (b'approved', b'approved'), (b'denied', b'denied')]),
        ),
        migrations.AddField(
            model_name='registrar',
            name='status',
            field=models.CharField(default=b'pending', max_length=20, choices=[(b'pending', b'pending'), (b'approved', b'approved'), (b'denied', b'denied')]),
        ),

        migrations.RunPython(set_registrar_status),

        migrations.RemoveField(
            model_name='historicalregistrar',
            name='is_approved',
        ),
        migrations.RemoveField(
            model_name='registrar',
            name='is_approved',
        ),
    ]
