from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('perma', '0076_alter_historicallinkuser_options_and_more'),
        ('axes', '0009_add_session_hash'),
    ]

    # Retain the name already applied on staging. The project-owned Axes 0009
    # now creates the column with its persistent default in one transaction,
    # so Salt never sees a required column without a database default.
    operations = []
