---
status: accepted
date: 2026-10-31
decision-makers: Ecnassianer
---

# Find Python with a launcher script instead of calling python3 directly

## Context and Problem Statement

Every hook command and every script command in the skill called `python3`. That name was picked when the plugin was first scaffolded, without a recorded decision. It is the safe choice on macOS and Linux: macOS ships no `python` at all, many Linux distros provide only `python3`, and on older systems `python` may still be Python 2 ([PEP 394](https://peps.python.org/pep-0394/) recommends `python3` for that reason).

Windows is the opposite. The python.org installer provides `python` and the `py` launcher, not `python3`, and `python3` is often a Microsoft Store alias that prints an install hint and exits. On Windows, prompt logging and the Stop hook failed without any visible error, and the skill's script commands failed when the agent ran them as written ([#57](https://github.com/Ecnassianer/daydream-dictation/issues/57)). How do we run Python on every platform from one set of hook commands?

## Decision Drivers

* One hook definition that works on macOS, Linux and Windows. Skill frontmatter hooks have no per-platform variants.
* No change on machines where `python3` already works.
* The hooks read JSON on stdin, and the Stop hook blocks with exit code 2, so the interpreter must get the same stdin and its exit code must come back unchanged.
* The skill must stay self-contained ([ADR-0010](0010-make-the-dictation-skill-self-contained.md)).

## Considered Options

* Keep `python3`, and document that Windows users must provide a `python3` command
* Chain commands in the hook: `python3 … || python … || py -3 …`
* A POSIX sh launcher, `hooks/dd_python.sh`, that tries `python3`, `python` and `py -3` and runs the first one that is really Python 3
* Separate hook commands for Windows, using the `shell: powershell` hook field

## Decision Outcome

Chosen option: **a POSIX sh launcher**, because it is the only option that works on every platform from one command and keeps the hooks' stdin and exit codes intact.

* Hook commands become `sh "${CLAUDE_PLUGIN_ROOT}/hooks/dd_python.sh" "${CLAUDE_PLUGIN_ROOT}/hooks/<hook>.py"`. Claude Code runs hook commands with `sh -c` on macOS and Linux and with Git Bash on Windows, so `sh` is always there.
* The launcher checks each candidate with a tiny `-c` probe that must exit 0 on Python 3, which skips the Store stub. The probe reads `/dev/null`, so it doesn't consume the hook's stdin. Then it `exec`s the chosen command, so stdin and the exit code pass straight through.
* If no candidate works, it prints `no Python 3 found` to stderr and exits 1, instead of failing silently.
* The scripts the agent runs (`dd_switch_project.py`, `dd_init_project.py`) are run by the agent, not by a hook. A *Python command* note in `SKILL.md` tells the agent to retry with `python`, then `py -3`, when `python3` is missing or isn't Python 3. That keeps the skill free of a dependency on the plugin's `hooks/` folder.

### Consequences

* Good, because the hooks work on a stock python.org Windows install, and a machine with no Python now gets a clear error.
* Good, because nothing changes where `python3` works: it is tried first.
* Bad, because each hook now starts Python twice: once for the probe and once for the hook. That adds tens of milliseconds, well inside the hooks' timeouts.
* Bad, because on Windows without Git Bash, Claude Code runs hooks in PowerShell, which has no `sh`. Claude Code's own docs recommend Git Bash on Windows, so we accept this; a user without it can install Git for Windows.
* Neutral, because on Windows the agent may spend one failed command finding the right Python name for the scripts.

### Confirmation

`tests/test_python_launcher.py` runs the launcher against fake bin folders: `python3` preferred when present, a Store-style `python3` stub skipped in favour of `python`, `py -3` used when it is the only option, args, stdin and exit code 2 passed through, and a clear error when no Python 3 is found.

## Pros and Cons of the Options

### Keep `python3` and document it

* Good, because nothing changes.
* Bad, because it fails on a default Windows install, without an error, which is the bug.

### Chain commands with `||`

* Good, because it needs no extra file.
* Bad, because `||` also fires when the hook itself exits non-zero. A Stop hook that blocks with exit code 2 would run again under the next interpreter, with its stdin already used up.
* Bad, because a Store stub on PATH fails with its own exit code, indistinguishable from a hook failure.

### Separate Windows hook commands

* Good, because each platform gets a native command.
* Bad, because skill frontmatter hooks and `hooks.json` have no per-platform condition, so both commands would run everywhere.
