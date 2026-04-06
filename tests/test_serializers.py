from __future__ import annotations

from pathlib import Path

from promptgres.extractors import build_enum_collection, build_schema_collection
from promptgres.serializers import render_enums_xml, render_schema_xml, write_xml


def test_render_schema_xml(schema_records) -> None:
    document = build_schema_collection("example_app", schema_records)
    root = render_schema_xml(document)

    assert root.tag == "database"
    assert root.attrib["name"] == "example_app"
    table = root.findall("table")[0]
    assert table.attrib == {"schema": "public", "name": "users"}
    column = table.findall("column")[0]
    assert column.attrib["description"] == "Primary user identifier"


def test_render_enums_xml(enum_records) -> None:
    document = build_enum_collection("example_app", enum_records)
    root = render_enums_xml(document)

    enum = root.find("./schema/enum")
    assert enum is not None
    assert enum.attrib["name"] == "user_status"
    assert [value.text for value in enum.findall("value")] == ["active", "invited"]


def test_write_xml_creates_output_directory(tmp_path: Path, schema_records) -> None:
    document = build_schema_collection("example_app", schema_records)
    output_path = tmp_path / "nested" / "schema.xml"

    written = write_xml(render_schema_xml(document), output_path)

    assert written == output_path
    assert output_path.exists()
    assert "example_app" in output_path.read_text(encoding="utf-8")
