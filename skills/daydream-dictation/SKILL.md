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

This skill covers voice parsing, prompt logging, commit discipline, and project initialization. The agent's job is to create well structured documents that capture everything that user has expressed.

If the user asks questions about the process itself — "what is Phase 1?", "how does this work?", "what should I do next?" — activate the `/dd-teach` skill to handle the explanation.

---

## Quick Reference — The Three Phases

**Phase 1 — Structured Daydreaming.** The user talks out loud about their idea for 20–60 minutes. They don't edit, don't review, and don't look at what the agent is writing. The agent captures everything and organizes it into the document as the user speaks. The agent is free to ask clarifying questions or make suggestions, but recognize that the user won't be back to answer them until much later. Flag open items inline and keep going. Write notes about uncertain factors and plan to return to them later when a decision is made or an inferrance is confirmed.

**Phase 2 — Response and Agent Engagement.** The user engages with the agent's replies from Phase 1, top to bottom. They answer questions, fill in gaps, and add anything that comes up. When the user has caught up on all the agent responses, the agent should suggest running `/dd-gap-analysis` and facilitate that if the user agrees, or the user might suggest this themselves unprompted.

**Phase 3 — Diff Review.** The user opens the pull request and reads the actual diff. They leave inline comments with feedback or talk to the agent directly; the agent addresses review comments and new prompts, commiting additional changes to the same pull request. Because every prompt is also recorded in each commit, the user has a record of what dictation caused which changes. When satisfied, the user approves and merges. 

---

## Starting a Session

When the user tells you which project to work on:

1. **Switch to the project** — run `dd_switch_project.py` with the project slug or name. This sets `dd-current-dictation-project` and verifies the project files exist. Do this as your very first action.
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/dd_switch_project.py "ProjectSlug"
   ```
   For new projects, use `dd_init_project.py` instead (it switches automatically after creation).
2.**Load commonly confused words** — check for variant files in `.claude/` (e.g., `.claude/dd-voice-variants.md`). If found, familiarize yourself with the substitutions so you can apply them throughout the session.
3. **Read the tail of the Prompts document** — last 20–30 entries. Do not read the entire file; it can be very long.
4. **Confirm the prompt logging hook is firing** — check whether new entries appear after the user's next prompt. If not, prompts will need to be backfilled manually at session end.

If no specific project is active, clear the active project:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/dd_switch_project.py --clear
```
Prompts will then log to `Prompts-ddMetadiscussion` at the repo root.

### The `dd-current-dictation-project` State File

A plain text file at the repo root containing the absolute path to the currently active **project folder** (not the Prompts file). Not tracked by git (listed in `.gitignore`).

The `UserPromptSubmit` hook reads this folder path and dynamically finds the Prompts file inside it. This decouples the state file from the exact Prompts filename.

The file is not automatically cleared between sessions — it persists. Always set it explicitly when the user names a project.

**Important:** `SessionStart` hooks and `UserPromptSubmit`-based clearing have both been tried and cause sessions to hang on startup. `Stop`/`SessionEnd` hooks clear too aggressively (after every response). Manual management is the current approach.

---

## Slash Command — `/daydream-dictation`

**Aliases:** `/daydream-dictation`, `/dictate-daydream`

Runs the session-start workflow:

1. If no project is specified, ask the user which project they're working on
2. If the project doesn't exist, run `dd_init_project.py` to create it
3. Run `dd_switch_project.py` to set the active project (skip if `dd_init_project.py` just ran — it switches automatically)
4. Read the tail of the Prompts document (last 20–30 entries)
5. Load commonly confused words from `.claude/dd-variants.md` if present
6. Confirm the prompt logging hook is firing
7. Tell the user you're ready — briefly remind them of the three phases if this seems like their first time

**With argument:** `/daydream-dictation "My New Project"` — if the project exists, start it; if not, create it first via the script.

---

## Processing Voice Dictation

Prompts are typically raw voice transcriptions. Parse them as speech, not text:

- **Mid-sentence corrections** — "a cement smokestack I mean chimney" → use "chimney", discard "smokestack"
- **Restarts** — the user may circle back mid-prompt and restate something. Capture the final intent, not every false start.
- **Multiple topics in one prompt** — handle all of them. Don't ignore the second topic because the first was long.
- **Informal phrasing** — parse intent, not literal words. "Throw in a thing about networking" means "add a networking section."
- **Brief commands embedded in dictation** — "Make a section for FAQs" or "Add a TODO for this" are real instructions. Execute them, don't just transcribe them.

### What You Do During Phase 1

The user is in a creative flow state and will not be reading your responses. Your job:

- Absorb everything they say and organize it into the document
- Create structure (sections, headings, lists) as the content demands it — don't wait for the user to tell you how to organize
- When the user flags something ("note to come back to this"), mark it with a TODO in the document and add it to `TODO-<Slug>.md`
- When the user gives a brief instruction ("make a section for X"), execute it immediately
- When something is ambiguous, make your best judgment and keep going. Flag it with an inline note like `<!-- clarify: did the user mean X or Y? -->` so it surfaces in Phase 2
- Do not ask clarifying questions during Phase 1 — the user is not reading your responses

---

## The Prompts Document

Every project has a companion Prompts document (`Prompts-<Slug>.md`) that logs every prompt used during sessions. This is a permanent record.

### Rules

