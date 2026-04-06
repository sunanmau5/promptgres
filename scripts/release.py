"""Maintainer release helper."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from promptgres.release import (  # noqa: E402
    build_release_plan,
    collect_conventional_commits,
    current_version,
    latest_tag,
    suggest_version,
    working_tree_is_clean,
    write_release_files,
)


def build_parser() -> argparse.ArgumentParser:
    """Create the release helper CLI."""

    parser = argparse.ArgumentParser(prog="python scripts/release.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    draft_parser = subparsers.add_parser(
        "draft",
        help="Render draft release notes from Conventional Commits",
    )
    _add_common_release_args(draft_parser)

    suggest_parser = subparsers.add_parser(
        "suggest",
        help="Suggest the next semantic version from commit history",
    )
    suggest_parser.add_argument("--since", default=None)
    suggest_parser.add_argument(
        "--pyproject",
        type=Path,
        default=Path("pyproject.toml"),
    )

    prepare_parser = subparsers.add_parser(
        "prepare",
        help="Update release files and print follow-up commands",
    )
    _add_common_release_args(prepare_parser)
    prepare_parser.add_argument(
        "--apply",
        action="store_true",
        help="Write CHANGELOG.md and pyproject.toml",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the release helper."""

    args = build_parser().parse_args(argv)
    if args.command == "suggest":
        since_ref = args.since or latest_tag()
        current = current_version(args.pyproject)
        commits = collect_conventional_commits(since_ref)
        print(suggest_version(current, commits))
        return 0

    since_ref = args.since or latest_tag()
    commits = collect_conventional_commits(since_ref)
    plan = build_release_plan(args.version, commits)

    print(f"Current version: {current_version(args.pyproject)}")
    print(f"Base ref: {since_ref or 'repository start'}")
    print("")
    print(plan.changelog_entry.rstrip())
    print("")

    if args.command == "prepare":
        if not working_tree_is_clean():
            print(
                (
                    "Working tree is not clean. Commit or stash changes "
                    "before preparing a release."
                ),
                file=sys.stderr,
            )
            return 2
        if args.apply:
            plan = write_release_files(
                version=args.version,
                changelog_path=args.changelog,
                pyproject_path=args.pyproject,
                commits=commits,
            )
            print(f"Updated {args.changelog} and {args.pyproject}")
            print("")

        print("Follow-up commands:")
        for command in plan.commands:
            print(command)

    return 0


def _add_common_release_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--version", required=True)
    parser.add_argument("--since", default=None)
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))


if __name__ == "__main__":
    raise SystemExit(main())
