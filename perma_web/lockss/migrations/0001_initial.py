# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Mirror',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('ip', models.CharField(help_text=b'E.g. 12.34.56.78', max_length=15)),
                ('hostname', models.CharField(help_text=b'E.g. mirror.example.com', max_length=255)),
                ('peer_port', models.IntegerField(default=9729, help_text=b'Port where this mirror listens for other LOCKSS nodes.')),
                ('content_url', models.URLField(help_text=b'E.g. https://mirror.example.edu:8080/', max_length=255)),
                ('enabled', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
    ]
