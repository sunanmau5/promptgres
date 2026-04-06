"""Typed domain models used across the package."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SchemaColumnRecord:
    """Flat row returned from schema metadata queries."""

    schema_name: str
    table_name: str
    column_name: str
    data_type: str
    is_nullable: bool
    description: str | None = None


@dataclass(frozen=True, slots=True)
class EnumValueRecord:
    """Flat row returned from enum metadata queries."""

    schema_name: str
    enum_name: str
    enum_value: str


@dataclass(frozen=True, slots=True)
class Column:
    """Column metadata."""

    name: str
    data_type: str
    is_nullable: bool
    description: str | None = None


@dataclass(frozen=True, slots=True)
class Table:
    """Table metadata."""

    schema_name: str
    name: str
    columns: tuple[Column, ...]


@dataclass(frozen=True, slots=True)
class DatabaseSchema:
    """Structured database schema."""

    database_name: str
    tables: tuple[Table, ...]


@dataclass(frozen=True, slots=True)
class EnumDefinition:
    """Enum metadata."""

    name: str
    values: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EnumSchema:
    """Schema-scoped enum collection."""

    name: str
    enums: tuple[EnumDefinition, ...]


@dataclass(frozen=True, slots=True)
class DatabaseEnums:
    """Structured enum document."""

    database_name: str
    schemas: tuple[EnumSchema, ...]


@dataclass(frozen=True, slots=True)
class ColumnDescription:
    """Serializable description entry."""

    data_type: str
    nullable: bool
    description: str = ""


DescriptionMap = dict[str, dict[str, dict[str, ColumnDescription]]]


@dataclass(slots=True)
class MutableTable:
    """Internal mutable builder for grouping flat rows."""

    schema_name: str
    name: str
    columns: list[Column] = field(default_factory=list)
