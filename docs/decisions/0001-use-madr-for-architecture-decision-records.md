---
status: accepted
date: 2026-10-29
decision-makers: Ecnassianer
---

# Use MADR for architecture decision records

## Context and Problem Statement

Daydream Dictation has grown from a single skill into a plugin with several skills, hooks, helper scripts, multiple install paths (CLI, Desktop, Cloud), and support for several version control systems. Along the way we have made decisions and compromises — for example, how Cloud users install without the plugin system, or which VCSs get first-class support — whose reasoning currently lives only in PR threads and people's heads.

We want a lightweight, repeatable way to record significant decisions about the plugin itself so that future contributors (human or agent) can understand *why* things are the way they are and what trade-offs were accepted. Which decision-record process and format should we use?

## Decision Drivers

* **Low ceremony.** This is a small project; writing a record should take minutes, not hours.
* **Captures compromises.** We specifically want to record the options we rejected and the downsides we accepted, not just the final answer.
* **Lives in the repo and is reviewed in PRs**, alongside the code it explains.
* **Readable by agents.** Much of the work here is done with Claude Code, so records should be plain Markdown with a predictable structure that an agent can find, read, and write.
* **No required tooling.** Contributors shouldn't need to install anything to read or write a record.
* **Well-known format**, so new contributors may already be familiar with it and there's external documentation to point to.

## Considered Options

* MADR (Markdown Architectural Decision Records)
* Nygard-style ADRs (the original Context / Decision / Status / Consequences format)
* Y-statements
* Reuse the plugin's own `DecisionTrace` document format
* Keep decisions in PR descriptions and issues only (status quo)

## Decision Outcome

Chosen option: **MADR**, because it is the only option that is both lightweight and explicitly structured around *considered options and their pros and cons*, which is exactly the "compromises we made" information we want to preserve. It is plain Markdown, needs no tooling, has a stable current version (MADR 4.0.0, September 2024), and is one of the best-known ADR formats.

We adopt it as follows (details in [`README.md`](README.md)):

* Records live in `docs/decisions/`, named `NNNN-title-in-kebab-case.md`, starting from the [`adr-template.md`](adr-template.md) in that folder (based on the MADR 4.0.0 template, trimmed and annotated for this project; we dropped MADR's optional `consulted` and `informed` front-matter fields).
* Status, date, and decision-makers go in YAML front matter.
* ADRs are proposed and discussed via pull requests, ideally in the same PR as the change they describe.
* Accepted ADRs are immutable; changed decisions are recorded by a new ADR that supersedes the old one.
* An index of all ADRs is kept in `docs/decisions/README.md`.

### Consequences

* Good, because the reasoning behind significant decisions, including rejected alternatives, is preserved in the repo next to the code.
* Good, because reviewers can discuss a decision in the same PR as its implementation.
* Good, because the predictable file layout and headings make it easy for Claude Code to find and follow past decisions, or draft new ADRs.
* Neutral, because the MADR template has more sections than Nygard's; we mitigate this by marking optional sections and encouraging authors to delete them.
* Bad, because it adds a small amount of process: contributors must judge when a decision is "significant" and remember to write an ADR and update the index by hand.
* Bad, because the index in `README.md` is maintained manually and can drift from the files in the folder. We accept this rather than add tooling (see *More Information*).

### Confirmation

Reviewers check that PRs making a significant decision (see "When to write an ADR" in `README.md`) include a new or updated ADR, and that the index is updated.

## Pros and Cons of the Options

### MADR

[adr.github.io/madr](https://adr.github.io/madr/)

* Good, because its *Considered Options* and *Pros and Cons of the Options* sections directly capture trade-offs and compromises.
* Good, because it is plain Markdown with optional YAML front matter; no tooling required.
* Good, because it is well documented and widely used, with a stable release (4.0.0, September 2024) and an active GitHub project.
* Good, because sections are explicitly optional, so short decisions can stay short.
* Neutral, because it ships tooling-friendly conventions (YAML front matter, the `docs/decisions/` folder it has recommended since MADR 3.0) that tools such as Log4brains already understand.
* Bad, because the full template is longer than Nygard's and can feel heavyweight for small decisions.

### Nygard-style ADRs

[Michael Nygard, *Documenting Architecture Decisions* (2011)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

* Good, because it is the original and most widely recognized ADR format.
* Good, because it is extremely short: Title, Status, Context, Decision, Consequences.
* Good, because tools like `adr-tools` use it as their default template.
* Bad, because it has no dedicated place for alternatives considered; rejected options end up buried in the Context prose or omitted, which works against our main goal of recording compromises.

### Y-statements

A format created by Olaf Zimmermann: a single structured sentence, "In the context of *use case*, facing *concern*, we decided for *option* and neglected *other options*, to achieve *quality*, accepting *downside*."

* Good, because it is the most concise format and forces the author to name the accepted downside.
* Bad, because one sentence leaves little room for context, multiple options, or nuanced pros and cons.
* Bad, because it is less familiar to most contributors than Nygard or MADR.

### Reuse the plugin's own `DecisionTrace` format

The `DecisionTrace-<Slug>.md` companion document that Daydream Dictation creates for user projects: one evolving file with dated entries under topical sections.

* Good, because it dogfoods our own product.
* Good, because it already asks for options not chosen and why.
* Bad, because it is a single mutable document that is expected to be rewritten as requirements change; it does not preserve an immutable history of *when* and *why* a decision was replaced.
* Bad, because it is designed for implementing a user's Daydream design doc, not for maintaining a codebase, and mixing the two purposes would blur the plugin's own guidance.
* Bad, because it has no standard status lifecycle or numbering that other tools and contributors recognize.

### Keep decisions in PR descriptions and issues only (status quo)

* Good, because it requires no new process.
* Bad, because the reasoning is scattered across GitHub, hard to search, and not available offline or to agents working from a clone.
* Bad, because there is no single place to see which decisions are current and which were superseded.

## More Information

* [adr.github.io](https://adr.github.io/) — overview of ADRs, templates, and tooling.
* [MADR project and template](https://github.com/adr/madr).
* The [architecture-decision-record](https://github.com/architecture-decision-record/architecture-decision-record) collection of templates and examples, started by Joel Parker Henderson.
* Tooling we chose *not* to adopt for now: [`adr-tools`](https://github.com/npryce/adr-tools) (shell CLI for Nygard-style records, default folder `doc/adr`) and [Log4brains](https://github.com/thomvaill/log4brains) (CLI and static-site generator whose default template is MADR). Revisit if the number of ADRs grows enough that maintaining the index by hand becomes a burden.
