# Generated by Django 4.2.8 on 2023-12-11 20:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('perma', '0035_link_ia_eligible_for_date_idx'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MinuteStats',
        ),
        migrations.DeleteModel(
            name='WeekStats',
        ),
    ]
