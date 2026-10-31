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

- Python 3.9+
- Git (or another supported VCS)
- Claude Code 2.1.94 or later (earlier versions silently ignore hooks in a plugin skill's frontmatter)

There are three installation methods depending on how you run Claude Code.

---

### Method 1 — Claude Code CLI

Run these commands inside Claude Code:

```shell
/plugin marketplace add ecnassianer/daydream-dictation
/plugin install daydream-dictation@daydream-dictation
/reload-plugins
```

---

### Method 2 — Claude Code Desktop (local or SSH sessions)

The Desktop app supports plugins for local and SSH sessions (not remote sessions).

1. Click **Customize** in the left sidebar.
2. Next to **Personal plugins**, click the **+** button, then select **Create plugin > Add marketplace**.
3. In the **Add marketplace** dialog, enter `ecnassianer/daydream-dictation` and click **Sync**.
4. Click **+** next to Personal plugins again, then select **Browse plugins**.
5. Open the **Personal** tab, find the **Daydream Dictation** tile, and click **+** to install it.

---

### Method 3 — Claude Code cloud sessions (claude.ai/code)

Cloud sessions don't install plugins from a marketplace, but they load a plugin directory named in `CLAUDE_CODE_PLUGIN_DIRS`. Configure your cloud environment once, in its settings on claude.ai, and every cloud session that uses that environment gets the full plugin, whatever the repo ([ADR-0007](docs/decisions/0007-load-the-plugin-in-cloud-sessions-with-claude-code-plugin-dirs.md)).

**Setup script:**

```bash
git clone --depth 1 https://github.com/Ecnassianer/daydream-dictation.git /opt/daydream-dictation || true
```

**Environment variable:**

```text
CLAUDE_CODE_PLUGIN_DIRS=/opt/daydream-dictation
```

The environment needs network access to github.com; the default **Trusted** level allows it.

**Updating:** cloud environments cache the setup script's result for about a week, so new plugin versions arrive when that cache rebuilds. To control the version, clone a release tag (`--branch v0.3.0`) and change the tag to update.

**Upgrading from the old manual install:** earlier versions of this README had cloud users clone the plugin into their repo, wire its hooks into `.claude/settings.json`, and list the skills in `CLAUDE.md`. That setup no longer works, because the dictation hooks are registered only when the skill is actually invoked. Remove the cloned folder, the Daydream Dictation hook entries in `.claude/settings.json`, and the skill list in `CLAUDE.md`, then configure the environment as above.

---

### Let Claude start the skill on its own

The `daydream-dictation` skill registers hooks, so Claude Code asks for permission before Claude invokes it by itself (typing `/daydream-dictation` yourself never asks). After a resumed session, Claude needs to re-invoke the skill to restore prompt logging, so allow it in your settings:

```json
{
  "permissions": {
    "allow": ["Skill(daydream-dictation:daydream-dictation)"]
  }
}
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

Optional companion documents (`DecisionTrace-`, `StringTable-`, `DebugTools-`) can be added as a project grows.

Project-specific instructions (for example, localization rules) go in an `AGENTS.md` in the project folder, which most coding agents read. Next to it, keep a short `CLAUDE.md` that points at it, so older versions of Claude Code load the same instructions:

```markdown
See the AGENTS.md file for further instructions.

@AGENTS.md
```

The `@AGENTS.md` line makes Claude Code import the file rather than just mention it. The `CLAUDE.md` pointer is planned for removal around October 2027 ([ADR-0008](docs/decisions/0008-use-agents-md-for-per-project-instructions.md)).

## Hooks

The dictation hooks run only while the `daydream-dictation` skill is active: from the moment it's invoked until `/clear` or the end of the session. Sessions that never use the skill run none of them ([ADR-0002](docs/decisions/0002-scope-dictation-hooks-to-the-active-skill.md)).

- **UserPromptSubmit** -- Logs each prompt to the active project's Prompts document. With no active project, nothing is logged.
- **Stop** -- Logs the prompt that started the session, commits it, and checks for uncommitted or unpushed changes before Claude stops responding.
- **StopFailure** -- Makes sure the session-start or resume backfill still happens when a turn ends with an API error.

One hook is always registered: a **SessionStart** hook that runs only when a session is resumed or continued. If the session was a dictation session, it notes the resume in the Prompts document and asks Claude to re-invoke the skill; the prompts sent in between are backfilled automatically ([ADR-0005](docs/decisions/0005-recover-prompts-after-a-resumed-session.md)).

## Supported VCS

- Git (first-class, default)
- Mercurial
- Perforce
- Unity VCS / Plastic SCM

Override auto-detection by creating `.agents/dd-vcs` with the VCS name.

## Voice Variants

Create `.agents/dd-voice-variants.md` in your repo to list words your dictation software commonly confuses. See `skills/daydream-dictation/references/example-voice-variants.md` for the format.

## Config files

Daydream Dictation's repo-level settings live in `.agents/` at the repo root, a folder that any coding agent can use:

| File | Purpose |
| --- | --- |
| `.agents/dd-vcs` | Override VCS auto-detection |
| `.agents/dd-projects-root` | Create new project folders under this absolute path instead of the repo root |
| `.agents/dd-voice-variants.md` | Words your dictation software commonly confuses |

Earlier versions kept these files in `.claude/`. That location is still read when there's no `.agents/` copy, until about October 2027 ([ADR-0009](docs/decisions/0009-move-config-and-state-out-of-the-claude-folder.md)). To migrate, move the files: `mkdir -p .agents && mv .claude/dd-* .agents/` (use `git mv` for any that are committed).

The hooks keep per-session state outside the repo, in `$XDG_STATE_HOME/daydream-dictation/sessions/` (by default `~/.local/state/daydream-dictation/sessions/`). Set `DD_STATE_DIR` to use a different folder.

## Contributing

Significant design decisions about the plugin are recorded as Architecture Decision Records in [`docs/decisions/`](docs/decisions/README.md). Read that folder's README before proposing a change that affects how the plugin works, and add an ADR when you make a decision worth remembering.

Run the tests with:

```shell
pip install pytest
python3 -m pytest tests/ -v
```

## License

MIT
