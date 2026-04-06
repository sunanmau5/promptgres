# Contributing

## Setup

```bash
uv sync --group dev --group test --group release
```

## Quality Gates

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
```

## Commit Convention

Use Angular-style Conventional Commits:

- `feat(scope):` for user-visible behavior
- `fix(scope):` for correctness fixes
- `refactor(scope):` for structural changes
- `test(scope):` for test-only changes
- `docs(scope):` for documentation changes
- `build(scope):` for packaging or dependency changes
- `ci(scope):` for workflow changes
- `chore(scope):` for maintenance and releases

Rules:

- Keep the subject imperative and lowercase after the prefix
- Prefer a short scope such as `core`, `cli`, `docs`, `release`, `tests`
- Use `!` or a `BREAKING CHANGE:` footer for incompatible changes
- Keep release commits as `chore(release): <version>`

Examples:

```text
feat(cli): add descriptions sql command
test(core): cover schema and enum serialization
build(python): configure hatch and commitizen
chore(release): 0.1.0
```

You can validate recent commit messages with:

```bash
uv run cz check --rev-range HEAD~5..HEAD
uv run python scripts/release.py suggest
```

## Release Runbook

1. Ensure the working tree is clean.
2. Run the quality gates.
3. Generate draft notes:

   ```bash
   uv run python scripts/release.py draft --version 0.1.0
   ```

4. Prepare the release files:

   ```bash
   uv run python scripts/release.py prepare --version 0.1.0 --apply
   ```

5. Review the generated `CHANGELOG.md` section.
6. Create the release commit:

   ```bash
   git commit -m "chore(release): 0.1.0"
   ```

7. Create and push the annotated tag:

   ```bash
   git tag -a v0.1.0 -m "v0.1.0"
   git push origin main
   git push origin v0.1.0
   ```

## Guidelines

- Keep transformation logic pure where practical.
- Keep CLI handlers thin.
- Add or update tests for every behavioral change.
- Do not commit local database credentials or generated private schema artifacts.
