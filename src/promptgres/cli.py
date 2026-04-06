"""Command line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from promptgres.config import load_database_config
from promptgres.db import fetch_enum_records, fetch_schema_records
from promptgres.descriptions import (
    description_template_from_xml,
    load_description_yaml,
    render_description_sql,
    render_description_template_yaml,
    write_text,
)
from promptgres.exceptions import PromptgresError
from promptgres.extractors import build_enum_collection, build_schema_collection
from promptgres.serializers import render_enums_xml, render_schema_xml, write_xml


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser."""

    parser = argparse.ArgumentParser(prog="promptgres")
    parser.add_argument("--dotenv-path", type=Path, default=None)

    subparsers = parser.add_subparsers(dest="resource", required=True)

    schema_parser = subparsers.add_parser("schema", help="Export database schema")
    schema_subparsers = schema_parser.add_subparsers(dest="action", required=True)
    schema_export = schema_subparsers.add_parser("export", help="Export schema as XML")
    _add_database_args(schema_export)
    schema_export.add_argument(
        "--output",
        type=Path,
        default=Path("schema/pg_schema.xml"),
    )
    schema_export.set_defaults(handler=_handle_schema_export)

    enums_parser = subparsers.add_parser("enums", help="Export database enums")
    enums_subparsers = enums_parser.add_subparsers(dest="action", required=True)
    enums_export = enums_subparsers.add_parser("export", help="Export enums as XML")
    _add_database_args(enums_export)
    enums_export.add_argument(
        "--output",
        type=Path,
        default=Path("schema/pg_enums.xml"),
    )
    enums_export.set_defaults(handler=_handle_enums_export)

    descriptions_parser = subparsers.add_parser(
        "descriptions", help="Generate description files"
    )
    descriptions_subparsers = descriptions_parser.add_subparsers(
        dest="action", required=True
    )

    template_parser = descriptions_subparsers.add_parser(
        "template", help="Generate YAML description template from schema XML"
    )
    template_parser.add_argument(
        "--schema", type=Path, default=Path("schema/pg_schema.xml")
    )
    template_parser.add_argument(
        "--output", type=Path, default=Path("schema/column_descriptions.yaml")
    )
    template_parser.set_defaults(handler=_handle_descriptions_template)

    sql_parser = descriptions_subparsers.add_parser(
        "sql", help="Generate SQL comments from description YAML"
    )
    sql_parser.add_argument(
        "--descriptions", type=Path, default=Path("schema/column_descriptions.yaml")
    )
    sql_parser.add_argument(
        "--output", type=Path, default=Path("schema/add_comments.sql")
    )
    sql_parser.set_defaults(handler=_handle_descriptions_sql)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        args.handler(args)
    except PromptgresError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    return 0


def _add_database_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--database")
    parser.add_argument("--user")
    parser.add_argument("--password")


def _handle_schema_export(args: argparse.Namespace) -> None:
    config = load_database_config(
        dotenv_path=args.dotenv_path,
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password,
    )
    records = fetch_schema_records(config)
    document = build_schema_collection(config.database, records)
    output_path = write_xml(render_schema_xml(document), args.output)
    print(f"Schema exported to {output_path}")


def _handle_enums_export(args: argparse.Namespace) -> None:
    config = load_database_config(
        dotenv_path=args.dotenv_path,
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password,
    )
    records = fetch_enum_records(config)
    document = build_enum_collection(config.database, records)
    output_path = write_xml(render_enums_xml(document), args.output)
    print(f"Enums exported to {output_path}")


def _handle_descriptions_template(args: argparse.Namespace) -> None:
    description_map = description_template_from_xml(args.schema)
    output_path = write_text(
        args.output,
        render_description_template_yaml(description_map),
    )
    print(f"Description template exported to {output_path}")


def _handle_descriptions_sql(args: argparse.Namespace) -> None:
    description_map = load_description_yaml(args.descriptions)
    output_path = write_text(args.output, render_description_sql(description_map))
    print(f"Description SQL exported to {output_path}")
