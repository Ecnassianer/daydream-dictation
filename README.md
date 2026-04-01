# Daydream Dictation

A Claude Code plugin for voice-driven document authoring. Talk out loud about your ideas and let Claude organize them into well-structured design documents.

## How It Works

Daydream Dictation uses a three-phase workflow:

1. **Structured Daydreaming** -- Talk freely about your idea for 20-60 minutes. Don't edit, don't review. Claude captures and organizes everything as you speak.
2. **Response & Engagement** -- Read through Claude's responses, answer questions, fill gaps. Run a gap analysis to check completeness.
3. **Diff Review** -- Review the pull request diff, leave feedback, and merge when satisfied.

Use `/dd-teach` to learn the process interactively, tailored to your experience level.

## Installation

### Prerequisites

- [Claude Code](https://claude.ai/code) (CLI, desktop app, or IDE extension)
- Python 3.9+
- Git (or another supported VCS)

### Install the plugin

```bash
claude plugin add Ecnassianer/daydream-dictation
```

## Usage

### Start a session

```
/daydream-dictation "My Project Name"
```

Or use the alias `/dictate-daydream`.

This creates the project folder and files if they don't exist, sets it as the active project, and begins the session.

### Run a gap analysis

```
/dd-gap-analysis
```

Analyzes the current project's documents for missing coverage, open TODOs, and implementation gaps.

### Learn the process

```
/dd-teach
```

Interactive onboarding that explains the three phases, voice dictation tips, and version control for the review cycle.

## Project Structure

Each project gets a folder with three documents:

- `Daydream-<Slug>.md` -- The main design document
- `TODO-<Slug>.md` -- Outstanding work items
- `Prompts-<Slug>.md` -- Verbatim log of every voice prompt

Optional companion documents (`TechDesign-`, `StringTable-`, `DebugTools-`) can be added as a project grows.

## Hooks

The plugin includes two hooks that fire automatically:

- **UserPromptSubmit** -- Logs every prompt to the active project's Prompts document
- **Stop** -- Checks for uncommitted or unpushed changes before Claude stops responding

## Supported VCS

- Git (first-class, default)
- Mercurial
- Perforce
- Unity VCS / Plastic SCM

Override auto-detection by creating `.claude/dd-vcs` with the VCS name.

## Voice Variants

Create `.claude/dd-voice-variants.md` in your repo to list words your dictation software commonly confuses. See `skills/daydream-dictation/example-voice-variants.md` for the format.

## License

MIT
