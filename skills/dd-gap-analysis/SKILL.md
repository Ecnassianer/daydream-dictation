---
name: dd-gap-analysis
description: Run a structured gap analysis on any design document or project folder. Use when asked to check what's missing, find gaps, or review completeness of a design.
argument-hint: "[project folder or name]"
version: 0.1.0
allowed-tools:
  - Read
  - Glob
  - Grep
---

# Gap Analysis

A standalone skill that analyzes design documents for gaps, missing coverage, and open work. This skill has no dependency on the Daydream Dictation process — it works on any set of documents at any time. A user might invoke it during a Phase 2 session, run it cold on a project they haven't touched in weeks, or use it as the first step when picking up an unfamiliar document.

## How to Execute

1. Resolve the target project:
   - If `$ARGUMENTS` names a project, find its folder
   - If `$ARGUMENTS` is a path, use it directly
   - If empty, read `dd-current-dictation-project` for the active project
   - If still nothing, ask the user which project to analyze

2. Read the project's documents:
   - `Daydream-<Slug>.md` — the main design document
   - `TODO-<Slug>.md` — the to-do list
   - `Prompts-<Slug>.md` — tail of the prompts log (last 20–30 entries for recent context)

3. Answer each of the seven questions below. For each one, give concrete findings — not generic advice. Quote specific sections, name specific gaps, reference specific TODOs.

4. After answering all seven, write a summary of actionable items and offer to address them.

---

## The Seven Questions

### 1. What are we missing from the design?

Are there systems, features, or areas that have been mentioned or implied but not yet documented? Are there sections that feel thin or underspecified? Look for things the user talked about in prompts that never made it into the document.

### 2. What to-do items are still open?

Review `TODO-<Slug>.md`. Which items remain unresolved? Scan the Prompts log and the design document for to-do items that were mentioned but never added to the TODO file. Report any discrepancies.

### 3. What are opportunities for improvement?

Beyond what's missing — where does the existing design feel unclear, inconsistent, or underdeveloped? What could be strengthened? Look for contradictions between sections, vague language that would block implementation, or areas where the user changed their mind but the document wasn't fully updated.

### 4. What will the implementing agent need to know?

Identify anything that an agent picking up this design document would find ambiguous or underspecified. What decisions would they have to make on their own because the document doesn't answer them?

### 5. Are there missing control definitions?

For any interactive or playable system: are the player controls fully defined? Are all inputs accounted for across all relevant states? Skip this question if the project is not interactive.

### 6. Are there untranslated strings?

If the project has string tables or localization files, are there strings that have not yet been translated? If so, ask: should translation happen now, or is it deferred?  Skip this question if the project has no localization.

### 7. Are there any other gaps?

Catch-all for anything not covered above — missing asset lists, undefined edge cases, unresolved working names, placeholder items (`[Item N — not yet documented]`), or anything else that would block a complete implementation.

---

## Design Principles

- **No Daydream Dictation awareness required.** Do not assume the documents were created through the dictation process. This skill works on any design document in any project folder.
- **TODO document integration.** Look specifically for a TODO file alongside the design document (matching `TODO-*.md`). If found, surface open items as part of question 2. If no TODO file exists, note this and move on.
- **Contextual skipping.** Questions 5 and 6 are domain-specific (controls, string tables). Evaluate whether they apply to the project and skip them with a brief note if they don't, rather than producing empty sections.
- **Standalone output.** The gap analysis produces a self-contained report. Do not modify any documents — only read and report. The user decides what to act on.

## Output Format

For each question, respond with:
- **Finding** — what you found (or "No gaps identified" if clean)
- **Severity** — critical (blocks implementation), moderate (should be addressed), minor (nice to have)
- **Suggestion** — what to do about it

End with a numbered list of all actionable items sorted by severity, and ask the user which ones to tackle.
