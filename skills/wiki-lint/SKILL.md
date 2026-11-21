---
name: wiki-lint
description: 'Diagnostic and repair toolkit for a scientific markdown wiki (Obsidian-compatible): 33 health checks over links, provenance, frontmatter, tables, encoding, synthesis blocks and seals. Resolves wikilinks against the FULL vault (cross-folder aware), skips false positives from HTML comments, code fences and escaped table pipes, exempts `status: stub` notes where it makes sense, and ships fixtures plus `--self-test` for regression safety. Triggered by /wiki-lint or "lint the wiki / check wiki health".'
---

# wiki-lint

> Before the first run, read `docs/GOTCHAS.md` in the kit (known false positives, operating notes).

A read-only health scan of the wiki (`wiki_root` in `wiki.config.json`) plus three repair tools. Everything is Python standard library and runs the same on Windows, macOS and Linux. Every wiki-specific rule (folders, status taxonomy, field map, exemptions, verb list, placeholder patterns, thresholds) lives in configuration, so the logic does not change when the wiki grows a new field, folder or check. Designed to stay fast past 3,000 notes (a full run is seconds, except Check 13 which takes about half a minute at that size).

## Related skills

- `wiki-ingest`, `wiki-ingest-book`: write the notes this skill checks (same configuration for status decisions and index routing).
- `wiki-synthesize`: Check 15 produces its worklist; Check 32 audits its seals.
- `vocabulary-update`: the remedy for Check 30.

## Layout

```
skills/wiki-lint/
  SKILL.md
  scripts/
    lint.py        # run the checks (--only, --out-dir, --self-test)
    fix.py         # repair tools: index proposal, Check 12 backlinks, promote drafts
  references/
    check-origins.md   # WHY each check exists (single authority)
    cli-reference.md   # flags, configuration keys, output files, report shape
wikikit/lint/        # the implementation: context.py, checks_*.py, fixes.py, defaults.json
tests/fixtures/lint/ # synthetic mini-wiki exercising every check + expected_counters.txt
```

**Where each kind of fact lives** (never duplicate across these): `references/check-origins.md` = **why** a check exists; this file = **what** it does; `wikikit/lint/checks_*.py` = **how** it is implemented; `tests/fixtures/lint/expected_counters.txt` = **why the fixture value is what it is**. At the end of a live run the tool prints the `check-origins.md` pointer for every check that fired, so the motive arrives when you are deciding whether a hit is real or noise.

## Engineering invariants (do not break)

