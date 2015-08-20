# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0017_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='linkuser',
            name='organizations',
            field=models.ManyToManyField(help_text=b'If set, this user is an org member. This should not be set if registrar is set!', related_name='users', null=True, to='perma.Organization', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='linkuser',
            name='registrar',
            field=models.ForeignKey(related_name='users', blank=True, to='perma.Registrar', help_text=b'If set, this user is a registrar member. This should not be set if org is set!', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='organization',
            name='registrar',
            field=models.ForeignKey(related_name='organizations', to='perma.Registrar', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='organization',
            name='shared_folder',
            field=models.OneToOneField(related_name='organization_', null=True, blank=True, to='perma.Folder'),
            preserve_default=True,
        ),
    ]
