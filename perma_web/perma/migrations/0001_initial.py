# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import mptt.fields
import django.db.models.deletion
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
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('email', models.EmailField(unique=True, max_length=255, verbose_name=b'email address', db_index=True)),
                ('pending_registrar', models.IntegerField(null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_confirmed', models.BooleanField(default=False)),
                ('is_staff', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
                ('first_name', models.CharField(max_length=45, blank=True)),
                ('last_name', models.CharField(max_length=45, blank=True)),
                ('confirmation_code', models.CharField(max_length=45, blank=True)),
                ('requested_account_type', models.CharField(max_length=45, null=True, blank=True)),
                ('requested_account_note', models.CharField(max_length=45, null=True, blank=True)),
            ],
            options={
                'verbose_name': 'User',
            },
        ),
        migrations.CreateModel(
            name='Capture',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(max_length=10, choices=[(b'primary', b'primary'), (b'screenshot', b'screenshot'), (b'favicon', b'favicon')])),
                ('status', models.CharField(max_length=10, choices=[(b'pending', b'pending'), (b'failed', b'failed'), (b'success', b'success')])),
                ('url', models.CharField(max_length=2100, null=True, blank=True)),
                ('record_type', models.CharField(max_length=10, choices=[(b'response', b'WARC Response record -- recorded from web'), (b'resource', b'WARC Resource record -- file without web headers')])),
                ('content_type', models.CharField(default=b'', help_text=b'HTTP Content-type header.', max_length=255)),
                ('user_upload', models.BooleanField(default=False, help_text=b'True if the user uploaded this capture.')),
            ],
        ),
        migrations.CreateModel(
            name='CDXLine',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('urlkey', models.CharField(max_length=2100)),
                ('raw', models.TextField()),
            ],
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
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HistoricalLink',
            fields=[
                ('user_deleted', models.BooleanField(default=False, verbose_name=b'Deleted by user')),
                ('user_deleted_timestamp', models.DateTimeField(null=True, blank=True)),
                ('guid', models.CharField(max_length=255, editable=False, db_index=True)),
                ('view_count', models.IntegerField(default=1)),
                ('submitted_url', models.URLField(max_length=2100)),
                ('creation_timestamp', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('submitted_title', models.CharField(max_length=2100)),
                ('notes', models.TextField(blank=True)),
                ('uploaded_to_internet_archive', models.BooleanField(default=False)),
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
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical link',
            },
        ),
        migrations.CreateModel(
            name='HistoricalLinkUser',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('email', models.EmailField(max_length=255, verbose_name=b'email address', db_index=True)),
                ('pending_registrar', models.IntegerField(null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_confirmed', models.BooleanField(default=False)),
                ('is_staff', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(editable=False, blank=True)),
                ('first_name', models.CharField(max_length=45, blank=True)),
                ('last_name', models.CharField(max_length=45, blank=True)),
                ('confirmation_code', models.CharField(max_length=45, blank=True)),
                ('requested_account_type', models.CharField(max_length=45, null=True, blank=True)),
                ('requested_account_note', models.CharField(max_length=45, null=True, blank=True)),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('history_user', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical User',
            },
        ),
        migrations.CreateModel(
            name='HistoricalOrganization',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('user_deleted', models.BooleanField(default=False, verbose_name=b'Deleted by user')),
                ('user_deleted_timestamp', models.DateTimeField(null=True, blank=True)),
                ('name', models.CharField(max_length=400)),
                ('date_created', models.DateTimeField(null=True, editable=False, blank=True)),
                ('default_to_private', models.BooleanField(default=False)),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('history_user', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical organization',
            },
        ),
        migrations.CreateModel(
            name='HistoricalRegistrar',
            fields=[
                ('id', models.IntegerField(verbose_name='ID', db_index=True, auto_created=True, blank=True)),
                ('name', models.CharField(max_length=400)),
                ('email', models.EmailField(max_length=254)),
                ('website', models.URLField(max_length=500)),
                ('date_created', models.DateTimeField(null=True, editable=False, blank=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('show_partner_status', models.BooleanField(default=False, help_text=b'Whether to show this registrar in our list of partners.')),
                ('partner_display_name', models.CharField(help_text=b"Optional. Use this to override 'name' for the partner list.", max_length=400, null=True, blank=True)),
                ('logo', models.TextField(max_length=100, null=True, blank=True)),
                ('latitude', models.FloatField(null=True, blank=True)),
                ('longitude', models.FloatField(null=True, blank=True)),
                ('history_id', models.AutoField(serialize=False, primary_key=True)),
                ('history_date', models.DateTimeField()),
                ('history_type', models.CharField(max_length=1, choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')])),
                ('history_user', models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical registrar',
            },
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('user_deleted', models.BooleanField(default=False, verbose_name=b'Deleted by user')),
                ('user_deleted_timestamp', models.DateTimeField(null=True, blank=True)),
                ('guid', models.CharField(max_length=255, serialize=False, editable=False, primary_key=True)),
                ('view_count', models.IntegerField(default=1)),
                ('submitted_url', models.URLField(max_length=2100)),
                ('creation_timestamp', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('submitted_title', models.CharField(max_length=2100)),
                ('notes', models.TextField(blank=True)),
                ('uploaded_to_internet_archive', models.BooleanField(default=False)),
                ('is_private', models.BooleanField(default=False)),
                ('private_reason', models.CharField(blank=True, max_length=10, null=True, choices=[(b'policy', b'Robots.txt or meta tag'), (b'user', b'At user direction'), (b'takedown', b'At request of content owner')])),
                ('is_unlisted', models.BooleanField(default=False)),
                ('archive_timestamp', models.DateTimeField(help_text=b'Date after which this link is eligible to be copied by the mirror network.', null=True, blank=True)),
                ('thumbnail_status', models.CharField(blank=True, max_length=10, null=True, choices=[(b'generating', b'generating'), (b'generated', b'generated'), (b'failed', b'failed')])),
                ('created_by', models.ForeignKey(related_name='created_links', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('folders', models.ManyToManyField(related_name='links', to='perma.Folder', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MinuteStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creation_timestamp', models.DateTimeField(auto_now_add=True)),
                ('links_sum', models.IntegerField(default=0)),
                ('users_sum', models.IntegerField(default=0)),
                ('organizations_sum', models.IntegerField(default=0)),
                ('registrars_sum', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_deleted', models.BooleanField(default=False, verbose_name=b'Deleted by user')),
                ('user_deleted_timestamp', models.DateTimeField(null=True, blank=True)),
                ('name', models.CharField(max_length=400)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('default_to_private', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Registrar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=400)),
                ('email', models.EmailField(max_length=254)),
                ('website', models.URLField(max_length=500)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('is_approved', models.BooleanField(default=False)),
                ('show_partner_status', models.BooleanField(default=False, help_text=b'Whether to show this registrar in our list of partners.')),
                ('partner_display_name', models.CharField(help_text=b"Optional. Use this to override 'name' for the partner list.", max_length=400, null=True, blank=True)),
                ('logo', models.ImageField(null=True, upload_to=b'registrar_logos', blank=True)),
                ('latitude', models.FloatField(null=True, blank=True)),
                ('longitude', models.FloatField(null=True, blank=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='WeekStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('links_sum', models.IntegerField(default=0)),
                ('users_sum', models.IntegerField(default=0)),
                ('organizations_sum', models.IntegerField(default=0)),
                ('registrars_sum', models.IntegerField(default=0)),
            ],
        ),
        migrations.AddField(
            model_name='organization',
            name='registrar',
            field=models.ForeignKey(related_name='organizations', to='perma.Registrar', null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='shared_folder',
            field=models.OneToOneField(related_name='organization_', null=True, blank=True, to='perma.Folder'),
        ),
        migrations.AddField(
            model_name='link',
            name='organization',
            field=models.ForeignKey(related_name='links', blank=True, to='perma.Organization', null=True),
        ),
        migrations.AddField(
            model_name='historicalorganization',
            name='registrar',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='perma.Registrar', null=True),
        ),
        migrations.AddField(
            model_name='historicalorganization',
            name='shared_folder',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='perma.Folder', null=True),
        ),
        migrations.AddField(
            model_name='historicallinkuser',
            name='registrar',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='perma.Registrar', null=True),
        ),
        migrations.AddField(
            model_name='historicallinkuser',
            name='root_folder',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='perma.Folder', null=True),
        ),
        migrations.AddField(
            model_name='historicallink',
            name='organization',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='perma.Organization', null=True),
        ),
        migrations.AddField(
            model_name='folder',
            name='organization',
            field=models.ForeignKey(related_name='folders', blank=True, to='perma.Organization', null=True),
        ),
        migrations.AddField(
            model_name='folder',
            name='owned_by',
            field=models.ForeignKey(related_name='folders', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='folder',
            name='parent',
            field=mptt.fields.TreeForeignKey(related_name='children', blank=True, to='perma.Folder', null=True),
        ),
        migrations.AddField(
            model_name='cdxline',
            name='link',
            field=models.ForeignKey(related_name='cdx_lines', to='perma.Link', null=True),
        ),
        migrations.AddField(
            model_name='capture',
            name='link',
            field=models.ForeignKey(related_name='captures', to='perma.Link'),
        ),
        migrations.AddField(
            model_name='linkuser',
            name='organizations',
            field=models.ManyToManyField(help_text=b'If set, this user is an org member. This should not be set if registrar is set!', related_name='users', to='perma.Organization', blank=True),
        ),
        migrations.AddField(
            model_name='linkuser',
            name='registrar',
            field=models.ForeignKey(related_name='users', blank=True, to='perma.Registrar', help_text=b'If set, this user is a registrar member. This should not be set if org is set!', null=True),
        ),
        migrations.AddField(
            model_name='linkuser',
            name='root_folder',
            field=models.OneToOneField(null=True, blank=True, to='perma.Folder'),
        ),
    ]
