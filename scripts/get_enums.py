"""Script to extract user-defined enums from PostgreSQL and output as XML.

This script connects to a PostgreSQL database, extracts all user-defined enum types
and their values, and outputs them in a machine-readable XML format.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path

import psycopg
from dotenv import load_dotenv


def get_enums_as_xml(
    host: str, port: int, database: str, user: str, password: str
) -> ET.Element:
    """Extract enums from PostgreSQL database and return as XML Element.

    Args:
        host: PostgreSQL server host
        port: PostgreSQL server port
        database: Database name
        user: Database user
        password: Database password

    Returns:
        ET.Element: XML Element containing the database enums
    """
    # connect to the PostgreSQL database
    conn = psycopg.connect(
        host=host, port=port, dbname=database, user=user, password=password
    )

    # get all enum types and their values
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                n.nspname AS schema_name,
                t.typname AS enum_name,
                e.enumlabel AS enum_value
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY n.nspname, t.typname, e.enumsortorder
        """)
        enums = cur.fetchall()

    conn.close()

    # create XML root
    root = ET.Element("database")
    root.set("name", database)

    # group enums by schema and type
    current_schema = None
    current_enum = None
    schema_elem = None
    enum_elem = None

    for schema_name, enum_name, enum_value in enums:
        # create schema element if needed
        if current_schema != schema_name:
            schema_elem = ET.SubElement(root, "schema")
            schema_elem.set("name", schema_name)
            current_schema = schema_name
            current_enum = None

        # create enum element if needed
        if current_enum != enum_name:
            enum_elem = ET.SubElement(schema_elem, "enum")
            enum_elem.set("name", enum_name)
            current_enum = enum_name

        # add enum value
        value_elem = ET.SubElement(enum_elem, "value")
        value_elem.text = enum_value

    return root


def save_enums_to_file(root: ET.Element, output_path: str) -> None:
    """Save the XML enums to a file with pretty printing.

    Args:
        root: XML Element containing the enums
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

    output_path = "schema/pg_enums.xml"

    root = get_enums_as_xml(host, port, database, user, password)
    save_enums_to_file(root, output_path)
    print(f"Enums saved to {output_path}")
