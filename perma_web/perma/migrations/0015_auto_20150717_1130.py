# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0014_merge'),
    ]

    operations = [
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
                ('link', models.ForeignKey(related_name='captures', to='perma.Link')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='cdxline',
            name='link',
            field=models.ForeignKey(related_name='cdx_lines', to='perma.Link', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='link',
            name='thumbnail_status',
            field=models.CharField(blank=True, max_length=10, null=True, choices=[(b'generating', b'generating'), (b'generated', b'generated'), (b'failed', b'failed')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='cdxline',
            name='asset',
            field=models.ForeignKey(related_name='cdx_lines', to='perma.Asset', null=True),
            preserve_default=True,
        ),
    ]
