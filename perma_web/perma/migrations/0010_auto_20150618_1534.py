# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def approve_registrars(apps, schema_editor):
    # We can't import the Registrar model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Registrar = apps.get_model("perma", "Registrar")
    for registrar in Registrar.objects.all():
        registrar.is_approved = True
        registrar.save()


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0009_auto_20150618_1531'),
    ]

    operations = [
        migrations.RunPython(approve_registrars),
    ]
