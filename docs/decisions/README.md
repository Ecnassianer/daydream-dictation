# Architecture Decision Records

This folder holds the **Architecture Decision Records (ADRs)** for the Daydream Dictation plugin itself. Each ADR captures one significant decision we made while building the plugin: the context that forced the decision, the options we weighed, what we chose, and the compromises we accepted.

ADRs are for the *plugin's own development*. They are separate from the `DecisionTrace-<Slug>.md` companion document that the plugin creates inside a user's Daydream projects (see [ADR-0001](0001-use-madr-for-architecture-decision-records.md) for why we didn't reuse that format here).

## What is an ADR?

An ADR is a short Markdown file that records a single architecturally significant decision. The practice was popularized by Michael Nygard's 2011 post [*Documenting Architecture Decisions*](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions), and is now widely used (see [adr.github.io](https://adr.github.io/) for an overview of the community, formats, and tooling).

The key ideas:

- **One decision per file.** Small, focused records are easy to write, review, and link to.
- **Kept with the code.** ADRs live in the repo and are reviewed in pull requests like any other change.
- **Append-only history.** Once accepted, an ADR is not rewritten. If we change our minds, we write a *new* ADR that supersedes the old one, so the history of *why* is never lost.
- **Record the trade-offs, not just the answer.** The rejected options and the downsides of the chosen option are often the most useful part for a future reader.

We use the [MADR](https://adr.github.io/madr/) (Markdown Architectural Decision Records) template, version 4.0.0 ([source on GitHub](https://github.com/adr/madr)). The template for new records is [`adr-template.md`](adr-template.md).

## When to write an ADR

Write an ADR when a decision is **hard to reverse, affects more than one part of the plugin, or is likely to be questioned later**. Good signals:

- Choosing or dropping a dependency, language feature, or external tool (e.g. Python version floor, test framework).
- Changing how hooks, skills, or scripts interact, or how the plugin is installed and distributed.
- Changing the on-disk format of project files (`Daydream-`, `TODO-`, `Prompts-`, etc.) or anything users depend on.
- Adding or removing support for a VCS, platform, or Claude Code surface (CLI, Desktop, Cloud).
- Accepting a known limitation or compromise ("we can't do X on Cloud, so we do Y instead").
- Any time a reviewer asks "why did we do it this way?" and the answer isn't obvious from the code.

You **don't** need an ADR for bug fixes, refactors that don't change behavior, wording tweaks to skills, or decisions that are trivially reversible. When in doubt, a short ADR is cheap — write one.

## How to add an ADR

1. **Copy the template.** Copy [`adr-template.md`](adr-template.md) to `NNNN-short-title-in-kebab-case.md`, where `NNNN` is the next unused four-digit number (look at the index below). Numbers are never reused, even if an ADR is rejected.
   - Use a present-tense, imperative title that names the decision, e.g. `0002-log-prompts-with-a-userpromptsubmit-hook.md`.
2. **Fill it in.** Set `status: proposed` and today's date in the front matter. At minimum fill in *Context and Problem Statement*, *Considered Options*, and *Decision Outcome* (including *Consequences*). Delete optional sections you don't need rather than leaving them empty.
3. **Open a pull request.** Ideally the ADR goes in the same PR as the change it describes, so reviewers see the reasoning next to the code. For bigger decisions that should be agreed *before* implementation, open a PR with just the ADR. Discussion happens in PR review.
4. **Accept it.** Once reviewers agree, change the status to `accepted` (and update the date if it moved) in the PR before merging. If we decide against it, you can still merge it as `rejected` — a record of a road not taken is useful too.
5. **Update the index** at the bottom of this file.

## Statuses and lifecycle

| Status | Meaning |
| --- | --- |
| `proposed` | Under discussion in an open PR. |
| `accepted` | Agreed and in effect. |
| `rejected` | Considered and decided against. Kept for the record. |
| `deprecated` | No longer applies (e.g. the feature was removed), but nothing replaced it. |
| `superseded by ADR-NNNN` | Replaced by a newer decision. |

**Accepted ADRs are immutable.** Don't edit the substance of an accepted ADR. When a decision changes:

1. Write a new ADR that explains the new decision and links back to the old one in its *More Information* section.
2. In the old ADR, change only the `status` to `superseded by ADR-NNNN` and add a link to the new ADR. Leave the rest of the text alone.

Fixing typos, broken links, or formatting in an old ADR is fine.

## Index

| ADR | Title | Status |
| --- | --- | --- |
| [0001](0001-use-madr-for-architecture-decision-records.md) | Use MADR for architecture decision records | accepted |
| [0002](0002-scope-dictation-hooks-to-the-active-skill.md) | Scope dictation hooks to the active daydream-dictation skill | accepted |
| [0003](0003-stop-logging-prompts-outside-a-dictation-session.md) | Stop logging prompts outside a dictation session | accepted |
| [0004](0004-keep-prompt-logging-on-userpromptsubmit.md) | Keep prompt logging on UserPromptSubmit, with one shared prompt-log library | accepted |
| [0005](0005-recover-prompts-after-a-resumed-session.md) | Log the session-start prompt and recover prompts after a resume with marker-driven backfill | accepted |
| [0006](0006-merge-commit-enforcement-into-the-skill-stop-hook.md) | Merge commit enforcement into the skill's Stop hook, and commit backfilled prompts per the skill's commit discipline | accepted |
| [0007](0007-load-the-plugin-in-cloud-sessions-with-claude-code-plugin-dirs.md) | Load the plugin in cloud sessions with CLAUDE_CODE_PLUGIN_DIRS | accepted |
| [0008](0008-use-agents-md-for-per-project-instructions.md) | Use AGENTS.md for per-project instructions, with a CLAUDE.md pointer for one year | proposed |
| [0009](0009-move-config-and-state-out-of-the-claude-folder.md) | Move Daydream Dictation's config and state out of the .claude folder | proposed |
| [0010](0010-make-the-dictation-skill-self-contained.md) | Make the daydream-dictation skill self-contained, with skill-relative script paths | proposed |
