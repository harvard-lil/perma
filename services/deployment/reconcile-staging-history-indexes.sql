-- One-time reconciliation for staging, which already applied the original
-- Perma 0076. Run with psql ON_ERROR_STOP=1, NOT inside a transaction, after
-- confirming the connection is staging and deploying the revised settings.
-- This changes no data and requires no django_migrations edits. Axes 0009
-- plus the original Perma 0077 already produced the intended persistent default.
SET lock_timeout = '5s';
SET statement_timeout = '60s';
DROP INDEX CONCURRENTLY IF EXISTS perma_historicallinkuser_history_date_21006d54;
DROP INDEX CONCURRENTLY IF EXISTS perma_historicalorganization_history_date_09d590c2;
DROP INDEX CONCURRENTLY IF EXISTS perma_historicalregistrar_history_date_b166b734;
RESET lock_timeout;
RESET statement_timeout;
