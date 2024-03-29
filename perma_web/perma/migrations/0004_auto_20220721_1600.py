# Generated by Django 2.2.28 on 2022-07-21 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0003_auto_20220120_1522'),
    ]

    operations = [
        migrations.AlterField(
            model_name='registrar',
            name='logo',
            # This originally saved to f"registrar_logos/{instance.id}/{filename}",
            # but since this functionality has since been removed, that utility
            # function has been replaced, and the reference to it in this old migration
            # has been replaced with a placeholder string.
            field=models.ImageField(blank=True, null=True, upload_to='some/path'),
        ),
    ]
