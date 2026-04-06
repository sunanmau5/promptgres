"""Helpers for Conventional Commit release notes and release prep."""

from __future__ import annotations

import re
import subprocess
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from promptgres.exceptions import PromptgresError

CONVENTIONAL_COMMIT_RE = re.compile(
    r"^(?P<type>feat|fix|refactor|docs|test|build|ci|chore)"
    r"(?:\((?P<scope>[^)]+)\))?"
    r"(?P<breaking>!)?: (?P<subject>.+)$"
)

SECTION_TITLES = {
    "feat": "Features",
    "fix": "Fixes",
    "refactor": "Refactors",
    "docs": "Documentation",
    "test": "Tests",
    "build": "Build",
    "ci": "CI",
    "chore": "Chore",
}


@dataclass(frozen=True, slots=True)
class ConventionalCommit:
    """Structured representation of a commit message."""

    commit_hash: str
    commit_type: str
    scope: str | None
    subject: str
    body: str
    is_breaking: bool = False


@dataclass(frozen=True, slots=True)
class ReleasePlan:
    """Release note content and follow-up commands."""

    version: str
    changelog_entry: str
    release_commit_message: str
    tag_name: str
    commands: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Version:
    """Semantic version."""

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


def parse_conventional_commit(
    commit_hash: str,
    subject: str,
    body: str = "",
) -> ConventionalCommit | None:
    """Parse an Angular-style Conventional Commit subject."""

    match = CONVENTIONAL_COMMIT_RE.match(subject.strip())
    if match is None:
        return None

    body = body.strip()
    return ConventionalCommit(
        commit_hash=commit_hash,
        commit_type=match.group("type"),
        scope=match.group("scope"),
        subject=match.group("subject").strip(),
        body=body,
        is_breaking=bool(match.group("breaking")) or "BREAKING CHANGE:" in body,
    )


def parse_version(version: str) -> Version:
    """Parse a simple semantic version string."""

    match = re.match(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$", version)
    if match is None:
        raise PromptgresError(f"Invalid semantic version: {version!r}")

    return Version(
        major=int(match.group("major")),
        minor=int(match.group("minor")),
        patch=int(match.group("patch")),
    )


def suggest_version(current: str, commits: list[ConventionalCommit]) -> str:
    """Suggest the next semantic version from commit history."""

    version = parse_version(current)
    has_breaking = any(commit.is_breaking for commit in commits)
    has_feature = any(commit.commit_type == "feat" for commit in commits)
    has_changes = bool(commits)

    if has_breaking:
        if version.major == 0:
            return str(Version(0, version.minor + 1, 0))
        return str(Version(version.major + 1, 0, 0))
    if has_feature:
        return str(Version(version.major, version.minor + 1, 0))
    if has_changes:
        return str(Version(version.major, version.minor, version.patch + 1))
    return current


def render_changelog_entry(
    version: str,
    commits: list[ConventionalCommit],
    *,
    release_date: date | None = None,
) -> str:
    """Render a markdown changelog section for a release."""

    release_date = release_date or date.today()
    heading = f"## [{version}] - {release_date.isoformat()}"
    grouped: dict[str, list[str]] = {key: [] for key in SECTION_TITLES}
    breaking: list[str] = []

    for commit in commits:
        if commit.commit_type == "chore" and commit.scope == "release":
            continue

        label = (
            f"**{commit.scope}**: {commit.subject}" if commit.scope else commit.subject
        )
        grouped[commit.commit_type].append(f"- {label}")
        if commit.is_breaking:
            breaking.append(f"- {label}")

    sections = [heading, ""]
    if breaking:
        sections.extend(["### Breaking Changes", *breaking, ""])

    for commit_type, title in SECTION_TITLES.items():
        items = grouped[commit_type]
        if not items:
            continue
        sections.extend([f"### {title}", *items, ""])

    return "\n".join(sections).rstrip() + "\n"


def update_changelog(changelog_text: str, release_entry: str) -> str:
    """Insert a release entry below the Unreleased heading."""

    unreleased_heading = "## [Unreleased]"
    if unreleased_heading not in changelog_text:
        raise PromptgresError("CHANGELOG.md is missing an [Unreleased] section")

    before, after = changelog_text.split(unreleased_heading, maxsplit=1)
    after = after.lstrip("\n")
    new_body = f"{unreleased_heading}\n\n{release_entry}\n"
    if after:
        new_body += after
    return before + new_body


def update_pyproject_version(pyproject_text: str, version: str) -> str:
    """Update the package version in pyproject content."""

    return re.sub(
        r'^version = "[^"]+"$',
        f'version = "{version}"',
        pyproject_text,
        count=1,
        flags=re.MULTILINE,
    )


def build_release_plan(version: str, commits: list[ConventionalCommit]) -> ReleasePlan:
    """Assemble the generated release entry and follow-up commands."""

    entry = render_changelog_entry(version, commits)
    tag_name = f"v{version}"
    commands = (
        f'git commit -m "chore(release): {version}"',
        f'git tag -a {tag_name} -m "{tag_name}"',
        "git push origin main",
        f"git push origin {tag_name}",
    )
    return ReleasePlan(
        version=version,
        changelog_entry=entry,
        release_commit_message=f"chore(release): {version}",
        tag_name=tag_name,
        commands=commands,
    )


def current_version(pyproject_path: str | Path) -> str:
    """Read the current version from pyproject.toml."""

    data = tomllib.loads(Path(pyproject_path).read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def latest_tag() -> str | None:
    """Return the latest reachable git tag, if present."""

    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def working_tree_is_clean() -> bool:
    """Return whether the git working tree is clean."""

    result = subprocess.run(
        ["git", "status", "--short"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() == ""


def collect_conventional_commits(
    since_ref: str | None = None,
) -> list[ConventionalCommit]:
    """Collect Conventional Commits from git history."""

    range_spec = f"{since_ref}..HEAD" if since_ref else "HEAD"
    result = subprocess.run(
        ["git", "log", "--format=%H%x1f%s%x1f%b%x1e", range_spec],
        check=True,
        capture_output=True,
        text=True,
    )

    commits: list[ConventionalCommit] = []
    for entry in result.stdout.strip("\n\x1e").split("\x1e"):
        if not entry.strip():
            continue
        commit_hash, subject, body = entry.split("\x1f", maxsplit=2)
        parsed = parse_conventional_commit(commit_hash, subject, body)
        if parsed is not None:
            commits.append(parsed)
    commits.reverse()
    return commits


def write_release_files(
    *,
    version: str,
    changelog_path: str | Path,
    pyproject_path: str | Path,
    commits: list[ConventionalCommit],
) -> ReleasePlan:
    """Apply the generated changelog and version updates."""

    release_plan = build_release_plan(version, commits)

    changelog_file = Path(changelog_path)
    changelog_file.write_text(
        update_changelog(
            changelog_file.read_text(encoding="utf-8"),
            release_plan.changelog_entry,
        ),
        encoding="utf-8",
    )

    pyproject_file = Path(pyproject_path)
    pyproject_file.write_text(
        update_pyproject_version(
            pyproject_file.read_text(encoding="utf-8"),
            version,
        ),
        encoding="utf-8",
    )

    return release_plan
