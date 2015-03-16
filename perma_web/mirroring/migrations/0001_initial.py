# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UpdateQueue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action', models.CharField(default=b'update', max_length=10, choices=[(b'update', b'update'), (b'delete', b'delete')])),
                ('json', models.TextField()),
                ('sent', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['pk'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FakeLinkUser',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('perma.linkuser',),
        ),
    ]
