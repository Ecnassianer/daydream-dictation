#!/usr/bin/env python3
"""
dd_stop_failure_hook.py — StopFailure hook for Daydream Dictation.

Registered in the daydream-dictation skill's frontmatter. When a turn ends
with an API error, Stop doesn't fire, so this hook makes sure prompts held by
a session-start or resume marker still get logged and committed (ADR-0005,
ADR-0006). A failed turn can't be blocked, so there is no cleanliness check.
"""

import os
import sys

# Import the shared libraries from the daydream-dictation skill's scripts/ folder
_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.join(_PLUGIN_ROOT, "skills", "daydream-dictation", "scripts"))
import dd_lib as dd
import dd_prompt_log as pl


def main() -> None:
    data = pl.read_hook_input()
    repo_root = dd.find_repo_root()
    try:
        result = pl.backfill(data, repo_root)
        if result:
            pl.commit_backfill(repo_root, result)
    except OSError as e:
        print(f"dd-stop-failure: WARNING — could not backfill prompts: {e}", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
