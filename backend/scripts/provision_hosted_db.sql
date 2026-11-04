-- Run once on Neon / Vercel Postgres as the project owner.
-- Replace CHANGE_ME_* passwords, then connect with those roles for migrate/seed.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bazaar_owner') THEN
    CREATE ROLE bazaar_owner LOGIN PASSWORD 'CHANGE_ME_OWNER';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bazaar_app') THEN
    CREATE ROLE bazaar_app LOGIN PASSWORD 'CHANGE_ME_APP'
      NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
  END IF;
END
$$;

-- Neon: grant the new roles onto your DB (replace neondb if needed)
GRANT bazaar_owner TO CURRENT_USER;
ALTER SCHEMA public OWNER TO bazaar_owner;
GRANT CONNECT ON DATABASE neondb TO bazaar_app;
GRANT CONNECT ON DATABASE neondb TO bazaar_owner;
GRANT USAGE ON SCHEMA public TO bazaar_app;
GRANT USAGE ON SCHEMA public TO bazaar_owner;
