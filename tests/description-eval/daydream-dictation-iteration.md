# Description optimization — `daydream-dictation` skill

Iterate the `description:` field in `skills/daydream-dictation/SKILL.md` until the eval at `trigger-eval-daydream-dictation.json` passes well.

## Setup (do this first)

1. Confirm the `daydream-dictation` plugin is installed in this environment (`/plugin` should list it). If it isn't, install it from this branch's fork — the harness has a known shadowing bug (see `README.md`) that produces silent 0/N false negatives when the real plugin isn't present to anchor matching.
2. `cd tests/description-eval`
3. Sanity check: `python run_eval.py --help`

## Run the eval

```
python run_eval.py \
  --skill-path ../../skills/daydream-dictation \
  --description "<candidate description>" \
  --eval-set trigger-eval-daydream-dictation.json \
  --num-workers 1
```

**Use `--num-workers 1`.** Parallel workers collide on the temp slash command directory and produce false negatives (second known harness bug, also documented in README).

## Current description (baseline — measure this first)

> Voice-driven document authoring using the Daydream Dictation workflow. Activates when the user is dictating design documents, mentions a Daydream project, refers to Prompts documents or dd-current-dictation-project, or starts a dictation session.

## Candidate starting points

Pick one to seed iteration. Don't treat these as final — rewrite freely to hit the eval.

**A — tighter, action-focused**
> Use when the user is starting or resuming a Daydream Dictation session, dictating into a Daydream project, or referencing a Prompts document, `Daydream-` folder, or `dd-current-dictation-project` state. Do not trigger for plugin install, hook debugging, voice-app questions, or generic document feedback.

**B — jargon-forward**
> Daydream Dictation session behavior. Activates on session-start phrases ("start dictation", "dd <ProjectName>"), references to Prompts documents or `Daydream-` project folders, or any utterance naming an active dictation project. Excludes plugin install, hook debugging, and unrelated voice-tool questions.

**C — close to current, scoped**
> Voice or typed authoring inside the Daydream Dictation workflow. Activates when the user is in or starting a dictation session, references a Daydream project by name, or mentions Prompts documents / `dd-current-dictation-project`. Does not handle plugin install, hook errors, or general voice-dictation tooling questions.

## What "passing well" means

The 12 queries split:
- **7 should-trigger** — mostly DD-shorthand ("dd OldFriend", "start dictation", "switch dd to X") plus one where the user says "daydream" as a verb
- **5 should-not-trigger** — install, tooling, hook debug, git op, generic editing without DD context

Aim for ≥6/7 on should-trigger and ≥4/5 on should-not. If a query keeps misfiring, look at the description text and ask whether a real user's wording would actually match it; the description is the only thing the model sees when deciding.

## When you have a winner

1. Edit `skills/daydream-dictation/SKILL.md` — replace the `description:` line with the winner.
2. Commit with the eval results in the message (e.g. "8/8 trigger, 5/5 no-trigger over N runs").
3. Push to this branch (`feat/daydream-dictation-description-eval`).

## Notes

- The eval JSON intentionally lets a few should-not queries that look DD-adjacent (teaching questions, gap-analysis prompts) live elsewhere in the suite — those route to other skills (`dd-teach`, `dd-gap-analysis`) and are not this skill's job.
- Don't worry about `dd-teach`'s description; it's been optimized separately (PR #39) and shouldn't change here.
