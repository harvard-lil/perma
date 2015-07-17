# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0012_rename_org_model'),
    ]

    operations = [

        migrations.RenameField(
            model_name='registrar',
            old_name='default_vesting_org',
            new_name='default_organization',
        ),
        migrations.RenameField(
            model_name='linkuser',
            old_name='vesting_org',
            new_name='organizations',
        ),
        migrations.RenameField(
            model_name='folder',
            old_name='vesting_org',
            new_name='organization',
        ),
        migrations.RenameField(
            model_name='link',
            old_name='vesting_org',
            new_name='organization',
        ),
        
        migrations.RenameField(
            model_name='stat',
            old_name='vesting_org_count',
            new_name='org_count',
        ),
        migrations.RenameField(
            model_name='stat',
            old_name='vesting_manager_count',
            new_name='org_manager_count',
        ),
        migrations.RenameField(
            model_name='stat',
            old_name='vesting_member_count',
            new_name='org_member_count',
        ),
    ]
