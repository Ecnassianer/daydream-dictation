# Working on the Daydream Dictation plugin

These instructions are for agents changing this repo (the plugin itself), not for agents using the plugin to dictate.

Read [`docs/decisions/README.md`](docs/decisions/README.md) before changing how the plugin works, and add an ADR for decisions worth remembering. Run the tests with `python3 -m pytest tests/ -v` (install `pytest` first if needed).

## Releasing a new version

Installs only update when the version changes, so after changes merge to `main`, they reach users only once someone cuts a release. Do it when the user asks for a release, or asks how to get their merged changes to existing installs.

1. Pick the next version (`MAJOR.MINOR.PATCH`), based on what has merged since the last `v*` tag:
   - **PATCH** for wording, documentation and bug fixes that don't change how the plugin behaves.
   - **MINOR** for new features or changed behavior. While the version is below 1.0, also use MINOR for breaking changes.
   - **MAJOR** only once the plugin is at 1.0 or later and a change breaks existing setups.
2. Run `python3 tools/bump_version.py <version>`. It updates every version field: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `metadata.version` in each `skills/*/SKILL.md`, and the example release tag in `README.md`. Don't edit these fields by hand.
3. Commit, open a pull request and get it merged as usual.
4. When the change reaches `main`, the Release workflow (`.github/workflows/release.yml`) runs `tools/bump_version.py --check`, then creates the `v<version>` tag and a GitHub release with generated notes. Confirm the release exists afterward.

Don't create or push tags yourself. Cloud sessions can't push tags (the push returns HTTP 403), and the workflow already does it. If the workflow fails, read its log: a version mismatch means a field was edited by hand, so rerun the script; a 403 means the repository's Actions settings don't let workflows write (Settings → Actions → General → Workflow permissions), which the user has to change.
