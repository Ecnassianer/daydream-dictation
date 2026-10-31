"""
tests/test_python_launcher.py — Tests for hooks/dd_python.sh, which picks
python3, python or py -3 for the hook commands (docs/decisions/0011).

Run with:
    cd <plugin-root>
    python3 -m pytest tests/test_python_launcher.py -v

Each test builds a fake bin folder and runs the launcher with PATH set to
only that folder, to imitate machines with different Python commands.
"""

import os
import shutil
import subprocess
import sys
import tempfile

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LAUNCHER = os.path.join(_REPO_ROOT, "hooks", "dd_python.sh")
_SH = shutil.which("sh")

pytestmark = pytest.mark.skipif(
    _SH is None or sys.platform == "win32",
    reason="needs a POSIX sh and executable shell-script stubs",
)

# Prints which command ran, echoes its args and stdin, and exits with the
# code given in argv[1].
_PROBE_SCRIPT = """\
import sys
print("argv=" + " ".join(sys.argv[2:]))
print("stdin=" + sys.stdin.read())
sys.exit(int(sys.argv[1]))
"""


def _write_exe(folder, name, body):
    path = os.path.join(folder, name)
    with open(path, "w") as f:
        f.write("#!/bin/sh\n" + body)
    os.chmod(path, 0o755)


def _real_python(folder, name, required_first_arg=None):
    """A command that runs the real Python, tagging its output with `name`."""
    if required_first_arg:
        # Like `py`: insist on the version flag, then drop it.
        body = (
            f'[ "$1" = "{required_first_arg}" ] || exit 7\n'
            "shift\n"
        )
    else:
        body = ""
    body += f'echo "ran={name}"\nexec "{sys.executable}" "$@"\n'
    _write_exe(folder, name, body)


def _store_stub(folder, name):
    """Imitates the Windows Store alias: prints a hint and fails."""
    _write_exe(folder, name, 'echo "Python was not found; run without arguments to install from the Microsoft Store" >&2\nexit 9009\n')


@pytest.fixture
def env():
    folder = tempfile.mkdtemp(prefix="dd_launcher_")
    script = os.path.join(folder, "probe.py")
    with open(script, "w") as f:
        f.write(_PROBE_SCRIPT)
    yield folder, script
    shutil.rmtree(folder, ignore_errors=True)


def _run(folder, script, exit_code=0, stdin="{}"):
    return subprocess.run(
        [_SH, _LAUNCHER, script, str(exit_code), "a b", "c"],
        input=stdin, capture_output=True, text=True,
        env={"PATH": folder},
    )


def test_prefers_python3(env):
    folder, script = env
    _real_python(folder, "python3")
    _real_python(folder, "python")
    r = _run(folder, script)
    assert r.returncode == 0, r.stderr
    assert r.stdout.startswith("ran=python3\n")


def test_skips_store_stub_and_uses_python(env):
    folder, script = env
    _store_stub(folder, "python3")
    _real_python(folder, "python")
    r = _run(folder, script)
    assert r.returncode == 0, r.stderr
    assert r.stdout.startswith("ran=python\n")


def test_falls_back_to_py_dash_3(env):
    folder, script = env
    _real_python(folder, "py", required_first_arg="-3")
    r = _run(folder, script)
    assert r.returncode == 0, r.stderr
    assert r.stdout.startswith("ran=py\n")


def test_passes_args_stdin_and_exit_code_through(env):
    folder, script = env
    _real_python(folder, "python3")
    # Exit code 2 is how the Stop hook blocks, so it must survive the launcher.
    r = _run(folder, script, exit_code=2, stdin='{"prompt": "hello"}')
    assert r.returncode == 2
    assert "argv=a b c\n" in r.stdout
    assert 'stdin={"prompt": "hello"}' in r.stdout


def test_reports_missing_python(env):
    folder, script = env
    _store_stub(folder, "python3")
    r = _run(folder, script)
    assert r.returncode == 1
    assert "no Python 3 found" in r.stderr
