# Generated by Django 2.2.28 on 2022-10-03 20:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0004_auto_20220721_1600'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicallink',
            name='screenshot_view',
            field=models.BooleanField(default=False, help_text='User defaults to screenshot view.'),
        ),
        migrations.AddField(
            model_name='link',
            name='screenshot_view',
            field=models.BooleanField(default=False, help_text='User defaults to screenshot view.'),
        ),
    ]