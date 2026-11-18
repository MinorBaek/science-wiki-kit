---
name: vocabulary-update
description: Regenerates the _VOCABULARY.md synonym table of a scientific wiki from concept and method frontmatter aliases, and surfaces what changed (new or removed notes, changed aliases, near-duplicate concept candidates) for the user to review before committing. Use periodically after ingesting notes or when aliases change. Triggered by /vocabulary-update or "update the vocabulary / rebuild _VOCABULARY".
---

# vocabulary-update

Keeps `<wiki_root>/_VOCABULARY.md` in sync with the wiki. The vocabulary is a **generated** artifact (single source: the `aliases` frontmatter of each concept and method note), so maintenance is *re-run, diff, approve*, never hand-editing the table.

The generator is one script, `scripts/build_vocabulary.py` (Python standard library only; Windows, macOS and Linux). It reads `wiki.config.json` (see the keys listed at the top of the script) and writes:

- `<wiki_root>/_VOCABULARY.md`: one table per field (`field_titlecase_map` gives the section order and titles), with canonical note, aliases, subfield and a source hint.
- `<wiki_root>/_lint/vocabulary_dupes.txt`: near-duplicate candidates. It lives inside the wiki, not in a gitignored temp folder, so any triage you write next to it survives cleanups.

## Why it matters

Without an embedding or semantic-search layer, `_VOCABULARY.md` is the **only** synonym bridge for retrieval: a term found in text should resolve to its canonical note. It also powers `wiki-lint` Check 13 (alias documented but used without a link) and Check 30 (vocabulary in sync with the notes).

If your wiki is multilingual, put the second-language terms in `aliases:`; the generator keeps every alias as written and does not translate or strip any language.

## Procedure

Run from the vault root (or pass `--vault-root`).

1. **Regenerate:**
   ```bash
   python <kit>/skills/vocabulary-update/scripts/build_vocabulary.py
   ```
   The summary prints the entry count and entries per field.
2. **Show what changed** (present to the user; do not auto-commit):
   - Entry-count delta and per-field deltas, from the summary.
   - `git diff --stat -- <wiki_root>/_VOCABULARY.md`, then `git diff` on that file, summarised (do not dump the whole table). New or removed rows show as added or deleted lines; changed aliases show as modified rows. On the first run the file is untracked and there is no diff.
   - **Near-duplicate candidates**: read `<wiki_root>/_lint/vocabulary_dupes.txt` and list them. These are concepts in the same field sharing 2 or more normalised aliases (case, accents and punctuation folded). **Report only: never auto-merge notes.** Merging has to reconcile backlinks and is a separate, confirmed wiki-edit task.
3. **Optional, alias-link backlog:** run `wiki-lint` and read Check 13 to see how many documented aliases appear in prose without a link to their canonical note (an INFO backlog, not a gate).
4. **Wait for approval, then commit** (Conventional Commit):
   ```
   docs(wiki): refresh _VOCABULARY.md (/vocabulary-update)
   ```
   Commit only `_VOCABULARY.md` (and the duplicate report if you keep it tracked).

## Guardrails

- **Do not hand-edit `_VOCABULARY.md`.** Fix the source (the note's `aliases` frontmatter), then re-run.
- **Never auto-merge** duplicate-candidate concepts. Surface them; the user decides.
- The vocabulary note is exempt from the index-coverage check through its `_` prefix; keep the prefix (`vocabulary_file` in the config).
- If a run changes many rows unexpectedly, stop and show the diff before committing. A frontmatter parse regression, not an intended change, is the usual cause. The parser handles inline lists (`aliases: [a, b]`) and block lists (`- a`); anything more exotic in frontmatter is ignored rather than guessed.
- The script exits with an error, writing nothing, if `wiki_root` or a configured concept folder does not exist, or if it finds no notes.
