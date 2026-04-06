from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from promptgres.models import EnumValueRecord, SchemaColumnRecord  # noqa: E402


@pytest.fixture
def schema_records() -> list[SchemaColumnRecord]:
    return [
        SchemaColumnRecord(
            schema_name="public",
            table_name="users",
            column_name="id",
            data_type="uuid",
            is_nullable=False,
            description="Primary user identifier",
        ),
        SchemaColumnRecord(
            schema_name="public",
            table_name="users",
            column_name="email",
            data_type="text",
            is_nullable=False,
        ),
        SchemaColumnRecord(
            schema_name="analytics",
            table_name="events",
            column_name="id",
            data_type="uuid",
            is_nullable=False,
        ),
    ]


@pytest.fixture
def enum_records() -> list[EnumValueRecord]:
    return [
        EnumValueRecord(
            schema_name="public",
            enum_name="user_status",
            enum_value="active",
        ),
        EnumValueRecord(
            schema_name="public",
            enum_name="user_status",
            enum_value="invited",
        ),
    ]


@pytest.fixture
def schema_xml_root() -> ET.Element:
    return ET.fromstring(
        """
        <database name="example_app">
          <table schema="public" name="users">
            <column
              name="id"
              type="uuid"
              nullable="NO"
              description="Primary user identifier"
            />
            <column name="email" type="text" nullable="NO" />
          </table>
        </database>
        """
    )
