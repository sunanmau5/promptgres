"""Serialization helpers for XML outputs."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from promptgres.models import DatabaseEnums, DatabaseSchema


def render_schema_xml(document: DatabaseSchema) -> ET.Element:
    """Render schema metadata to XML."""

    root = ET.Element("database", {"name": document.database_name})
    for table in document.tables:
        table_elem = ET.SubElement(
            root,
            "table",
            {"schema": table.schema_name, "name": table.name},
        )
        for column in table.columns:
            attrs = {
                "name": column.name,
                "type": column.data_type,
                "nullable": "YES" if column.is_nullable else "NO",
            }
            if column.description:
                attrs["description"] = column.description
            ET.SubElement(table_elem, "column", attrs)
    return root


def render_enums_xml(document: DatabaseEnums) -> ET.Element:
    """Render enum metadata to XML."""

    root = ET.Element("database", {"name": document.database_name})
    for schema in document.schemas:
        schema_elem = ET.SubElement(root, "schema", {"name": schema.name})
        for enum in schema.enums:
            enum_elem = ET.SubElement(schema_elem, "enum", {"name": enum.name})
            for value in enum.values:
                value_elem = ET.SubElement(enum_elem, "value")
                value_elem.text = value
    return root


def write_xml(root: ET.Element, output_path: str | Path) -> Path:
    """Write an XML element to disk."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return path
