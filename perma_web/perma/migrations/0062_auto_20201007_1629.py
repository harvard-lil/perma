# Generated by Django 2.2.16 on 2020-10-07 16:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0061_auto_20200618_1803'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicallinkuser',
            name='confirmation_code',
        ),
        migrations.RemoveField(
            model_name='linkuser',
            name='confirmation_code',
        ),
    ]