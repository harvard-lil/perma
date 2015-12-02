# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0025_historicallink'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalLinkUser',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('email', models.EmailField(max_length=255, verbose_name=b'email address', db_index=True)),
                ('pending_registrar', models.IntegerField(null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_confirmed', models.BooleanField(default=False)),
                ('is_staff', models.BooleanField(default=False)),
                ('date_joined', models.DateField(editable=False, blank=True)),
                ('first_name', models.CharField(max_length=45, blank=True)),
                ('last_name', models.CharField(max_length=45, blank=True)),
                ('confirmation_code', models.CharField(max_length=45, blank=True)),
                ('requested_account_type', models.CharField(max_length=45, null=True, blank=True)),
                ('requested_account_note', models.CharField(max_length=45, null=True, blank=True)),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('history_user', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
                ('registrar', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='perma.Registrar', null=True)),
                ('root_folder', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='perma.Folder', null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical User',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HistoricalOrganization',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('name', models.CharField(max_length=400)),
                ('date_created', models.DateField(null=True, editable=False, blank=True)),
                ('default_to_private', models.BooleanField(default=False)),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('history_user', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
                ('registrar', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='perma.Registrar', null=True)),
                ('shared_folder', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='perma.Folder', null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical organization',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='HistoricalRegistrar',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('name', models.CharField(max_length=400)),
                ('email', models.EmailField(max_length=254)),
                ('website', models.URLField(max_length=500)),
                ('date_created', models.DateField(null=True, editable=False, blank=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('show_partner_status', models.BooleanField(default=False, help_text=b'Whether to show this registrar in our list of partners.')),
                ('partner_display_name', models.CharField(help_text=b"Optional. Use this to override 'name' for the partner list.", max_length=400, null=True, blank=True)),
                ('logo', models.TextField(max_length=100, null=True, blank=True)),
                ('latitude', models.FloatField(null=True, blank=True)),
                ('longitude', models.FloatField(null=True, blank=True)),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('default_organization', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='perma.Organization', null=True)),
                ('history_user', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical registrar',
            },
            bases=(models.Model,),
        ),
    ]
