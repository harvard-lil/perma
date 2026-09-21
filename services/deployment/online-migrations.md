# Initial Salt-to-ECS migration compatibility

The unreleased ECS migration history is revised before the production handoff:

- Perma 0076 preserves the old unindexed history dates. The model-options and
  through-fields changes remain; they produce no database SQL.
- `SIMPLE_HISTORY_DATE_INDEX=False` keeps runtime model state consistent.
- `MIGRATION_MODULES['axes']` selects a project package whose search path falls
  back to upstream Axes migrations. Only 0009 is overridden: the new NOT NULL
  `session_hash` column retains its database default from creation onward.
  Upstream migration names, dependencies and model state are preserved.
- Perma 0077 remains as a no-op because staging has recorded that name already.
  Its previous SQL is now incorporated in the atomic Axes column addition.

Fresh databases and production at the Salt migration state need no fake
migrations. Staging already has the final Axes column/default; after deploying
these changes, run `reconcile-staging-history-indexes.sql` against staging to
remove the three old indexes. Do not unapply Axes migrations or delete migration
records. An environment with original Axes 0009 applied but original Perma 0077
not applied needs its missing default restored explicitly before this revision.

Validate the connection and applied state before any reconciliation. The SQL
must run outside a transaction because it drops indexes concurrently. Afterwards
verify there are no history_date indexes, `axes_accesslog.session_hash` has a
persistent empty-string default, `migrate --plan` is empty, and
`makemigrations --check --dry-run` reports no changes.

The column addition still requires a brief exclusive table lock. During the
attended production migration set a short PostgreSQL lock timeout so contention
fails the attempt instead of leaving a long queue of blocked login writes. This
change does not itself flip traffic, scale services, or configure those timeouts.
