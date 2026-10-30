---
status: proposed
date: 2026-10-29
decision-makers: Ecnassianer
---

# Keep prompt logging on UserPromptSubmit, with one shared prompt-log library

## Context and Problem Statement

Moving the hooks into the skill ([ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md)) opened the question of which hook event should write Prompts entries. A `Stop` hook could do all the logging by reading the session transcript, which would also fill gaps such as the prompt that arrives right after a resume. Several hooks will now write to the Prompts doc: `UserPromptSubmit`, `Stop`, `StopFailure` and the `SessionStart` resume hook. Should logging stay on `UserPromptSubmit`, and how do we keep these hooks from each implementing logging their own way?

Neither repo records why `UserPromptSubmit` was originally chosen. It dates to the first bespoke setup in DesignDocDictation (`.claude/hooks/log-prompt.sh`, PR #59, 2026-03-28) and was carried into the plugin unchanged. It was the natural fit: Claude Code passes the exact prompt text to the hook at the moment it's submitted.

## Decision Drivers

* Prompt entries must be verbatim.
* The co-commit rule: a prompt's entry belongs in the same commit as the work it caused.
* Interrupted or failed turns shouldn't lose prompts.
* Avoid depending on undocumented formats where possible.
* Logging behavior (finding the Prompts doc, numbering, skipping automated notifications, formatting entries) is defined once.

## Considered Options

* Log on `UserPromptSubmit`; use the transcript only to backfill the session-start and resume gaps
* Log everything on `Stop` by syncing new prompts from the transcript

## Decision Outcome

Chosen option: **keep logging on `UserPromptSubmit`**, and use the transcript only to backfill the prompts that arrive while the hooks can't log them: the prompt that starts the session, and prompts after a resume ([ADR-0005](0005-recover-prompts-after-a-resumed-session.md)).

All hooks that write to the Prompts doc use one shared module (for example `scripts/dd_prompt_log.py`) for:

* resolving the active project's Prompts doc from `dd-current-dictation-project`;
* entry numbering (`^N. ` lines only);
* filtering automated notifications (`<task-notification>`, `<github-webhook-activity>`) and non-prompt transcript entries;
* writing numbered entries, backfilled entries, and session-start and resume notes;
* reading user prompts from the transcript;
* creating, reading and clearing the session-start and resume markers, and the per-session state file.

Each hook script stays a thin wrapper that reads its hook input and calls the library.

### Consequences

* Good, because entries are written before Claude starts working, so Claude's commits in that turn include them (co-commit rule).
* Good, because the prompt is logged even if the user presses Esc or the turn fails with an API error. `Stop` doesn't fire on a user interrupt, and API errors fire `StopFailure` instead.
* Good, because the prompt text comes straight from Claude Code rather than from parsing the transcript file.
* Good, because a fix to logging (numbering, filtering, format) is made once and applies to every hook.
* Bad, because a separate path is still needed for prompts that arrive while the hooks aren't registered (see [ADR-0005](0005-recover-prompts-after-a-resumed-session.md)).

### Confirmation

* Hook scripts contain no logging logic of their own; reviewers check that new logging behavior goes into the shared module.
* Unit tests for the shared module, plus integration tests per hook script.

## Pros and Cons of the Options

### Log on `UserPromptSubmit`, transcript only for backfill

* Good, for the reasons in *Consequences*.
* Neutral, because transcript parsing is still needed, but only to fill the session-start and resume gaps.

### Log everything on `Stop` from the transcript

* Good, because one mechanism covers normal turns and gaps alike, and any missed prompt is picked up at the next Stop.
* Bad, because the entry lands *after* Claude's last commit in the turn, so every turn ends with an uncommitted Prompts doc and an extra commit cycle.
* Bad, because it would race with the commit check if they were separate `Stop` hooks (hooks for the same event run in parallel).
* Bad, because a prompt isn't logged if the user interrupts the turn.
* Bad, because Claude can't see the current prompt in the Prompts doc during the turn.
* Bad, because all logging would depend on the transcript JSONL layout, which isn't a documented, stable format.

## More Information

* Claude Code docs: [Stop](https://code.claude.com/docs/en/hooks) ("Does not run if the stoppage occurred due to a user interrupt. API errors fire StopFailure instead.").
* [#38](https://github.com/Ecnassianer/daydream-dictation/issues/38) (have the hook commit the prompt log) is related and may change how entries get committed.
