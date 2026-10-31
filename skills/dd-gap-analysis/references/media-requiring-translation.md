# Gap Analysis: Media Requiring Translation

Read this file only during a `dd-gap-analysis` run, and only when the project ships text to more than one language: a game, an app, a website, or any other software or media with a string table or localization files.

## What good localization coverage has

- **A list of supported languages.**
- **A string table** (`StringTable-<Slug>.md` or the project's own localization files) with an entry for every player- or user-facing string the design names.
- **A translation for every entry in every supported language**, or a stated decision to defer translation.

## Questions

### Are there untranslated strings?

If the project has a `StringTable-<Slug>.md` or other localization files, check for completeness: are there strings missing translations for any supported language? Are there strings referenced in the design doc that don't have string table entries? If gaps exist, ask: should translation happen now, or is it deferred? Skip this question if the project has no localization.
