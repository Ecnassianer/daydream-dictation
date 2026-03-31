---
name: daydream-dictation
description: Voice-driven document authoring using the Daydream Dictation workflow. Activates when the user is dictating design documents, mentions a Daydream project, refers to Prompts documents or dd-current-dictation-project, or starts a dictation session.
version: 0.1.0
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Daydream Dictation — Agent Behavior

This skill defines how you behave during Daydream Dictation sessions.

---

## Starting a Session

When the user names a project to work on:

1. **Immediately** write the absolute path to that project's folder into `dd-current-dictation-project` at the repo root. Do this before anything else — the file may contain a stale path from a previous session.
2. Read the **tail** of the companion Prompts document — last 20–30 entries. Do not read the entire file. It can be very long; loading it all wastes context.
3. Confirm the prompt logging hook is firing by checking whether new entries appear after the user's next prompt. If not, prompts will need to be backfilled manually at session end.

If no specific project is active, write an empty string to `dd-current-dictation-project` — prompts will log to `Prompts-ddMetadiscussion` at the repo root.

---

## Processing Voice Dictation

Prompts are typically raw voice transcriptions. Parse them as speech, not text:

- **Mid-sentence corrections** — "a cement smokestack I mean chimney" → use "chimney", discard "smokestack"
- **Restarts** — the user may circle back mid-prompt and restate something. Capture the final intent, not every false start.
- **Multiple topics in one prompt** — handle all of them. Don't ignore the second topic because the first was long.
- **Informal phrasing** — parse intent, not literal words. "Throw in a thing about networking" means "add a networking section."
- **Brief commands embedded in dictation** — "Make a section for FAQs" or "Add a TODO for this" are real instructions. Execute them, don't just transcribe them.

### Commonly Confused Words

Check for a `.claude/dd-variants.md` file in the repo. If it exists, it lists words the user's dictation software consistently mis-transcribes. When you see any listed variant in a prompt, silently substitute the correct word.

### What You Do During Phase 1

The user is in a creative flow state and will not be reading your responses. Your job:

- Absorb everything they say and organize it into the document
- Create structure (sections, headings, lists) as the content demands it — don't wait for the user to tell you how to organize
- When the user flags something ("note to come back to this"), mark it with a TODO in the document and add it to `TODO-<Slug>.md`
- When the user gives a brief instruction ("make a section for X"), execute it immediately
- When something is ambiguous, make your best judgment and keep going. Flag it with an inline note like `<!-- clarify: did the user mean X or Y? -->` so it surfaces in Phase 2
- Do not ask clarifying questions during Phase 1 — the user is not reading your responses

---

## Prompt Log Rules

- **Never delete logged prompts.** The prompt log is a permanent record.
- **Never move session-opening prompts.** The first prompt of a session (e.g. "I want to work on X") is logged to `Prompts-ddMetadiscussion` by the hook before you set the active project. This is correct — it's metadiscussion, not project content.
- If a prompt clearly belongs to a different project, move it to that project's Prompts doc — but never delete it.
- **Co-commit rule:** Prompt log entries belong in the same commit as the document changes they accompany. Do not commit the Prompts doc ahead of the corresponding work.

---

## Creating New Projects

Always use `dd_init_project.py` — never manually create project files.

```bash
python3 ${CLAUDE_SKILL_DIR}/../../scripts/dd_init_project.py "Project Name"
python3 ${CLAUDE_SKILL_DIR}/../../scripts/dd_init_project.py --project-root /path "Project Name"
```

The script creates `<Slug>/Daydream-<Slug>.md`, `TODO-<Slug>.md`, `Prompts-<Slug>.md`, sets `dd-current-dictation-project`, and commits.

If the folder already exists, don't re-run the script — just set the active project and start working. Verify `TODO-<Slug>.md` and `Prompts-<Slug>.md` exist alongside the main doc.

**Project root resolution:** CLI `--project-root` → `.claude/dd-projects-root` file → repo root.

### Error Recovery

- `dd-current-dictation-project` points to nonexistent folder → rewrite with correct path
- Prompts doc exists but `Daydream-<Slug>.md` or `TODO-<Slug>.md` missing → create missing files manually with matching header format
- No git remote configured → stop hook will fail on push; help user set up remote

---

## Document Conventions

- Placeholder for undocumented items in ordered lists: `**[Item N — not yet documented]**`
- Working names: `**Name** *(working name)*`
- Debug/test tools → `DebugTools-<ProjectName>.md`, not the main document
- To-do items → always add to `TODO-<ProjectName>.md` (canonical list). May also appear inline in the design doc where contextually useful.

---

## Committing and Pushing

- Commit after every set of changes with a clear, descriptive message
- Push to the active branch immediately after committing
- Daydream doc and Prompts doc committed together when both change in the same turn
- Prompt log entries belong in the same commit as the work they accompany

---

## Switching Projects Mid-Session

When the user says to switch projects:

1. Immediately update `dd-current-dictation-project` to the new project's folder path — this is your first action
2. Read the tail of the new project's Prompts document
3. Continue working — subsequent prompts will log to the new project

---

## Handling PR Review Comments (Phase 3)

When the user says "address the comments on the PR" or similar:

- **Simple changes** (word substitutions, small fixes, clear directives): make the edit, commit, reply "Done." on the PR comment. No explanation needed.
- **Complex comments** (questions, design discussions, ambiguous requests): reply on the PR with a question or proposed approach. Wait for user response before making changes.

---

## The `dd-` Prefix Convention

Any file or artifact that lives outside a project folder and is part of the Daydream Dictation system must be prefixed with `dd-`. This distinguishes plugin infrastructure from the user's work.

Exception: `Prompts-ddMetadiscussion` — the `Prompts-` prefix wins because its identity is as a Prompts document first.
