#!/usr/bin/env python3
"""
dd_switch_project.py — Switch the active Daydream Dictation project.

Usage:
    python3 dd_switch_project.py "ProjectSlug"
    python3 dd_switch_project.py "My Project Name"
    python3 dd_switch_project.py --clear

Resolves the project folder, verifies it exists with the expected files
(Daydream-<Slug>.md, TODO-<Slug>.md, Prompts-<Slug>.md), and writes the
folder path to dd-current-dictation-project at the repo root.

With --clear, writes an empty string (prompts log to Prompts-ddMetadiscussion).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dd_lib as dd


def main() -> None:
    args = sys.argv[1:]

    if not args:
        print('Usage: python3 dd_switch_project.py "ProjectSlug"', file=sys.stderr)
        print('       python3 dd_switch_project.py --clear', file=sys.stderr)
        sys.exit(1)

    repo_root = dd.find_repo_root()

    if args == ["--clear"]:
        current_project_path = os.path.join(repo_root, "dd-current-dictation-project")
        with open(current_project_path, "w", encoding="utf-8") as f:
            f.write("")
        print("Cleared dd-current-dictation-project (prompts → Prompts-ddMetadiscussion)")
        return

    name = " ".join(args).strip()
    if not name:
        print("ERROR: project name cannot be empty.", file=sys.stderr)
        sys.exit(1)

    slug = dd.slugify(name)
    project_root = dd.resolve_project_root(repo_root, None)
    project_dir = os.path.join(project_root, slug)

    if not os.path.isdir(project_dir):
        print(f"ERROR: project folder not found: {project_dir}", file=sys.stderr)
        print(f"  To create a new project, use dd_init_project.py instead.", file=sys.stderr)
        sys.exit(1)

    # Verify expected files exist
    expected = [f"Daydream-{slug}.md", f"TODO-{slug}.md", f"Prompts-{slug}.md"]
    missing = [f for f in expected if not os.path.isfile(os.path.join(project_dir, f))]
    if missing:
        print(f"WARNING: missing files in {project_dir}:", file=sys.stderr)
        for f in missing:
            print(f"  - {f}", file=sys.stderr)
        print("  Switching anyway — create missing files before proceeding.", file=sys.stderr)

    current_project_path = os.path.join(repo_root, "dd-current-dictation-project")
    with open(current_project_path, "w", encoding="utf-8") as f:
        f.write(project_dir)
    print(f"Switched to: {slug}")
    print(f"  dd-current-dictation-project → {project_dir}")


if __name__ == "__main__":
    main()
