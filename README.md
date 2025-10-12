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
│   ├── get_schema.p
│   └── get_enums.p
└── .sqlfluff
```

## Workflow

### 1. Extract Database Context

First, extract your database schema and enums so Cursor has full context:

```bash
# Extract tables, columns, and data types
uv run scripts/get_schema.py

# Extract enum definitions
uv run scripts/get_enums.py
```

This generates `schema/pg_schema.xml` and `schema/pg_enums.xml` which provide Cursor with complete database structure.

### 2. Generate Queries with Cursor

Ask Cursor to generate queries in natural language:

**Example prompts:**

- "Give me a SQL query for daily active users"
- "Show me revenue by month for the last quarter"
- "Create a query to find inactive customers"

Cursor will:

- Use the schema context to understand your database structure
- Reference enum values from the extracted definitions
- Follow the SQL formatting rules (uppercase keywords, proper indentation)
- Create a separate `.sql` file in the `queries/` directory
