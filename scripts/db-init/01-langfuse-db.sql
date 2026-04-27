-- Creates the Langfuse database on the same Postgres instance used by the Django app.
-- This script runs automatically on first container boot (docker-entrypoint-initdb.d).
SELECT 'CREATE DATABASE langfuse'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'langfuse')\gexec
