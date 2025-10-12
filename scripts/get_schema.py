"""Script to extract database schema from PostgreSQL and output as XML.

This script connects to a PostgreSQL database, extracts the schema information,
and outputs it in a machine-readable XML format that can be used in Cursor.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path

import psycopg
from dotenv import load_dotenv


def get_schema_as_xml(
    host: str, port: int, database: str, user: str, password: str
) -> ET.Element:
    """Extract schema from PostgreSQL database and return as XML Element.

    Args:
        host: PostgreSQL server host
        port: PostgreSQL server port
        database: Database name
        user: Database user
        password: Database password

    Returns:
        ET.Element: XML Element containing the database schema
    """
    # connect to the PostgreSQL database
    conn = psycopg.connect(
        host=host, port=port, dbname=database, user=user, password=password
    )

    # get all tables from all schemas (excluding system schemas)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        """)
        tables = cur.fetchall()

    # create XML root
    root = ET.Element("database")
    root.set("name", database)

    # for each table, get its schema
    for table_schema, table_name in tables:
        table_elem = ET.SubElement(root, "table")
        table_elem.set("schema", table_schema)
        table_elem.set("name", table_name)

        # get column information with actual udt names for user-defined types and descriptions
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
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
                WHERE c.table_schema = %s AND c.table_name = %s
                ORDER BY c.ordinal_position
            """,
                (table_schema, table_name),
            )
            columns = cur.fetchall()

        for col_name, data_type, is_nullable, description in columns:
            column_elem = ET.SubElement(table_elem, "column")
            column_elem.set("name", col_name)
            column_elem.set("type", data_type)
            column_elem.set("nullable", is_nullable)
            if description:
                column_elem.set("description", description)

    conn.close()
    return root


def save_schema_to_file(root: ET.Element, output_path: str) -> None:
    """Save the XML schema to a file with pretty printing.

    Args:
        root: XML Element containing the schema
        output_path: Path where to save the XML file
    """
    # create directory if it doesn't exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    ET.indent(root)
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    # load environment variables from .env file
    load_dotenv()

    # read connection parameters from environment variables
    host = os.getenv("PGHOST", "localhost")
    port = int(os.getenv("PGPORT", "5432"))
    database = os.getenv("PGDATABASE", "postgres")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "")

    output_path = "schema/pg_schema.xml"

    root = get_schema_as_xml(host, port, database, user, password)
    save_schema_to_file(root, output_path)
    print(f"Schema saved to {output_path}")
