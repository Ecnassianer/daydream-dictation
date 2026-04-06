"""
tests/test_integration.py — Integration tests for scripts and hooks.

Run with:
    cd <plugin-root>
    python3 -m pytest tests/test_integration.py -v

These tests create temporary git repos and invoke scripts as subprocesses.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_REPO_ROOT, "scripts")
_HOOKS = os.path.join(_REPO_ROOT, "hooks")
_INIT_SCRIPT = os.path.join(_SCRIPTS, "dd_init_project.py")
_SWITCH_SCRIPT = os.path.join(_SCRIPTS, "dd_switch_project.py")
_LOG_PROMPT = os.path.join(_HOOKS, "dd_log_prompt.py")
_STOP_HOOK = os.path.join(_HOOKS, "dd_stop_hook.py")


def _make_git_repo():
    """Create a temp dir with a git repo initialized."""
    tmpdir = tempfile.mkdtemp(prefix="dd_integ_")
    subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)
    readme = os.path.join(tmpdir, "README.md")
    with open(readme, "w") as f:
        f.write("# test\n")
    subprocess.run(["git", "add", "README.md"], cwd=tmpdir, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmpdir, capture_output=True)
    return tmpdir


def _run_script(script, args, cwd, stdin_data=None):
    """Run a Python script as a subprocess."""
    cmd = [sys.executable, script] + args
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True,
        input=stdin_data,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )


# ---------------------------------------------------------------------------
# Section 5 — dd_init_project.py Integration
# ---------------------------------------------------------------------------

class TestInitProjectIntegration:

    def setup_method(self):
        self.repo = _make_git_repo()

    def teardown_method(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def test_rejects_duplicate_project_name(self):
        """T-049: Running init twice with the same name should fail."""
        _run_script(_INIT_SCRIPT, ["Test Project"], self.repo)
        r = _run_script(_INIT_SCRIPT, ["Test Project"], self.repo)
        assert r.returncode != 0
        assert "already exists" in r.stderr

    def test_project_root_flag(self):
        """T-050: --project-root directs files to specified directory."""
        subdir = os.path.join(self.repo, "docs")
        os.makedirs(subdir)
        r = _run_script(_INIT_SCRIPT, ["--project-root", subdir, "My Game"], self.repo)
        # Push will fail (no remote) but files should be created
        project_dir = os.path.join(subdir, "MyGame")
        assert os.path.isdir(project_dir)
        assert os.path.isfile(os.path.join(project_dir, "Daydream-MyGame.md"))

    def test_slugifies_project_name(self):
        """T-051: Multi-word names become CamelCase folder names."""
        _run_script(_INIT_SCRIPT, ["RC Boat Racer"], self.repo)
        assert os.path.isdir(os.path.join(self.repo, "RCBoatRacer"))
        assert os.path.isfile(os.path.join(self.repo, "RCBoatRacer", "Daydream-RCBoatRacer.md"))

    def test_state_file_not_committed(self):
        """T-056: dd-current-dictation-project should not be in git."""
        _run_script(_INIT_SCRIPT, ["Test Project"], self.repo)
        r = subprocess.run(
            ["git", "ls-files", "dd-current-dictation-project"],
            cwd=self.repo, capture_output=True, text=True,
        )
        assert r.stdout.strip() == "", "dd-current-dictation-project should not be tracked"

    def test_gitignore_updated(self):
        """T-055: .gitignore should contain dd-current-dictation-project after init."""
        _run_script(_INIT_SCRIPT, ["Test Project"], self.repo)
        gitignore = os.path.join(self.repo, ".gitignore")
        assert os.path.isfile(gitignore)
        with open(gitignore) as f:
            assert "dd-current-dictation-project" in f.read()

    def test_sets_state_file_to_folder_path(self):
        """T-046: State file should contain folder path, not file path."""
        _run_script(_INIT_SCRIPT, ["Test Project"], self.repo)
        state = os.path.join(self.repo, "dd-current-dictation-project")
        with open(state, encoding="utf-8") as f:
            path = f.read().strip()
        assert path.endswith("TestProject")
        assert os.path.isdir(path)

    def test_creates_commit(self):
        """T-044: Project files should be committed to git."""
        _run_script(_INIT_SCRIPT, ["Test Project"], self.repo)
        r = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=self.repo, capture_output=True, text=True,
        )
        assert "Initialize Test Project" in r.stdout

    def test_empty_name_rejected(self):
        """Script should reject empty project names."""
        r = _run_script(_INIT_SCRIPT, [], self.repo)
        assert r.returncode != 0


# ---------------------------------------------------------------------------
# Section 6 — dd_log_prompt.py Integration
# ---------------------------------------------------------------------------

class TestLogPromptIntegration:

    def setup_method(self):
        self.repo = _make_git_repo()

    def teardown_method(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def _set_project(self, folder_path):
        state = os.path.join(self.repo, "dd-current-dictation-project")
        with open(state, "w", encoding="utf-8") as f:
            f.write(folder_path)

    def _make_project(self, slug, name):
        project_dir = os.path.join(self.repo, slug)
        os.makedirs(project_dir, exist_ok=True)
        prompts = os.path.join(project_dir, f"Prompts-{slug}.md")
        with open(prompts, "w", encoding="utf-8") as f:
            f.write(f"# Prompts \u2014 {name}\n\n---\n\n")
        return project_dir

    def _log_prompt(self, text):
        data = json.dumps({"prompt": text})
        return _run_script(_LOG_PROMPT, [], self.repo, stdin_data=data)

    def test_creates_metadiscussion_if_missing(self):
        """T-068: Prompts-ddMetadiscussion created on first fallback prompt."""
        # No state file at all
        r = self._log_prompt("hello world")
        assert r.returncode == 0
        meta = os.path.join(self.repo, "Prompts-ddMetadiscussion")
        assert os.path.isfile(meta)
        with open(meta, encoding="utf-8") as f:
            assert "hello world" in f.read()

    def test_numbering_starts_at_one(self):
        """T-060: First prompt in a fresh file gets number 1."""
        project_dir = self._make_project("TestProj", "Test Proj")
        self._set_project(project_dir)
        self._log_prompt("first prompt")
        prompts = os.path.join(project_dir, "Prompts-TestProj.md")
        with open(prompts, encoding="utf-8") as f:
            content = f.read()
        assert "\n1. first prompt\n" in content

    def test_numbering_continues(self):
        """T-061: Second prompt gets number 2."""
        project_dir = self._make_project("TestProj", "Test Proj")
        self._set_project(project_dir)
        self._log_prompt("first")
        self._log_prompt("second")
        prompts = os.path.join(project_dir, "Prompts-TestProj.md")
        with open(prompts, encoding="utf-8") as f:
            content = f.read()
        assert "\n1. first\n" in content
        assert "\n2. second\n" in content

    def test_preserves_verbatim(self):
        """T-062: Prompt text is stored exactly as received."""
        project_dir = self._make_project("TestProj", "Test Proj")
        self._set_project(project_dir)
        raw = "it has a cement smokestack I mean chimney"
        self._log_prompt(raw)
        prompts = os.path.join(project_dir, "Prompts-TestProj.md")
        with open(prompts, encoding="utf-8") as f:
            assert raw in f.read()

    def test_empty_state_file_falls_back(self):
        """T-063: Empty state file causes fallback to Prompts-ddMetadiscussion."""
        self._set_project("")
        self._log_prompt("should go to meta")
        meta = os.path.join(self.repo, "Prompts-ddMetadiscussion")
        assert os.path.isfile(meta)
        with open(meta, encoding="utf-8") as f:
            assert "should go to meta" in f.read()

    def test_digit_line_doesnt_inflate_count(self):
        """T-071: Lines starting with digits but not matching 'N. ' don't inflate numbering."""
        project_dir = self._make_project("TestProj", "Test Proj")
        self._set_project(project_dir)
        # Write a prompt that contains a line starting with a digit
        self._log_prompt("first prompt")
        # Manually append a line that starts with a digit but isn't a prompt
        prompts = os.path.join(project_dir, "Prompts-TestProj.md")
        with open(prompts, "a", encoding="utf-8") as f:
            f.write("\n42 is the answer to everything\n")
        self._log_prompt("second prompt")
        with open(prompts, encoding="utf-8") as f:
            content = f.read()
        # Should be numbered 2, not 3
        assert "\n2. second prompt\n" in content

    def test_creates_prompts_file_when_missing(self):
        """T-086: Project folder exists but has no Prompts file — hook creates one."""
        project_dir = os.path.join(self.repo, "MyProject")
        os.makedirs(project_dir)
        self._set_project(project_dir)
        self._log_prompt("hello from new project")
        prompts = os.path.join(project_dir, "Prompts-MyProject.md")
        assert os.path.isfile(prompts), "Prompts file should be created in project folder"
        with open(prompts, encoding="utf-8") as f:
            content = f.read()
        assert "hello from new project" in content
        # Should NOT fall back to metadiscussion
        meta = os.path.join(self.repo, "Prompts-ddMetadiscussion")
        assert not os.path.isfile(meta), "Should not fall back to metadiscussion"

    def test_exits_zero_on_write_failure(self):
        """T-067: Hook exits 0 even when it can't write."""
        # Point to a nonexistent directory
        self._set_project("/nonexistent/path/that/does/not/exist")
        r = self._log_prompt("this will fail to write")
        assert r.returncode == 0


