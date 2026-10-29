---
status: proposed
date: 2026-10-29
decision-makers: Ecnassianer
---

# Stop logging prompts outside a dictation session

## Context and Problem Statement

When no project is set in `dd-current-dictation-project`, `dd_log_prompt.py` falls back to logging every prompt to `Prompts-ddMetadiscussion` at the repo root. The fallback was meant to capture the few prompts a user says before `/daydream-dictation` sets the project. In practice it captures everything: skill development, debugging and unrelated work in any repo where the plugin is enabled. The untracked file then triggers the Stop hook's commit check ([#40](https://github.com/Ecnassianer/daydream-dictation/issues/40), [#42](https://github.com/Ecnassianer/daydream-dictation/issues/42)).

What should happen to prompts that aren't part of a dictation session?

## Decision Drivers

* Unrelated work should leave no trace in the working tree.
* The maintainer has said losing the session-opening prompt ("let's start a Daydream Dictation session") is acceptable.

## Considered Options

* Keep the fallback (status quo)
* Keep the fallback but `.gitignore` `Prompts-ddMetadiscussion`
* Remove the fallback: log only to an active project's Prompts doc, otherwise log nothing

## Decision Outcome

Chosen option: **remove the fallback**. The skill's hooks log only while the skill is active ([ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md)) and only to the Prompts doc of the project in `dd-current-dictation-project`. With no active project, nothing is logged.

* `dd_switch_project.py --clear` now means "stop logging" instead of "log to `Prompts-ddMetadiscussion`".
* The skill, README and switch-script messages stop mentioning `Prompts-ddMetadiscussion`, including the `dd-` naming-prefix exception for it.
* Existing `Prompts-ddMetadiscussion` files in user repos are left alone. The plugin doesn't delete user files.

### Consequences

* Good, because unrelated prompts are never written anywhere.
* Good, because one less special file to explain.
* Bad, because the prompts a user says before the project is set aren't logged. The skill can re-derive what matters from context. A user who cares can backfill by hand.

## Pros and Cons of the Options

### Keep the fallback

* Good, because nothing is ever lost.
* Bad, because it logs unrelated work and clutters every repo.

### Keep the fallback, gitignore the file

* Good, because it stops the commit-check nagging and keeps an audit trail.
* Bad, because every unrelated prompt is still captured and kept on disk, which the user doesn't want.
* Bad, because the plugin would need to edit each repo's `.gitignore`.

### Remove the fallback

* Good, because it matches the original intent: Prompts docs belong to dictation projects.
* Bad, because session-opening prompts are lost (accepted above).

## More Information

* Related: [ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md) (when the hooks run at all).
* A review of what has accumulated in existing `Prompts-ddMetadiscussion` files is being done separately, to check whether anything valuable was only captured there.
