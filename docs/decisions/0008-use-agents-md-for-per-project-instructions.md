---
status: proposed
date: 2026-10-31
decision-makers: Ecnassianer
---

# Use AGENTS.md for per-project instructions, with a CLAUDE.md pointer for one year

## Context and Problem Statement

We want Daydream Dictation to work with more agents than Claude Code, following the [Agent Skills](https://agentskills.io/specification) conventions ([#47](https://github.com/Ecnassianer/daydream-dictation/issues/47)). The `daydream-dictation` skill tells users to put per-project rules (localization requirements and the like) in a `CLAUDE.md` inside the project folder. Only Claude Code reads `CLAUDE.md`. Codex, Gemini CLI, Cursor, GitHub Copilot, OpenCode and most other agents read `AGENTS.md`.

The plugin repo itself has no `CLAUDE.md`, so the change is to the convention the skill teaches, not to files we ship. Which file should hold per-project instructions, and how do we keep older Claude Code versions working?

## Decision Drivers

* Per-project instructions should reach whichever agent the user dictates with.
* Users on older Claude Code versions must keep getting their project's instructions.
* One source of truth: instructions shouldn't be duplicated across two files.
* Existing projects with a `CLAUDE.md` shouldn't break.

## Considered Options

* Keep `CLAUDE.md`
* `AGENTS.md` only
* `AGENTS.md`, plus a `CLAUDE.md` that only points at it
* `AGENTS.md`, plus a `CLAUDE.md` symlink

## Decision Outcome

Chosen option: **`AGENTS.md`, plus a `CLAUDE.md` that only points at it**, because it reaches every agent that reads `AGENTS.md` and keeps older Claude Code versions working, with the instructions in one file.

The pointer is:

```markdown
See the AGENTS.md file for further instructions.

@AGENTS.md
```

The sentence is for a human reader and for any agent that reads the file literally. The `@AGENTS.md` line is Claude Code's import syntax, so Claude Code loads the instructions instead of only being told they exist. The import matters: newer Claude Code versions reportedly read `AGENTS.md` on their own only when there is *no* `CLAUDE.md`, so a pointer without the import would hide the instructions from them.

The skill also tells the agent to read the project folder's `AGENTS.md` (or a legacy `CLAUDE.md`) when a session starts. Agents differ in when they load nested instruction files, and some load them only when touching a file in that folder; reading it explicitly makes the behavior the same everywhere.

### Consequences

* Good, because Codex, Gemini CLI, Cursor, Copilot, OpenCode and others pick up per-project instructions.
* Good, because the instructions live in one file.
* Good, because the session-start step makes loading the file independent of each agent's discovery rules.
* Bad, because each project carries a second file for a year.
* Bad, because Claude Code shows a one-time approval prompt the first time it sees an import.
* Neutral, because existing projects with a real `CLAUDE.md` keep working; the skill migrates them only when the user asks.

### Confirmation

* The skill's *Document Conventions* section and the README describe `AGENTS.md` plus the pointer.
* Around October 2027, write an ADR that deprecates the `CLAUDE.md` pointer.

## Pros and Cons of the Options

### Keep `CLAUDE.md`

* Good, because nothing changes.
* Bad, because no agent other than Claude Code reads it.

### `AGENTS.md` only

* Good, because there's one file.
* Bad, because older Claude Code versions don't read `AGENTS.md`.

### `AGENTS.md`, plus a `CLAUDE.md` symlink

* Good, because there's one copy of the text.
* Bad, because symlinks need admin rights or Developer Mode on Windows, and some VCSs (Perforce, Plastic) handle them poorly.

## More Information

* The wider work to support more agents (skill frontmatter, script paths, hooks, transcript parsing, the `.claude/` config folder) is tracked in [#52](https://github.com/Ecnassianer/daydream-dictation/issues/52).
* Revisit in October 2027 to remove the `CLAUDE.md` pointer.
