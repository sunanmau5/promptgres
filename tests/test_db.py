from __future__ import annotations

from typing import Any

import psycopg
import pytest

from promptgres.config import DatabaseConfig
from promptgres.db import fetch_enum_records, fetch_schema_records
from promptgres.exceptions import DatabaseError


class FakeCursor:
    def __init__(self, rows: list[tuple[Any, ...]], should_fail: bool = False) -> None:
        self.rows = rows
        self.should_fail = should_fail
        self.executed = False

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, _query: str) -> None:
        self.executed = True
        if self.should_fail:
            raise psycopg.OperationalError("boom")

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self.rows


class FakeConnection:
    def __init__(self, rows: list[tuple[Any, ...]], should_fail: bool = False) -> None:
        self.rows = rows
        self.should_fail = should_fail

    def __enter__(self) -> FakeConnection:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return FakeCursor(self.rows, should_fail=self.should_fail)


@pytest.fixture
def config() -> DatabaseConfig:
    return DatabaseConfig(
        host="localhost",
        port=5432,
        database="example_app",
        user="postgres",
        password="postgres",
    )


def test_fetch_schema_records(
    monkeypatch: pytest.MonkeyPatch,
    config: DatabaseConfig,
) -> None:
    monkeypatch.setattr(
        "promptgres.db._connect",
        lambda _config: FakeConnection(
            [("public", "users", "id", "uuid", "NO", "Primary user identifier")]
        ),
    )

    records = fetch_schema_records(config)

    assert records[0].schema_name == "public"
    assert records[0].is_nullable is False


def test_fetch_enum_records(
    monkeypatch: pytest.MonkeyPatch,
    config: DatabaseConfig,
) -> None:
    monkeypatch.setattr(
        "promptgres.db._connect",
        lambda _config: FakeConnection([("public", "user_status", "active")]),
    )

    records = fetch_enum_records(config)

    assert records[0].enum_name == "user_status"


def test_fetch_schema_records_wraps_errors(
    monkeypatch: pytest.MonkeyPatch, config: DatabaseConfig
) -> None:
    monkeypatch.setattr(
        "promptgres.db._connect",
        lambda _config: FakeConnection([], should_fail=True),
    )

    with pytest.raises(DatabaseError):
        fetch_schema_records(config)


def test_connect_wraps_psycopg_errors(
    monkeypatch: pytest.MonkeyPatch, config: DatabaseConfig
) -> None:
    monkeypatch.setattr(
        "promptgres.db.psycopg.connect",
        lambda **_kwargs: (_ for _ in ()).throw(psycopg.OperationalError("boom")),
    )

    with pytest.raises(DatabaseError):
        fetch_enum_records(config)
