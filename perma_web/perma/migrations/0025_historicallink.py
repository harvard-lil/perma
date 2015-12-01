# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0024_auto_20151130_2149'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalLink',
            fields=[
                ('guid', models.CharField(max_length=255, editable=False, db_index=True)),
                ('view_count', models.IntegerField(default=1)),
                ('submitted_url', models.URLField(max_length=2100)),
                ('creation_timestamp', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('submitted_title', models.CharField(max_length=2100)),
                ('user_deleted', models.BooleanField(default=False)),
                ('user_deleted_timestamp', models.DateTimeField(null=True, blank=True)),
                ('vested', models.BooleanField(default=False)),
                ('vested_timestamp', models.DateTimeField(null=True, blank=True)),
                ('notes', models.TextField(blank=True)),
                ('is_private', models.BooleanField(default=False)),
                ('private_reason', models.CharField(blank=True, max_length=10, null=True, choices=[(b'policy', b'Robots.txt or meta tag'), (b'user', b'At user direction'), (b'takedown', b'At request of content owner')])),
                ('is_unlisted', models.BooleanField(default=False)),
                ('archive_timestamp', models.DateTimeField(help_text=b'Date after which this link is eligible to be copied by the mirror network.', null=True, blank=True)),
                ('thumbnail_status', models.CharField(blank=True, max_length=10, null=True, choices=[(b'generating', b'generating'), (b'generated', b'generated'), (b'failed', b'failed')])),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('created_by', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('history_user', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
                ('organization', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='perma.Organization', null=True)),
                ('vested_by_editor', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical link',
            },
            bases=(models.Model,),
        ),
    ]
