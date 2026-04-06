"""Pure grouping logic for database metadata rows."""

from __future__ import annotations

from collections import OrderedDict

from promptgres.models import (
    Column,
    DatabaseEnums,
    DatabaseSchema,
    EnumDefinition,
    EnumSchema,
    EnumValueRecord,
    MutableTable,
    SchemaColumnRecord,
    Table,
)


def build_schema_collection(
    database_name: str, records: list[SchemaColumnRecord]
) -> DatabaseSchema:
    """Group flat schema rows into a structured document."""

    grouped: OrderedDict[tuple[str, str], MutableTable] = OrderedDict()
    for record in records:
        key = (record.schema_name, record.table_name)
        if key not in grouped:
            grouped[key] = MutableTable(
                schema_name=record.schema_name,
                name=record.table_name,
            )
        grouped[key].columns.append(
            Column(
                name=record.column_name,
                data_type=record.data_type,
                is_nullable=record.is_nullable,
                description=record.description,
            )
        )

    tables = tuple(
        Table(
            schema_name=table.schema_name,
            name=table.name,
            columns=tuple(table.columns),
        )
        for table in grouped.values()
    )
    return DatabaseSchema(database_name=database_name, tables=tables)


def build_enum_collection(
    database_name: str, records: list[EnumValueRecord]
) -> DatabaseEnums:
    """Group flat enum rows into a structured document."""

    grouped: OrderedDict[str, OrderedDict[str, list[str]]] = OrderedDict()
    for record in records:
        grouped.setdefault(record.schema_name, OrderedDict()).setdefault(
            record.enum_name, []
        ).append(record.enum_value)

    schemas = tuple(
        EnumSchema(
            name=schema_name,
            enums=tuple(
                EnumDefinition(name=enum_name, values=tuple(values))
                for enum_name, values in enums.items()
            ),
        )
        for schema_name, enums in grouped.items()
    )
    return DatabaseEnums(database_name=database_name, schemas=schemas)
