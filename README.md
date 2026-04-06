# Promptgres

Promptgres packages a small PostgreSQL metadata toolkit as a reusable Python library and CLI. It extracts schema and enum metadata, turns schema XML into editable YAML description templates, and renders SQL `COMMENT` statements back from those descriptions.

The repository is structured for open-source use:

- install and run with `uv`
- lint and format with Ruff
- test with pytest and coverage gates
- publish as a normal Python package

## Install

```bash
uv sync --group dev --group test
```

## CLI Usage

Configure PostgreSQL access in `.env` or via flags:

```bash
PGHOST=localhost
PGPORT=5432
PGDATABASE=postgres
PGUSER=postgres
PGPASSWORD=postgres
```

Export schema metadata:

```bash
uv run promptgres schema export --output schema/pg_schema.xml
```

Export enum metadata:

```bash
uv run promptgres enums export --output schema/pg_enums.xml
```

Generate a description template from schema XML:

```bash
uv run promptgres descriptions template \
  --schema schema/pg_schema.xml \
  --output schema/column_descriptions.yaml
```

Generate SQL comments from the description YAML:

```bash
uv run promptgres descriptions sql \
  --descriptions schema/column_descriptions.yaml \
  --output schema/add_comments.sql
```

## Python API

```python
from promptgres import (
    build_schema_collection,
    render_schema_xml,
)
```

The library surface is intentionally small. Transformation logic is kept pure so it can be tested without a live database.

## Development

Run linting and formatting checks:

```bash
uv run ruff check .
uv run ruff format --check .
```

Run tests with coverage:

```bash
uv run pytest
```

Build distributable artifacts:

```bash
uv build
```

## Commits

This repository uses Angular-style Conventional Commits. Preferred types are:

- `feat`
- `fix`
- `refactor`
- `test`
- `docs`
- `build`
- `ci`
- `chore`

Examples:

```text
feat(cli): add schema export subcommand
refactor(core): split XML serialization from database access
chore(release): 0.1.0
```

To validate local commit messages or inspect the next version bump:

```bash
uv sync --group release
uv run cz check --rev-range HEAD~5..HEAD
uv run python scripts/release.py suggest
```

## Release Workflow

Release flow is intentionally manual, but helper-driven:

```bash
uv sync --group dev --group test --group release
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
uv run python scripts/release.py draft --version 0.1.0
```

To prepare a release locally:

```bash
uv run python scripts/release.py prepare --version 0.1.0 --apply
git commit -m "chore(release): 0.1.0"
git tag -a v0.1.0 -m "v0.1.0"
git push origin main
git push origin v0.1.0
```

The helper updates `CHANGELOG.md`, keeps `pyproject.toml` aligned with the chosen version, and prints the exact follow-up commands. Review the generated changelog before committing the release.

## Examples

Sanitized fixtures live under `examples/` and are safe to publish. Generated local outputs belong in `schema/` and `queries/`, which are ignored by default.
