#!/usr/bin/env bash
# Creates the two PostgreSQL roles and the two databases that Bazaar uses.
#
#   bazaar_owner  owns the schema and runs migrations and the seed.
#   bazaar_app    is the runtime role used by the API. It cannot create objects,
#                 cannot bypass row-level security, and cannot UPDATE or DELETE
#                 the audit and commission tables (granted later by the migration).
#
# Usage (local Homebrew PostgreSQL, connecting as your macOS superuser):
#   ./scripts/create_db.sh
# Other servers: set PGHOST, PGPORT and PGUSER to a superuser connection first.
set -euo pipefail

PGHOST="${PGHOST:-127.0.0.1}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-$(whoami)}"
OWNER_PASSWORD="${BAZAAR_OWNER_PASSWORD:-bazaar_owner}"
APP_PASSWORD="${BAZAAR_APP_PASSWORD:-bazaar_app}"
DATABASES="${BAZAAR_DATABASES:-bazaar bazaar_test}"

run_sql() {
  local db="$1"
  shift
  psql -v ON_ERROR_STOP=1 -q -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$db" "$@"
}

echo "Creating roles on ${PGHOST}:${PGPORT} as ${PGUSER}"
run_sql postgres <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bazaar_owner') THEN
    CREATE ROLE bazaar_owner LOGIN PASSWORD '${OWNER_PASSWORD}';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bazaar_app') THEN
    CREATE ROLE bazaar_app LOGIN PASSWORD '${APP_PASSWORD}'
      NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
  END IF;
END
\$\$;
SQL

for db in $DATABASES; do
  if [ "$(run_sql postgres -Atc "SELECT 1 FROM pg_database WHERE datname = '${db}'")" != "1" ]; then
    echo "Creating database ${db}"
    run_sql postgres -c "CREATE DATABASE ${db} OWNER bazaar_owner"
  else
    echo "Database ${db} already exists"
  fi
  run_sql "$db" <<SQL
ALTER SCHEMA public OWNER TO bazaar_owner;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO bazaar_app;
GRANT CONNECT ON DATABASE ${db} TO bazaar_app;
SQL
done

echo "Done. Next: uv run alembic upgrade head && uv run python -m app.seed"
