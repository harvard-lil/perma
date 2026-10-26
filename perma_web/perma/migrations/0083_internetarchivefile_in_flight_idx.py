from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    An index for InternetArchiveFile.in_flight(), which
    InternetArchiveItem.refresh_tasks_in_progress counts overall and per item
    every five minutes. It holds only files in the four in-flight statuses:
    about 8,200 of perma_internetarchivefile's 9.5M rows in September 2026,
    nearly all of them stranded 'upload_attempted' files.

    Also indexes for the few InternetArchiveItems held back because IA lists
    tasks for them in error or paused (ia_tasks_blocked_since) or refused to
    create them (ia_creation_refused_at), so that finding them does not read
    the whole item table (2.6M rows, 2.9 GB).

    Built concurrently so that writes to both tables continue during the builds,
    which read each whole table.
    """

    atomic = False

    dependencies = [
        ('perma', '0082_internet_archive_confirmation_state'),
    ]

    operations = [
        AddIndexConcurrently(
            model_name='internetarchivefile',
            index=models.Index(condition=models.Q(('status__in', ['upload_attempted', 'upload_submitted', 'deletion_attempted', 'deletion_submitted'])), fields=['item', 'status_updated'], name='perma_iafile_in_flight_idx'),
        ),
        AddIndexConcurrently(
            model_name='internetarchiveitem',
            index=models.Index(condition=models.Q(('ia_tasks_blocked_since__isnull', False)), fields=['ia_tasks_blocked_since'], name='perma_iaitem_blocked_idx'),
        ),
        AddIndexConcurrently(
            model_name='internetarchiveitem',
            index=models.Index(condition=models.Q(('ia_creation_refused_at__isnull', False)), fields=['ia_creation_refused_at'], name='perma_iaitem_refused_idx'),
        ),
    ]
