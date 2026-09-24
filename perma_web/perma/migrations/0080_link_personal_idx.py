from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    An index for LinkUser.links_remaining_in_period, which counts a user's
    links with no organization. Without it, Postgres combines the created_by
    index with the organization index's entries for all such links (about 17%
    of perma_link, 1.3M rows in September 2026), which took 45-146 seconds when
    those pages were not cached.

    Built concurrently so that writes to perma_link continue during the build,
    which reads the whole table and takes minutes in production.
    """

    atomic = False

    dependencies = [
        ('perma', '0079_historicalregistrar_sponsored_link_count_and_more'),
    ]

    operations = [
        AddIndexConcurrently(
            model_name='link',
            index=models.Index(condition=models.Q(('organization', None)), fields=['created_by', 'creation_timestamp'], name='perma_link_personal_idx'),
        ),
    ]
