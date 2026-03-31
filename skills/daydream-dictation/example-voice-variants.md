# Voice Dictation Variants — Example Template

This file shows the format for listing words your voice dictation software commonly confuses. Create your own file at `.claude/dd-voice-variants.md` in your repository root. The agent will check it during dictation sessions and silently substitute the correct word when it sees a listed variant.

## Format

Each section has a heading with the correct word/phrase, followed by a list of common mis-transcriptions:

```markdown
# Voice Dictation Variants — "Correct Phrase"

The user's voice dictation software frequently misspells "Correct Phrase". When any of these appear in a prompt, treat them as "Correct Phrase":

- Misspelling One
- Misspelling Two
- Misspelling Three
```

## Example

```markdown
# Voice Dictation Variants — "Kubernetes"

- Cooper Netties
- Kuber Netties
- Cooper net ease
- Cube er net ease
```

Add your own entries based on words your dictation software consistently gets wrong. The more specific the list, the better Claude can clean up your transcriptions.
