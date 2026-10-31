"""
tests/test_prompt_log.py — Session-start and resume backfill (ADR-0005) and
committing backfilled entries (ADR-0006).

Run with:
    cd <plugin-root>
    python3 -m pytest tests/test_prompt_log.py -v

These tests build synthetic Claude Code transcripts and run the hook scripts
as subprocesses, the way Claude Code would.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HOOKS = os.path.join(_REPO_ROOT, "hooks")
_LOG_PROMPT = os.path.join(_HOOKS, "dd_log_prompt.py")
_STOP_HOOK = os.path.join(_HOOKS, "dd_stop_hook.py")
_STOP_FAILURE = os.path.join(_HOOKS, "dd_stop_failure_hook.py")
_RESUME_HOOK = os.path.join(_HOOKS, "dd_resume_hook.py")

sys.path.insert(0, os.path.join(_REPO_ROOT, "scripts"))
import dd_prompt_log as pl  # noqa: E402

PAST = "2020-01-01T10:00:00.000Z"
FUTURE = "2099-01-01T10:00:00.000Z"


# ---------------------------------------------------------------------------
# Transcript builders
# ---------------------------------------------------------------------------

def prompt(text, ts=PAST):
    return {"type": "user", "timestamp": ts, "message": {"role": "user", "content": text}}


def command(name, args="", ts=PAST):
    content = (f"<command-message>{name}</command-message>\n"
               f"<command-name>/{name}</command-name>\n"
               f"<command-args>{args}</command-args>")
    return {"type": "user", "timestamp": ts, "message": {"role": "user", "content": content}}


def skill_call(skill="daydream-dictation:daydream-dictation", ts=PAST):
    return {"type": "assistant", "timestamp": ts, "message": {"role": "assistant", "content": [
        {"type": "tool_use", "id": "toolu_1", "name": "Skill", "input": {"skill": skill}}]}}


def skill_text(ts=PAST):
    """The skill body Claude Code injects after an invocation."""
    return {"type": "user", "isMeta": True, "timestamp": ts,
            "message": {"role": "user", "content": [{"type": "text", "text": "Base directory for this skill: ..."}]}}


def tool_result(ts=PAST):
    return {"type": "user", "timestamp": ts, "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "toolu_1", "content": "done"}]}}


def reply(text="OK", ts=PAST):
    return {"type": "assistant", "timestamp": ts, "message": {"role": "assistant", "content": [
        {"type": "text", "text": text}]}}


# ---------------------------------------------------------------------------
# Fixture: a git repo with a remote, a project, and a transcript
# ---------------------------------------------------------------------------

def _git(args, cwd, env=None):
    return subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True,
                          env={**os.environ, **(env or {})})


class Session:
    def __init__(self):
        self.base = tempfile.mkdtemp(prefix="dd_pl_")
        self.state = os.path.join(self.base, "state")
        bare = os.path.join(self.base, "remote.git")
        self.repo = os.path.join(self.base, "work")
        _git(["init", "--bare", bare], self.base)
        _git(["clone", bare, self.repo], self.base)
        for key, value in (("user.email", "t@t.com"), ("user.name", "Test"), ("commit.gpgsign", "false")):
            _git(["config", key, value], self.repo)
        with open(os.path.join(self.repo, ".gitignore"), "w") as f:
            f.write("dd-current-dictation-project\n")
        self.project = os.path.join(self.repo, "MyGame")
        os.makedirs(self.project)
        self.prompts = os.path.join(self.project, "Prompts-MyGame.md")
        with open(self.prompts, "w") as f:
            f.write("# Prompts — MyGame\n\n---\n\n")
        _git(["add", "."], self.repo)
        _git(["commit", "-m", "init"], self.repo, {"GIT_COMMITTER_DATE": "2019-01-01T00:00:00Z",
                                                    "GIT_AUTHOR_DATE": "2019-01-01T00:00:00Z"})
        _git(["push", "-u", "origin", "HEAD"], self.repo)
        self.branch = _git(["branch", "--show-current"], self.repo).stdout.strip()
        self.transcript = os.path.join(self.base, "session.jsonl")
        self.entries = []
        self.session_id = "7be2518d-ba92-49c2-bc13-0bb8844af307"

    def set_project(self):
        with open(os.path.join(self.repo, "dd-current-dictation-project"), "w") as f:
            f.write(self.project)

    def add(self, *entries):
        self.entries.extend(entries)
        with open(self.transcript, "w") as f:
            for e in self.entries:
                f.write(json.dumps(e) + "\n")

    def run(self, hook, **extra):
        data = {"session_id": self.session_id, "transcript_path": self.transcript,
                "cwd": self.repo, **extra}
        return subprocess.run(
            [sys.executable, hook], cwd=self.repo, capture_output=True, text=True,
            input=json.dumps(data),
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "DD_STATE_DIR": self.state},
        )

    def log(self):
        with open(self.prompts, encoding="utf-8") as f:
            return f.read()

    def entry_lines(self):
        return [l for l in self.log().splitlines() if l[:1].isdigit() or l.startswith(">")]

    def head_subject(self):
        return _git(["log", "-1", "--format=%s"], self.repo).stdout.strip()

    def commit_count(self):
        return int(_git(["rev-list", "--count", "HEAD"], self.repo).stdout.strip())

    def unpushed(self):
        return _git(["rev-list", "--count", f"origin/{self.branch}..HEAD"], self.repo).stdout.strip()

    def cleanup(self):
        shutil.rmtree(self.base, ignore_errors=True)


@pytest.fixture
def s():
    session = Session()
    yield session
    session.cleanup()


# ---------------------------------------------------------------------------
# Session start
# ---------------------------------------------------------------------------

class TestSessionStart:

    def test_typed_command_logged_with_start_note(self, s):
        """The typed /daydream-dictation prompt, with its text, is logged at the end of the first turn."""
        s.set_project()
        s.add(command("daydream-dictation:daydream-dictation", "start a game that has floating islands"),
              skill_text(), reply())
        s.run(_STOP_HOOK)
        lines = s.entry_lines()
        assert lines[0].startswith("> ▶ Session started 2020-01-01 10:00 UTC (session 7be2518d)")
        assert lines[1] == ("1. (session start) /daydream-dictation:daydream-dictation "
                            "start a game that has floating islands")

    def test_natural_language_invocation(self, s):
        """When Claude invokes the skill itself, the prompt before its Skill call is logged."""
        s.set_project()
        s.add(prompt("hello"), reply(),
              prompt("start a daydream dictation about a game that has a grumpy lighthouse keeper"),
              skill_call(), tool_result(), skill_text(), reply())
        s.run(_STOP_HOOK)
        lines = s.entry_lines()
        assert lines[1] == "1. (session start) start a daydream dictation about a game that has a grumpy lighthouse keeper"
        assert "hello" not in s.log()

    def test_alias_invocation(self, s):
        s.set_project()
        s.add(command("dictate-daydream", "about boats"), reply())
        s.run(_STOP_HOOK)
        assert "1. (session start) /dictate-daydream about boats" in s.log()

    def test_logged_only_once(self, s):
        s.set_project()
        s.add(command("daydream-dictation", "start"), reply())
        s.run(_STOP_HOOK)
        s.add(prompt("more"), reply())
        s.run(_LOG_PROMPT, prompt="more")
        s.run(_STOP_HOOK)
        assert s.log().count("(session start)") == 1
        assert s.log().count("Session started") == 1
        assert s.entry_lines()[-1] == "2. more"

    def test_project_chosen_later(self, s):
        """With no project at first, the opening prompt and the answer are backfilled in order."""
        s.add(prompt("start a daydream dictation about a game that has robots"), skill_call(),
              skill_text(), reply("Which project?"))
        s.run(_STOP_HOOK)
        assert "robots" not in s.log()

        s.add(prompt("MyGame"))
        s.run(_LOG_PROMPT, prompt="MyGame")
        assert "MyGame\n" not in s.log().split("---", 1)[1]

        s.set_project()
        s.add(reply("Switched."))
        s.run(_STOP_HOOK)
        lines = s.entry_lines()
        assert lines[0].startswith("> ▶ Session started")
        assert lines[1] == "1. (session start) start a daydream dictation about a game that has robots"
        assert lines[2] == "2. (backfilled at session start) MyGame"

    def test_user_prompt_submit_backfills_first(self, s):
        """If Stop never ran (Esc), the next prompt's hook logs the start prompt before its own."""
        s.set_project()
        s.add(command("daydream-dictation", "start"), skill_text(), prompt("next idea"))
        s.run(_LOG_PROMPT, prompt="next idea")
        lines = s.entry_lines()
        assert lines[1] == "1. (session start) /daydream-dictation start"
        assert lines[2] == "2. next idea"

    def test_stop_failure_backfills(self, s):
        s.set_project()
        s.add(command("daydream-dictation", "start"))
        s.run(_STOP_FAILURE, error="rate_limit")
        assert "1. (session start) /daydream-dictation start" in s.log()

    def test_skips_non_prompts(self, s):
        """Meta entries, tool results, notifications and interrupts are not logged."""
        s.add(command("daydream-dictation", "start"), skill_text(), tool_result(),
              prompt("<task-notification>\n<status>completed</status>\n</task-notification>"),
              prompt("[Request interrupted by user]"),
              prompt("<local-command-stdout>done</local-command-stdout>"),
              prompt("real answer"))
        s.set_project()
        s.run(_STOP_HOOK)
        numbered = [l for l in s.entry_lines() if l[:1].isdigit()]
        assert numbered == ["1. (session start) /daydream-dictation start",
                            "2. (backfilled at session start) real answer"]


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------

