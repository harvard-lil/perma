# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def update_upload_to_ia_field(apps, schema_editor):
    Link = apps.get_model('perma', 'Link')
    for link in Link.objects.all():
        if link.uploaded_to_internet_archive:
            link.internet_archive_upload_status = 'completed'
        elif not link.uploaded_to_internet_archive:
            link.internet_archive_upload_status = 'not_started'

        link.save()

    HistoricalLink = apps.get_model('perma','HistoricalLink')
    for hlink in HistoricalLink.objects.all():
        if hlink.uploaded_to_internet_archive:
            hlink.internet_archive_upload_status = 'completed'
        elif not hlink.uploaded_to_internet_archive:
            hlink.internet_archive_upload_status = 'not_started'

        hlink.save()


def reverse_update_upload_to_ia_field(apps, schema_editor):
    Link = apps.get_model('perma', 'Link')
    for link in Link.objects.all():
        if link.internet_archive_upload_status == 'completed':
            link.uploaded_to_internet_archive = True
        else:
            link.uploaded_to_internet_archive = False
    link.save()
class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0005_auto_20160513_2006'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicallink',
            name='internet_archive_upload_status',
            field=models.CharField(default=b'not_started', max_length=15, choices=[(b'not_started', b'not_started'), (b'completed', b'completed'), (b'failed', b'failed'), (b'failed_permanently', b'failed_permanently'), (b'deleted', b'deleted')]),
        ),
        migrations.AddField(
            model_name='link',
            name='internet_archive_upload_status',
            field=models.CharField(default=b'not_started', max_length=15, choices=[(b'not_started', b'not_started'), (b'completed', b'completed'), (b'failed', b'failed'), (b'failed_permanently', b'failed_permanently'), (b'deleted', b'deleted')]),
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
# class Migration(migrations.Migration):
#
#     dependencies = [
#         ('perma', '0006_add_internetarchive_status'),
#     ]
#
#     operations = [
#         migrations.RemoveField(
#             model_name='historicallink',
#             name='uploaded_to_internet_archive',
#         ),
#         migrations.RemoveField(
#             model_name='link',
#             name='uploaded_to_internet_archive',
#         ),
#         migrations.AddField(
#             model_name='historicallink',
#             name='internet_archive_upload_status',
#             field=models.CharField(default=b'not_started', max_length=15, choices=[(b'not_started', b'not_started'), (b'completed', b'completed'), (b'failed', b'failed'), (b'failed_permanently', b'failed_permanently'), (b'deleted', b'deleted')]),
#         ),
#         migrations.AddField(
#             model_name='link',
#             name='internet_archive_upload_status',
#             field=models.CharField(default=b'not_started', max_length=15, choices=[(b'not_started', b'not_started'), (b'completed', b'completed'), (b'failed', b'failed'), (b'failed_permanently', b'failed_permanently'), (b'deleted', b'deleted')]),
#         ),
#     ]
