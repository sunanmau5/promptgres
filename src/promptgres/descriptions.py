"""Description template and SQL rendering helpers."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

from promptgres.exceptions import InputFileError
from promptgres.models import ColumnDescription, DescriptionMap


def description_template_from_root(root: ET.Element) -> DescriptionMap:
    """Build a serializable description template from schema XML."""

    schemas: DescriptionMap = {}
    for table_elem in root.findall("table"):
        schema_name = table_elem.get("schema")
        table_name = table_elem.get("name")
        if not schema_name or not table_name:
            raise InputFileError(
                "Schema XML table entries must include schema and name"
            )

        columns: dict[str, ColumnDescription] = {}
        for column_elem in table_elem.findall("column"):
            column_name = column_elem.get("name")
            data_type = column_elem.get("type")
            nullable = column_elem.get("nullable")
            if not column_name or not data_type or nullable not in {"YES", "NO"}:
                raise InputFileError("Schema XML column entries are malformed")

            columns[column_name] = ColumnDescription(
                data_type=data_type,
                nullable=nullable == "YES",
                description=column_elem.get("description", ""),
            )

        schemas.setdefault(schema_name, {})[table_name] = columns

    return schemas


def description_template_from_xml(schema_path: str | Path) -> DescriptionMap:
    """Load a schema XML file and convert it to a description template."""

    path = Path(schema_path)
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, FileNotFoundError) as exc:
        raise InputFileError(f"Failed to parse schema XML: {path}") from exc
    return description_template_from_root(root)


def render_description_template_yaml(description_map: DescriptionMap) -> str:
    """Render a description template to YAML."""

    payload = {
        schema_name: {
            table_name: {
                column_name: {
                    "type": column.data_type,
                    "nullable": column.nullable,
                    "description": column.description,
                }
                for column_name, column in columns.items()
            }
            for table_name, columns in tables.items()
        }
        for schema_name, tables in description_map.items()
    }
    return yaml.safe_dump(payload, sort_keys=False, width=120)


def load_description_yaml(yaml_path: str | Path) -> DescriptionMap:
    """Load YAML descriptions from disk."""

    path = Path(yaml_path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (FileNotFoundError, yaml.YAMLError) as exc:
        raise InputFileError(f"Failed to parse description YAML: {path}") from exc

    if not isinstance(data, dict):
        raise InputFileError("Description YAML must contain a mapping at the root")

    description_map: DescriptionMap = {}
    try:
        for schema_name, tables in data.items():
            description_map[schema_name] = {}
            for table_name, columns in tables.items():
                description_map[schema_name][table_name] = {}
                for column_name, details in columns.items():
                    if not isinstance(details, dict):
                        raise InputFileError("Column descriptions must be mappings")
                    description_map[schema_name][table_name][column_name] = (
                        ColumnDescription(
                            data_type=str(details["type"]),
                            nullable=bool(details["nullable"]),
                            description=str(details.get("description", "")),
                        )
                    )
    except KeyError as exc:
        raise InputFileError(f"Missing description field: {exc.args[0]}") from exc
    return description_map


def render_description_sql(description_map: DescriptionMap) -> str:
    """Render SQL COMMENT statements from descriptions."""

    statements: list[str] = []
    for schema_name, tables in description_map.items():
        for table_name, columns in tables.items():
            for column_name, details in columns.items():
                description = details.description.strip()
                if not description:
                    continue
                escaped_description = description.replace("'", "''")
                statements.append(
                    f"COMMENT ON COLUMN {schema_name}.{table_name}.{column_name} "
                    f"IS '{escaped_description}';"
                )

    header = [
        "-- Generated column descriptions",
        "-- Apply with: psql -f schema/add_comments.sql",
        "",
    ]
    return "\n".join(header + statements + [""])


def write_text(output_path: str | Path, content: str) -> Path:
    """Write UTF-8 text to disk."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
