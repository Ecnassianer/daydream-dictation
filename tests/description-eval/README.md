# dd-teach Description Eval

Trigger evaluation for the `dd-teach` skill description. Tests whether realistic user queries cause Claude to invoke the skill at the expected rate, while leaving alone the queries that should be handled some other way.

## Why this lives here, not in skill-creator

`skill-creator`'s `scripts/run_eval.py` works by writing a temporary slash command into `.claude/commands/` and watching for Claude to invoke it. If the real `daydream-dictation:dd-teach` plugin skill is also installed in the same environment, Claude routes the trigger to the real skill instead of the temp command, and the eval reports false-negative 0-hits. To get an honest signal you need to run this in an environment where dd-teach is **not** installed as a plugin.

## What's here

- `run_eval.py` — vendored copy of skill-creator's evaluator, with `parse_skill_md` inlined so it's a single file
- `trigger-eval.json` — 21 realistic queries (10 should-trigger, 11 should-not), tuned for the target audience: writers, designers, PMs, grant writers, policy folks, civil servants
- `README.md` — this file

## How to run

In a Claude Code environment where `dd-teach` is **not** installed (a fresh cloud workspace, a clean Claude Code session on another machine, etc.):

1. Clone or upload this folder somewhere accessible
2. Put a copy of the `dd-teach` skill directory somewhere accessible too — you'll point the eval at it via `--skill-path`. The skill needs at minimum its `SKILL.md` (the eval reads the description from frontmatter unless you override).
3. Run:

```bash
python run_eval.py \
  --skill-path /path/to/dd-teach \
  --runs-per-query 3 \
  --num-workers 10 \
  --verbose
```

Output: per-query pass/fail printed to stderr, full JSON results to stdout. Redirect stdout to a file if you want to keep it.

### Override the description without editing SKILL.md

Pass `--description "..."` to test a candidate description without modifying the skill file:

```bash
python run_eval.py \
  --skill-path /path/to/dd-teach \
  --description "Use this skill whenever the user mentions ..." \
  --verbose
```

This is the fast way to A/B candidate descriptions during optimization.

## What "pass" means

Each query has a `should_trigger` flag. The eval runs the query through `claude -p` `runs-per-query` times and computes the trigger rate. Pass = trigger rate matches the expectation (above the threshold for `should_trigger: true`, below for `false`). Default threshold is 0.5.

## Interpreting results

- All should-trigger fail with 0/N triggers → the description isn't reaching Claude's "use a skill" decision point. Make it pushier (the skill-creator guide recommends explicit "use this skill any time..." phrasing).
- All should-not-trigger pass with 0/N → the description isn't pulling on adjacent topics. Good signal, but check that the should-trigger ones are firing too — otherwise the skill is just inert.
- Mixed → look at the specific failing queries. They tell you what shape of language the description doesn't catch.

## Updating the eval set

Edit `trigger-eval.json` directly. Each entry is `{"query": "...", "should_trigger": true|false}`. Keep queries realistic — full sentences with personal context, casual phrasing, the kind of thing a real user types. The skill-creator guide has good advice on writing eval queries.