class TestResume:

    def _dictation_history(self, s):
        s.set_project()
        s.add(command("daydream-dictation", "start"), skill_text(), reply())
        s.run(_STOP_HOOK)
        s.add(prompt("idea one"))
        s.run(_LOG_PROMPT, prompt="idea one")
        s.add(reply())

    def test_resume_hook_notes_and_nudges(self, s):
        self._dictation_history(s)
        r = s.run(_RESUME_HOOK, source="resume", hook_event_name="SessionStart")
        out = json.loads(r.stdout)
        assert "invoke the daydream-dictation skill" in out["hookSpecificOutput"]["additionalContext"]
        assert s.entry_lines()[-1].startswith("> ⟳ Session resumed")

    def test_resume_hook_ignores_other_sessions(self, s):
        s.add(prompt("unrelated work"), reply())
        r = s.run(_RESUME_HOOK, source="resume")
        assert r.returncode == 0 and r.stdout == ""
        assert not os.path.isdir(s.state) or os.listdir(s.state) == []

    @pytest.mark.parametrize("hook", ["stop", "stop_failure", "user_prompt_submit"])
    def test_backfill_after_resume(self, s, hook):
        """Prompts sent before re-invocation are backfilled by whichever skill hook fires first."""
        self._dictation_history(s)
        s.run(_RESUME_HOOK, source="resume")
        s.add(prompt("the garden has a pond", ts=FUTURE), skill_call(ts=FUTURE), skill_text(ts=FUTURE))
        if hook == "stop":
            s.run(_STOP_HOOK)
        elif hook == "stop_failure":
            s.run(_STOP_FAILURE, error="server_error")
        else:
            s.add(prompt("add a bench", ts=FUTURE))
            s.run(_LOG_PROMPT, prompt="add a bench")
        numbered = [l for l in s.entry_lines() if l[:1].isdigit()]
        assert numbered[:2] == ["1. (session start) /daydream-dictation start", "2. idea one"]
        assert numbered[2] == "3. (backfilled after resume) the garden has a pond"
        if hook == "user_prompt_submit":
            assert numbered[3:] == ["4. add a bench"]
        assert s.log().count("(session start)") == 1

    def test_resume_without_project_writes_note_at_backfill(self, s):
        self._dictation_history(s)
        os.remove(os.path.join(s.repo, "dd-current-dictation-project"))
        s.run(_RESUME_HOOK, source="resume")
        assert "Session resumed" not in s.log()
        s.add(prompt("back again", ts=FUTURE), skill_call(ts=FUTURE))
        s.set_project()
        s.run(_STOP_HOOK)
        lines = s.entry_lines()
        assert lines[-2].startswith("> ⟳ Session resumed")
        assert lines[-1] == "3. (backfilled after resume) back again"


