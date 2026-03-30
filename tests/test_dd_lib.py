"""
tests/test_dd_lib.py — Automated unit tests for dd_lib.py

Run with:
    cd <plugin-root>
    python3 -m pytest tests/test_dd_lib.py -v

Notes:
    - Tests that exercise checkpoint_* functions (which run real VCS commands) are
      integration-level and are NOT included here. See TestPlan-DaydreamDictationSkill.md.
"""

import importlib.util
import os
import sys
import tempfile
import shutil

import pytest


# ---------------------------------------------------------------------------
# Load dd_lib.py via importlib (direct path load instead of bare import)
# ---------------------------------------------------------------------------

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DD_LIB_PATH = os.path.join(_REPO_ROOT, "scripts", "dd_lib.py")


def _load_dd_lib():
    spec = importlib.util.spec_from_file_location("dd_lib", _DD_LIB_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dd_lib = _load_dd_lib()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_temp_dir():
    """Create a temporary directory; caller is responsible for cleanup."""
    return tempfile.mkdtemp(prefix="dd_test_")


# ---------------------------------------------------------------------------
# T-006 through T-013: slugify
# ---------------------------------------------------------------------------

class TestSlugify:

    def test_single_word(self):
        # T-006
        assert dd_lib.slugify("Campfire") == "Campfire"

    def test_multi_word(self):
        # T-007 — preserves internal casing (RC stays RC)
        assert dd_lib.slugify("RC Boat Racer") == "RCBoatRacer"

    def test_all_lowercase(self):
        # T-008
        assert dd_lib.slugify("my cool game") == "MyCoolGame"

    def test_already_camel_cased(self):
        # T-009 — already-camelcased input preserved
        assert dd_lib.slugify("MyGame") == "MyGame"

    def test_extra_spaces_between_words(self):
        # T-010 — split() (no args) handles multiple spaces
        assert dd_lib.slugify("Old  Friend") == "OldFriend"

    def test_numbers_in_name(self):
        # T-013
        assert dd_lib.slugify("Zone 51") == "Zone51"

    def test_single_character_words(self):
        # T-012
        assert dd_lib.slugify("A B C") == "ABC"

    def test_two_words(self):
        assert dd_lib.slugify("Jump Brothers") == "JumpBrothers"

    def test_all_caps_preserved(self):
        # Fix: internal casing is preserved, only first char uppercased
        # "HELLO WORLD" → "HELLOWORLD"
        assert dd_lib.slugify("HELLO WORLD") == "HELLOWORLD"

    def test_empty_string_returns_empty(self):
        # Edge case: empty string → empty slug (no crash)
        assert dd_lib.slugify("") == ""


# ---------------------------------------------------------------------------
# T-014 through T-028: detect_vcs
# ---------------------------------------------------------------------------

class TestDetectVcs:

    def setup_method(self):
        self.tmpdir = make_temp_dir()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        # Clean up P4CONFIG env var if set by a test
        os.environ.pop("P4CONFIG", None)

    def _write_override(self, content):
        claude_dir = os.path.join(self.tmpdir, ".claude")
        os.makedirs(claude_dir, exist_ok=True)
        with open(os.path.join(claude_dir, "dd-vcs"), "w") as f:
            f.write(content)

    # --- Auto-detection ---

    def test_git_dir_detected(self):
        # T-014
        os.makedirs(os.path.join(self.tmpdir, ".git"))
        assert dd_lib.detect_vcs(self.tmpdir) == "git"

    def test_hg_dir_detected(self):
        # T-015
        os.makedirs(os.path.join(self.tmpdir, ".hg"))
        assert dd_lib.detect_vcs(self.tmpdir) == "hg"

    def test_plastic_dir_detected(self):
        # T-016
        os.makedirs(os.path.join(self.tmpdir, ".plastic"))
        assert dd_lib.detect_vcs(self.tmpdir) == "unity-vcs"

    def test_p4config_file_detected(self):
        # T-017
        open(os.path.join(self.tmpdir, ".p4config"), "w").close()
        assert dd_lib.detect_vcs(self.tmpdir) == "perforce"

    def test_p4config_env_var_detected(self):
        # T-018
        os.environ["P4CONFIG"] = "p4config"
        assert dd_lib.detect_vcs(self.tmpdir) == "perforce"

    def test_no_vcs_returns_none(self):
        # T-019 — empty dir with no VCS markers, no env var
        os.environ.pop("P4CONFIG", None)
        assert dd_lib.detect_vcs(self.tmpdir) is None

    def test_git_wins_over_hg_when_both_present(self):
        # T-028 — git is checked before hg in auto-detect
        os.makedirs(os.path.join(self.tmpdir, ".git"))
        os.makedirs(os.path.join(self.tmpdir, ".hg"))
        assert dd_lib.detect_vcs(self.tmpdir) == "git"

    # --- dd-vcs override ---

    def test_override_git(self):
        # T-020 — override wins over any auto-detected VCS
        os.makedirs(os.path.join(self.tmpdir, ".hg"))
        self._write_override("git")
        assert dd_lib.detect_vcs(self.tmpdir) == "git"

    def test_override_hg(self):
        # T-021
        self._write_override("hg")
        assert dd_lib.detect_vcs(self.tmpdir) == "hg"

    def test_override_alias_mercurial(self):
        # T-022
        self._write_override("mercurial")
        assert dd_lib.detect_vcs(self.tmpdir) == "hg"

    def test_override_alias_p4(self):
        # T-023
        self._write_override("p4")
        assert dd_lib.detect_vcs(self.tmpdir) == "perforce"

    def test_override_alias_plastic(self):
        # T-024
        self._write_override("plastic")
        assert dd_lib.detect_vcs(self.tmpdir) == "unity-vcs"

    def test_override_custom_returns_none(self):
        # T-025
        self._write_override("custom")
        assert dd_lib.detect_vcs(self.tmpdir) is None

    def test_override_none_returns_none(self):
        # T-026
        self._write_override("none")
        assert dd_lib.detect_vcs(self.tmpdir) is None

    def test_override_empty_returns_none(self):
        self._write_override("")
        assert dd_lib.detect_vcs(self.tmpdir) is None

    def test_override_unknown_falls_through_to_autodetect(self):
        # T-027 — unknown value like "svn" falls through; .git is present so git returned
        os.makedirs(os.path.join(self.tmpdir, ".git"))
        self._write_override("svn")
        assert dd_lib.detect_vcs(self.tmpdir) == "git"

    def test_override_unknown_no_autodetect_returns_none(self):
        # T-027 variant — unknown override + no VCS markers → None
        self._write_override("svn")
        assert dd_lib.detect_vcs(self.tmpdir) is None

    def test_override_case_insensitive(self):
        # Override file value is .lower()ed before processing
        self._write_override("GIT")
        assert dd_lib.detect_vcs(self.tmpdir) == "git"

    def test_override_with_trailing_whitespace(self):
        # Trailing whitespace in override file stripped before comparison
        self._write_override("  git  ")
        assert dd_lib.detect_vcs(self.tmpdir) == "git"


# ---------------------------------------------------------------------------
# T-029 through T-036: resolve_project_root
# ---------------------------------------------------------------------------

class TestResolveProjectRoot:

    def setup_method(self):
        self.repo = make_temp_dir()
        self.claude_dir = os.path.join(self.repo, ".claude")
        os.makedirs(self.claude_dir)

    def teardown_method(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def _write_config(self, content):
        with open(os.path.join(self.claude_dir, "dd-projects-root"), "w") as f:
            f.write(content)

    # T-029
    def test_no_override_no_config_returns_repo_root(self):
        result = dd_lib.resolve_project_root(self.repo, None)
        assert result == self.repo

    # T-030
    def test_cli_override_with_valid_path(self):
        override = make_temp_dir()
        try:
            result = dd_lib.resolve_project_root(self.repo, override)
            assert result == os.path.abspath(override)
        finally:
            shutil.rmtree(override, ignore_errors=True)

    # T-031
    def test_cli_override_nonexistent_path_exits(self):
        with pytest.raises(SystemExit):
            dd_lib.resolve_project_root(self.repo, "/tmp/nonexistent_dd_xyz_abc")

    # T-032
    def test_config_file_with_valid_path(self):
        target = make_temp_dir()
        try:
            self._write_config(target)
            result = dd_lib.resolve_project_root(self.repo, None)
            assert result == target
        finally:
            shutil.rmtree(target, ignore_errors=True)

    # T-033
    def test_config_file_with_nonexistent_path_exits(self):
        self._write_config("/tmp/nonexistent_dd_xyz_abc")
        with pytest.raises(SystemExit):
            dd_lib.resolve_project_root(self.repo, None)

    # T-034
    def test_config_file_empty_falls_back_to_repo_root(self):
        self._write_config("")
        result = dd_lib.resolve_project_root(self.repo, None)
        assert result == self.repo

    # T-035
    def test_cli_override_takes_precedence_over_config(self):
        config_target = make_temp_dir()
        cli_target = make_temp_dir()
        try:
            self._write_config(config_target)
            result = dd_lib.resolve_project_root(self.repo, cli_target)
            assert result == os.path.abspath(cli_target)
        finally:
            shutil.rmtree(config_target, ignore_errors=True)
            shutil.rmtree(cli_target, ignore_errors=True)

    # T-036
    def test_config_file_with_trailing_newline(self):
        target = make_temp_dir()
        try:
            self._write_config(target + "\n")
            result = dd_lib.resolve_project_root(self.repo, None)
            assert result == target
        finally:
            shutil.rmtree(target, ignore_errors=True)


# ---------------------------------------------------------------------------
# write_file
# ---------------------------------------------------------------------------

class TestWriteFile:

    def setup_method(self):
        self.tmpdir = make_temp_dir()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_creates_file_with_content(self):
        path = os.path.join(self.tmpdir, "test.md")
        dd_lib.write_file(path, "# Hello\n")
        assert os.path.isfile(path)
        with open(path) as f:
            assert f.read() == "# Hello\n"

    def test_overwrites_existing_file(self):
        path = os.path.join(self.tmpdir, "test.md")
        dd_lib.write_file(path, "first content")
        dd_lib.write_file(path, "second content")
        with open(path) as f:
            assert f.read() == "second content"

    def test_creates_file_in_existing_directory(self):
        subdir = os.path.join(self.tmpdir, "subdir")
        os.makedirs(subdir)
        path = os.path.join(subdir, "doc.md")
        dd_lib.write_file(path, "content")
        assert os.path.isfile(path)


# ---------------------------------------------------------------------------
# checkpoint dispatch (no actual VCS calls — just verify dispatcher works)
# ---------------------------------------------------------------------------

class TestCheckpointDispatch:
    """
    Verify that checkpoint() dispatches to the right function and that
    vcs=None is a safe no-op. We don't run actual git/hg commands here —
    those are integration tests in the test plan.
    """

    def test_none_vcs_is_noop(self, capsys):
        # Should print a skip message and return without error
        dd_lib.checkpoint([], "test commit", "/tmp", None)
        out = capsys.readouterr().out
        assert "skipping" in out.lower()

    def test_unknown_vcs_raises_key_error(self):
        # dispatch dict doesn't have "svn" — should raise KeyError
        with pytest.raises(KeyError):
            dd_lib.checkpoint([], "test", "/tmp", "svn")
