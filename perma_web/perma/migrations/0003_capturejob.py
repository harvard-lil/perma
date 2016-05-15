# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0002_auto_20160408_1603'),
    ]

    operations = [
        migrations.CreateModel(
            name='CaptureJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(default=b'pending', max_length=15, choices=[(b'pending', b'pending'), (b'in_progress', b'in_progress'), (b'completed', b'completed'), (b'deleted', b'deleted'), (b'failed', b'failed')])),
                ('human', models.BooleanField(default=False)),
                ('attempt', models.SmallIntegerField(default=0)),
                ('step_count', models.FloatField(default=0)),
                ('step_description', models.CharField(max_length=255, null=True, blank=True)),
                ('capture_start_time', models.DateTimeField(null=True, blank=True)),
                ('capture_end_time', models.DateTimeField(null=True, blank=True)),
                ('link', models.OneToOneField(related_name='capture_job', to='perma.Link')),
            ],
        ),
    ]
