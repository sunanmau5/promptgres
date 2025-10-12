# Promptgres

A Cursor toolkit for rapidly generating PostgreSQL queries from stakeholder requirements. By maintaining extracted database schemas and cursor rules, this enables natural language to SQL query generation with full context awareness.

## Tools

- **[uv](https://docs.astral.sh/uv/)** - fast Python package manager and runtime
- **[Ruff](https://docs.astral.sh/ruff/)** - fast Python linter and formatter
- **[SQLFluff](https://sqlfluff.com/)** - SQL linter and formatter (PostgreSQL dialect)
- **[psycopg](https://www.psycopg.org/)** - PostgreSQL adapter for Python

## Setup

Install dependencies:

```bash
uv sync
```

Configure database connection in `.env`:

```bash
PGHOST=localhost
PGPORT=5432
PGDATABASE=your_database
PGUSER=your_user
PGPASSWORD=your_password
```

## Project Structure

```
promptgres/
├── .cursor/rules/
│   ├── clarification-first.mdc
│   ├── sql.mdc
│   ├── schema.mdc
│   └── python.mdc
├── schema/
│   ├── pg_schema.xml
│   └── pg_enums.xml
├── queries/
├── scripts/
│   ├── get_schema.py
│   └── get_enums.py
└── .sqlfluff
```

## Workflow

### 1. Extract Database Context

Extract your database schema and enums:

```bash
uv run scripts/get_schema.py
uv run scripts/get_enums.py
```

This generates `schema/pg_schema.xml` and `schema/pg_enums.xml`.

### 2. (Optional) Add Column Descriptions

Add descriptions to your database columns:

```bash
# Generate YAML template
uv run scripts/generate_description_template.py

# Manually fill in descriptions in schema/column_descriptions.yaml

# Generate SQL COMMENT statements
uv run scripts/apply_descriptions.py

# Apply to database
psql -f schema/add_comments.sql

# Re-extract schema to include descriptions
uv run scripts/get_schema.py
```

### 3. Generate Queries with Cursor

Ask Cursor to generate queries in natural language:

**Example prompts:**

- "Give me a SQL query for daily active users"
- "Show me revenue by month for the last quarter"
- "Create a query to find inactive customers"

Cursor will:

- Use the schema context including column descriptions
- Reference enum values from extracted definitions
- Follow SQL formatting rules
- Create separate `.sql` files in `queries/` directory
