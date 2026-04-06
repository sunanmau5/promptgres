from __future__ import annotations

from pathlib import Path

import pytest

from promptgres.config import load_database_config
from promptgres.exceptions import ConfigError


def test_load_database_config_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PGHOST", "db.internal")
    monkeypatch.setenv("PGPORT", "6543")
    monkeypatch.setenv("PGDATABASE", "warehouse")
    monkeypatch.setenv("PGUSER", "analyst")
    monkeypatch.setenv("PGPASSWORD", "secret")

    config = load_database_config()

    assert config.host == "db.internal"
    assert config.port == 6543
    assert config.database == "warehouse"
    assert config.user == "analyst"
    assert config.password == "secret"


def test_load_database_config_invalid_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PGPORT", "not-a-port")

    with pytest.raises(ConfigError):
        load_database_config()


def test_load_database_config_with_dotenv_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text(
        "PGHOST=dotenv-host\nPGPORT=6000\nPGDATABASE=dotenv-db\nPGUSER=dotenv-user\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("PGHOST", raising=False)
    monkeypatch.delenv("PGPORT", raising=False)
    monkeypatch.delenv("PGDATABASE", raising=False)
    monkeypatch.delenv("PGUSER", raising=False)

    config = load_database_config(dotenv_path=dotenv_file, password="pw")

    assert config.host == "dotenv-host"
    assert config.port == 6000
    assert config.database == "dotenv-db"
    assert config.user == "dotenv-user"
    assert config.password == "pw"
