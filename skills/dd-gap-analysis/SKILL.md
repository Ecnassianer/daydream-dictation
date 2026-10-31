---
name: dd-gap-analysis
description: Run a structured gap analysis on a design document, staffing plan, or any other document or project folder. Use when asked to check what's missing, find gaps, or review completeness of a document.
argument-hint: "[project folder or name]"
license: MIT
metadata:
  version: "0.2.0"
allowed-tools: Read Glob Grep
---

# Gap Analysis

A standalone skill that analyzes documents for gaps, missing coverage, and open work. This skill has no dependency on the Daydream Dictation process — it works on any set of documents at any time. A user might invoke it during a Phase 2 session, run it cold on a project they haven't touched in weeks, or use it as the first step when picking up an unfamiliar document.

The analysis has two layers:

- **Core questions** (below) apply to every document.
- **Document-type questions** come from a reference file in `references/` and apply only when the document is that type. They hold everything that only makes sense for one kind of document, so a staffing plan never gets asked about player controls.

## How to Execute

1. Resolve the target project:
   - If the user named a project (in their message or as arguments to this skill), find its folder
   - If the user gave a path, use it directly
   - If neither, read `dd-current-dictation-project` for the active project
   - If still nothing, ask the user which project to analyze

2. Read the project's documents:
   - `Daydream-<Slug>.md` — the main document
   - `TODO-<Slug>.md` — the to-do list
   - `Prompts-<Slug>.md` — tail of the prompts log (last 20–30 entries for recent context)

   Not all project folders follow this exact naming. If the folder uses different filenames, look for a root document that serves as the main document (e.g., `Overview-*.md`) and use whatever documentation is present.

3. Identify the document type. Compare the main document against the types below and read the reference file for each one that matches. Read only the matching files.

   | Type | Reference file | Signals |
   | --- | --- | --- |
   | Game design document | [references/game-design-document.md](references/game-design-document.md) | Describes a video game, tabletop game, or other playable experience: players, mechanics, levels, controls, game loops |
   | Staffing plan | [references/staffing-plan.md](references/staffing-plan.md) | Argues for adding people to a team: headcount, roles, hiring, budget, capacity |
   | Media requiring translation | [references/media-requiring-translation.md](references/media-requiring-translation.md) | Has a `StringTable-<Slug>.md` or other localization files, or names more than one supported language. Often matches alongside another type, such as a game |

   - A document can match more than one type. A game pitch with a hiring section matches both game design document and staffing plan. Use every reference that matches.
   - If nothing matches, run the core questions only. Don't borrow questions from a reference that doesn't fit.
   - Name the type (or types) you picked at the top of the report, in one line, so the user can correct you if you guessed wrong.

4. Answer the core questions and the questions from each matching reference. For each one, give concrete findings — not generic advice. Quote specific sections, name specific gaps, reference specific TODOs.

5. After answering every question, write a summary of actionable items and offer to address them.

- **Standalone output.** The gap analysis produces a self-contained report. Do not modify any documents — only read, report and offer to help. The user decides what to act on.

---

## Core Questions

### What are we missing?

Are there topics, systems, features, or arguments that have been mentioned or implied but not yet written down? Are there sections that feel thin or underspecified? Look for things the user talked about in prompts that never made it into the document.

### What to-do items are still open?

Review `TODO-<Slug>.md`. Which items remain unresolved? Scan the Prompts log and the document for to-do items that were mentioned but never added to the TODO file. Report any discrepancies.

### What are opportunities for improvement?

Beyond what's missing — where does the existing document feel unclear, inconsistent, or underdeveloped? What could be strengthened? Look for contradictions between sections, vague language that would block the reader from acting, or areas where the user changed their mind but the document wasn't fully updated.

### What will the reader need to know to act on this?

Work out who acts on this document next — an implementing agent, a manager approving a request — and what they will do with it. Then identify anything that reader would find ambiguous or underspecified. What decisions would they have to make on their own because the document doesn't answer them? Does the document call out open decisions? Does the user want to make them now?

If the project has a `DecisionTrace-<Slug>.md`, check whether it covers the technical decisions needed to implement the design. If no Decision Trace exists and the project has enough technical complexity to warrant one, note that.

### Are there any other gaps?

Catch-all for anything not covered by the other questions — undefined edge cases, unresolved working names, placeholder items (`[Item N — not yet documented]`), or anything else that would stop the document from doing its job.

### Is the document what it says it is?

A wandering dictation can leave a document shaped by where the conversation started rather than where it ended up. Look for statements of what the document is or is for: "This document is a concrete plan for execution", "This is a pitch for…", "The goal of this doc is…". The title and the opening paragraph usually carry the claim, but it can appear anywhere.

For each claim, check whether the structure and the bulk of the content deliver it. Warning signs:

- Most sections are organized around early ideas, background, or musings, while the content the claim promises is scattered across them.
- The section order follows the order the user talked, not the order a reader needs.
- The opening describes one kind of document and the closing describes another.

If the document doesn't match its claim, don't patch it section by section. Recommend a planning step that produces a restructure plan:

1. The target structure — an outline of the document it says it is.
2. Where each existing section's content goes in that outline, or that it should be cut or moved to an appendix.
3. An ordered task list that moves the document from what it is to what it claims to be.

Offer to write that plan.

---

## Output Format

For each question, respond with:
- **Finding** — what you found (or "No gaps identified" if clean)
- **Severity** — critical (blocks the document from doing its job), moderate (should be addressed), minor (nice to have)
- **Suggestion** — what to do about it

End with a numbered list of all actionable items sorted by severity, and ask the user which ones to tackle.

## Goal

The gap analysis is a signal that the document is complete enough to hand off — to an implementing agent, a recipient, or a decision-maker. By the time every question is answered satisfactorily, you should be confident that the reader has everything they need, and that the user has touched every part of the document before moving on. If significant gaps remain, say so clearly. If the document looks solid, tell the user it's ready.
