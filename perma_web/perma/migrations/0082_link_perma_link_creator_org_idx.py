from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Built concurrently so that writes to perma_link continue during the build,
    which reads the whole table and, like 0080's, takes minutes in production.
    """

    atomic = False

    dependencies = [
        ('perma', '0081_link_autovacuum_settings'),
        ('taggit', '0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx'),
    ]

    operations = [
        AddIndexConcurrently(
            model_name='link',
            index=models.Index(condition=models.Q(('organization__isnull', False), ('user_deleted', False)), fields=['created_by', 'organization'], name='perma_link_creator_org_idx'),
        ),
    ]
