---
status: proposed
date: 2026-10-31
decision-makers: Ecnassianer
---

# Make the daydream-dictation skill self-contained, with skill-relative script paths

## Context and Problem Statement

The `daydream-dictation` skill tells the agent to run the plugin's scripts through Claude Code-only variables: `${CLAUDE_PLUGIN_ROOT}/scripts/…` in some places and `${CLAUDE_SKILL_DIR}/../../scripts/…` in others. It also points to its example file as `${CLAUDE_SKILL_DIR}/example-voice-variants.md`. Only Claude Code fills these in. Codex sets `CLAUDE_PLUGIN_ROOT` only while running hooks, and every other agent sees the literal text. The scripts also sit at the plugin root, outside the skill folder, so a user who installs just the skill (for example by copying it into `.agents/skills/`) gets a skill whose scripts are missing ([#52](https://github.com/Ecnassianer/daydream-dictation/issues/52), item A2).

The [Agent Skills spec](https://agentskills.io/specification) expects a skill's scripts in its own `scripts/` folder and its reference files in `references/`, referred to by paths relative to the skill folder. Clients resolve those against the folder holding `SKILL.md`. How do we adopt that without changing anything a Claude Code user sees?

## Decision Drivers

* No visible change in Claude Code: same commands, same output, no extra failed attempts or permission prompts.
* The skill should work in any agent that follows the spec, including a skill-only install.
* Hooks must keep working; Claude Code and Codex find them through the plugin's `hooks/hooks.json`.

## Considered Options

* Keep the scripts at the plugin root and the Claude Code variables in the skill text
* Move the scripts into the skill folder and keep `${CLAUDE_SKILL_DIR}` in the skill text
* Move the scripts into the skill folder and use skill-relative paths, with one line telling the agent to run them by absolute path

## Decision Outcome

Chosen option: **move the scripts into the skill folder and use skill-relative paths**, because it is the only option that works outside Claude Code. Real Claude Code sessions showed no visible change (see *Confirmation*).

* `scripts/` moves to `skills/daydream-dictation/scripts/`, and `example-voice-variants.md` moves to `skills/daydream-dictation/references/`.
* The skill text says `python3 scripts/dd_switch_project.py "Slug"` and the like. A new *Script paths* note near the top tells the agent that these paths are relative to the skill's folder (the base directory it was given when the skill loaded), and to run scripts by absolute path because commands run from the repo root. Claude Code gives that base directory at the top of the loaded skill, and the spec's client guide tells other clients to do the same.
* Hooks stay at the plugin root (`hooks/`). They import the shared libraries from `skills/daydream-dictation/scripts/`. The hook commands in the skill frontmatter and `hooks/hooks.json` still use `${CLAUDE_PLUGIN_ROOT}/hooks/…`, which Claude Code and Codex both provide.
* `dd-gap-analysis` and `dd-teach` run no scripts, so they don't change.

### Consequences

* Good, because the skill no longer depends on Claude Code variables in its text, and a skill-only install brings its scripts along.
* Good, because the plugin layout follows the spec's `scripts/` and `references/` conventions.
* Bad, because the agent now builds each script's absolute path itself, instead of Claude Code substituting it. A model that ran a bare `scripts/…` path from the repo root would fail once and retry; the *Script paths* note is there to prevent that.
* Neutral, because the hooks reach into the skill folder for their libraries. That ties `hooks/` to the skill's layout, which is fine while they ship together.

### Confirmation

* Unit and integration tests import the scripts from their new location.
* Real Claude Code sessions (v2.1.316, 2026-10-31) ran the same scenario five times against the plugin before this change and five times after it. Each run had seven prompts, one per turn: start a new project, dictate, start a second project, dictate, switch back with a voice-variant word, then resume the session, dictate, and clear the project. Results:
  * Every script call in the "after" runs used the new absolute path (`…/skills/daydream-dictation/scripts/…`) on the first try. No call failed because of a path.
  * All seven prompts were logged exactly once in all ten runs. The session-start and resume notes appeared in every run.
  * Every run ended with a clean working tree, everything pushed and no active project. The resume hook and the post-resume backfill worked in all ten.
  * Differences between runs were the model's own choices and appeared on both sides: whether to put each project on its own branch (1 of 5 before, 3 of 5 after, explained each time by the skill's pull-request workflow, which this change doesn't touch), and which Prompts doc gets the "switch back" prompt.

## More Information

* [#52](https://github.com/Ecnassianer/daydream-dictation/issues/52), item A2.
* [Agent Skills spec: file references](https://agentskills.io/specification#file-references) and [client guide](https://agentskills.io/client-implementation/adding-skills-support).
