from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('perma', '0076_alter_historicallinkuser_options_and_more'),
        ('axes', '0009_add_session_hash'),
    ]

    operations = [
        # Axes 0009 drops its temporary default after adding this NOT NULL
        # column. Older Axes versions omit it when logging successful logins,
        # so retain a database default for temporary application rollbacks.
        # This deliberately leaves the third-party model state unchanged.
        migrations.RunSQL(
            sql="ALTER TABLE axes_accesslog ALTER COLUMN session_hash SET DEFAULT '';",
            reverse_sql="ALTER TABLE axes_accesslog ALTER COLUMN session_hash DROP DEFAULT;",
        ),
    ]
