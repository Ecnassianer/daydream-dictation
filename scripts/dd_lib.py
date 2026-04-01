#!/usr/bin/env python3
"""
dd_lib.py — Shared utilities for Daydream Dictation scripts.

Imported by dd_init_project.py, dd_log_prompt.py, and dd_stop_hook.py.
"""

import os
import subprocess
import sys


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    """Convert 'My Cool New Game' → 'MyCoolNewGame'."""
    return "".join(word[0].upper() + word[1:] for word in name.split() if word)


def ensure_project_files(project_dir: str, slug: str, full_name: str) -> list[str]:
    """Create any missing standard project files. Returns list of created paths."""
    templates = {
        f"Daydream-{slug}.md": f"# {full_name}\n\n## Overview\n\n",
        f"TODO-{slug}.md": f"# To-Do — {full_name}\n\n---\n\n## Pending\n\n",
        f"Prompts-{slug}.md": f"# Prompts — {full_name}\n\n---\n\n",
    }
    created = []
    for filename, content in templates.items():
        path = os.path.join(project_dir, filename)
        if not os.path.isfile(path):
            write_file(path, content)
            created.append(path)
    return created


def write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Created: {path}")


def run(cmd: list[str], cwd: str, fatal: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if fatal and result.returncode != 0:
        print(f"ERROR running {' '.join(cmd)}:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result


# ---------------------------------------------------------------------------
# Repo root detection
# ---------------------------------------------------------------------------

def _try_run(cmd: list[str]) -> subprocess.CompletedProcess | None:
    """Run a command, returning None if the executable is not found."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        return None


def find_repo_root() -> str:
    """Find the VCS repo root, trying each supported system in order."""
    r = _try_run(["git", "rev-parse", "--show-toplevel"])
    if r and r.returncode == 0:
        return r.stdout.strip()

    r = _try_run(["hg", "root"])
    if r and r.returncode == 0:
        return r.stdout.strip()

    r = _try_run(["p4", "info"])
    if r and r.returncode == 0:
        for line in r.stdout.splitlines():
            if line.lower().startswith("client root:"):
                return line.split(":", 1)[1].strip()

    r = _try_run(["cm", "workspace", "list"])
    if r and r.returncode == 0:
        return os.getcwd()

    return os.getcwd()


# ---------------------------------------------------------------------------
# VCS detection
# ---------------------------------------------------------------------------

def detect_vcs(repo_root: str) -> str | None:
    """Determine which VCS to use. Returns vcs name or None."""
    # User override: .claude/dd-vcs takes precedence
    override_file = os.path.join(repo_root, ".claude", "dd-vcs")
    if os.path.isfile(override_file):
        with open(override_file, encoding="utf-8") as f:
            value = f.read().strip().lower()
        aliases = {"p4": "perforce", "mercurial": "hg", "plastic": "unity-vcs"}
        value = aliases.get(value, value)
        if value in ("git", "perforce", "hg", "unity-vcs"):
            return value
        if value in ("none", "custom", ""):
            return None

    # Auto-detect
    if os.path.isdir(os.path.join(repo_root, ".git")):
        return "git"
    if os.path.isdir(os.path.join(repo_root, ".hg")):
        return "hg"
    if os.path.isdir(os.path.join(repo_root, ".plastic")):
        return "unity-vcs"
    if os.path.isfile(os.path.join(repo_root, ".p4config")) or os.environ.get("P4CONFIG"):
        return "perforce"

    return None


# ---------------------------------------------------------------------------
# Project root config
# ---------------------------------------------------------------------------

def resolve_project_root(repo_root: str, cli_override: str | None) -> str:
    """Determine where new project folders should be created."""
    if cli_override:
        path = os.path.abspath(cli_override)
        if not os.path.isdir(path):
            print(f"ERROR: --project-root '{path}' does not exist.", file=sys.stderr)
            sys.exit(1)
        return path

    config_file = os.path.join(repo_root, ".claude", "dd-projects-root")
    if os.path.isfile(config_file):
        with open(config_file, encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            if not os.path.isdir(content):
                print(f"ERROR: .claude/dd-projects-root points to '{content}' which does not exist.",
                      file=sys.stderr)
                sys.exit(1)
            return content

    return repo_root


# ---------------------------------------------------------------------------
# VCS checkpoint functions
# ---------------------------------------------------------------------------

def checkpoint_git(files: list[str], msg: str, repo_root: str) -> None:
    run(["git", "add"] + files, repo_root)
    run(["git", "commit", "-m", msg], repo_root)
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_root).stdout.strip()
    if branch and branch != "HEAD":
        run(["git", "push", "-u", "origin", branch], repo_root)
    else:
        print("  Warning: detached HEAD — skipping push.", file=sys.stderr)


def checkpoint_hg(files: list[str], msg: str, repo_root: str) -> None:
    run(["hg", "add"] + files, repo_root)
    run(["hg", "commit", "-m", msg], repo_root)
    run(["hg", "push"], repo_root)


def checkpoint_perforce(files: list[str], msg: str, repo_root: str) -> None:
    run(["p4", "add"] + files, repo_root)
    run(["p4", "submit", "-d", msg], repo_root)


def checkpoint_unity_vcs(files: list[str], msg: str, repo_root: str) -> None:
    run(["cm", "add"] + files, repo_root)
    run(["cm", "checkin", f"--comment={msg}"] + files, repo_root)
    run(["cm", "push"], repo_root, fatal=False)


def checkpoint(files: list[str], msg: str, repo_root: str, vcs: str | None) -> None:
    """Commit and push files using the appropriate VCS. No-op if vcs is None."""
    if vcs is None:
        print("\n  No VCS detected — skipping commit.")
        return
    print(f"\nCommitting and pushing ({vcs})...")
    dispatch = {
        "git": checkpoint_git,
        "hg": checkpoint_hg,
        "perforce": checkpoint_perforce,
        "unity-vcs": checkpoint_unity_vcs,
    }
    dispatch[vcs](files, msg, repo_root)
