---
status: accepted
date: 2026-10-31
decision-makers: Ecnassianer
---

# Log the session-start prompt and recover prompts after a resume with marker-driven backfill

## Context and Problem Statement

Skill-scoped hooks ([ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md)) leave two gaps where prompts never reach `UserPromptSubmit`:

1. **Session start.** The prompt that invokes the skill is submitted before the hooks exist. That prompt often carries real content, for example "start a daydream dictation about a game that has…" followed by several statements about the document. If Claude has to ask "which project?" first, the answer is also sent while no project is set.
2. **Resume.** Skill hooks don't survive `--resume` or `--continue`. A resumed dictation session has no prompt logging and no commit enforcement until the skill is invoked again, and the prompts sent before that have already missed `UserPromptSubmit`. A hook can't invoke a skill or register hooks itself; the only way, writing to a settings file, was rejected in ADR-0002.

How do we get the prompts from both gaps into the project's Prompts doc, in order, and make it clear afterwards which entries came from which path?

## Decision Drivers

* No silent gaps in a dictation session's Prompts doc, including its opening prompt.
* The opening prompt belongs in the Prompts doc of the project it describes ([ADR-0003](0003-stop-logging-prompts-outside-a-dictation-session.md)).
* Only the smallest possible piece runs outside dictation sessions.
* Anything that went wrong should be easy to trace from the Prompts doc itself, and a session start must not be mistaken for a resume.
* No settings-file writes, and no race between hooks.

## Considered Options

* No recovery: the opening prompt is lost, and the user re-runs `/daydream-dictation` after resuming
* Resume nudge only: a `SessionStart` hook tells Claude to re-invoke the skill
* Resume nudge plus marker-driven backfill from the transcript, for both gaps
* A separate `once: true` skill hook to log the opening prompt
* Resume nudge plus hooks written into settings files (rejected in ADR-0002)

## Decision Outcome

Chosen option: **resume nudge plus marker-driven backfill, used for both gaps.** A *marker* means "user prompts in the transcript from this position onward haven't been logged yet". Markers have two kinds, `start` and `resume`. Each kind gets its own note in the Prompts doc and its own entry label.

