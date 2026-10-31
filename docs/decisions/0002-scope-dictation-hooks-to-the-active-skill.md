---
status: accepted
date: 2026-10-31
decision-makers: Ecnassianer
---

# Scope dictation hooks to the active daydream-dictation skill

## Context and Problem Statement

The plugin registers its `UserPromptSubmit` (prompt logging) and `Stop` (commit enforcement) hooks in `hooks/hooks.json`. Plugin hooks run whenever the plugin is enabled, so they fire in every session in every repo, whether or not the user is dictating. In practice this logs unrelated prompts to `Prompts-ddMetadiscussion` and blocks Claude from stopping until unrelated work is committed and pushed ([#40](https://github.com/Ecnassianer/daydream-dictation/issues/40), [#42](https://github.com/Ecnassianer/daydream-dictation/issues/42)).

A major goal of this change is to keep all of the skill's machinery out of sessions that aren't using Daydream Dictation. How do we make the hooks run only while a dictation session is active?

## Decision Drivers

* Nothing should run on prompts or on Stop in sessions that never used Daydream Dictation.
* Logging should turn on when the user starts dictating, not when a project file happens to exist in the repo.
* No prompt in a dictation session should be lost silently.
* No self-modifying settings files or other state that can be left behind and re-enable the hooks everywhere.
* Prefer deterministic mechanisms over relying on Claude to follow an instruction.

## Considered Options

* Keep plugin-wide hooks (status quo)
* Plugin-wide hooks that exit early unless `dd-current-dictation-project` is set ("hybrid")
* Enable the plugin per-repo instead of user-wide
* Register the hooks in the `daydream-dictation` SKILL.md frontmatter (skill-scoped hooks)
* Have a `SessionStart` hook write hooks into `.claude/settings.local.json`

## Decision Outcome

Chosen option: **register the hooks in the `daydream-dictation` SKILL.md frontmatter**, because it is the only option that makes the hooks exist exactly while the skill is in use. Every other option either keeps a hook running in every session or leaves state behind.

The hooks' gaps after a resumed session are handled separately ([ADR-0005](0005-recover-prompts-after-a-resumed-session.md)). The `Stop` hook's commit enforcement moves into the skill too ([ADR-0006](0006-merge-commit-enforcement-into-the-skill-stop-hook.md)).

Behavior we verified with Claude Code 2.1.312 (headless `claude -p`, project and `--plugin-dir` skills):

| Event | Skill-scoped hooks |
| --- | --- |
| Prompts before the skill is invoked | Don't fire |
| The prompt that invokes the skill | `UserPromptSubmit` doesn't fire (hooks register after it's submitted); `Stop` does fire at the end of that turn, and the transcript holds the full prompt, including the text typed after `/daydream-dictation` |
| Later prompts in the same session | Fire every turn |
| Invoking the skill a second time | Hooks are not registered twice |
| `/compact` | Hooks survive |
| `/clear` | Hooks are removed |
| `--resume` / `--continue` | Hooks are gone until the skill is invoked again |
| Exit code 2 from a skill `Stop` hook | Blocks stopping, same as a settings hook; `stop_hook_active` is set on the follow-up |
| `once: true` on a skill hook | Runs once after invocation; a failing run stays registered and retries at the next event. Not used: hooks for the same event run in parallel, so a separate one-shot `Stop` hook would race the main one |

### Consequences

* Good, because sessions that never invoke the skill run none of the dictation hooks.
* Good, because `/clear` ends the dictation hooks, which matches the user's intent: the skill's context is gone too.
* Good, because the hooks travel with the skill definition instead of being wired separately.
* Bad, because the skill must actually be *invoked* (with `/daydream-dictation` or by Claude through the Skill tool). Telling Claude to read `SKILL.md` by path, as the current manual/Cloud install does, never registers the hooks. That install method has to change.
* Bad, because the prompt that invokes the skill misses `UserPromptSubmit`, and so does a resumed session until the skill is invoked again. Both gaps are filled from the transcript; see [ADR-0005](0005-recover-prompts-after-a-resumed-session.md).
* Bad, because a skill that declares hooks needs permission when *Claude* invokes it. In headless tests the Skill call failed with no content until `Skill` was allowed. Typed `/daydream-dictation` works without it. Users who want Claude to invoke the skill on its own (including the resume nudge) should add an allow rule such as `Skill(daydream-dictation:daydream-dictation)`. This behavior isn't documented, so we should re-check it on new Claude Code versions.
* Bad, because skill-scoped hooks are a Claude Code extension. Other agents that read the Agent Skills format ignore unknown frontmatter, so they get no logging and no commit enforcement. Today's `hooks/hooks.json` is Claude Code–only as well, so this doesn't lose anything we had.
* Neutral, because `${CLAUDE_PLUGIN_ROOT}` means different things to a skill hook depending on how the skill is installed: the plugin root for a plugin skill, but the skill's own directory for a project skill. `${CLAUDE_SKILL_DIR}` isn't expanded in hook commands, and `${CLAUDE_PLUGIN_DATA}` is rejected for skill hooks. The hook command must resolve the plugin root itself in both cases, following symlinks.

### Confirmation

* Integration tests cover the hook scripts directly.
* A manual check on each release: in a fresh session, prompts before `/daydream-dictation` aren't logged, prompts after it are, and none are logged after `/clear`.

## Pros and Cons of the Options

### Keep plugin-wide hooks (status quo)

* Good, because it needs no change.
* Bad, because it logs and enforces commits in every session in every repo; this is the bug.

### Plugin-wide hooks gated on `dd-current-dictation-project`

* Good, because it survives resume, compaction and restarts with no extra machinery, and loses no prompts.
* Good, because the check is a single file read.
* Bad, because the hooks are still registered and run a Python process on every prompt and every Stop in every session, even after the skill is long forgotten. This fails the main goal of separating the skill's machinery from unrelated sessions.
* Bad, because "on" means "a project file exists", not "the user is dictating", and `/clear` doesn't turn it off.

### Enable the plugin per-repo

* Good, because it uses existing Claude Code settings (`enabledPlugins` in a repo's `.claude/settings.json`).
* Bad, because it also hides the skills everywhere else, so you can't start a dictation session in a new repo without editing settings first.
* Bad, because inside a dictation repo the hooks are still always on.

### Skill-scoped hooks in SKILL.md frontmatter

* Good, because the hooks exist exactly from invocation until `/clear` or the session ends.
* Good, because they are documented Claude Code behavior: "registers them when you or Claude invoke the skill and keeps running them for the rest of the session".
* Bad, because of the resume, permission, install-method and portability consequences listed above.

### `SessionStart` hook writes hooks into `.claude/settings.local.json`

Tested: Claude Code reloads settings mid-session, so hooks written this way take effect from the next prompt.

* Good, because it can restore logging after a resume without Claude's help.
* Bad, because the entries stay in the file after the session. Every later session in that repo logs prompts again, which brings back the original bug.
* Bad, because cleanup depends on a `SessionEnd` hook that doesn't run if the session crashes or a cloud container is reclaimed.
* Bad, because it rewrites a user-owned settings file and has to merge with existing content and with other sessions in the same repo.
* Rejected by the maintainer as too risky.

## More Information

* Claude Code docs: [Hooks in skills and agents](https://code.claude.com/docs/en/hooks#hooks-in-skills-and-agents), [Skills frontmatter reference](https://code.claude.com/docs/en/skills).
* [anthropics/claude-code#17688](https://github.com/anthropics/claude-code/issues/17688): plugin skill hooks were silently ignored until Claude Code 2.1.94. The plugin needs at least that version.
* [microsoft/vscode#303777](https://github.com/microsoft/vscode/issues/303777): a request for skill-scoped hooks in VS Code/Copilot, closed as not planned (2026-09-17). Revisit portability if another agent adopts skill-scoped hooks.
* The [Agent Skills specification](https://agentskills.io/specification) defines no `hooks` field.
* Related: [ADR-0003](0003-stop-logging-prompts-outside-a-dictation-session.md), [ADR-0004](0004-keep-prompt-logging-on-userpromptsubmit.md), [ADR-0005](0005-recover-prompts-after-a-resumed-session.md), [ADR-0006](0006-merge-commit-enforcement-into-the-skill-stop-hook.md).
