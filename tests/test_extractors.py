from __future__ import annotations

from promptgres.extractors import build_enum_collection, build_schema_collection


def test_build_schema_collection_groups_tables(schema_records) -> None:
    document = build_schema_collection("example_app", schema_records)

    assert document.database_name == "example_app"
    assert len(document.tables) == 2
    assert document.tables[0].schema_name == "public"
    assert document.tables[0].columns[0].description == "Primary user identifier"


def test_build_enum_collection_groups_values(enum_records) -> None:
    document = build_enum_collection("example_app", enum_records)

    assert document.database_name == "example_app"
    assert len(document.schemas) == 1
    assert document.schemas[0].name == "public"
    assert document.schemas[0].enums[0].values == ("active", "invited")
