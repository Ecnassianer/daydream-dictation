#!/bin/sh
# Run a Python script with whichever Python 3 command this machine has
# (docs/decisions/0011).
#
#   sh dd_python.sh script.py [args...]
#
# macOS and most Linux distros provide `python3`, and often no `python`. The
# python.org installer on Windows provides `python` and the `py` launcher, and
# `python3` is often a Microsoft Store stub that only prints an install hint.
# So try each command in turn and use the first one that really runs Python 3.
# Hook commands run under `sh -c` on macOS and Linux and under Git Bash on
# Windows, so this script is plain POSIX sh.

for dd_python in python3 python "py -3"; do
    # $dd_python is unquoted on purpose, so "py -3" splits into two words.
    # The probe reads /dev/null so it can't consume the hook's stdin.
    if $dd_python -c 'import sys; sys.exit(sys.version_info[0] != 3)' \
            </dev/null >/dev/null 2>&1; then
        exec $dd_python "$@"
    fi
done

echo "daydream-dictation: no Python 3 found (tried python3, python and py -3)." \
     "Install Python 3.9 or later and make sure it is on PATH." >&2
exit 1