# ---------------------------------------------------------------------------
# Section 8 — dd-current-dictation-project State Management
# ---------------------------------------------------------------------------

class TestStateManagement:

    def setup_method(self):
        self.repo = _make_git_repo()

    def teardown_method(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def _set_state(self, content):
        state = os.path.join(self.repo, "dd-current-dictation-project")
        with open(state, "w", encoding="utf-8") as f:
            f.write(content)

    def _log_prompt(self, text):
        data = json.dumps({"prompt": text})
        return _run_script(_LOG_PROMPT, [], self.repo, stdin_data=data)

    def _make_project(self, slug):
        project_dir = os.path.join(self.repo, slug)
        os.makedirs(project_dir, exist_ok=True)
        prompts = os.path.join(project_dir, f"Prompts-{slug}.md")
        with open(prompts, "w", encoding="utf-8") as f:
            f.write(f"# Prompts\n\n")
        return project_dir

    def test_missing_state_file_falls_back(self):
        """T-084: No state file → Prompts-ddMetadiscussion."""
        self._log_prompt("no state file")
        meta = os.path.join(self.repo, "Prompts-ddMetadiscussion")
        assert os.path.isfile(meta)

    def test_trailing_whitespace_handled(self):
        """T-087: Trailing whitespace/newlines in state file are handled."""
        project_dir = self._make_project("TestProj")
        self._set_state(project_dir + "  \n")
        self._log_prompt("should work")
        prompts = os.path.join(project_dir, "Prompts-TestProj.md")
        with open(prompts, encoding="utf-8") as f:
            assert "should work" in f.read()

    def test_state_file_not_tracked(self):
        """T-089: State file should not be in git after init."""
        _run_script(_INIT_SCRIPT, ["Test Project"], self.repo)
        r = subprocess.run(
            ["git", "ls-files", "dd-current-dictation-project"],
            cwd=self.repo, capture_output=True, text=True,
        )
        assert r.stdout.strip() == ""

    def test_empty_state_redirects_to_meta(self):
        """T-091: Empty string in state file → Prompts-ddMetadiscussion."""
        self._set_state("")
        self._log_prompt("empty state")
        meta = os.path.join(self.repo, "Prompts-ddMetadiscussion")
        assert os.path.isfile(meta)
        with open(meta, encoding="utf-8") as f:
            assert "empty state" in f.read()

    def test_switch_script_clear(self):
        """T-090: dd_switch_project.py --clear empties the state file."""
        project_dir = self._make_project("TestProj")
        self._set_state(project_dir)
        r = _run_script(_SWITCH_SCRIPT, ["--clear"], self.repo)
        assert r.returncode == 0
        state = os.path.join(self.repo, "dd-current-dictation-project")
        with open(state, encoding="utf-8") as f:
            assert f.read().strip() == ""

    def test_stale_state_falls_back(self):
        """T-085: State file pointing to nonexistent folder → Prompts-ddMetadiscussion."""
        self._set_state("/nonexistent/folder/that/does/not/exist")
        self._log_prompt("stale state")
        meta = os.path.join(self.repo, "Prompts-ddMetadiscussion")
        assert os.path.isfile(meta)
        with open(meta, encoding="utf-8") as f:
            assert "stale state" in f.read()


# ---------------------------------------------------------------------------
# Section 7 — dd_stop_hook.py Integration
# ---------------------------------------------------------------------------

def _make_git_repo_with_remote():
    """Create a temp git repo with a local bare remote for push testing."""
    base = tempfile.mkdtemp(prefix="dd_stop_")
    bare = os.path.join(base, "remote.git")
    work = os.path.join(base, "work")
    subprocess.run(["git", "init", "--bare", bare], capture_output=True)
    subprocess.run(["git", "clone", bare, work], capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=work, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=work, capture_output=True)
    readme = os.path.join(work, "README.md")
    with open(readme, "w") as f:
        f.write("# test\n")
    subprocess.run(["git", "add", "README.md"], cwd=work, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=work, capture_output=True)
    subprocess.run(["git", "push"], cwd=work, capture_output=True)
    return base, work


class TestStopHookIntegration:

    def setup_method(self):
        self.base, self.repo = _make_git_repo_with_remote()

    def teardown_method(self):
        shutil.rmtree(self.base, ignore_errors=True)

    def _run_stop_hook(self, stdin_data=None):
        if stdin_data is None:
            stdin_data = "{}"
        return _run_script(_STOP_HOOK, [], self.repo, stdin_data=stdin_data)

    def test_clean_repo_exits_zero(self):
        """Clean repo with everything committed and pushed exits 0."""
        r = self._run_stop_hook()
        assert r.returncode == 0

    def test_uncommitted_changes_exit_two(self):
        """Modified tracked file without committing exits 2."""
        readme = os.path.join(self.repo, "README.md")
        with open(readme, "a") as f:
            f.write("dirty\n")
        r = self._run_stop_hook()
        assert r.returncode == 2
        assert "uncommitted" in r.stderr.lower()

    def test_staged_changes_exit_two(self):
        """Staged but uncommitted changes exit 2."""
        readme = os.path.join(self.repo, "README.md")
        with open(readme, "a") as f:
            f.write("staged\n")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo, capture_output=True)
        r = self._run_stop_hook()
        assert r.returncode == 2
        assert "uncommitted" in r.stderr.lower()

    def test_untracked_files_exit_two(self):
        """Untracked file in repo exits 2."""
        newfile = os.path.join(self.repo, "newfile.txt")
        with open(newfile, "w") as f:
            f.write("untracked\n")
        r = self._run_stop_hook()
        assert r.returncode == 2
        assert "untracked" in r.stderr.lower()

    def test_unpushed_commits_exit_two(self):
        """Committed but unpushed changes exit 2."""
        readme = os.path.join(self.repo, "README.md")
        with open(readme, "a") as f:
            f.write("new content\n")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "local only"], cwd=self.repo, capture_output=True)
        r = self._run_stop_hook()
        assert r.returncode == 2
        assert "unpushed" in r.stderr.lower()

    def test_recursion_guard_exits_zero(self):
        """stop_hook_active=true bypasses all checks, even with dirty state."""
        readme = os.path.join(self.repo, "README.md")
        with open(readme, "a") as f:
            f.write("dirty but guarded\n")
        stdin = json.dumps({"stop_hook_active": True})
        r = self._run_stop_hook(stdin_data=stdin)
        assert r.returncode == 0

    def test_no_vcs_exits_zero(self):
        """Directory with no VCS exits 0."""
        plain_dir = tempfile.mkdtemp(prefix="dd_novcs_")
        try:
            r = _run_script(_STOP_HOOK, [], plain_dir, stdin_data="{}")
            assert r.returncode == 0
        finally:
            shutil.rmtree(plain_dir, ignore_errors=True)
