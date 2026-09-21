from importlib import import_module

from django.db import migrations

upstream = import_module("axes.migrations.0009_add_session_hash")


class Migration(upstream.Migration):
    # Salt's Axes version omits session_hash when inserting login logs. Keep
    # the database default from the instant the new NOT NULL column appears.
    # Preserve upstream model state: this is a database compatibility default.
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE axes_accesslog ADD COLUMN session_hash varchar(64) DEFAULT '' NOT NULL;",
                    reverse_sql="ALTER TABLE axes_accesslog DROP COLUMN session_hash;",
                ),
            ],
            state_operations=upstream.Migration.operations,
        ),
    ]
