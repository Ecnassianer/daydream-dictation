#!/usr/bin/env python3
"""
dd_prompt_log.py — Shared prompt-logging library for Daydream Dictation hooks.

Every hook that writes to a Prompts document goes through this module
(ADR-0004): resolving the active project's Prompts doc, numbering entries,
filtering automated notifications, reading prompts back out of the session
transcript, the session-start and resume markers (ADR-0005), and committing
backfilled entries (ADR-0006).

A *marker* means "user prompts in the transcript from this position onward
haven't been logged yet". It is either a `start` marker (the prompt that
invoked the skill) or a `resume` marker (prompts after --resume/--continue).
Markers and per-session state live outside the repo, under
$XDG_STATE_HOME/daydream-dictation/sessions/ (by default
~/.local/state/daydream-dictation/sessions/). State left in the legacy
~/.claude/daydream-dictation/sessions/ is picked up and moved (ADR-0009).
"""

from __future__ import annotations

import glob as glob_module
import json
import os
import re
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import dd_lib as dd


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Skill names whose invocation starts a dictation session. A plugin install
# namespaces them ("daydream-dictation:daydream-dictation").
_SKILL_NAMES = ("daydream-dictation", "dictate-daydream")

# Claude Code delivers some automated events (background task results, PR
# webhook activity) into the session as prompts. They aren't user prompts,
# so they don't belong in any Prompts document.
_AUTOMATED_PREFIXES = (
    "<task-notification>",
    "<github-webhook-activity>",
)

# Transcript user entries that aren't prompts the user typed.
_NON_PROMPT_PREFIXES = (
    "<local-command-",
    "[Request interrupted by user",
)

# Entry labels and notes, per marker kind.
LABELS = {
    "start": ("session start", "backfilled at session start"),
    "resume": ("backfilled after resume", "backfilled after resume"),
}

STALE_STATE_SECONDS = 7 * 24 * 3600


# ---------------------------------------------------------------------------
# Prompts document
# ---------------------------------------------------------------------------

def active_prompts_doc(repo_root: str) -> str | None:
    """Return the active project's Prompts doc, creating it if needed.

    Returns None when no project is set or its folder is missing: with no
    active project, nothing is logged (ADR-0003).
    """
    state_file = os.path.join(repo_root, "dd-current-dictation-project")
    if not os.path.isfile(state_file):
        return None
    with open(state_file, encoding="utf-8") as f:
        project_folder = f.read().strip()
    if not project_folder or not os.path.isdir(project_folder):
        return None

    matches = sorted(glob_module.glob(os.path.join(project_folder, "Prompts-*")))
    if matches:
        return matches[0]

    slug = os.path.basename(project_folder.rstrip("/"))
    prompts_doc = os.path.join(project_folder, f"Prompts-{slug}.md")
    with open(prompts_doc, "w", encoding="utf-8") as f:
        f.write(f"# Prompts — {slug}\n\n---\n\n")
    return prompts_doc


def next_entry_number(path: str) -> int:
    """Return the next prompt number by counting lines matching '^N. '.

    Uses '^[0-9]+\\. ' so multi-line prompt text, code blocks, notes and
    other lines that happen to start with a digit don't inflate the count.
    """
    if not os.path.isfile(path):
        return 1
    count = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if re.match(r'^\d+\. ', line):
                count += 1
    return count + 1


def append_entry(path: str, text: str, label: str | None = None) -> int:
    """Append a numbered entry and return its number."""
    number = next_entry_number(path)
    prefix = f"({label}) " if label else ""
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n{number}. {prefix}{text}\n")
    return number


