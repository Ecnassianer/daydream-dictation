#!/usr/bin/env python3
"""
dd_init_project.py — Initialize a new Daydream Dictation project.

Usage:
    python3 dd_init_project.py "My Cool New Game"
    python3 dd_init_project.py --project-root /path/to/docs "My Cool New Game"

Creates under the project root:
    <Slug>/
        Daydream-<Slug>.md
        TODO-<Slug>.md
        Prompts-<Slug>.md

Then commits and pushes using the active VCS.

Project root resolution (first match wins):
  1. --project-root <path> argument
  2. .claude/dd-projects-root file (contains an absolute path)
  3. Repo root (current working directory)

VCS detection order:
  1. .claude/dd-vcs file (user override)
  2. Auto-detection (.git, .hg, .plastic, P4CONFIG / .p4config)
  3. Nothing detected — Claude asks the user which VCS they're using

Supported VCS:
  git        — git add / commit / push
  hg         — hg add / commit / push
  perforce   — p4 add / submit
  unity-vcs  — cm add / checkin / push (Plastic SCM / Unity Version Control)
  custom     — unsupported VCS; Claude manages checkpoints conversationally
"""

import os
import sys

# Allow importing dd_lib from the same directory regardless of cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dd_lib as dd


def _ensure_gitignore(repo_root: str) -> None:
    """Append dd-current-dictation-project to .gitignore if not already present."""
    gitignore_path = os.path.join(repo_root, ".gitignore")
    marker = "dd-current-dictation-project"

    if os.path.isfile(gitignore_path):
        with open(gitignore_path, encoding="utf-8") as f:
            content = f.read()
        if marker in content:
            return
        # Ensure we start on a new line
        if content and not content.endswith("\n"):
            content += "\n"
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(content + marker + "\n")
    else:
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(marker + "\n")
    print(f"  Updated .gitignore with {marker}")


def main() -> None:
    args = sys.argv[1:]
    cli_project_root = None

    if "--project-root" in args:
        idx = args.index("--project-root")
        if idx + 1 >= len(args):
            print("ERROR: --project-root requires a path argument.", file=sys.stderr)
            sys.exit(1)
        cli_project_root = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    if not args:
        print('Usage: python3 dd_init_project.py [--project-root <path>] "Project Name"',
              file=sys.stderr)
        sys.exit(1)

    full_name = " ".join(args).strip()
    if not full_name:
        print("ERROR: project name cannot be empty.", file=sys.stderr)
        sys.exit(1)

    slug = dd.slugify(full_name)

    repo_root = dd.find_repo_root()
    vcs = dd.detect_vcs(repo_root)
    project_root = dd.resolve_project_root(repo_root, cli_project_root)

    project_dir = os.path.join(project_root, slug)
    if os.path.exists(project_dir):
        print(f"ERROR: '{project_dir}' already exists.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(project_dir)
    print(f"\nInitializing project: {full_name}")
    print(f"  Folder:  {project_dir}")
    print(f"  VCS:     {vcs or 'none detected'}\n")

    created = dd.ensure_project_files(project_dir, slug, full_name)

    # Ensure dd-current-dictation-project is in .gitignore
    _ensure_gitignore(repo_root)

    # Set active project — stores folder path; hook resolves Prompts file dynamically.
    # (dd-current-dictation-project is gitignored; not added to commit)
    current_project_path = os.path.join(repo_root, "dd-current-dictation-project")
    with open(current_project_path, "w", encoding="utf-8") as f:
        f.write(project_dir)
    print(f"\n  Set dd-current-dictation-project -> {project_dir}")

    commit_msg = (f"Initialize {full_name} project\n\n"
                  f"Creates Daydream, TODO, and Prompts documents for {slug}.")
    dd.checkpoint(created, commit_msg, repo_root, vcs)

    print(f"\nDone. Project '{full_name}' is ready in {project_dir}/")


if __name__ == "__main__":
    main()
