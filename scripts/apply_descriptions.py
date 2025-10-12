"""Generate SQL COMMENT statements from column descriptions YAML."""

import yaml


def generate_comment_sql(yaml_file: str, output_file: str) -> None:
    """Generate SQL COMMENT statements from YAML.

    Args:
        yaml_file: Path to column descriptions YAML
        output_file: Path to output SQL file
    """
    with open(yaml_file) as f:
        schemas = yaml.safe_load(f)

    statements = []

    for schema_name, tables in schemas.items():
        for table_name, columns in tables.items():
            for col_name, col_info in columns.items():
                description = col_info.get("description", "").strip()

                if description:
                    # escape single quotes for SQL
                    escaped_desc = description.replace("'", "''")
                    statement = f"COMMENT ON COLUMN {schema_name}.{table_name}.{col_name} IS '{escaped_desc}';"
                    statements.append(statement)

    # write to file
    with open(output_file, "w") as f:
        f.write("-- generated column descriptions\n")
        f.write("-- run with: psql -f schema/add_comments.sql\n\n")
        f.write("\n".join(statements))
        f.write("\n")


if __name__ == "__main__":
    yaml_file = "schema/column_descriptions.yaml"
    output_file = "schema/add_comments.sql"

    generate_comment_sql(yaml_file, output_file)
    print(f"SQL generated at {output_file}")
    print(f"Run: psql -f {output_file}")
