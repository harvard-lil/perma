# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import mptt.fields
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LinkUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('email', models.EmailField(unique=True, max_length=255, verbose_name=b'email address', db_index=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_confirmed', models.BooleanField(default=False)),
                ('is_staff', models.BooleanField(default=False)),
                ('date_joined', models.DateField(auto_now_add=True)),
                ('first_name', models.CharField(max_length=45, blank=True)),
                ('last_name', models.CharField(max_length=45, blank=True)),
                ('confirmation_code', models.CharField(max_length=45, blank=True)),
            ],
            options={
                'verbose_name': 'User',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('base_storage_path', models.CharField(max_length=2100, null=True, blank=True)),
                ('favicon', models.CharField(max_length=2100, null=True, blank=True)),
                ('image_capture', models.CharField(max_length=2100, null=True, blank=True)),
                ('warc_capture', models.CharField(max_length=2100, null=True, blank=True)),
                ('pdf_capture', models.CharField(max_length=2100, null=True, blank=True)),
                ('text_capture', models.CharField(max_length=2100, null=True, blank=True)),
                ('instapaper_timestamp', models.DateTimeField(null=True)),
                ('instapaper_hash', models.CharField(max_length=2100, null=True)),
                ('instapaper_id', models.IntegerField(null=True)),
                ('last_integrity_check', models.DateTimeField(null=True, blank=True)),
                ('integrity_check_succeeded', models.NullBooleanField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Folder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('creation_timestamp', models.DateTimeField(auto_now_add=True)),
                ('is_shared_folder', models.BooleanField(default=False)),
                ('is_root_folder', models.BooleanField(default=False)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('created_by', models.ForeignKey(related_name='folders_created', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('owned_by', models.ForeignKey(related_name='folders', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('parent', mptt.fields.TreeForeignKey(related_name='children', blank=True, to='perma.Folder', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('guid', models.CharField(max_length=255, serialize=False, editable=False, primary_key=True)),
                ('view_count', models.IntegerField(default=1)),
                ('submitted_url', models.URLField(max_length=2100)),
                ('creation_timestamp', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('submitted_title', models.CharField(max_length=2100)),
                ('dark_archived', models.BooleanField(default=False)),
                ('dark_archived_robots_txt_blocked', models.BooleanField(default=False)),
                ('user_deleted', models.BooleanField(default=False)),
                ('user_deleted_timestamp', models.DateTimeField(null=True, blank=True)),
                ('vested', models.BooleanField(default=False)),
                ('vested_timestamp', models.DateTimeField(null=True, blank=True)),
                ('notes', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(related_name='created_links', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('dark_archived_by', models.ForeignKey(related_name='darchived_links', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('folders', models.ManyToManyField(related_name='links', null=True, to='perma.Folder', blank=True)),
                ('vested_by_editor', models.ForeignKey(related_name='vested_links', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Registrar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=400)),
                ('email', models.EmailField(max_length=254)),
                ('website', models.URLField(max_length=500)),
                ('date_created', models.DateField(auto_now_add=True, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Stat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creation_timestamp', models.DateTimeField(auto_now_add=True)),
                ('regular_user_count', models.IntegerField(default=1)),
                ('vesting_member_count', models.IntegerField(default=1)),
                ('vesting_manager_count', models.IntegerField(default=1)),
                ('registrar_member_count', models.IntegerField(default=1)),
                ('registry_member_count', models.IntegerField(default=1)),
                ('vesting_org_count', models.IntegerField(default=1)),
                ('registrar_count', models.IntegerField(default=1)),
                ('unvested_count', models.IntegerField(default=1)),
                ('vested_count', models.IntegerField(default=1)),
                ('darchive_takedown_count', models.IntegerField(default=0)),
                ('darchive_robots_count', models.IntegerField(default=0)),
                ('global_uniques', models.IntegerField(default=1)),
                ('disk_usage', models.FloatField(default=0.0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VestingOrg',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=400)),
                ('date_created', models.DateField(auto_now_add=True, null=True)),
                ('registrar', models.ForeignKey(related_name='vesting_orgs', to='perma.Registrar', null=True)),
                ('shared_folder', models.OneToOneField(null=True, blank=True, to='perma.Folder')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='registrar',
            name='default_vesting_org',
            field=models.OneToOneField(related_name='default_for_registrars', null=True, blank=True, to='perma.VestingOrg'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='link',
            name='vesting_org',
            field=models.ForeignKey(blank=True, to='perma.VestingOrg', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='folder',
            name='vesting_org',
            field=models.ForeignKey(related_name='folders', blank=True, to='perma.VestingOrg', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='asset',
            name='link',
            field=models.ForeignKey(related_name='assets', to='perma.Link'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='linkuser',
            name='registrar',
            field=models.ForeignKey(related_name='users', blank=True, to='perma.Registrar', help_text=b'If set, this user is a registrar member. This should not be set if vesting org is set!', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='linkuser',
            name='root_folder',
            field=models.OneToOneField(null=True, blank=True, to='perma.Folder'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='linkuser',
            name='vesting_org',
            field=models.ForeignKey(related_name='users', blank=True, to='perma.VestingOrg', help_text=b'If set, this user is a vesting org member. This should not be set if registrar is set!', null=True),
            preserve_default=True,
        ),
    ]
