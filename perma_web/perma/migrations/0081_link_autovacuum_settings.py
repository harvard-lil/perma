from django.db import migrations


TABLES = ['perma_link', 'perma_link_folders']


class Migration(migrations.Migration):
    """
    Vacuum perma_link and perma_link_folders after 2% of rows change or are
    inserted, rather than the RDS parameter group's 10% and Postgres's default
    20% for inserts. At 7.6M rows, the old thresholds meant perma_link_folders
    had not been vacuumed since at least June 2026 and carried 720k dead
    tuples, and inserts alone never triggered a vacuum, so the visibility map
    that index-only scans rely on stayed stale.

    ALTER TABLE ... SET takes a SHARE UPDATE EXCLUSIVE lock: reads and writes
    continue, but it waits for any running vacuum of the table to finish.
    """

    dependencies = [
        ('perma', '0080_link_personal_idx'),
    ]

    operations = [
        migrations.RunSQL(
            sql=f"ALTER TABLE {table} SET (autovacuum_vacuum_scale_factor = 0.02, autovacuum_vacuum_insert_scale_factor = 0.02)",
            reverse_sql=f"ALTER TABLE {table} RESET (autovacuum_vacuum_scale_factor, autovacuum_vacuum_insert_scale_factor)",
        )
        for table in TABLES
    ]
