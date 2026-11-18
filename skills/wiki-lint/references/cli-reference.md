# wiki-lint: CLI reference (flags, configuration, output files, report shape)

The lint is a read-only health check of the wiki. It never modifies a note; the repair tools (`fix.py`) are separate and explicit.

**Authoritative rules**: `WIKI_SCHEMA.md` (frontmatter contracts, lint rules and the intentional design exceptions). The checks operationalise those rules; when in doubt, defer to the schema.

**Implementation**: `wikikit/lint/` (`context.py` loads everything once, `checks_basic.py` 1-5, `checks_structure.py` 6-12, `checks_content.py` 13-21, `checks_integrity.py` 22-33, `fixes.py`, `defaults.json`). Prefer running these tools over generating ad-hoc helpers each session: they carry the lessons learned (stub exemption, the +/-2-line citation radius, placeholder only on non-resolution, byte-safe I/O).

## Engineering risks (read once, do not repeat)

- **Line endings and encoding.** Read and write only through `wikikit.textio` (byte-level UTF-8, no BOM, EOL untouched). A text-mode round trip converts CRLF to LF behind your back; a multiline `$` regex over CRLF text splits the CR/LF pair and drops the CR (a bulk edit that way once corrupted over a hundred files without `git status` noticing).
- **`status: stub` exemption is uniform**, not just one check. The authoritative list is `lint.stub_exempt_checks`; read it there, because a list restated in prose goes stale silently. Check 11 also excludes stubs inline; Check 10 (Quick Stats) counts every file, stubs included.
- **Placeholder detection only flags non-resolving targets.** A wikilink that resolves in the vault index is never a placeholder, even if its name matches a pattern. This protects legitimate abbreviation notes (DOMS, ANCOVA, WOMAC...).

---

## Command line

```bash
python <kit>/skills/wiki-lint/scripts/lint.py [--vault-root DIR] [--only N[,N...]] [--out-dir DIR] [--json FILE] [--self-test]
python <kit>/skills/wiki-lint/scripts/fix.py  [--vault-root DIR] [--out-dir DIR] {index|check12|promote} ...
```

| Flag | Default | Meaning |
|---|---|---|
| `--vault-root DIR` | `.` | Where to look for `wiki.config.json` (it is searched upwards from here). |
| `--only N[,N...]` | all | Run only these check numbers (7 also runs 7b). Example: `--only 3,5,12`. |
| `--out-dir DIR` | `_temp` | Where the per-check lists are written. |
| `--json FILE` | off | Also write the counters as one JSON object (`{"check5": 0, ...}`). Scripts read this, never the printed lines, whose labels change. |
| `--self-test` | off | Run against `tests/fixtures/lint/` and compare every counter with `expected_counters.txt`. Exit 1 on any mismatch. |

Thresholds are configuration, not flags: `lint.defaults.stale_days` (Check 6, default 90), `min_distinct_sources_for_final` (Check 6 promote, default 2), `lint.defaults.unsourced_threshold` (Check 4, default 3) and `lint.defaults.unsourced_radius` (Checks 4 and 25, default 2).

`fix.py` subcommands:

| Subcommand | Does | Notes |
|---|---|---|
| `index [--out FILE]` | Proposes `index.md` entries for what Check 7 found missing, grouped by Title Case subsection | Read-only proposal. Needs `index_mode: "manual"` and a prior `lint.py --only 7`, which writes `wiki_check7_index_missing.txt`. |
| `check12 [--dry-run] [--log FILE]` | Inserts the missing `[[paper]]` backlink into every target of a Check 12 asymmetry | Computed live. Inserts `- [[paper]] - <claim_placeholder_text>` into `## Papers Using This Concept` / `## Papers Using This Method`, creating the section before `## Related Notes` (or at EOF). Idempotent. Never touches `missing_target` rows. Log: `check12_autofix_<timestamp>.md`. |
| `promote LISTFILE [--status final] [--log FILE]` | Flips `status: draft` to `--status` in the frontmatter of each listed note | One path or note name per line, `#` comments allowed. A note that is not `draft` is reported for manual review (including `review`, a manual gate). Log: `wiki_promotion_log.md`. |

`fix.py` does NOT touch: empty `concepts_touched` (Check 3, a content decision), orphans (1, 2, the fix is to ingest the missing source), broken links (5), index coverage (7, needs composed summaries), book sync (8), chapter `book:` (9), or uncited figures (25: each hit needs the source located and verified, or the figure removed; it carries known false positives, so **never bulk-edit from that list**; read `check-origins.md#check-25` first).

---

## Scan strategy

One pass builds everything the checks share (`wikikit/lint/context.py`):

- **Wiki notes**: every `.md` in the configured `folders` (those in `recursive_folders`, by default `fields`, recursively), with parsed frontmatter, body, the body's line offset (so reported line numbers match the file) and its wikilinks.
- **Vault index**: the set of basenames of every markdown file under the WHOLE vault, minus `vault_ignore_dirs`. This is the existence set Check 5 resolves against, so a link from the wiki to a project note is not "broken".
- **Index links**: the wikilink targets of `index.md`.

