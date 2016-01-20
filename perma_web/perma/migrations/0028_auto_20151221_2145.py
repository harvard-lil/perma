# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0027_auto_20151210_2328'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicallinkuser',
            name='last_login',
            field=models.DateTimeField(null=True, verbose_name='last login', blank=True),
        ),
        migrations.AlterField(
            model_name='link',
            name='folders',
            field=models.ManyToManyField(related_name='links', to='perma.Folder', blank=True),
        ),
        migrations.AlterField(
            model_name='linkuser',
            name='last_login',
            field=models.DateTimeField(null=True, verbose_name='last login', blank=True),
        ),
        migrations.AlterField(
            model_name='linkuser',
            name='organizations',
            field=models.ManyToManyField(help_text=b'If set, this user is an org member. This should not be set if registrar is set!', related_name='users', to='perma.Organization', blank=True),
        ),
    ]
