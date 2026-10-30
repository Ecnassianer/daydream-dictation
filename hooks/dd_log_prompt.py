#!/usr/bin/env python3
"""
dd_log_prompt.py — UserPromptSubmit hook for Daydream Dictation.

Registered in the daydream-dictation skill's frontmatter, so it runs only
while the skill is active (ADR-0002). Appends a numbered entry to the active
project's Prompts document. With no active project it logs nothing (ADR-0003).

Before logging, it backfills any prompts a session-start or resume marker is
holding (ADR-0005), so entries stay in order.
"""

import os
import sys

# Import the shared libraries from the scripts/ directory alongside hooks/
_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.join(_PLUGIN_ROOT, "scripts"))
import dd_lib as dd
import dd_prompt_log as pl


def main() -> None:
    data = pl.read_hook_input()
    prompt = str(data.get("prompt", "")).strip()
    if not prompt or pl.is_automated_notification(prompt):
        sys.exit(0)

    repo_root = dd.find_repo_root()
    try:
        pl.backfill(data, repo_root, current_prompt=prompt)
        prompts_doc = pl.active_prompts_doc(repo_root)
        if prompts_doc is not None:
            pl.append_entry(prompts_doc, prompt)
    except OSError as e:
        print(f"dd-log-prompt: WARNING — could not log prompt: {e}", file=sys.stderr)

    # Always exit 0 — this hook must never block the session (T-067)
    sys.exit(0)


if __name__ == "__main__":
    main()
