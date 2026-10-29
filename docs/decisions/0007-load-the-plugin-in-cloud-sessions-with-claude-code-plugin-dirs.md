---
status: proposed
date: 2026-10-29
decision-makers: Ecnassianer
---

# Load the plugin in cloud sessions with CLAUDE_CODE_PLUGIN_DIRS

## Context and Problem Statement

The README's "Method 3" install for Claude Code cloud sessions (claude.ai/code) was written when cloud sessions couldn't load plugins. It clones the plugin into the user's repo, wires the hook scripts into `.claude/settings.json` by hand, and lists the skills in `CLAUDE.md` so Claude reads each `SKILL.md` by path. It is hacky: every repo carries its own copy of the plugin, and updating that copy is a manual, undocumented chore.

The workaround also stops working under [ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md). Reading a `SKILL.md` by path never *invokes* the skill, so its frontmatter hooks are never registered. Cloud sessions need a way to load the plugin as a real plugin. What has changed in cloud sessions since Method 3 was written, and what should replace it?

## Decision Drivers

* Cloud sessions should behave the same as local plugin installs: same skill names, same hooks, same `${CLAUDE_PLUGIN_ROOT}`.
* No copy of the plugin committed into each user repo.
* Updating should be simple and predictable.
* Use documented Claude Code behavior.

## Considered Options

* Keep Method 3 (clone into the repo, hooks in `.claude/settings.json`, skills referenced from `CLAUDE.md`)
* Turn the plugin on in the repo's `.claude/settings.json` (`enabledPlugins` / `extraKnownMarketplaces`)
* Commit the whole plugin under the repo's `.claude/skills/` (a skills-directory plugin)
* Turn the plugin on for the user's claude.ai account (synced plugins)
* Clone the plugin in the cloud environment's setup script and load it with `CLAUDE_CODE_PLUGIN_DIRS`

## Decision Outcome

Chosen option: **clone the plugin in the cloud environment's setup script and load it with `CLAUDE_CODE_PLUGIN_DIRS`**, because it is the only option we have seen load the full plugin, hooks included, without committing the plugin into each repo.

The user configures their cloud environment once, in the environment settings on claude.ai:

* **Setup script:**
  ```bash
  git clone --depth 1 https://github.com/Ecnassianer/daydream-dictation.git /opt/daydream-dictation || true
  ```
  Add `--branch <tag>` to pin a release.
* **Environment variable:** `CLAUDE_CODE_PLUGIN_DIRS=/opt/daydream-dictation`

The plugin then loads as `daydream-dictation@inline` in every cloud session that uses that environment, whatever the repo. Method 3 is removed from the README, and so are the in-repo copy, the `settings.json` hook wiring and the `CLAUDE.md` skill pointers.

Verified with Claude Code 2.1.312 inside a cloud session's VM, by running `claude -p` with the variable set. The plugin's `hooks/hooks.json` hook and a skill's frontmatter hook both fired, and `CLAUDE_PLUGIN_ROOT` pointed at the plugin root for both. This hasn't yet been verified end to end in a new cloud session started from the app with the environment configured.

### Consequences

* Good, because cloud sessions get the real plugin: `/daydream-dictation:daydream-dictation`, the resume hook from `hooks.json`, and skill-scoped hooks.
* Good, because `${CLAUDE_PLUGIN_ROOT}` always means the plugin root. If this and the marketplace install are the only supported installs, the hook commands from [ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md) don't need to handle project-skill installs, where the variable points at the skill folder.
* Good, because user repos no longer carry a copy of the plugin.
* Bad, because the cloud environment caches the setup script's result. A new plugin version arrives only when the cache rebuilds (about every 7 days, or when the script or allowed hosts change). Pinning a tag makes this predictable; bumping the tag in the script is the update step.
* Bad, because it is per-environment setup the user does by hand on claude.ai; it can't be shipped in the repo.
* Bad, because the environment needs network access to github.com. The default **Trusted** level allows it.
* Neutral, because cloud threads in a claude.ai project may load configuration differently. Check this before documenting it for projects.

### Confirmation

* Before accepting this ADR: start a fresh cloud session from the app in an environment configured as above. Check that `/daydream-dictation:daydream-dictation` is listed, that its hooks fire, and that the resume hook runs after the session is reopened.
* The README's cloud install section describes only this method.

## Pros and Cons of the Options

### Keep Method 3

* Good, because it works today for loading skill text.
* Bad, because skill frontmatter hooks never register, which breaks the [ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md) design.
* Bad, because each repo holds a copy of the plugin that must be updated by hand.

### Turn the plugin on in the repo's `.claude/settings.json`

* Good, because it is the standard way to share a plugin with a team.
* Bad, because cloud sessions don't install plugins declared under `enabledPlugins`, or marketplaces listed under `extraKnownMarketplaces`. Those need the workspace trust dialog, which cloud sessions never show (documented in "What carries over from your setup").

### Commit the plugin under the repo's `.claude/skills/`

* Good, because repo `.claude/skills/` content is part of the clone and loads in cloud sessions.
* Bad, because a skills-directory plugin from a repo loads only after workspace trust. In a `claude -p` test in a cloud VM it didn't load.
* Bad, because every repo still carries a copy of the plugin.

### Synced plugins from the claude.ai account

* Good, because one switch on claude.ai would cover every surface: terminal, Cowork, and possibly cloud sessions.
* Neutral, because the docs only promise synced plugins in Cowork and terminal sessions. Cloud sessions have the sync machinery enabled (`CLAUDE_CODE_SYNC_PLUGINS=1`, `~/.claude/plugins/synced/`) but this is unverified.
* Bad, because skills *uploaded* to claude.ai reject a `hooks` frontmatter key. Whether a whole plugin with skill hooks and `hooks.json` can be added to an account, and whether its hooks run in cloud sessions, needs testing.
* Revisit: if synced plugins are confirmed to run hooks in cloud sessions, this becomes the better option, because it needs no per-environment setup.

### Setup script plus `CLAUDE_CODE_PLUGIN_DIRS`

* Good, because it is the only option seen loading the complete plugin.
* Bad, because of the caching and per-environment setup costs above.

## More Information

* Claude Code docs: [Configure cloud environments](https://code.claude.com/docs/en/cloud-environments) (setup scripts, environment caching, what carries over), [Plugin loading reference](https://code.claude.com/docs/en/plugins/loading) (`@inline`, `CLAUDE_CODE_PLUGIN_DIRS`, synced plugins, skills-directory plugins).
* Related: [ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md), [ADR-0005](0005-recover-prompts-after-a-resumed-session.md).
* The Metadiscussion review found a request to document manual updates for the Method 3 install. This ADR replaces that need with "bump the tag in the setup script".