**Pre-processing applied before link extraction** (these prevent false positives):

- Strip HTML comments (`<!-- ... -->`, multiline): links inside them do not render.
- Strip fenced code (``` and `~~~`, indentation-tolerant): links inside code do not resolve.
- Normalise table-alias escapes (`\|` to `|`) so `[[Note\|alias]]` in a table cell captures target `Note`.
- Wikilink regex `\[\[([^\]|#]+?)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]` keeps only the target (anchors and aliases dropped); trim whitespace and a trailing `\`.
- Path prefix: `[[folder/Note]]` resolves to the basename after the last `/`.

Pre-processing removes lines, so line numbers taken from the pre-processed body are approximate. Checks that report a line number from the raw body (5 for empty targets, 22 to 27) add the frontmatter offset and are exact.

---

## Configuration (`wiki.config.json`)

Top level (shared by every skill): `vault_root`, `wiki_root`, `papers_folder`, `books_folder`, `concepts_folder`, `methods_folder`, `folders`, `recursive_folders`, `vault_ignore_dirs`, `field_titlecase_map`, `vocabulary_file`, `min_distinct_sources_for_final`, `templates_dir`, `template_names`, `moc_names` (names an existing wiki already uses, resolved by `<kit>/tools/wiki_paths.py`), and `synthesis` (`min_sources`, `sr_levels`, `prefulltext_cutoff`, `priority_fields`). `note_language`, `pdf_library_dir` and `synthesis.priority_fields` are read by the agent from the skills, not by any script: no tool changes behaviour if you set them, and `pdf_library_dir` is empty until you fill it.

`lint` section (overrides the defaults in `wikikit/lint/defaults.json`; lists replace the default list, objects merge):

| Key | Used by | Meaning |
|---|---|---|
| `index_mode` | 7, 7b | `bases` (index embeds Bases views; checks 7 and 7b are skipped) or `manual` (per-note lists). `--self-test` forces `manual`. |
| `index_sections`, `index_exempt_patterns`, `quick_stats_labels` | 7, 7b, 10 | Heading to folder map; basename regexes exempt from Check 7 (default `^_`); Quick Stats row label to folder. Derived from the folder names when absent. |
| `stub_exempt_checks` | 1, 2, 4, 7, 8, 13, 14, 17, 18, 21, 25, 26 and 33 | Check numbers that skip `status: stub` (no effect on any other check). |
| `defaults.stale_days`, `defaults.unsourced_threshold`, `defaults.unsourced_radius` | 4, 6, 25 | Thresholds. |
| `verb_list` | 4 | Claim verbs. |
| `placeholder_wikilink_patterns`, `link_target_ignore_patterns` | 5 | Regexes. |
| `alias_link_stoplist` | 13 | Ubiquitous acronyms that would drown the check. |
| `language_radar` | 14 | `enabled`, `headings`, `stopwords`, `prose_threshold`, `case_sensitive_tokens`, `line_guards`, `heading_requires_accent`. Example: `examples/languages/es.json`. |
| `synthesis_block_heading` | 15 | Default `## State of Knowledge`. |
| `status_by_type` | 16 | Allowed statuses per note `type`. |
| `check18_exempt_stale_months` | 18 | Age after which a dated exemption counts as stale (12). |
| `evidence_level_vocab` | 19 | The closed vocabulary. |
| `unfilled_claim_patterns`, `claim_placeholder_text` | 23, fix check12 | Regexes for an unwritten claim; the text `fix.py check12` inserts. |
| `deprecated_frontmatter_keys` | 24 | `{old: canonical}`. |
| `numeric_claim_patterns`, `check25_methods_fields`, `check25_cited_pattern` | 25 | Figure patterns; fields whose notes class as `methods`; author-year pattern. |
| `memory_slug_prefixes`, `memory_slug_exempt_files` | 29 | Out-of-vault slug prefixes (empty = disabled) and exempt basenames (wildcards). |
| `seal_debt_file` | 32 | Declared seal debt, relative to the wiki (default `_lint/seal_debt.txt`). |

---

## Output files

Each check writes its findings to `--out-dir` as plain text, one finding per line, fields separated by `|`. The files are caches: they are rewritten on every run and must not be versioned.

| Check | File | Line shape |
|---|---|---|
| 1 | `wiki_check1_orphan_concepts.txt` | `note` |
| 2 | `wiki_check2_orphan_methods.txt` | `note` |
| 3 | `wiki_check3_empty_concepts.txt` | `note` |
| 4 | `wiki_check4_unsourced_claims.txt` | `note\|count` |
| 5 | `wiki_check5_broken_links.txt` | `note\|target\|line\|broken, placeholder or empty-target` |
| 6 | `wiki_check6_stale.txt`, `wiki_check6_promote.txt` | `note\|date\|works`, `note\|works` |
| 7, 7b | `wiki_check7_index_missing.txt`, `wiki_check7_stubs.txt`, `wiki_check7_misplaced.txt` | `note\|folder`, `target\|folder\|section` |
| 8 | `wiki_check8_book_sync.txt` | `book\|declared-only:[..] fs-only:[..]` |
| 9 | `wiki_check9_chapter_book_fm.txt` | `note` |
| 10 | `wiki_check10_quickstats.txt` | `label\|declared=N\|fs=M` |
| 11 | `wiki_check11_coverage.txt`, `wiki_check11_unfielded.txt` | `label\|Concepts or Methods\|declared=N\|fs=M`, `folder\|note\|field` |
| 12 | `wiki_check12_asymmetry.txt`, `wiki_check12_missing_target.txt` | `paper\|token\|folder`, `paper\|token` |
| 13 | `wiki_check13_alias_no_link.txt` | `note\|alias\|canonical(s)` (several canonicals are joined with `/`) |
| 14 | `wiki_check14_foreign_language.txt` | `note\|folder\|H=n\|S=n` |
| 15 | `wiki_check15_missing.txt`, `wiki_check15_stale.txt` | `note\|folder\|works=n\|srma=True/False`, `note\|folder\|updated=..\|maxLv=..` |
| 16 | `wiki_check16_status_vocab.txt` | `note\|folder\|reason` |
| 17-21 | `wiki_check17_no_provenance.txt`, `wiki_check18_incomplete_metadata.txt` (+ `_exemptions`, `_exempt_stale`), `wiki_check19_evidence_level.txt`, `wiki_check20_quote_sanity.txt`, `wiki_check21_prefulltext_cohort.txt` | `note` or `note\|detail`. Check 17's file is the live provenance work queue. |
| 22 | `wiki_check22_stale_warn.txt` | `note\|Lnn\|paper` |
| 23 | `wiki_check23_unfilled_claim.txt` | `note\|Lnn\|subject` (`-` when no source is named) |
| 24 | `wiki_check24_deprecated_key.txt` | `note\|Lnn\|old->new` |
| 25 | `wiki_check25_uncited_number.txt` | `note\|Lnn\|value\|class` (the class labels are display metadata and are not regression-guarded) |
| 26 | `wiki_check26_table_columns.txt` | `note\|Lnn\|expected\|found\|header or row` |
| 27 | `wiki_check27_mojibake.txt` | `note\|Lnn` |
| 28 | `wiki_check28_seal_no_lastverified.txt` | `note` |
| 29 | `wiki_check29_memory_slug_link.txt` | `path\|Lnn\|slug` |
| 30 | `wiki_check30_vocab_sync.txt` | `missing\|note`, `ghost\|note` |
| 31 | `wiki_check31_seal_no_text.txt` | `note` |
| 32 | `wiki_check32_seal_pairs.txt` | `note\|work` (the unsealed pairs) |
| 33 | `wiki_check33_no_title_venue.txt` | `note\|missing fields` |

---

## Console report

```
Loaded wiki notes: N
Check 1 (orphan concepts): 1=0
...
Check 15 (synthesis radar): 15_missing=5, 15_stale=85
Check 32 (note-work pair without a seal naming the note): 32=0, 32_debt=5, 32_stale=0

Why these checks exist (read before dismissing a finding as a false positive):
  Check 15 -> references/check-origins.md#check-15
```

Every counter is printed even when it is zero, so a run that executed and found nothing is distinguishable from a run that did not happen. The closing pointers are printed only for checks that fired.

### Reading the findings

Severity is the reader's call, but a useful split:

- **Critical (fix now):** 5 broken links, 3 empty `concepts_touched`, 8 book sync, 16 status violations, 19 vocabulary violations, 26 table mismatch, 27 mojibake, 32 unsealed pairs.
- **Warnings (triage):** 1, 2 orphans, 4 unsourced claims, 6 drafts, 9, 12, 18, 22, 23, 24, 33.
- **Info / backlog (do not gate on them):** 7, 7b, 10, 11 (index drift), 13, 14, 15, 17, 20, 21, 25, 28, 30, 31.
- **Promote:** the `check6_promote` list, to flip with `fix.py promote` after a human glance.

Do not close or block a batch because of a delta in Check 13: it is an INFO backlog with a large, slow-moving total. Of a Check 14 or 25 measurement, only the delta is transferable, never the absolute floor (the base keeps growing).

---

## Behavioural guardrails

- The lint never writes outside `--out-dir`; `fix.py` never writes outside the wiki.
- If a check would emit more than 100 items, summarise by group in your own report instead of pasting the list.
- When unsure whether a wikilink is broken because the target lives in a folder you cannot read, prefer "not broken": a false negative is safer than a false positive, and the user can re-run with a wider `--vault-root`.
- Always report the scope line (notes loaded, checks run) even when the issue count is zero.