def append_note(path: str, note: str) -> None:
    """Append an unnumbered note line (a Markdown quote)."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n> {note}\n")


def is_automated_notification(prompt: str) -> bool:
    """Return True if the prompt is an automated notification, not user input."""
    return prompt.startswith(_AUTOMATED_PREFIXES)


# ---------------------------------------------------------------------------
# Transcript
# ---------------------------------------------------------------------------

def read_transcript(path: str | None) -> list[dict]:
    """Read a session transcript (JSONL). Unreadable lines become {}."""
    if not path or not os.path.isfile(path):
        return []
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                entries.append({})
    return entries


def _is_skill_name(name: str) -> bool:
    name = name.strip().lstrip("/")
    return name.split(":")[-1] in _SKILL_NAMES


def _command_text(content: str) -> str | None:
    """Turn a transcript slash-command entry back into the line the user typed."""
    m = re.search(r"<command-name>(.*?)</command-name>", content, re.S)
    if not m:
        return None
    name = m.group(1).strip()
    if not name.startswith("/"):
        name = "/" + name
    a = re.search(r"<command-args>(.*?)</command-args>", content, re.S)
    args = a.group(1).strip() if a else ""
    return f"{name} {args}".strip()


def entry_prompt(entry: dict) -> str | None:
    """Return the prompt text of a transcript entry the user typed, else None."""
    if entry.get("type") != "user" or entry.get("isMeta") or entry.get("isCompactSummary"):
        return None
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, list):
        if any(b.get("type") == "tool_result" for b in content if isinstance(b, dict)):
            return None
        content = "\n".join(
            b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
        )
    if not isinstance(content, str):
        return None
    text = content.strip()
    if not text:
        return None
    command = _command_text(text)
    if command is not None:
        text = command
    if text.startswith(_NON_PROMPT_PREFIXES) or is_automated_notification(text):
        return None
    return text


def find_skill_invocation(entries: list[dict]) -> int | None:
    """Return the index of the prompt that first invoked the dictation skill.

    That is a typed /daydream-dictation (or /dictate-daydream) command, or
    the last prompt the user typed before the Skill tool call for it.
    """
    last_prompt = None
    for i, entry in enumerate(entries):
        text = entry_prompt(entry)
        if text is not None:
            if text.startswith("/") and _is_skill_name(text.split()[0]):
                return i
            last_prompt = i
        if entry.get("type") == "assistant":
            content = (entry.get("message") or {}).get("content")
            for block in content if isinstance(content, list) else []:
                if (isinstance(block, dict) and block.get("type") == "tool_use"
                        and block.get("name") == "Skill"
                        and _is_skill_name(str((block.get("input") or {}).get("skill", "")))):
                    return last_prompt
    return None


def prompts_from(entries: list[dict], position: int) -> list[tuple[str, str | None]]:
    """Return (text, timestamp) for every user prompt at or after position."""
    out = []
    for entry in entries[position:]:
        text = entry_prompt(entry)
        if text is not None:
            out.append((text, entry.get("timestamp")))
    return out


# ---------------------------------------------------------------------------
# Session state and markers
# ---------------------------------------------------------------------------

def state_dir() -> str:
    override = os.environ.get("DD_STATE_DIR")
    if override:
        return override
    base = os.environ.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    return os.path.join(base, "daydream-dictation", "sessions")


def legacy_state_dir() -> str | None:
    """Where state lived before ADR-0009, or None when DD_STATE_DIR is set.

    Read only to carry a session that started before the move across it.
    """
    if os.environ.get("DD_STATE_DIR"):
        return None
    config = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
    return os.path.join(config, "daydream-dictation", "sessions")


def _state_filename(session_id: str) -> str:
    return f"{re.sub(r'[^A-Za-z0-9_-]', '_', session_id)}.json"


# File locking. fcntl exists only on macOS and Linux; Windows has msvcrt.
# Both are in the standard library. The lock covers the session's state file
# while a hook reads and rewrites it, so overlapping hooks can't clobber
# each other's changes.

def _lock_posix(f) -> None:
    import fcntl
    fcntl.flock(f, fcntl.LOCK_EX)


def _unlock_posix(f) -> None:
    import fcntl
    fcntl.flock(f, fcntl.LOCK_UN)


def _lock_windows(f) -> None:
    import msvcrt
    # msvcrt locks a byte range starting at the current position. Lock the
    # first byte; that works even while the file is empty. LK_LOCK retries
    # for about 10 seconds, then raises OSError.
    f.seek(0)
    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)


def _unlock_windows(f) -> None:
    import msvcrt
    f.seek(0)
    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)


if os.name == "nt":
    _lock_file, _unlock_file = _lock_windows, _unlock_windows
else:
    _lock_file, _unlock_file = _lock_posix, _unlock_posix


@contextmanager
def session_state(session_id: str):
    """Lock, load and save the state for one session.

    State keys: "start_handled" (bool) and "marker" (dict or absent) with
    "kind", "position", "time" and "note_written".
    """
    directory = state_dir()
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, _state_filename(session_id))
    legacy = legacy_state_dir()
    legacy_path = os.path.join(legacy, _state_filename(session_id)) if legacy else None
    with open(path, "a+", encoding="utf-8") as f:
        _lock_file(f)
        try:
            f.seek(0)
            raw = f.read()
            if not raw.strip() and legacy_path and os.path.isfile(legacy_path):
                # A session that started before the state folder moved.
                try:
                    with open(legacy_path, encoding="utf-8") as old:
                        raw = old.read()
                    os.remove(legacy_path)
                except OSError:
                    pass
            try:
                state = json.loads(raw) if raw.strip() else {}
            except json.JSONDecodeError:
                state = {}
            yield state
            f.seek(0)
            f.truncate()
            json.dump(state, f)
        finally:
            # Write the new state to disk before another hook can take the lock.
            f.flush()
            _unlock_file(f)


def cleanup_stale_state(max_age: int = STALE_STATE_SECONDS) -> None:
    cutoff = time.time() - max_age
    for directory in (state_dir(), legacy_state_dir()):
        if not directory or not os.path.isdir(directory):
            continue
        for path in glob_module.glob(os.path.join(directory, "*.json")):
            try:
                if os.path.getmtime(path) < cutoff:
                    os.remove(path)
            except OSError:
                pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _display_time(ts: str | None) -> str:
    when = _parse_iso(ts) or datetime.now(timezone.utc)
    return when.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def start_note(ts: str | None, session_id: str) -> str:
    return (f"▶ Session started {_display_time(ts)} (session {session_id[:8]}). "
            "The prompt that started it is logged below.")


def resume_note(ts: str | None, session_id: str) -> str:
    return (f"⟳ Session resumed {_display_time(ts)} (session {session_id[:8]}). "
            "Prompts sent before the skill is re-invoked are backfilled below.")


def ensure_start_marker(session_id: str, entries: list[dict]) -> None:
    """Create the start marker the first time a skill hook runs in a session."""
    with session_state(session_id) as state:
        if state.get("start_handled"):
            return
        state["start_handled"] = True
        if "marker" in state:
            return
        index = find_skill_invocation(entries)
        if index is None:
            return
        state["marker"] = {
            "kind": "start",
            "position": index,
            "time": entries[index].get("timestamp"),
            "note_written": False,
        }


def mark_resumed(session_id: str, entries: list[dict], prompts_doc: str | None) -> None:
    """Record a resume: keep any earlier marker, write the resume note if possible."""
    with session_state(session_id) as state:
        # A resumed session already started; never treat its first
        # invocation as a new session start.
        state["start_handled"] = True
        marker = state.get("marker")
        if marker is None:
            marker = {"kind": "resume", "position": len(entries), "time": _now_iso(),
                      "note_written": False}
            state["marker"] = marker
        if marker["kind"] == "resume" and not marker["note_written"] and prompts_doc:
            append_note(prompts_doc, resume_note(marker["time"], session_id))
            marker["note_written"] = True


def flush_marker(session_id: str, entries: list[dict], repo_root: str,
                 current_prompt: str | None = None) -> dict | None:
    """Log every prompt from the marker onward, if a marker and a project exist.

    current_prompt is the prompt a UserPromptSubmit hook is about to log
    itself; it is left out of the backfill if the transcript already has it.
    Returns {"prompts_doc", "count", "kind", "first_time"} or None.
    """
    with session_state(session_id) as state:
        marker = state.get("marker")
        if not marker:
            return None
        prompts_doc = active_prompts_doc(repo_root)
        if prompts_doc is None:
            return None

        prompts = prompts_from(entries, marker["position"])
        if current_prompt is not None and prompts and prompts[-1][0] == current_prompt.strip():
            prompts.pop()

        kind = marker["kind"]
        if not marker["note_written"]:
            note = start_note if kind == "start" else resume_note
            append_note(prompts_doc, note(marker["time"], session_id))
        first_label, rest_label = LABELS[kind]
        for i, (text, _) in enumerate(prompts):
            append_entry(prompts_doc, text, first_label if i == 0 else rest_label)

        del state["marker"]
        return {
            "prompts_doc": prompts_doc,
            "count": len(prompts),
            "kind": kind,
            "first_time": prompts[0][1] if prompts else marker["time"],
        }


# ---------------------------------------------------------------------------
# Committing backfilled entries (ADR-0006)
# ---------------------------------------------------------------------------

def _git(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)


def _git_push(repo_root: str) -> bool:
    branch = _git(["branch", "--show-current"], repo_root).stdout.strip()
    if not branch:
        return False
    return _git(["push", "-u", "origin", branch], repo_root).returncode == 0


def commit_backfill(repo_root: str, result: dict) -> str:
    """Commit (and push) backfilled entries per the skill's commit discipline.

    On git, the entries are folded into the agent's own commit when that commit
    was made after the first backfilled prompt and hasn't been pushed;
    otherwise they get their own commit. Returns a short description of what
    happened. Never raises: the Stop hook's cleanliness check reports
    anything left over.
    """
    prompts_doc = result["prompts_doc"]
    if result["kind"] == "start":
        message = "Log session-start prompt"
    else:
        message = f"Backfill {result['count']} prompt(s) after resume"

    vcs = dd.detect_vcs(repo_root)
    if vcs is None:
        return "no-vcs"
    if vcs != "git":
        try:
            dd.checkpoint([prompts_doc], message, repo_root, vcs)
        except SystemExit:
            return "failed"
        return "own-commit"

    if not _git(["status", "--porcelain", "--", prompts_doc], repo_root).stdout.strip():
        return "nothing"

    # The Prompts doc may be new and untracked; --only needs it known to git.
    _git(["add", "--", prompts_doc], repo_root)
    if _should_amend(repo_root, result.get("first_time")):
        r = _git(["commit", "--amend", "--no-edit", "--only", "--", prompts_doc], repo_root)
        action = "amended"
    else:
        r = _git(["commit", "-m", message, "--only", "--", prompts_doc], repo_root)
        action = "own-commit"
    if r.returncode != 0:
        return "failed"
    _git_push(repo_root)
    return action


def _should_amend(repo_root: str, first_time: str | None) -> bool:
    first = _parse_iso(first_time)
    if first is None:
        return False
    r = _git(["log", "-1", "--format=%ct"], repo_root)
    if r.returncode != 0 or not r.stdout.strip():
        return False
    head_time = datetime.fromtimestamp(int(r.stdout.strip()), tz=timezone.utc)
    if head_time < first.replace(microsecond=0):
        return False
    pushed = _git(["branch", "-r", "--contains", "HEAD"], repo_root).stdout.strip()
    return not pushed


# ---------------------------------------------------------------------------
# Hook input
# ---------------------------------------------------------------------------

def read_hook_input() -> dict:
    """Read the hook's JSON input from stdin; {} if missing or invalid."""
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def backfill(data: dict, repo_root: str, current_prompt: str | None = None) -> dict | None:
    """Create the start marker if this is the session's first skill hook, then flush.

    Shared first step of the skill's UserPromptSubmit, Stop and StopFailure
    hooks. Does nothing without a session ID.
    """
    session_id = data.get("session_id")
    if not session_id:
        return None
    # Most turns have nothing to backfill; skip reading the transcript then.
    with session_state(session_id) as state:
        if state.get("start_handled") and "marker" not in state:
            return None
    entries = read_transcript(data.get("transcript_path"))
    ensure_start_marker(session_id, entries)
    return flush_marker(session_id, entries, repo_root, current_prompt)
