# Generated by Django 3.2.22 on 2023-10-31 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0028_auto_20230905_1813'),
    ]

    operations = [
        migrations.AddField(
            model_name='capturejob',
            name='scoop_job_id',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
    ]
