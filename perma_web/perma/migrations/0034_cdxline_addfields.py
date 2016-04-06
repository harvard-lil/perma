# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def forwards(apps, schema_editor):
    CDXLine = apps.get_model("perma", "CDXLine")

    for cdxline in CDXLine.objects.using('perma_cdxline').all():
        cdxline.link_reference = cdxline.link_id
        cdxline.save(using='perma-cdxline')

class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0033_auto_20160303_2215'),
    ]

    operations = [
        migrations.AddField(
            model_name='cdxline',
            name='is_private',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='cdxline',
            name='is_unlisted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='cdxline',
            name='link_reference',
            field=models.CharField(max_length=2100, null=True),
        ),
        migrations.RunPython(forwards, hints={'target_db':'perma-cdxline'})
    ]
