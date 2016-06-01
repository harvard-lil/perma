# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0006_add_internetarchive_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicallinkuser',
            name='link_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='historicalorganization',
            name='link_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='historicalregistrar',
            name='link_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='linkuser',
            name='link_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='organization',
            name='link_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='registrar',
            name='link_count',
            field=models.IntegerField(default=0),
        )
    ]
