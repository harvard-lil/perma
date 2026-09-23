from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    A new table only. Nothing existing is altered or locked: the foreign key to
    perma_capturejob has no database constraint (see CaptureAttemptFacts), so
    this is safe while Salt and ECS deployments share the database.
    """

    dependencies = [
        ('perma', '0077_axes_session_hash_database_default'),
    ]

    operations = [
        migrations.CreateModel(
            name='CaptureAttemptFacts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attempt', models.SmallIntegerField()),
                ('scoop_job_id', models.CharField(blank=True, max_length=255, null=True)),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('facts', models.JSONField()),
                ('capture_job', models.ForeignKey(
                    db_constraint=False,
                    db_index=False,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attempt_facts',
                    to='perma.capturejob',
                )),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(fields=('capture_job', 'attempt'), name='unique_capture_attempt_facts'),
                ],
            },
        ),
    ]
