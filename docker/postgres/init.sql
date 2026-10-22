-- The API connects as bazaar_app so row-level security applies.
-- bazaar_owner (POSTGRES_USER) owns the database and runs migrations.
CREATE ROLE bazaar_app LOGIN PASSWORD 'bazaar_app' NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
GRANT CONNECT ON DATABASE bazaar TO bazaar_app;
GRANT USAGE ON SCHEMA public TO bazaar_app;
