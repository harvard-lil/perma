"""Database compatibility required while Salt and ECS overlap."""
import importlib
import pkgutil

import pytest
from django.conf import settings
from django.db import connection
from django.db.migrations.loader import MigrationLoader


def test_axes_migration_override_preserves_upstream_graph():
    upstream = importlib.import_module('axes.migrations')
    expected = {name for _, name, _ in pkgutil.iter_modules(upstream.__path__) if name[0].isdigit()}
    loader = MigrationLoader(None)
    actual = {name for app, name in loader.disk_migrations if app == 'axes'}
    assert actual == expected
    for name in expected:
        original = importlib.import_module(f'axes.migrations.{name}').Migration
        loaded = loader.disk_migrations['axes', name]
        assert loaded.dependencies == original.dependencies
    override = loader.disk_migrations['axes', '0009_add_session_hash']
    assert override.__class__.__module__ == 'perma.axes_migrations.0009_add_session_hash'


@pytest.mark.django_db
def test_old_axes_insert_uses_persistent_session_hash_default():
    # Old Axes does not know this column. Exercise its INSERT shape directly.
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO axes_accesslog
                (user_agent, username, http_accept, path_info, attempt_time)
            VALUES ('cutover-test', 'cutover-test', '', '/login/', CURRENT_TIMESTAMP)
            RETURNING session_hash
        """)
        assert cursor.fetchone() == ('',)


@pytest.mark.django_db
def test_history_date_indexes_remain_opted_out():
    assert settings.SIMPLE_HISTORY_DATE_INDEX is False
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tablename, indexname FROM pg_indexes
            WHERE schemaname = current_schema()
              AND tablename IN ('perma_historicallinkuser',
                                'perma_historicalorganization',
                                'perma_historicalregistrar')
              AND indexdef LIKE '%%(history_date)%%'
        """)
        assert cursor.fetchall() == []


@pytest.mark.django_db(transaction=True)
def test_upgrade_from_salt_migration_state_preserves_existing_login_logs():
    from django.db.migrations.executor import MigrationExecutor

    executor = MigrationExecutor(connection)
    current = executor.loader.graph.leaf_nodes()
    salt = [('perma', '0075_remove_historicallinkuser_grandfathered_and_more'),
            ('axes', '0007_alter_accessattempt_unique_together')]
    statements = []

    def record_sql(execute, sql, params, many, context):
        statements.append(sql)
        return execute(sql, params, many, context)

    try:
        executor.migrate(salt)
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO axes_accesslog
                    (user_agent, username, http_accept, path_info, attempt_time)
                VALUES ('before-cutover', 'before-cutover', '', '/login/', CURRENT_TIMESTAMP)
                RETURNING id
            """)
            log_id = cursor.fetchone()[0]
        with connection.execute_wrapper(record_sql):
            MigrationExecutor(connection).migrate(current)
        with connection.cursor() as cursor:
            cursor.execute('SELECT session_hash FROM axes_accesslog WHERE id = %s', [log_id])
            assert cursor.fetchone() == ('',)
        sql = '\n'.join(statements).upper()
        assert 'ADD COLUMN SESSION_HASH' in sql
        assert 'DROP DEFAULT' not in sql
        assert not any('CREATE INDEX' in s.upper() and 'history_date' in s for s in statements)
    finally:
        MigrationExecutor(connection).migrate(current)
