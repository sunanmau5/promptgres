from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path

import pytest

from promptgres.exceptions import PromptgresError
from promptgres.release import (
    build_release_plan,
    collect_conventional_commits,
    current_version,
    latest_tag,
    parse_conventional_commit,
    parse_version,
    render_changelog_entry,
    suggest_version,
    update_changelog,
    update_pyproject_version,
    working_tree_is_clean,
    write_release_files,
)


def test_parse_conventional_commit_with_scope() -> None:
    commit = parse_conventional_commit(
        "abc123",
        "feat(cli): add release helper",
        "",
    )

    assert commit is not None
    assert commit.commit_type == "feat"
    assert commit.scope == "cli"
    assert commit.subject == "add release helper"


def test_parse_conventional_commit_with_breaking_footer() -> None:
    commit = parse_conventional_commit(
        "abc123",
        "refactor(core): reshape public api",
        "BREAKING CHANGE: import path changed",
    )

    assert commit is not None
    assert commit.is_breaking is True


def test_parse_conventional_commit_ignores_invalid_subject() -> None:
    assert parse_conventional_commit("abc123", "update stuff") is None


def test_parse_version_rejects_invalid_values() -> None:
    with pytest.raises(PromptgresError):
        parse_version("v1")


def test_render_changelog_entry_groups_sections() -> None:
    commits = [
        parse_conventional_commit("1", "feat(cli): add export command"),
        parse_conventional_commit("2", "fix(core): escape yaml descriptions"),
        parse_conventional_commit("3", "chore(release): 0.1.0"),
    ]

    entry = render_changelog_entry(
        "0.1.0",
        [commit for commit in commits if commit is not None],
        release_date=date(2026, 4, 6),
    )

    assert "## [0.1.0] - 2026-04-06" in entry
    assert "### Features" in entry
    assert "- **cli**: add export command" in entry
    assert "### Fixes" in entry
    assert "chore(release)" not in entry


def test_render_changelog_entry_includes_breaking_section() -> None:
    commit = parse_conventional_commit(
        "1",
        "feat(cli)!: change command layout",
    )

    entry = render_changelog_entry(
        "0.2.0",
        [commit] if commit is not None else [],
        release_date=date(2026, 4, 6),
    )

    assert "### Breaking Changes" in entry
    assert "- **cli**: change command layout" in entry


def test_update_changelog_inserts_release_section() -> None:
    changelog = "# Changelog\n\n## [Unreleased]\n\n"
    release_entry = "## [0.1.0] - 2026-04-06\n\n### Features\n- add cli\n"

    updated = update_changelog(changelog, release_entry)

    assert "## [Unreleased]" in updated
    assert "## [0.1.0] - 2026-04-06" in updated


def test_update_changelog_requires_unreleased() -> None:
    with pytest.raises(PromptgresError):
        update_changelog("# Changelog\n", "## [0.1.0] - 2026-04-06\n")


def test_update_pyproject_version_rewrites_version() -> None:
    updated = update_pyproject_version(
        '[project]\nname = "promptgres"\nversion = "0.1.0"\n',
        "0.2.0",
    )

    assert 'version = "0.2.0"' in updated


def test_build_release_plan_prints_expected_commands() -> None:
    commits = [
        parse_conventional_commit("1", "feat(cli): add export command"),
    ]

    plan = build_release_plan(
        "0.1.0",
        [commit for commit in commits if commit is not None],
    )

    assert plan.release_commit_message == "chore(release): 0.1.0"
    assert plan.tag_name == "v0.1.0"
    assert plan.commands[-1] == "git push origin v0.1.0"


def test_suggest_version_for_feature_on_zero_major() -> None:
    commit = parse_conventional_commit("1", "feat(cli): add release helper")

    version = suggest_version("0.1.0", [commit] if commit is not None else [])

    assert version == "0.2.0"


def test_suggest_version_for_fix_only() -> None:
    commit = parse_conventional_commit("1", "fix(core): escape output")

    version = suggest_version("0.1.0", [commit] if commit is not None else [])

    assert version == "0.1.1"


def test_suggest_version_for_breaking_change() -> None:
    commit = parse_conventional_commit("1", "feat(cli)!: change command layout")

    version = suggest_version("1.2.3", [commit] if commit is not None else [])

    assert version == "2.0.0"


def test_current_version_reads_pyproject(tmp_path: Path) -> None:
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(
        '[project]\nname = "promptgres"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )

    assert current_version(pyproject_file) == "1.2.3"


def test_latest_tag_returns_none_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 1, "", "fatal"),
    )

    assert latest_tag() is None


def test_latest_tag_returns_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, "v0.1.0\n", ""),
    )

    assert latest_tag() == "v0.1.0"


def test_working_tree_is_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, "", ""),
    )

    assert working_tree_is_clean() is True


def test_working_tree_is_not_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args,
            0,
            " M README.md\n",
            "",
        ),
    )

    assert working_tree_is_clean() is False


def test_collect_conventional_commits_filters_invalid_messages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    log_output = (
        "a1\x1ffeat(cli): add release helper\x1f\x1e"
        "a2\x1fnot conventional\x1f\x1e"
        "a3\x1ffix(core): escape output\x1fHandled edge case\x1e"
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, log_output, ""),
    )

    commits = collect_conventional_commits("v0.0.0")

    assert [commit.commit_type for commit in commits] == ["fix", "feat"]
    assert commits[0].subject == "escape output"


def test_write_release_files_updates_changelog_and_pyproject(tmp_path: Path) -> None:
    changelog_file = tmp_path / "CHANGELOG.md"
    changelog_file.write_text("# Changelog\n\n## [Unreleased]\n\n", encoding="utf-8")
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(
        '[project]\nname = "promptgres"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    commit = parse_conventional_commit("1", "feat(cli): add release helper")

    plan = write_release_files(
        version="0.2.0",
        changelog_path=changelog_file,
        pyproject_path=pyproject_file,
        commits=[commit] if commit is not None else [],
    )

    assert plan.tag_name == "v0.2.0"
    assert "## [0.2.0]" in changelog_file.read_text(encoding="utf-8")
    assert 'version = "0.2.0"' in pyproject_file.read_text(encoding="utf-8")
