from __future__ import annotations

from pathlib import Path

from promptgres import cli
from promptgres.exceptions import PromptgresError


def test_cli_schema_export(monkeypatch, tmp_path: Path, schema_records, capsys) -> None:
    output_path = tmp_path / "schema.xml"
    monkeypatch.setattr(cli, "fetch_schema_records", lambda _config: schema_records)

    exit_code = cli.main(
        ["schema", "export", "--database", "example_app", "--output", str(output_path)]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert output_path.exists()
    assert "Schema exported" in captured.out


def test_cli_enums_export(monkeypatch, tmp_path: Path, enum_records, capsys) -> None:
    output_path = tmp_path / "enums.xml"
    monkeypatch.setattr(cli, "fetch_enum_records", lambda _config: enum_records)

    exit_code = cli.main(
        ["enums", "export", "--database", "example_app", "--output", str(output_path)]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert output_path.exists()
    assert "Enums exported" in captured.out


def test_cli_descriptions_template(monkeypatch, tmp_path: Path, capsys) -> None:
    schema_path = tmp_path / "schema.xml"
    schema_path.write_text(
        """
<database name="example_app">
  <table schema="public" name="users">
    <column name="id" type="uuid" nullable="NO" />
  </table>
</database>
""",
        encoding="utf-8",
    )
    output_path = tmp_path / "descriptions.yaml"

    exit_code = cli.main(
        [
            "descriptions",
            "template",
            "--schema",
            str(schema_path),
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert output_path.exists()
    assert "Description template exported" in captured.out


def test_cli_descriptions_sql(tmp_path: Path, capsys) -> None:
    descriptions_path = tmp_path / "descriptions.yaml"
    descriptions_path.write_text(
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
    output_path = tmp_path / "comments.sql"

    exit_code = cli.main(
        [
            "descriptions",
            "sql",
            "--descriptions",
            str(descriptions_path),
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert output_path.exists()
    assert "Description SQL exported" in captured.out


def test_cli_returns_error_code_for_promptgres_errors(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        cli,
        "fetch_schema_records",
        lambda _config: (_ for _ in ()).throw(PromptgresError("failure")),
    )

    exit_code = cli.main(["schema", "export", "--database", "example_app"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Error: failure" in captured.err
