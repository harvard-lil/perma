from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    An index for InternetArchiveFile.in_flight(), which
    InternetArchiveItem.refresh_tasks_in_progress counts overall and per item
    every five minutes. It holds only files in the four in-flight statuses:
    about 8,200 of perma_internetarchivefile's 9.5M rows in September 2026,
    nearly all of them stranded 'upload_attempted' files.

    Built concurrently so that writes to perma_internetarchivefile continue
    during the build, which reads the whole table (8.5 GB).
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
    ]
