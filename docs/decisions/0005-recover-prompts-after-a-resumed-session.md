---
status: proposed
date: 2026-10-29
decision-makers: Ecnassianer
---

# Recover prompts after a resumed session with a resume nudge and marker-driven backfill

## Context and Problem Statement

Skill-scoped hooks ([ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md)) don't survive `--resume` or `--continue`: a resumed dictation session has no prompt logging and no commit enforcement until the skill is invoked again. A hook can't invoke a skill or register hooks itself (the only way, writing to a settings file, was rejected in ADR-0002). Even when the skill comes back, the prompts sent before it was re-invoked have already missed `UserPromptSubmit`. How do we bring the hooks back after a resume, and make sure the prompts in between still get logged?

## Decision Drivers

* No silent gaps in the Prompts doc of a resumed dictation session.
* Only the smallest possible piece runs outside dictation sessions.
* Anything that went wrong should be easy to trace from the Prompts doc itself.
* No settings-file writes.

## Considered Options

* No recovery: the user re-runs `/daydream-dictation` after resuming
* Resume nudge only: a `SessionStart` hook tells Claude to re-invoke the skill
* Resume nudge plus marker-driven backfill from the transcript
* Resume nudge plus hooks written into settings files (rejected in ADR-0002)

## Decision Outcome

Chosen option: **resume nudge plus marker-driven backfill.**

1. **Resume hook** (`hooks/hooks.json`, `SessionStart` with matcher `resume`). This is the plugin's only always-registered hook. It runs only when a session is resumed or continued (both report `source: "resume"`). It doesn't run on startup, `/clear` (the skill is gone, so it shouldn't come back) or `/compact` (skill hooks survive compaction). It exits immediately unless the session's transcript shows the `daydream-dictation` skill (or its `dictate-daydream` alias) was invoked. Otherwise it:
   * writes a **resume note** to the active project's Prompts doc. The note isn't a numbered line, and it says the session resumed, when, the session ID, and that prompts until the skill is re-invoked will be backfilled;
   * writes a **marker** keyed by session ID, outside the repo (for example under `~/.claude/`), recording the transcript position at resume and the current VCS revision (`HEAD`). If a marker already exists for the session, it is kept so the earliest gap is still covered;
   * returns `additionalContext` telling Claude to invoke the `daydream-dictation` skill again before anything else, without repeating the session-start greeting;
   * deletes markers older than a few days.
2. **Backfill.** Whichever of the skill's `UserPromptSubmit`, `Stop` or `StopFailure` hooks fires first after re-invocation checks for the marker. It logs every user prompt in the transcript after the marker's position, marked as backfilled (for example `5. (backfilled) …`), then deletes the marker. `UserPromptSubmit` then logs its own prompt as usual. When the backfill runs in `Stop` or `StopFailure`, the entries are committed as described in [ADR-0006](0006-merge-commit-enforcement-into-the-skill-stop-hook.md).

All of this uses the shared prompt-log library ([ADR-0004](0004-keep-prompt-logging-on-userpromptsubmit.md)).

Why "everything after the marker" is exactly the missed set: the skill's hooks are absent from the resume until partway through the turn in which Claude re-invokes the skill. No prompt in that span reached `UserPromptSubmit`. The first skill hook to fire afterwards sees all of them. This holds whether Claude re-invokes on the first turn or several turns later.

Why every skill hook checks the marker: `Stop` doesn't fire when the user presses Esc, and API errors fire `StopFailure` instead of `Stop`. If only `Stop` backfilled, an interrupted first turn would let the next prompt's `UserPromptSubmit` log first and break the numbering order.

Verified with Claude Code 2.1.312: the `SessionStart` input has `source` but no prompt text. After the nudge, Claude re-invoked the skill and the skill's `Stop` hook fired at the end of that same turn. The transcript already contained the missed prompt.

### Consequences

* Good, because no prompt is lost: missed prompts wait in the transcript until the skill is back, however many turns that takes.
* Good, because the resume note plus `(backfilled)` labels show exactly which entries came from the backfill path. A missing, garbled or duplicated entry points straight at the resume script or the backfill.
* Good, because outside dictation sessions the only cost is one transcript check per resume. Nothing runs on prompts, startup, `/clear` or `/compact`.
* Bad, because re-invocation depends on Claude following an instruction. In testing it once didn't. The backfill makes that a delay rather than a loss, but logging and commit enforcement are off until Claude or the user re-invokes the skill.
* Bad, because the backfill parses the transcript JSONL, which isn't a documented, stable format. Only the resume path depends on it, and tests should catch format changes.
* Bad, because Claude needs permission to invoke a skill with hooks; see [ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md).
* Bad, because the resume note is written before Claude does anything. If the skill is never re-invoked, the note sits uncommitted. That is also a visible sign the backfill never ran.
* Neutral, because transcript entries for slash commands are converted back to the typed form (`/name args`) so backfilled entries match what `UserPromptSubmit` would have logged. Meta entries, tool results, compact summaries and local-command output are skipped.
* Neutral, because `SessionStart` hooks reportedly hung session startup in the original bespoke setup (March 2026, noted in DesignDocDictation's early `CLAUDE.md`). No hang was seen with Claude Code 2.1.312, but this should be checked in the desktop and cloud apps before release.

### Confirmation

* Integration tests feed the hook scripts synthetic hook input and transcripts: resume, then a backfill from each of `UserPromptSubmit`, `Stop` and `StopFailure`, checking order and numbering.
* A manual end-to-end check per release: start a dictation session, resume it, dictate, and confirm the resume note, the backfilled entry and the following normal entries.

## Pros and Cons of the Options

### No recovery

* Good, because the plugin has no always-registered hooks at all.
* Bad, because prompts after a resume are silently lost until the user remembers to re-invoke the skill.

### Resume nudge only

* Good, because it's simple.
* Bad, because the first prompt after every resume is always lost, and so is every prompt until Claude complies.

### Resume nudge plus marker-driven backfill

* Good, because there are no silent losses, and failures are traceable.
* Bad, because of the transcript-format dependency and the extra code.

### Resume nudge plus settings-file writes

* Rejected; see [ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md).

## More Information

* Claude Code docs: [SessionStart](https://code.claude.com/docs/en/hooks) (`source` is `startup`, `resume`, `clear`, `compact` or `fork`).
* Related: [ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md), [ADR-0004](0004-keep-prompt-logging-on-userpromptsubmit.md), [ADR-0006](0006-merge-commit-enforcement-into-the-skill-stop-hook.md).
