# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='linkuser',
            name='vesting_org_new',
            field=models.ManyToManyField(help_text=b'If set, this user is a vesting org member. This should not be set if registrar is set!', related_name='users_new', null=True, to='perma.VestingOrg', blank=True),
            preserve_default=True,
        ),
    ]
