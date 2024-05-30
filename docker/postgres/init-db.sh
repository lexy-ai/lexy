#!/bin/bash
set -e

echo "Creating test database $POSTGRES_TEST_DB and vector extension in $POSTGRES_DB..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	\echo init-db: Running inside database '$POSTGRES_DB'

	\echo init-db: Creating vector extension
	CREATE EXTENSION IF NOT EXISTS "vector";

  /* check if the test database already exists */
  \echo init-db: Checking if test database '$POSTGRES_TEST_DB' already exists
  SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_TEST_DB') AS test_db_exists \gset

  /*	create the test database if it does not exist */
  \if :test_db_exists
    \echo init-db: Test database '$POSTGRES_TEST_DB' already exists
  \else
    \echo init-db: Creating test database '$POSTGRES_TEST_DB'
    CREATE DATABASE $POSTGRES_TEST_DB;
  \endif
EOSQL

echo "Creating vector extension in $POSTGRES_TEST_DB..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_TEST_DB" <<-EOSQL
	\echo init-db: Running inside database '$POSTGRES_TEST_DB'

	\echo init-db: Creating vector extension
	CREATE EXTENSION IF NOT EXISTS "vector";
EOSQL
