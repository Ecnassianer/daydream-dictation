---
status: accepted
date: 2026-10-31
decision-makers: Ecnassianer
---

# Move Daydream Dictation's config and state out of the .claude folder

## Context and Problem Statement

Daydream Dictation keeps three repo-level config files in Claude Code's `.claude/` folder: `dd-vcs`, `dd-projects-root` and `dd-voice-variants.md`. It keeps per-session hook state in `~/.claude/daydream-dictation/sessions/` (or under `CLAUDE_CONFIG_DIR`). We want the plugin to work with more agents than Claude Code ([#52](https://github.com/Ecnassianer/daydream-dictation/issues/52), item A3). Asking a Codex or Gemini CLI user to create a `.claude/` folder to configure us is odd, and the voice variants are useful to any agent. Where should these files live?

Claude Code never reads any of them itself. Our scripts read `dd-vcs` and `dd-projects-root` (`scripts/dd_lib.py`); the agent reads `dd-voice-variants.md` because the skill tells it to; and the hooks read and write the session state. So the location is ours to choose.

## Decision Drivers

* Not tied to one agent's folder layout.
* Existing repos and sessions keep working with no action from the user.
* One obvious place for a user to look.

## Considered Options

* Keep `.claude/`
* `.agents/` at the repo root, falling back to `.claude/`
* A dedicated `.daydream-dictation/` folder

For session state:

* Keep `~/.claude/daydream-dictation/sessions/`
* `$XDG_STATE_HOME/daydream-dictation/sessions/` (default `~/.local/state/…`), carrying over legacy files

## Decision Outcome

Chosen options: **`.agents/` with a `.claude/` fallback** for config, and **`$XDG_STATE_HOME`** for state.

* **Config.** `dd_lib.find_config_file()` looks in `.agents/` first, then `.claude/`. When a file exists in both, the `.agents/` copy wins. `.agents/` is the folder other agents already use for `.agents/skills/`, so it is where a multi-agent repo already keeps agent configuration. The `dd-` prefix keeps our files apart from anything else there.
* **State.** `state_dir()` is `DD_STATE_DIR` if set, else `$XDG_STATE_HOME/daydream-dictation/sessions/`, else `~/.local/state/daydream-dictation/sessions/`. If a session's state file is missing from the new folder but exists in the legacy one, `session_state()` reads it and deletes the legacy copy. That way a session that started before an upgrade keeps its markers, and its prompts aren't backfilled twice. `cleanup_stale_state()` cleans both folders.
* The skill, README and example file now name `.agents/`, and mention `.claude/` as the legacy location.

### Consequences

* Good, because any agent's users can configure Daydream Dictation without a `.claude/` folder.
* Good, because existing repos keep working: the `.claude/` files are still read.
* Good, because sessions in flight during an upgrade keep their state.
* Bad, because there are two possible locations for each file until the fallback is removed. The `.agents/` copy wins, which could surprise someone editing a stale `.claude/` copy.
* Neutral, because `.agents/` is only an established convention as the parent of `.agents/skills/`; nothing else standardizes its contents. Claude Code ignores `.agents/` entirely, which is fine because it never reads these files.
* Neutral, because Claude Code's own settings, such as the README's permission rule that lets Claude start the skill, stay in `.claude/`. They belong to Claude Code, not to us.

### Confirmation

* `tests/test_dd_lib.py` covers `.agents/`, the legacy fallback, and precedence when both exist.
* `tests/test_prompt_log.py` (`TestStateDir`) covers the new default, `DD_STATE_DIR`, carrying legacy state over, and cleanup of both folders.
* Around October 2027, together with the `CLAUDE.md` pointer from [ADR-0008](0008-use-agents-md-for-per-project-instructions.md), write an ADR that drops the `.claude/` fallbacks.

## Pros and Cons of the Options

### Keep `.claude/`

* Good, because nothing changes.
* Bad, because it ties configuration to Claude Code's folder layout.

### A dedicated `.daydream-dictation/` folder

* Good, because there's no chance of clashing with anything else.
* Bad, because it adds yet another dot-folder to the user's repo, when `.agents/` is already the shared place for agent configuration.

## More Information

* [#52](https://github.com/Ecnassianer/daydream-dictation/issues/52), item A3.
* [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/latest/) for `XDG_STATE_HOME`.
