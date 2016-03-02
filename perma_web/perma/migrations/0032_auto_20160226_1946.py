# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0031_merge'),
    ]

    operations = [
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
        migrations.DeleteModel(
            name='Stat',
        ),
        migrations.AlterField(
            model_name='historicallink',
            name='user_deleted',
            field=models.BooleanField(default=False, verbose_name=b'Deleted by user'),
        ),
        migrations.AlterField(
            model_name='historicallinkuser',
            name='date_joined',
            field=models.DateTimeField(editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='historicalorganization',
            name='date_created',
            field=models.DateTimeField(null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='historicalorganization',
            name='user_deleted',
            field=models.BooleanField(default=False, verbose_name=b'Deleted by user'),
        ),
        migrations.AlterField(
            model_name='historicalregistrar',
            name='date_created',
            field=models.DateTimeField(null=True, editable=False, blank=True),
        ),
        migrations.AlterField(
            model_name='link',
            name='user_deleted',
            field=models.BooleanField(default=False, verbose_name=b'Deleted by user'),
        ),
        migrations.AlterField(
            model_name='linkuser',
            name='date_joined',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='organization',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='organization',
            name='user_deleted',
            field=models.BooleanField(default=False, verbose_name=b'Deleted by user'),
        ),
        migrations.AlterField(
            model_name='registrar',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
