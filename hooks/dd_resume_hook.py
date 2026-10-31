#!/usr/bin/env python3
"""
dd_resume_hook.py — SessionStart (resume) hook for Daydream Dictation.

The plugin's only always-registered hook (hooks/hooks.json, matcher
"resume"), so it runs when a session is resumed or continued and at no other
time. Skill-scoped hooks don't survive a resume (ADR-0005). If the resumed
session used the daydream-dictation skill, this hook:

  * writes a resume note to the active project's Prompts doc;
  * leaves a resume marker so the skill's hooks backfill the prompts sent
    before the skill is re-invoked;
  * tells the agent to invoke the skill again.

Otherwise it exits without doing anything.
"""

import json
import os
import sys

# Import the shared libraries from the scripts/ directory alongside hooks/
_PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.join(_PLUGIN_ROOT, "scripts"))
import dd_lib as dd
import dd_prompt_log as pl

_CONTEXT = (
    "This resumed session was a Daydream Dictation session. Its prompt logging "
    "and commit checks stop when a session is resumed. Before responding to "
    "anything else, invoke the daydream-dictation skill again to restore them. "
    "Don't repeat the session-start steps or greeting; just continue with the "
    "user's request. Prompts sent before you re-invoke the skill are backfilled "
    "into the Prompts document automatically."
)


def main() -> None:
    data = pl.read_hook_input()
    session_id = data.get("session_id")
    if data.get("source", "resume") != "resume" or not session_id:
        sys.exit(0)

    try:
        pl.cleanup_stale_state()
        entries = pl.read_transcript(data.get("transcript_path"))
        if pl.find_skill_invocation(entries) is None:
            sys.exit(0)
        repo_root = dd.find_repo_root()
        pl.mark_resumed(session_id, entries, pl.active_prompts_doc(repo_root))
    except OSError as e:
        print(f"dd-resume-hook: WARNING — {e}", file=sys.stderr)
        sys.exit(0)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": _CONTEXT,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
