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

### Method 3 — Claude Code Cloud or manual install

Claude.ai/code (remote cloud sessions) does not support the plugin system. Install manually instead.

**Step 1 — Clone the plugin into your repo:**

```bash
git clone https://github.com/Ecnassianer/daydream-dictation.git DaydreamDictationSkill/CompletedSkill
```

**Step 2 — Wire up hooks in `.claude/settings.json`:**

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 DaydreamDictationSkill/CompletedSkill/hooks/dd_log_prompt.py",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 DaydreamDictationSkill/CompletedSkill/hooks/dd_stop_hook.py",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

If you already have other settings in this file, merge the `hooks` key in — don't replace the whole file.

**Step 3 — Reference the skills in `CLAUDE.md`:**

```markdown
## Daydream Dictation Skills (manually installed)

The following skills are available. Read the referenced SKILL.md file when invoked:

- **daydream-dictation** — Main workflow skill. See `DaydreamDictationSkill/CompletedSkill/skills/daydream-dictation/SKILL.md`
- **dd-gap-analysis** — Gap analysis skill. See `DaydreamDictationSkill/CompletedSkill/skills/dd-gap-analysis/SKILL.md`
- **dd-teach** — Interactive onboarding. See `DaydreamDictationSkill/CompletedSkill/skills/dd-teach/SKILL.md`
- **dictate-daydream** — Alias for daydream-dictation. See `DaydreamDictationSkill/CompletedSkill/skills/dictate-daydream/SKILL.md`

When the user invokes any of these skills, read the corresponding SKILL.md and follow its instructions.

## Utility Scripts

- `dd_init_project.py` — Create a new project: `python3 DaydreamDictationSkill/CompletedSkill/scripts/dd_init_project.py "Project Name"`
- `dd_switch_project.py` — Switch active project: `python3 DaydreamDictationSkill/CompletedSkill/scripts/dd_switch_project.py "ProjectSlug"`
```

**Step 4 — Fix tests for cloud environments (optional):**

Cloud environments often have `commit.gpgsign=true` set globally, which causes the integration tests to fail. To fix this, add the following line to both `_make_git_repo()` and `_make_git_repo_with_remote()` in `tests/test_integration.py`, immediately after the `git config user.name` line:

```python
subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=tmpdir, capture_output=True)
```

For `_make_git_repo_with_remote()`, use `cwd=work` instead of `cwd=tmpdir`. Then run:

```shell
cd DaydreamDictationSkill/CompletedSkill
pip install pytest
python3 -m pytest tests/ -v
```

All 75 tests should pass.

**Step 5 — Verify hooks are active:**

After updating `settings.json`, run `/hooks` or start a new session to activate the hooks. To confirm the `UserPromptSubmit` hook is working, type a message and check that it appears in `Prompts-ddMetadiscussion` (or your active project's Prompts file).

**What you get:**

- **Prompt logging** — Every message is automatically appended to the active project's Prompts document
- **Stop guard** — Claude won't stop until all changes are committed and pushed
- **Skills** — `daydream-dictation`, `dd-gap-analysis`, `dd-teach`, and `dictate-daydream` are all available via CLAUDE.md references
- **Project management** — `dd_init_project.py` and `dd_switch_project.py` work identically to the plugin version

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