- **Never delete logged prompts**, even if they seem off-topic. If a prompt clearly belongs to a different project, move it — but never delete it.
- **Record prompts verbatim**, transcription errors and all. The raw wording is part of the record.
- **Session-opening prompts stay in `Prompts-ddMetadiscussion`** — the hook fires before you set `dd-current-dictation-project`, so the first prompt of any session is logged there. This is correct and intentional. Do not move it into the project's Prompts document.
- **Co-commit rule:** Prompt log entries belong in the same commit as the document changes they accompany. Do not commit the Prompts doc ahead of the corresponding work.

### Why We Keep It

- **Reconstruction** — clarifies intent when the design doc is ambiguous
- **Audit trail** — trace any line back to the prompt that produced it
- **Session continuity** — new sessions read the Prompts doc to understand history
- **Debugging AI edits** — identifies whether an instruction was ambiguous or misinterpreted

### Backfilling Missed Prompts

If prompts were not captured automatically, add them manually in order. Use the conversation history to reconstruct exact wording. Number sequentially from the last captured entry. Commit with a note that entries were backfilled.

---

## Creating New Projects

Always use `dd_init_project.py` — never manually create project files.

```bash
python3 ${CLAUDE_SKILL_DIR}/../../scripts/dd_init_project.py "Project Name"
python3 ${CLAUDE_SKILL_DIR}/../../scripts/dd_init_project.py --project-root /path "Project Name"
```

The script creates `<Slug>/Daydream-<Slug>.md`, `TODO-<Slug>.md`, `Prompts-<Slug>.md`, sets `dd-current-dictation-project`, and commits.

If the folder already exists, don't re-run the script — use `dd_switch_project.py` to set the active project. It verifies that the expected files exist.

**Project root resolution:** CLI `--project-root` → `.claude/dd-projects-root` file → repo root.

### Error Recovery

- `dd-current-dictation-project` points to nonexistent folder → run `dd_switch_project.py` with the correct slug
- Prompts doc exists but `Daydream-<Slug>.md` or `TODO-<Slug>.md` missing → create missing files manually with matching header format
- No git remote configured → stop hook will fail on push; help user set up remote

---

## Document Conventions

- **Placeholders for undescribed items:** `**[Item N — not yet documented]**`
- **Working names:** `**Name** *(working name)*`
- **To-do items** always go in `TODO-<Slug>.md` (canonical list). May also appear inline where contextually useful.
- **Per-project instructions** can be placed in a `CLAUDE.md` inside the project folder (e.g., `Campfire/CLAUDE.md`). Use this for project-specific rules like localization requirements.

### Optional Companion Documents

These are not created by `dd_init_project.py` — create them when a project needs them.

- **`TechDesign-<Slug>.md`** — Technical design document maintained by the implementing agent. Records *how* (technologies, architecture, tradeoffs) vs the design doc's *what* and *why*. Dated entries under topical sections. Also defines testing instrumentation and the integration test suite. The implementing agent should not edit the main design document.
- **`StringTable-<Slug>.md`** — User-facing strings with translations, organized by string key. When a new string is added to the design, its translations go in the string table in the same commit. Referenced by gap analysis Q6.
- **`DebugTools-<Slug>.md`** — Debug commands, cheat codes, test shortcuts — anything that won't ship. Keeps debug-only features out of the main design doc.

---

## Committing and Pushing

- Commit after every set of changes with a clear, descriptive message
- Push to the active branch immediately after committing
- Daydream doc and Prompts doc committed together when both change in the same turn
- Prompt log entries belong in the same commit as the work they accompany
- The Stop hook will warn if there are uncommitted or unpushed changes

---

## Switching Projects Mid-Session

When the user says to switch projects:

1. Run `dd_switch_project.py` with the new project's slug — this is your first action
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/dd_switch_project.py "NewProjectSlug"
   ```
2. Read the tail of the new project's Prompts document
3. Continue working — subsequent prompts will log to the new project

---

## Handling PR Review Comments (Phase 3)

When the user says "address the comments on the PR" or similar:

- **Simple changes** (word substitutions, small fixes, clear directives): make the edit, commit, reply "Done." on the PR comment.
- **Complex comments** (questions, design discussions, ambiguous requests): reply on the PR with a question or proposed approach. Wait for user response before making changes.

---

## Version Control

Version control is **required**. The diff review phase depends on being able to see before/after. If the user doesn't have VCS set up, walk them through setting up Git before proceeding.

### Supported VCS

- `git` — full support; first-class default
- `hg` — Mercurial
- `perforce` (alias: `p4`) — Perforce
- `unity-vcs` (alias: `plastic`) — Unity Version Control / Plastic SCM
- `custom` — unsupported VCS; manage checkpoints conversationally

### Detection Order (first match wins)

1. `.claude/dd-vcs` file — user-supplied override
2. Auto-detection: `.git/` → git; `.hg/` → hg; `.plastic/` → unity-vcs; `.p4config` or `P4CONFIG` env var → perforce
3. Nothing detected → ask the user; if they don't know, walk them through setting up Git

---

## The `dd-` Naming Prefix

Any file or artifact that lives outside a project folder and is part of the Daydream Dictation system must be prefixed with `dd-`. This distinguishes skill infrastructure from the user's work.

**Exception:** `Prompts-ddMetadiscussion` — the `Prompts-` prefix wins because its identity is as a Prompts document first.
