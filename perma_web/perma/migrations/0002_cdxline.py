# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CDXLine',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('urlkey', models.URLField(max_length=2100)),
                ('raw', models.TextField()),
                ('asset', models.ForeignKey(related_name='cdx_lines', to='perma.Asset')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
