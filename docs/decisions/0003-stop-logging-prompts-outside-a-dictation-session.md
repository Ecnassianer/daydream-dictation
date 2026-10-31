---
status: accepted
date: 2026-10-31
decision-makers: Ecnassianer
---

# Stop logging prompts outside a dictation session

## Context and Problem Statement

When no project is set in `dd-current-dictation-project`, `dd_log_prompt.py` falls back to logging every prompt to `Prompts-ddMetadiscussion` at the repo root. The fallback was meant to capture the few prompts a user says before `/daydream-dictation` sets the project. In practice it captures everything: skill development, debugging and unrelated work in any repo where the plugin is enabled. The untracked file then triggers the Stop hook's commit check ([#40](https://github.com/Ecnassianer/daydream-dictation/issues/40), [#42](https://github.com/Ecnassianer/daydream-dictation/issues/42)).

What should happen to prompts that aren't part of a dictation session?

## Decision Drivers

* Unrelated work should leave no trace in the working tree.
* The prompt that starts a session often carries real content ("start a daydream dictation about a game that has…"). It belongs in that project's Prompts doc, not in a separate meta log. A review of existing `Prompts-ddMetadiscussion` files found almost nothing else worth keeping there.

## Considered Options

* Keep the fallback (status quo)
* Keep the fallback but `.gitignore` `Prompts-ddMetadiscussion`
* Remove the fallback: log only to an active project's Prompts doc, otherwise log nothing

## Decision Outcome

Chosen option: **remove the fallback**. The skill's hooks log only while the skill is active ([ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md)) and only to the Prompts doc of the project in `dd-current-dictation-project`. With no active project, nothing is logged.

The prompt that started the session is not lost. It is logged into the project's Prompts doc, with a session-start note, as soon as a project is set ([ADR-0005](0005-recover-prompts-after-a-resumed-session.md)). So are any prompts sent between invoking the skill and choosing the project, such as the answer to "which project?". Prompts sent in the session *before* the skill was invoked stay unlogged.

* `dd_switch_project.py --clear` now means "stop logging" instead of "log to `Prompts-ddMetadiscussion`".
* The skill, README and switch-script messages stop mentioning `Prompts-ddMetadiscussion`, including the `dd-` naming-prefix exception for it.
* Existing `Prompts-ddMetadiscussion` files in user repos are left alone. The plugin doesn't delete user files.

### Consequences

* Good, because unrelated prompts are never written anywhere.
* Good, because one less special file to explain.
* Good, because the session's opening statements land in the Prompts doc of the document they describe.
* Bad, because prompts sent before the skill is invoked aren't logged anywhere. A user who cares can backfill by hand.

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
* Neutral, because session-opening prompts need the start-of-session backfill in [ADR-0005](0005-recover-prompts-after-a-resumed-session.md) to reach the project's Prompts doc.

## More Information

* Related: [ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md) (when the hooks run at all), [ADR-0005](0005-recover-prompts-after-a-resumed-session.md) (logging the session-opening prompt).
* A review of what has accumulated in existing `Prompts-ddMetadiscussion` files is being done separately, to check whether anything valuable was only captured there.
