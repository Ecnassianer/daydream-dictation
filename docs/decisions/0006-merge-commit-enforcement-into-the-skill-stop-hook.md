---
status: accepted
date: 2026-10-31
decision-makers: Ecnassianer
---

# Merge commit enforcement into the skill's Stop hook, and commit backfilled prompts per the skill's commit discipline

## Context and Problem Statement

`hooks/dd_stop_hook.py` is registered plugin-wide. In any repo, it blocks Claude from stopping while there are uncommitted changes, untracked files or unpushed commits. That's the same "machinery outside dictation sessions" problem as prompt logging, only more intrusive.

The session-start and resume backfill ([ADR-0005](0005-recover-prompts-after-a-resumed-session.md)) also creates a new situation. When the backfill runs in `Stop`, it writes Prompts entries after Claude's last commit of the turn. Those entries must still be committed according to the skill's commit discipline: commit after every set of changes, push immediately, and keep prompt entries with the work they accompany. Claude doesn't get involved in that decision.

The plugin supports Git, Mercurial, Perforce and Unity VCS / Plastic through `dd_lib.detect_vcs()`, plus a `custom` mode where Claude manages commits.

## Decision Drivers

* No commit enforcement outside dictation sessions.
* No race between two `Stop` hooks (hooks for the same event run in parallel).
* Backfilled entries are committed and pushed per the commit discipline, and folded into Claude's own commit when that's safe.
* Never rewrite history that has already been pushed.
* Keep supporting every VCS the plugin supports today, accepting lower fidelity outside Git.

## Considered Options

* Keep `dd_stop_hook.py` plugin-wide, add a separate skill `Stop` hook for backfill
* One skill-scoped `Stop` hook that does backfill, commit, then the cleanliness check

## Decision Outcome

Chosen option: **one skill-scoped `Stop` hook**, registered in the `daydream-dictation` SKILL.md frontmatter ([ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md)). It runs these steps in order:

1. **Backfill** if a session-start or resume marker exists and a project is set ([ADR-0005](0005-recover-prompts-after-a-resumed-session.md)).
2. **Commit the backfilled entries**, chosen deterministically from VCS state:

   | Situation | Action |
   | --- | --- |
   | Git, `HEAD` was committed before the first backfilled prompt was sent | Own commit ("Log session-start prompt" or "Backfill N prompt(s) after resume") and push |
   | Git, `HEAD` was committed after the first backfilled prompt and isn't on any remote branch | `git commit --amend --no-edit --only <Prompts doc>`, then push |
   | Git, `HEAD` was committed after the first backfilled prompt but Claude already pushed it | Own commit and push; never amend a pushed commit |

   "After the first backfilled prompt" compares `HEAD`'s committer time with that prompt's timestamp in the transcript. It works the same for both marker kinds, including a session-start marker created after Claude's first commit.
   | Mercurial, Perforce, Unity VCS | Own commit and push through the existing `dd_lib.checkpoint()` |
   | `custom` / no VCS | Write the entries, don't commit; the skill's guidance covers it |

   If the commit or push fails, the hook carries on to step 3, which asks Claude to fix it.
3. **Cleanliness check**, using the existing per-VCS checks (`check_git`, `check_hg`, `check_perforce`, `check_unity_vcs`). It blocks with exit code 2 as today, and still returns early when `stop_hook_active` is set.

The skill's `StopFailure` hook runs steps 1 and 2 only. A failed turn can't be blocked.

`dd_stop_hook.py` is removed from `hooks/hooks.json`.

### Consequences

* Good, because sessions that don't use Daydream Dictation are never blocked for uncommitted work.
* Good, because backfill, commit and check run in one process in a fixed order, so there's no race.
* Good, because on Git the backfill usually disappears into Claude's own commit when Claude hasn't pushed yet, and history stays tidy.
* Good, because every supported VCS keeps working through code that already exists.
* Bad, because commit enforcement only applies while the skill is active. It is off between a resume and re-invocation, and after `/clear`.
* Bad, because outside Git the backfill always makes its own commit, so history is slightly noisier there.
* Bad, because the skill's commit discipline has Claude push right after committing, so the amend case will be the less common one in practice.
* Neutral, because the check still covers the whole repo, not only dictation files. That's unchanged and fine for dictation repos.
* Neutral, because the Mercurial, Perforce and Unity VCS paths are only covered by mocked tests, as today.

### Confirmation

* Integration tests with a local bare remote cover each Git row of the table (unchanged `HEAD`, unpushed commit amended, pushed commit left alone), plus the existing cleanliness-check tests moved to the merged hook.
* Unit tests check that non-Git backends go through `dd_lib.checkpoint()`.

## Pros and Cons of the Options

### Keep `dd_stop_hook.py` plugin-wide, separate backfill hook

* Good, because it doesn't change today's enforcement.
* Bad, because it keeps blocking unrelated sessions in every repo.
* Bad, because two parallel `Stop` hooks race: the check can run before or after the backfill writes, which causes flaky blocks or an extra commit round-trip.

### One skill-scoped `Stop` hook

* Good, for the reasons in *Consequences*.
* Bad, because enforcement depends on the skill being active.

## More Information

* Mercurial could also amend safely while the commit is still in draft phase (`hg commit --amend`). We chose not to add that for now. Perforce submits can't be amended.
* Related: [#38](https://github.com/Ecnassianer/daydream-dictation/issues/38) (auto-commit the prompt log), [ADR-0002](0002-scope-dictation-hooks-to-the-active-skill.md), [ADR-0005](0005-recover-prompts-after-a-resumed-session.md).
