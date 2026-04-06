"""Configuration loading."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from promptgres.exceptions import ConfigError


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    """Connection settings for PostgreSQL."""

    host: str
    port: int
    database: str
    user: str
    password: str


def load_database_config(
    *,
    dotenv_path: str | Path | None = None,
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
    user: str | None = None,
    password: str | None = None,
) -> DatabaseConfig:
    """Load database configuration from environment with optional overrides."""

    load_dotenv(dotenv_path=dotenv_path)

    raw_port = str(port) if port is not None else os.getenv("PGPORT", "5432")
    try:
        resolved_port = int(raw_port)
    except ValueError as exc:
        raise ConfigError(f"Invalid PGPORT value: {raw_port!r}") from exc

    resolved_host = host or os.getenv("PGHOST", "localhost")
    resolved_database = database or os.getenv("PGDATABASE", "postgres")
    resolved_user = user or os.getenv("PGUSER", "postgres")
    resolved_password = (
        password if password is not None else os.getenv("PGPASSWORD", "")
    )

    for field_name, value in {
        "PGHOST": resolved_host,
        "PGDATABASE": resolved_database,
        "PGUSER": resolved_user,
    }.items():
        if not value:
            raise ConfigError(f"{field_name} must not be empty")

    return DatabaseConfig(
        host=resolved_host,
        port=resolved_port,
        database=resolved_database,
        user=resolved_user,
        password=resolved_password,
    )