1. **All file I/O goes through `wikikit.textio`** (byte-level UTF-8, no BOM, line endings never translated). Never use text-mode `open()` with default newline handling: reading and re-writing a CRLF file that way silently converts it.
2. **Never use a multiline regex with `$` over text that may contain CRLF**: `$` sits between the CR and the LF and splits the pair. Edit by lines (`frontmatter.set_key`, `fixes._insert_backlinks`).
3. **Configuration is the single source of truth.** When the wiki gains a field, folder, status or exemption, edit `wiki.config.json` (`lint` section), not the code. Defaults live in `wikikit/lint/defaults.json`.
4. **Stub exemption is uniform.** `lint.stub_exempt_checks` lists the check numbers that skip `status: stub` notes; read the list from the config, never restate it in prose. Only checks 1, 2, 4, 7, 8, 13, 14, 17, 18, 21, 25, 26 and 33 read the list; Check 3 skips stubs on its own, Check 11 excludes them inline, and Check 10 (Quick Stats) counts every file, stubs included.
5. **Placeholder detection is gated on non-resolution.** A wikilink target that resolves in the vault index is NEVER flagged as a placeholder, even if its name matches a pattern; legitimate ALL-CAPS abbreviation notes must not flag.
6. **Self-test before shipping logic changes.** Any edit to a check (new check, changed threshold, refactored heuristic) must run green: `python <kit>/skills/wiki-lint/scripts/lint.py --self-test`. Update `tests/fixtures/lint/` and `expected_counters.txt` together when the change is intentional. **Prove the fixture discriminates**: revert the logic change, re-run, and confirm the counter moves. A fixture that passes both before and after guards nothing.
7. **A zero is a measurement of the detector, not of the wiki.** Before trusting a new check's zero, inject a positive case and see it fire.
8. **Warning-marker ownership is positional, never regex-chained (Check 22).** The wiki may use both `[[Paper]]⚠` and `⚠[[Paper]]`. The owner of a glyph is the link immediately to its LEFT if the left-trimmed text ends in `]]`, otherwise the link to its RIGHT; a glyph adjacent to no link is a prose caution. Do not resolve this with two chained regexes (the second eats the neighbouring link's marker and silently de-flags an unverified source). Any bulk edit of markers needs a per-citekey census before and after.

## How the checks work

| # | Name | What it flags | Exemption |
|---|---|---|---|
| 1 | Orphan concepts | No backlink from any paper/book (inline link or `concepts_touched`) AND none from a sibling concept (inline or `related_concepts`); the sibling leg keeps synthesis hubs from false-flagging | stub |
| 2 | Orphan methods | No backlink from a paper/book AND no outgoing link to any paper/book | stub |
| 3 | Empty `concepts_touched` | A paper note with the field null, empty or `[]` (also the canary for frontmatter corruption in batch ingests) | stub |
| 4 | Unsourced claims | Concept notes with at least `unsourced_threshold` lines carrying a claim verb (`verb_list`) and no wikilink within +/-`unsourced_radius` lines nor under a wikilinked heading | stub |
| 5 | Broken / placeholder wikilinks | Target not in the whole-vault index (`broken`), or matching `placeholder_wikilink_patterns` when non-resolving (`placeholder`), or empty (`[[]]`, `empty-target`) | `link_target_ignore_patterns` (Bases embeds) |
| 6 | Drafts | `promote`: a draft citing at least `min_distinct_sources_for_final` DISTINCT source works (a book plus its chapters is one work). `stale`: a draft older than `stale_days` below that, or undated | none |
| 7 | Index coverage | A note whose basename is not a wikilink in `index.md` | stub; **skipped when `index_mode` is `bases`** |
| 7b | Index section misplacement | A `- [[X]]` under the wrong `##` section (`index_sections`) | skipped in `bases` mode |
| 8 | Book `chapters_ingested` sync | Declared set differs from the `{book}_ChNN.md` files on disk | stub chapters |
| 9 | Chapter without `book:` | A `*_ChNN` note whose `book:` link is missing or does not resolve | none |
| 10 | Quick Stats drift | A declared count in `## Quick Stats` differs from the live file count of the mapped folder (`quick_stats_labels`) | none |
| 11 | Coverage by Field drift | Concepts/Methods columns of `## Coverage by Field` differ from the live non-stub counts (field rows by `field:`, `->` subfield rows by `subfield:` keyed off the `[[MOC_*]]` link; a subfield with notes and no row is `MISSING-ROW`) | stubs; unfielded notes are INFO |
| 12 | Bidirectional `concepts_touched` | `paper -> concepts_touched[token]` whose target lacks the `[[paper]]` backlink (`asymmetry`, auto-fixable) or resolves to no note (`missing_target`, triage the token) | none |
| 13 | Alias without link | A documented alias (distinctive acronym or multi-word phrase) used in another concept/method's prose without a link to its canonical note. INFO | stub; `alias_link_stoplist`; blockquotes are not searched |
| 14 | Language radar | A heading (H2-H6) in a language other than the wiki's, or at least `prose_threshold` stopword hits in prose. Report-only; **disabled unless `language_radar.enabled`** | stub |
| 15 | Synthesis radar | Over `final` concepts/methods: `missing` = qualifies for a State-of-Knowledge block and has none; `stale` = block older than the newest `last_verified` of its cited works | non-final |
| 16 | Status vocabulary | `status` not in `status_by_type[type]`, missing `status` or `type`, or a template leak (`draft \| final`) | none |
| 17 | No `source_verification` | A paper without a seal; a value starting with `abstract` is NOT a seal. INFO backlog | stub |
| 18 | Verified but incomplete | A sealed paper lacking `volume` or `pages` and without a dated `check18_exempt: "YYYY-MM-DD, reason"`; conference papers and theses are exempt by venue and shape | stub |
| 19 | `evidence_level` out of vocabulary | Value not in `evidence_level_vocab` (papers only) | none |
| 20 | Useful Quotes `]]` | A blockquote under `## Useful Quotes` with a leaked `]]` | none |
| 21 | Pre-fulltext cohort | A paper dated before `synthesis.prefulltext_cutoff` with no fulltext-level seal. INFO | stub |
| 22 | Stale pre-fulltext marker | A `⚠` whose owning wikilink is a paper that already has a fulltext seal, after three tail exemptions (prose caveat, dated italic annotation, `(N src` confidence). Has real false positives | none |
| 23 | Unfilled claim placeholder | A line matching `unfilled_claim_patterns` (a source named but no claim written) | none |
| 24 | Deprecated frontmatter key | A key in `deprecated_frontmatter_keys` (default `journal` to `venue`); exact match, so no false positives | none |
| 25 | Uncited figure | A statistical figure (`numeric_claim_patterns`) with no wikilink within the radius, classed `cited` / `block` / `methods` / `domain`. INFO. Nothing is exempted | stub; blockquotes skipped |
| 26 | Table column mismatch | A table whose rows have a different number of cells than the delimiter row (the only structural check) | none |
| 27 | Mojibake | A line that round-trips through `encode('cp1252').decode('utf-8')` to a different string | none |
| 28 | Seal without `last_verified` | A paper/book with `source_verification` and no `last_verified` (invisible to Check 15 `stale`). INFO | none |
| 29 | Out-of-vault slug link | A wikilink to a slug in `memory_slug_prefixes`, vault-wide. **Disabled unless the list is non-empty** | `memory_slug_exempt_files` |
| 30 | Vocabulary sync | `_VOCABULARY.md` missing a live concept/method (`missing`) or holding a row for a note that is gone (`ghost`). INFO; remedy `/vocabulary-update` | none |
| 31 | Seal without text | A seal of at most 60 chars with no descriptive verification text in any channel. INFO | none |
| 32 | Pair without a seal | A (note, work cited in its State-of-Knowledge block) pair whose source note seal does not name the note. **Blocking**; declared debt in `seal_debt_file` is reported but not counted | declared debt |
| 33 | No title or venue | A paper with an empty `title` or `venue` | stub |

## Invocation

From the vault (the nearest `wiki.config.json` upwards is the config):

```bash
python <kit>/skills/wiki-lint/scripts/lint.py                 # all checks; lists go to _temp/
python <kit>/skills/wiki-lint/scripts/lint.py --only 5,12     # selected checks
python <kit>/skills/wiki-lint/scripts/lint.py --self-test     # fixtures vs expected_counters.txt
python <kit>/skills/wiki-lint/scripts/fix.py check12 --dry-run
python <kit>/skills/wiki-lint/scripts/fix.py promote _temp/promote_batch.txt
python <kit>/skills/wiki-lint/scripts/fix.py index            # needs index_mode "manual" and a prior lint run
```

Flags, configuration keys and the files each check writes: `references/cli-reference.md`.

## When to edit what

- **New wiki folder** (for example `datasets/`): add it to `folders` in `wiki.config.json`. It must be registered BEFORE notes are created, or every link to it reads as broken.
- **New status value**: add it to `lint.status_by_type.{type}`. **New note type**: add the type with its allowed statuses.
- **New field for concepts/methods**: add the slug to `field_titlecase_map`.
- **Refine Check 4**: `lint.verb_list`. **Loosen/tighten its tolerance**: `lint.defaults.unsourced_radius`.
- **New placeholder pattern**: `lint.placeholder_wikilink_patterns` (remember it only applies to non-resolving targets).
- **A check should skip stubs**: add its number to `lint.stub_exempt_checks` (it takes effect only for checks 1, 2, 4, 7, 8, 13, 14, 17, 18, 21, 25, 26 and 33; any other needs a code change).
- **Turn on the language radar**: copy `examples/languages/es.json` (or write your own lists) into `lint.language_radar`.
- **Add a new check**: implement it in `wikikit/lint/checks_*.py`, add its counters to `expected_counters.txt`, add a fixture that exercises it, **write its entry in `references/check-origins.md`**. A check whose motive is not written down gets disabled the first time it looks noisy. If the motive cannot be sourced, write "not documented"; never invent one.

## Safety rules

- The lint is read-only against the wiki; it only writes the per-check lists into `--out-dir` (default `_temp/` next to `wiki.config.json`, wherever the script is run from).
- `fix.py` mutates notes only where it reports (backlinks, status), keeps each file's line endings, and logs every change for rollback.
- When unsure whether a heuristic change is right, write the fixture first, watch the self-test fail, then make the change.
- **Cache directories are never versioned** (`_temp/` and friends stay in `.gitignore`). A versioned measurement gets read months later as if it were today's.