# ---------------------------------------------------------------------------
# Committing backfilled entries (ADR-0006)
# ---------------------------------------------------------------------------

class TestCommitBackfill:

    def test_own_commit_when_head_predates_prompt(self, s):
        s.set_project()
        s.add(command("daydream-dictation", "start", ts=FUTURE), reply(ts=FUTURE))
        before = s.commit_count()
        r = s.run(_STOP_HOOK)
        assert s.commit_count() == before + 1
        assert s.head_subject() == "Log session-start prompt"
        assert s.unpushed() == "0"
        assert r.returncode == 0

    def test_amends_unpushed_commit_made_after_prompt(self, s):
        s.set_project()
        s.add(command("daydream-dictation", "start", ts=PAST), reply())
        with open(os.path.join(s.project, "Daydream-MyGame.md"), "w") as f:
            f.write("# MyGame\n")
        _git(["add", "."], s.repo)
        _git(["commit", "-m", "Claude's work"], s.repo)
        before = s.commit_count()
        r = s.run(_STOP_HOOK)
        assert s.commit_count() == before
        assert s.head_subject() == "Claude's work"
        assert "Prompts-MyGame.md" in _git(["show", "--stat", "HEAD"], s.repo).stdout
        assert s.unpushed() == "0"
        assert r.returncode == 0

    def test_never_amends_pushed_commit(self, s):
        s.set_project()
        s.add(command("daydream-dictation", "start", ts=PAST), reply())
        with open(os.path.join(s.project, "Daydream-MyGame.md"), "w") as f:
            f.write("# MyGame\n")
        _git(["add", "."], s.repo)
        _git(["commit", "-m", "Claude's work"], s.repo)
        _git(["push"], s.repo)
        pushed_head = _git(["rev-parse", "HEAD"], s.repo).stdout.strip()
        s.run(_STOP_HOOK)
        assert s.head_subject() == "Log session-start prompt"
        assert _git(["rev-parse", "HEAD~1"], s.repo).stdout.strip() == pushed_head

    def test_resume_commit_message(self, s):
        s.set_project()
        s.add(command("daydream-dictation", "start", ts=PAST), reply())
        s.run(_STOP_HOOK)
        s.run(_RESUME_HOOK, source="resume")
        s.add(prompt("one", ts=FUTURE), prompt("two", ts=FUTURE), skill_call(ts=FUTURE))
        s.run(_STOP_HOOK)
        assert s.head_subject() == "Backfill 2 prompt(s) after resume"
        assert s.unpushed() == "0"

    def test_other_changes_stay_out_of_backfill_commit(self, s):
        """Only the Prompts doc is committed; Claude's uncommitted work is left for the check."""
        s.set_project()
        s.add(command("daydream-dictation", "start", ts=FUTURE))
        with open(os.path.join(s.repo, "README.md"), "w") as f:
            f.write("work in progress\n")
        _git(["add", "README.md"], s.repo)
        r = s.run(_STOP_HOOK)
        assert "README.md" not in _git(["show", "--stat", "HEAD"], s.repo).stdout
        assert r.returncode == 2
        assert "uncommitted" in r.stderr.lower()


