# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def update_upload_to_ia_field(apps, schema_editor):
    Link = apps.get_model('perma', 'Link')
    Link.objects.filter(uploaded_to_internet_archive=True).update(internet_archive_upload_status='completed')
    Link.objects.filter(uploaded_to_internet_archive=False).update(internet_archive_upload_status='not_started')
    HistoricalLink = apps.get_model('perma','HistoricalLink')
    HistoricalLink.objects.filter(uploaded_to_internet_archive=True).update(internet_archive_upload_status='completed')
    HistoricalLink.objects.filter(uploaded_to_internet_archive=False).update(internet_archive_upload_status='not_started')

def reverse_update_upload_to_ia_field(apps, schema_editor):
    Link = apps.get_model('perma', 'Link')
    Link.objects.filter(internet_archive_upload_status='completed').update(uploaded_to_internet_archive=True)
    Link.objects.filter(
        Q(internet_archive_upload_status='deleted') | Q(internet_archive_upload_status='not_started') | Q(internet_archive_upload_status='failed') | Q(internet_archive_upload_status='failed_permanently')
        ).update(uploaded_to_internet_archive=False)

    HistoricalLink = apps.get_model('perma', 'HistoricalLink')
    HistoricalLink.objects.filter(internet_archive_upload_status='completed').update(uploaded_to_internet_archive=True)
    HistoricalLink.objects.filter(
        Q(internet_archive_upload_status='deleted') | Q(internet_archive_upload_status='not_started') | Q(internet_archive_upload_status='failed') | Q(internet_archive_upload_status='failed_permanently')
        ).update(uploaded_to_internet_archive=False)

class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0005_auto_20160513_2006'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicallink',
            name='internet_archive_upload_status',
            field=models.CharField(default=b'not_started', max_length=20, choices=[(b'not_started', b'not_started'), (b'completed', b'completed'), (b'failed', b'failed'), (b'failed_permanently', b'failed_permanently'), (b'deleted', b'deleted')]),
        ),
        migrations.AddField(
            model_name='link',
            name='internet_archive_upload_status',
            field=models.CharField(default=b'not_started', max_length=20, choices=[(b'not_started', b'not_started'), (b'completed', b'completed'), (b'failed', b'failed'), (b'failed_permanently', b'failed_permanently'), (b'deleted', b'deleted')]),
        ),

        migrations.RunPython(update_upload_to_ia_field, reverse_code=reverse_update_upload_to_ia_field),

        migrations.RemoveField(
            model_name='historicallink',
            name='uploaded_to_internet_archive',
        ),
        migrations.RemoveField(
            model_name='link',
            name='uploaded_to_internet_archive',
        ),

     ]
