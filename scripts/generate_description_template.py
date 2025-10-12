"""Generate YAML template for column descriptions from pg_schema.xml."""

import xml.etree.ElementTree as ET
from pathlib import Path

import yaml


def generate_template(schema_file: str, output_file: str) -> None:
    """Generate YAML template from schema XML.

    Args:
        schema_file: Path to pg_schema.xml
        output_file: Path to output YAML file
    """
    tree = ET.parse(schema_file)
    root = tree.getroot()

    # organize by schema -> table -> columns
    schemas = {}

    for table_elem in root.findall("table"):
        schema_name = table_elem.get("schema")
        table_name = table_elem.get("name")

        if schema_name not in schemas:
            schemas[schema_name] = {}

        columns = {}
        for col_elem in table_elem.findall("column"):
            col_name = col_elem.get("name")
            col_type = col_elem.get("type")
            col_nullable = col_elem.get("nullable")

            columns[col_name] = {
                "type": col_type,
                "nullable": col_nullable == "YES",
                "description": "",  # to be filled
            }

        schemas[schema_name][table_name] = columns

    # write to YAML
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        yaml.dump(schemas, f, default_flow_style=False, sort_keys=False, width=120)


if __name__ == "__main__":
    schema_file = "schema/pg_schema.xml"
    output_file = "schema/column_descriptions.yaml"

    generate_template(schema_file, output_file)
    print(f"Template generated at {output_file}")
    print("Fill in the 'description' fields, then run scripts/apply_descriptions.py")
