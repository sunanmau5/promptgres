"""Database access helpers."""

from __future__ import annotations

from collections.abc import Sequence

import psycopg

from promptgres.config import DatabaseConfig
from promptgres.exceptions import DatabaseError
from promptgres.models import EnumValueRecord, SchemaColumnRecord

SCHEMA_QUERY = """
SELECT
    c.table_schema,
    c.table_name,
    c.column_name,
    CASE
        WHEN c.data_type = 'USER-DEFINED' THEN c.udt_name
        ELSE c.data_type
    END AS data_type,
    c.is_nullable,
    pgd.description
FROM information_schema.columns c
LEFT JOIN pg_catalog.pg_statio_all_tables st
    ON c.table_schema = st.schemaname
    AND c.table_name = st.relname
LEFT JOIN pg_catalog.pg_description pgd
    ON pgd.objoid = st.relid
    AND pgd.objsubid = c.ordinal_position
WHERE c.table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY c.table_schema, c.table_name, c.ordinal_position
"""

ENUM_QUERY = """
SELECT
    n.nspname AS schema_name,
    t.typname AS enum_name,
    e.enumlabel AS enum_value
FROM pg_type t
JOIN pg_enum e ON t.oid = e.enumtypid
JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
ORDER BY n.nspname, t.typname, e.enumsortorder
"""


def _connect(config: DatabaseConfig) -> psycopg.Connection:
    try:
        return psycopg.connect(
            host=config.host,
            port=config.port,
            dbname=config.database,
            user=config.user,
            password=config.password,
        )
    except psycopg.Error as exc:
        raise DatabaseError(f"Failed to connect to PostgreSQL: {exc}") from exc


def fetch_schema_records(config: DatabaseConfig) -> list[SchemaColumnRecord]:
    """Fetch schema metadata rows from PostgreSQL."""

    try:
        with _connect(config) as conn, conn.cursor() as cur:
            cur.execute(SCHEMA_QUERY)
            rows: Sequence[tuple[str, str, str, str, str, str | None]] = cur.fetchall()
    except psycopg.Error as exc:
        raise DatabaseError(f"Failed to fetch schema metadata: {exc}") from exc

    return [
        SchemaColumnRecord(
            schema_name=schema_name,
            table_name=table_name,
            column_name=column_name,
            data_type=data_type,
            is_nullable=is_nullable == "YES",
            description=description,
        )
        for (
            schema_name,
            table_name,
            column_name,
            data_type,
            is_nullable,
            description,
        ) in rows
    ]


def fetch_enum_records(config: DatabaseConfig) -> list[EnumValueRecord]:
    """Fetch enum metadata rows from PostgreSQL."""

    try:
        with _connect(config) as conn, conn.cursor() as cur:
            cur.execute(ENUM_QUERY)
            rows: Sequence[tuple[str, str, str]] = cur.fetchall()
    except psycopg.Error as exc:
        raise DatabaseError(f"Failed to fetch enum metadata: {exc}") from exc

    return [
        EnumValueRecord(
            schema_name=schema_name,
            enum_name=enum_name,
            enum_value=enum_value,
        )
        for schema_name, enum_name, enum_value in rows
    ]
