# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.core.exceptions import ObjectDoesNotExist


def rename_folders_helper(apps, schema_editor, old, new):
    Folder = apps.get_model("perma", "Folder")
    try:
        folders = Folder.objects.filter(name=old, is_root_folder=True)
        folders.update(name=new)
    except ObjectDoesNotExist:
        pass

def rename_folders(apps, schema_editor):
    rename_folders_helper(apps, schema_editor, "My Links", "Personal Links")

def reverse_rename_folders(apps, schema_editor):
    rename_folders_helper(apps, schema_editor, "Personal Links", "My Links")

class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0016_auto_20161004_2215'),
    ]

    operations = [
        migrations.RunPython(rename_folders, reverse_code=reverse_rename_folders)
    ]
