from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from promptgres.descriptions import (
    description_template_from_root,
    description_template_from_xml,
    load_description_yaml,
    render_description_sql,
    render_description_template_yaml,
    write_text,
)
from promptgres.exceptions import InputFileError
from promptgres.models import ColumnDescription


def test_description_template_from_root(schema_xml_root) -> None:
    description_map = description_template_from_root(schema_xml_root)

    assert description_map["public"]["users"]["id"].data_type == "uuid"
    assert (
        description_map["public"]["users"]["id"].description
        == "Primary user identifier"
    )
    assert description_map["public"]["users"]["email"].nullable is False


def test_description_template_from_xml_invalid(tmp_path: Path) -> None:
    invalid = tmp_path / "broken.xml"
    invalid.write_text("<database>", encoding="utf-8")

    with pytest.raises(InputFileError):
        description_template_from_xml(invalid)


def test_description_template_from_root_invalid_table() -> None:
    with pytest.raises(InputFileError):
        description_template_from_root(
            ET.fromstring("<database><table schema='public'></table></database>")
        )


def test_render_description_template_yaml(schema_xml_root) -> None:
    description_map = description_template_from_root(schema_xml_root)

    rendered = render_description_template_yaml(description_map)

    assert "public:" in rendered
    assert "description: Primary user identifier" in rendered


def test_load_description_yaml(tmp_path: Path) -> None:
    yaml_file = tmp_path / "descriptions.yaml"
    yaml_file.write_text(
        """
public:
  users:
    id:
      type: uuid
      nullable: false
      description: Primary key
""",
        encoding="utf-8",
    )

    description_map = load_description_yaml(yaml_file)

    assert description_map["public"]["users"]["id"] == ColumnDescription(
        data_type="uuid",
        nullable=False,
        description="Primary key",
    )


def test_load_description_yaml_missing_field(tmp_path: Path) -> None:
    yaml_file = tmp_path / "descriptions.yaml"
    yaml_file.write_text(
        """
public:
  users:
    id:
      nullable: false
""",
        encoding="utf-8",
    )

    with pytest.raises(InputFileError):
        load_description_yaml(yaml_file)


def test_load_description_yaml_invalid_root(tmp_path: Path) -> None:
    yaml_file = tmp_path / "descriptions.yaml"
    yaml_file.write_text("- invalid\n", encoding="utf-8")

    with pytest.raises(InputFileError):
        load_description_yaml(yaml_file)


def test_render_description_sql_escapes_quotes() -> None:
    description_map = {
        "public": {
            "users": {
                "id": ColumnDescription(
                    data_type="uuid",
                    nullable=False,
                    description="User's primary key",
                ),
                "email": ColumnDescription(
                    data_type="text",
                    nullable=False,
                    description="",
                ),
            }
        }
    }

    sql = render_description_sql(description_map)

    assert "User''s primary key" in sql
    assert "email" not in sql


def test_write_text_creates_output_directory(tmp_path: Path) -> None:
    output_path = tmp_path / "nested" / "file.txt"

    written = write_text(output_path, "hello")

    assert written == output_path
    assert output_path.read_text(encoding="utf-8") == "hello"
