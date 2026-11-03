#!/usr/bin/env python3
"""Set or check the plugin version everywhere it appears.

    python3 tools/bump_version.py 0.6.0   # set every version field to 0.6.0
    python3 tools/bump_version.py --check # fail if the fields disagree

The version lives in:
  - .claude-plugin/plugin.json            "version"
  - .claude-plugin/marketplace.json       plugins[daydream-dictation].version
  - skills/*/SKILL.md                     metadata.version in the frontmatter
  - README.md                             the example release tag (--branch v<version>)

The Release workflow runs --check, then tags v<version> on main.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

# (path, pattern) pairs. Each pattern's group 2 is the version.
PLUGIN = (".claude-plugin/plugin.json", re.compile(r'^(  "version": ")([^"]+)(")', re.M))
MARKETPLACE = (".claude-plugin/marketplace.json", re.compile(r'^(      "version": ")([^"]+)(")', re.M))
SKILL = re.compile(r'^(  version: ")([^"]+)(")', re.M)
README = ("README.md", re.compile(r"(--branch v)(\d+\.\d+\.\d+)(`)"))


def targets():
    yield PLUGIN
    yield MARKETPLACE
    for path in sorted(glob.glob(os.path.join(ROOT, "skills", "*", "SKILL.md"))):
        yield os.path.relpath(path, ROOT), SKILL
    yield README


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def found_versions():
    """Map each file to the version(s) found in it."""
    result = {}
    for rel, pattern in targets():
        matches = [m.group(2) for m in pattern.finditer(read(rel))]
        if len(matches) != 1:
            sys.exit(f"{rel}: expected one version field, found {len(matches)}")
        result[rel] = matches[0]
    # marketplace.json may list other plugins; make sure ours is the one matched.
    data = json.loads(read(MARKETPLACE[0]))
    ours = [p["version"] for p in data["plugins"] if p["name"] == "daydream-dictation"]
    if ours != [result[MARKETPLACE[0]]]:
        sys.exit(f"{MARKETPLACE[0]}: could not find the daydream-dictation version")
    return result


def check():
    versions = found_versions()
    expected = versions[PLUGIN[0]]
    wrong = {rel: v for rel, v in versions.items() if v != expected}
    if wrong:
        for rel, v in wrong.items():
            print(f"{rel}: {v} (plugin.json is {expected})", file=sys.stderr)
        print("Run: python3 tools/bump_version.py " + expected, file=sys.stderr)
        sys.exit(1)
    print(expected)


def bump(new):
    if not SEMVER.match(new):
        sys.exit(f"Not a MAJOR.MINOR.PATCH version: {new}")
    for rel, pattern in targets():
        text = read(rel)
        updated, count = pattern.subn(lambda m: m.group(1) + new + m.group(3), text)
        if count != 1:
            sys.exit(f"{rel}: expected one version field, found {count}")
        with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as f:
            f.write(updated)
        print(f"  {rel}")
    check()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--check":
        check()
    else:
        bump(sys.argv[1])