# ---------------------------------------------------------------------------
# Library units
# ---------------------------------------------------------------------------

class TestLibrary:

    def test_command_text_round_trip(self):
        e = command("daydream-dictation:daydream-dictation", "about a game")
        assert pl.entry_prompt(e) == "/daydream-dictation:daydream-dictation about a game"

    def test_command_without_args(self):
        assert pl.entry_prompt(command("daydream-dictation")) == "/daydream-dictation"

    def test_find_invocation_none_without_skill(self):
        assert pl.find_skill_invocation([prompt("hi"), reply()]) is None

    def test_find_invocation_ignores_other_skills(self):
        entries = [prompt("make a chart"), skill_call("dataviz"), prompt("dictate"), skill_call()]
        assert pl.find_skill_invocation(entries) == 2

    def test_notes_are_not_numbered(self, tmp_path):
        doc = tmp_path / "Prompts-X.md"
        doc.write_text("# Prompts\n")
        pl.append_note(str(doc), "▶ Session started")
        assert pl.append_entry(str(doc), "first") == 1
        pl.append_note(str(doc), "⟳ Session resumed")
        assert pl.append_entry(str(doc), "second", "backfilled after resume") == 2


class TestStateDir:
    """Session state moved out of ~/.claude (ADR-0009)."""

    @pytest.fixture
    def dirs(self, tmp_path, monkeypatch):
        monkeypatch.delenv("DD_STATE_DIR", raising=False)
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude"))
        new = tmp_path / "state" / "daydream-dictation" / "sessions"
        legacy = tmp_path / "claude" / "daydream-dictation" / "sessions"
        return new, legacy

    def test_default_is_under_xdg_state_home(self, dirs):
        new, _ = dirs
        assert pl.state_dir() == str(new)

    def test_dd_state_dir_overrides_and_disables_legacy(self, dirs, tmp_path, monkeypatch):
        monkeypatch.setenv("DD_STATE_DIR", str(tmp_path / "custom"))
        assert pl.state_dir() == str(tmp_path / "custom")
        assert pl.legacy_state_dir() is None

    def test_legacy_session_state_is_carried_over(self, dirs):
        new, legacy = dirs
        legacy.mkdir(parents=True)
        (legacy / "sess-1.json").write_text(json.dumps({"start_handled": True}))
        with pl.session_state("sess-1") as state:
            assert state.get("start_handled") is True
        assert not (legacy / "sess-1.json").exists()
        assert json.loads((new / "sess-1.json").read_text())["start_handled"] is True

    def test_new_state_wins_over_legacy(self, dirs):
        new, legacy = dirs
        new.mkdir(parents=True)
        legacy.mkdir(parents=True)
        (new / "sess-2.json").write_text(json.dumps({"start_handled": True}))
        (legacy / "sess-2.json").write_text(json.dumps({"start_handled": False}))
        with pl.session_state("sess-2") as state:
            assert state.get("start_handled") is True

    def test_cleanup_removes_stale_files_in_both_folders(self, dirs):
        new, legacy = dirs
        for d in (new, legacy):
            d.mkdir(parents=True)
            stale = d / "old.json"
            stale.write_text("{}")
            os.utime(stale, (0, 0))
        pl.cleanup_stale_state()
        assert not (new / "old.json").exists()
        assert not (legacy / "old.json").exists()
