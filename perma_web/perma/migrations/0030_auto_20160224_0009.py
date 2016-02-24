# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0029_auto_20160203_2024'),
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
                ('start_date', models.DateTimeField(auto_now_add=True)),
                ('end_date', models.DateTimeField(auto_now_add=True)),
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
            model_name='historicalregistrar',
            name='date_created',
            field=models.DateTimeField(null=True, editable=False, blank=True),
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
            model_name='registrar',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
