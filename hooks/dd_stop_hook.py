#!/usr/bin/env python3
"""
dd_stop_hook.py — Stop hook for Daydream Dictation.

Fires when a session ends or Claude finishes responding. Checks for
uncommitted changes, untracked files, and unpushed commits.

Exit codes:
  0 — repo is clean; Claude is allowed to stop.
  2 — violations found; blocks Claude from stopping. The stderr message
      is fed back to Claude, which is expected to commit/push and retry.
      (Exit code 2 is the Claude Code convention for "blocking error".)

Supports multiple VCS backends via dd_lib.detect_vcs().
"""

import json
import os
import subprocess
import sys

# Import dd_lib from the scripts/ directory alongside hooks/
_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_PLUGIN_ROOT, "scripts"))
import dd_lib as dd


def _run_quiet(cmd: list[str], cwd: str) -> subprocess.CompletedProcess:
    """Run a command and return the result without printing errors."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


# ---------------------------------------------------------------------------
# VCS-specific checks
# ---------------------------------------------------------------------------

def check_git(repo_root: str) -> None:
    """Check git repo for uncommitted changes, untracked files, unpushed commits."""
    # Uncommitted changes (staged or unstaged)
    r1 = _run_quiet(["git", "diff", "--quiet"], repo_root)
    r2 = _run_quiet(["git", "diff", "--cached", "--quiet"], repo_root)
    if r1.returncode != 0 or r2.returncode != 0:
        print(
            "There are uncommitted changes in the repository. "
            "Please commit and push these changes to the remote branch.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Untracked files
    r = _run_quiet(["git", "ls-files", "--others", "--exclude-standard"], repo_root)
    if r.stdout.strip():
        print(
            "There are untracked files in the repository. "
            "Please commit and push these changes to the remote branch.",
            file=sys.stderr,
        )
        sys.exit(2)

    # Unpushed commits
    r = _run_quiet(["git", "branch", "--show-current"], repo_root)
    current_branch = r.stdout.strip()
    if not current_branch:
        # Detached HEAD — nothing to compare
        return

    # Check if remote branch exists
    r = _run_quiet(["git", "rev-parse", f"origin/{current_branch}"], repo_root)
    if r.returncode == 0:
        # Branch exists on remote — compare against it
        r = _run_quiet(
            ["git", "rev-list", f"origin/{current_branch}..HEAD", "--count"],
            repo_root,
        )
        unpushed = int(r.stdout.strip()) if r.returncode == 0 else 0
        if unpushed > 0:
            print(
                f"There are {unpushed} unpushed commit(s) on branch '{current_branch}'. "
                "Please push these changes to the remote repository.",
                file=sys.stderr,
            )
            sys.exit(2)
    else:
        # Branch doesn't exist on remote — compare against default branch
        r = _run_quiet(
            ["git", "rev-list", "origin/HEAD..HEAD", "--count"],
            repo_root,
        )
        unpushed = int(r.stdout.strip()) if r.returncode == 0 else 0
        if unpushed > 0:
            print(
                f"Branch '{current_branch}' has {unpushed} unpushed commit(s) "
                "and no remote branch. Please push these changes to the remote repository.",
                file=sys.stderr,
            )
            sys.exit(2)


def check_hg(repo_root: str) -> None:
    """Check Mercurial repo for uncommitted/unpushed changes."""
    r = _run_quiet(["hg", "status"], repo_root)
    if r.stdout.strip():
        print(
            "There are uncommitted changes in the repository. "
            "Please commit and push these changes.",
            file=sys.stderr,
        )
        sys.exit(2)

    r = _run_quiet(["hg", "outgoing", "--quiet"], repo_root)
    if r.returncode == 0 and r.stdout.strip():
        print(
            "There are unpushed commits. Please push these changes.",
            file=sys.stderr,
        )
        sys.exit(2)


def check_perforce(repo_root: str) -> None:
    """Check Perforce for pending changelists."""
    r = _run_quiet(["p4", "opened"], repo_root)
    if r.returncode == 0 and r.stdout.strip():
        print(
            "There are open files in Perforce. "
            "Please submit your pending changelists.",
            file=sys.stderr,
        )
        sys.exit(2)


def check_unity_vcs(repo_root: str) -> None:
    """Check Unity VCS (Plastic SCM) for pending changes."""
    r = _run_quiet(["cm", "status", "--short"], repo_root)
    if r.returncode == 0 and r.stdout.strip():
        print(
            "There are pending changes in Unity VCS. "
            "Please checkin and push your changes.",
            file=sys.stderr,
        )
        sys.exit(2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    # Recursion prevention
    if data.get("stop_hook_active") is True:
        sys.exit(0)

    repo_root = dd.find_repo_root()
    vcs = dd.detect_vcs(repo_root)

    if vcs is None:
        sys.exit(0)

    checks = {
        "git": check_git,
        "hg": check_hg,
        "perforce": check_perforce,
        "unity-vcs": check_unity_vcs,
    }

    check_fn = checks.get(vcs)
    if check_fn:
        check_fn(repo_root)

    sys.exit(0)


if __name__ == "__main__":
    main()