1. **Start marker.** The first skill hook to run in a session creates it. That is normally the `Stop` at the end of the turn that invoked the skill. The shared library keeps a small per-session state file, outside the repo, so this happens once per session; invoking the skill again in the same live session does nothing new. The marker points at the prompt that invoked the skill. That is either the typed `/daydream-dictation …` command, whose full text the transcript keeps, or the user message just before Claude's Skill tool call. If a `resume` marker already exists for the session, no start marker is created.
2. **Resume hook** (`hooks/hooks.json`, `SessionStart` with matcher `resume`). This is the plugin's only always-registered hook. It runs only when a session is resumed or continued (both report `source: "resume"`). It doesn't run on startup, `/clear` (the skill is gone, so it shouldn't come back) or `/compact` (skill hooks survive compaction). It exits immediately unless the session's transcript shows the `daydream-dictation` skill (or its `dictate-daydream` alias) was invoked. Otherwise it:
   * writes the **resume note** to the active project's Prompts doc (see below);
   * writes a `resume` marker at the transcript position at resume. If a marker already exists for the session, it is kept so the earliest gap is still covered;
   * returns `additionalContext` telling Claude to invoke the `daydream-dictation` skill again before anything else, without repeating the session-start greeting;
   * deletes markers and state files older than a few days.
3. **Backfill.** Whichever of the skill's `UserPromptSubmit`, `Stop` or `StopFailure` hooks fires first checks for a marker. When one exists *and* a project is set, it logs every user prompt in the transcript from the marker's position onward, with the label for the marker's kind, then deletes the marker. If no project is set yet, the marker waits for the next hook. `UserPromptSubmit` logs its own prompt after the backfill. When the backfill runs in `Stop` or `StopFailure`, the entries are committed as described in [ADR-0006](0006-merge-commit-enforcement-into-the-skill-stop-hook.md).

**Notes and labels.** Notes aren't numbered lines, so they don't affect entry numbering. The exact wording is set during implementation; the shape is:

| | Session start | Resume |
| --- | --- | --- |
| Note written by | The backfill, when it first logs the start marker | The resume hook, at resume |
| Note | `> ▶ Session started 2026-10-29 14:02 UTC (session 7be2518d). The prompt that started it is logged below.` | `> ⟳ Session resumed 2026-10-29 16:40 UTC (session 7be2518d). Prompts sent before the skill is re-invoked are backfilled below.` |
| First entry label | `12. (session start) start a daydream dictation about a game that has…` | `15. (backfilled after resume) …` |
| Later entries from the same marker | `13. (backfilled at session start) …` | `16. (backfilled after resume) …` |

The session-start note uses the time of the invoking prompt, taken from the transcript, not the time the backfill ran.

All of this uses the shared prompt-log library ([ADR-0004](0004-keep-prompt-logging-on-userpromptsubmit.md)).

Why "everything from the marker onward" is exactly the missed set: from the invoking prompt, or from the resume, until the hooks exist and a project is set, no prompt reached a hook that could log it. The first skill hook to run after that sees all of them. This holds whether the gap lasts one turn or several.

Why every skill hook checks the marker: `Stop` doesn't fire when the user presses Esc, and API errors fire `StopFailure` instead of `Stop`. If only `Stop` backfilled, an interrupted turn would let the next prompt's `UserPromptSubmit` log first and break the numbering order.

Why not a separate `once: true` hook for the opening prompt: `once: true` works on skill hooks; tested, it ran once after invocation and a failing run retried at the next event. But Claude Code runs all hooks for the same event in parallel. A second `Stop` hook would race the main one's backfill, commit and cleanliness check. The per-session state file gives the same "once" behavior inside the single `Stop` hook.

Verified with Claude Code 2.1.312: the skill's `Stop` hook fires at the end of the invoking turn, and the transcript holds the invoking prompt with its full text. The `SessionStart` input has `source` but no prompt text. After the resume nudge, Claude re-invoked the skill and the skill's `Stop` hook fired at the end of that same turn, when the transcript already contained the missed prompt.

### Consequences

* Good, because the opening prompt, with whatever the user said about the document in it, lands in that project's Prompts doc instead of being lost or sent to a meta log.
* Good, because no prompt is lost after a resume: missed prompts wait in the transcript until the skill is back, however many turns that takes.
* Good, because distinct notes and labels show where every non-standard entry came from. A missing, garbled or duplicated entry points straight at the session-start or resume path.
* Good, because outside dictation sessions the only cost is one transcript check per resume. Nothing runs on prompts, startup, `/clear` or `/compact`.
* Bad, because re-invocation after a resume depends on Claude following an instruction. In testing it once didn't. The backfill makes that a delay rather than a loss, but logging and commit enforcement are off until Claude or the user re-invokes the skill.
* Bad, because the backfill parses the transcript JSONL, which isn't a documented, stable format. Every session now reads the transcript once, to find the invoking prompt, but normal turn-by-turn logging doesn't depend on it. Tests should catch format changes.
* Bad, because Claude needs permission to invoke a skill with hooks; see [ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md).
* Bad, because the opening prompt is committed at the end of the first turn instead of with it. ADR-0006 folds it into Claude's commit when that commit isn't pushed yet.
* Bad, because the resume note is written before Claude does anything. If the skill is never re-invoked, the note sits uncommitted. That is also a visible sign the backfill never ran.
* Neutral, because transcript entries for slash commands are converted back to the typed form (`/name args`) so backfilled entries match what `UserPromptSubmit` would have logged. Meta entries, tool results, compact summaries and local-command output are skipped.
* Neutral, because `SessionStart` hooks reportedly hung session startup in the original bespoke setup (March 2026, noted in DesignDocDictation's early `CLAUDE.md`). No hang was seen with Claude Code 2.1.312, but this should be checked in the desktop and cloud apps before release.

### Confirmation

* Integration tests feed the hook scripts synthetic hook input and transcripts:
  * session start with the project set in the first turn;
  * session start where the project is chosen a turn later, so the answer is backfilled after the opening prompt;
  * a typed `/daydream-dictation …` with text and a natural-language invocation through the Skill tool;
  * resume, then a backfill from each of `UserPromptSubmit`, `Stop` and `StopFailure`, checking order, numbering, notes and labels.
* A manual end-to-end check per release: start a session with a content-heavy first prompt, dictate, resume, dictate, and confirm both notes and every entry.

## Pros and Cons of the Options

### No recovery

* Good, because the plugin has no always-registered hooks at all.
* Bad, because the opening prompt is always lost, and prompts after a resume are silently lost until the user remembers to re-invoke the skill.

### Resume nudge only

* Good, because it's simple.
* Bad, because the opening prompt and the first prompt after every resume are always lost, and so is every prompt until Claude complies.

### Resume nudge plus marker-driven backfill, for both gaps

* Good, because there are no silent losses, failures are traceable, and one mechanism covers both gaps.
* Bad, because of the transcript-format dependency and the extra code.

### Separate `once: true` hook for the opening prompt

* Good, because it's Claude Code's built-in "run once after invocation" mechanism.
* Bad, because it would race the main `Stop` hook; see above.

### Resume nudge plus settings-file writes

* Rejected; see [ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md).

## More Information

* Claude Code docs: [SessionStart](https://code.claude.com/docs/en/hooks) (`source` is `startup`, `resume`, `clear`, `compact` or `fork`), and the hooks docs' `once` field.
* The file name keeps its original slug; the ADR now also covers the session-start gap.
* Related: [ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md), [ADR-0003](0003-stop-logging-prompts-outside-a-dictation-session.md), [ADR-0004](0004-keep-prompt-logging-on-userpromptsubmit.md), [ADR-0006](0006-merge-commit-enforcement-into-the-skill-stop-hook.md).
