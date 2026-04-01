#!/usr/bin/env python3
"""
dd_log_prompt.py — UserPromptSubmit hook for Daydream Dictation.

Fires on every prompt. Appends a numbered entry to the active project's
Prompts document, or to Prompts-ddMetadiscussion if no project is active.

Active project is read from dd-current-dictation-project at the repo root.
That file contains the absolute path to the project folder; this hook
resolves the Prompts file inside it dynamically.
"""

import glob as glob_module
import json
import os
import re
import sys

# Import dd_lib from the scripts/ directory alongside hooks/
_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_PLUGIN_ROOT, "scripts"))
import dd_lib as dd


# ---------------------------------------------------------------------------
# Entry numbering
# ---------------------------------------------------------------------------

def next_entry_number(path: str) -> int:
    """Return the next prompt number by counting lines matching '^N. '.

    Uses '^[0-9]+\\. ' so multi-line prompt text, code blocks, and other
    lines that happen to start with a digit don't inflate the count.
    """
    if not os.path.isfile(path):
        return 1
    count = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if re.match(r'^\d+\. ', line):
                count += 1
    return count + 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    prompt = data.get("prompt", "").strip()
    if not prompt:
        sys.exit(0)

    repo_root = dd.find_repo_root()

    # Determine target Prompts document
    prompts_doc = None
    state_file = os.path.join(repo_root, "dd-current-dictation-project")
    if os.path.isfile(state_file):
        with open(state_file, encoding="utf-8") as f:
            project_folder = f.read().strip()
        if project_folder:
            matches = sorted(glob_module.glob(os.path.join(project_folder, "Prompts-*")))
            if matches:
                prompts_doc = matches[0]

    if prompts_doc is None:
        prompts_doc = os.path.join(repo_root, "Prompts-ddMetadiscussion")
        if not os.path.isfile(prompts_doc):
            with open(prompts_doc, "w", encoding="utf-8") as f:
                f.write("# Prompts \u2014 ddMetadiscussion\n\n---\n\n")

    # Append numbered entry
    entry_num = next_entry_number(prompts_doc)
    entry = f"\n{entry_num}. {prompt}\n"

    try:
        with open(prompts_doc, "a", encoding="utf-8") as f:
            f.write(entry)
    except OSError as e:
        print(
            f"dd-log-prompt: WARNING — could not write to {prompts_doc}: {e}",
            file=sys.stderr,
        )
        # Always exit 0 — hook must never block the session (T-067)
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
