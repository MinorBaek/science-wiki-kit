---
name: wiki-ingest
description: Ingests a scientific paper into a markdown knowledge wiki (Obsidian-compatible). Creates or updates the paper note and propagates its findings to concept and method notes, with source-fidelity checks. Use when the user says "/wiki-ingest", "add this paper to the wiki", or "ingest paper". Filesystem-first, no database or plugin required. Works for any scientific field defined in the wiki's WIKI_SCHEMA.md.
---

# wiki-ingest

Implements the LLM-wiki ingest pattern for a scientific knowledge base.
Every paper ingested creates traceable, compounding knowledge, not just an isolated note.

> Before the first ingest, read `docs/GOTCHAS.md` in the kit (operational gotchas for ingest, synthesis and lint).

## Modes

- **default (ingest):** `/wiki-ingest <paper>` creates or updates the paper note and propagates to concepts and methods (Default Workflow below).
- **verify mode:** `/wiki-ingest verify:<PaperNote>` re-verifies an existing note against its fulltext and reports diffs without regenerating or overwriting anything (see `references/VERIFY-DIFF-MODE.md`). Read-only unless the user confirms each edit.

## Role and Boundaries

**Does**: create or update paper notes, propagate to concept and method notes, update the index and log, report every change.

**Does NOT**: invent citations, create concept notes for single-use concepts, or write to a database. All writes go through the host's file tools (Read/Write/Edit).

## Where things live

Paths come from `wiki.config.json` (vault root, wiki root, folder names, language, thresholds). Defaults:

```
<vault_root>/
  <wiki_root>/            # default: wiki/
    papers/  concepts/  methods/  books/  fields/  debates/
    WIKI_SCHEMA.md        # frontmatter contracts, naming, taxonomy, ingest protocol
    index.md  log.md
  templates/              # paper.md, concept.md, method.md, book.md, chapter.md, submoc.md, synthesis.md
```

`<kit>` below means the science-wiki-kit checkout that holds `tools/` (`seal.py`, `pmc_tables.py`). Its path is the `kit_dir` key of `wiki.config.json`, written by the installer; if it is missing, it is two folders above this skill's directory when the skill is linked from the checkout.

**Always read `WIKI_SCHEMA.md` before starting.** It defines the frontmatter contracts, naming rules and the field taxonomy of this wiki.

## Related skills

- `wiki-lint`: shares `wiki.config.json` (the kebab-case to Title Case field map used in index updates). Run it after each ingest to verify no drift was introduced.
- `wiki-ingest-book`: companion skill for books and chapters. Same status rules and index routing apply.
- `wiki-synthesize`: consumes the notes this skill produces.

## Initial status decision (applied to every new note)

Set `status` deliberately. Do not leave the template default. `N` below is `min_distinct_sources_for_final` in the config (default 2).

| Note type | Condition | Initial `status` |
|---|---|---|
| Paper | Abstract + at least 2 sourced findings extracted | `read` |
| Paper | Only DOI/title metadata, no fulltext | `stub` + `> [!warning] Stub: pending ingest.` callout |
| Concept | At least 2 sourced findings from **N or more distinct source works** | `final` |
| Concept | At least 2 sourced findings, all from a **single source work** | `draft` (single-source synthesis) |
| Concept | Definition + 1 sourced finding | `draft` |
| Concept | Definition only, no Key Findings | `stub` + `> [!warning] Stub: no sourced findings yet.` callout |
| Method | Definition + **N or more distinct source works** under "Papers Using This Method" | `final` |
| Method | Definition and only 1 source work | `draft` (single-source) |
| Method | Definition but no source citations | `draft` |
| Method | Skeleton only | `stub` |

> **Promotion to `final` requires N DISTINCT source works.** "Distinct" counts independent papers or books: a book parent note and its own chapter notes (`Author_2025` + `Author_2025_Ch01` + `Author_2025_Ch02`) collapse to **one** work, as do several chapters of the same book. A single rich source (systematic review, textbook chapter) may create a concept and yield several findings, but the note stays `draft` until a second independent source corroborates it. When adding a finding to a `draft` note, count distinct works **after** the edit, promote only if the count reaches N, and log the promotion in the ingest report. Single-source `draft` notes (concept or method) carry a brief "single-source synthesis, corroborate when a 2nd source is ingested" line in the body.

## Default Workflow

### 1. Read schema
Read `WIKI_SCHEMA.md`.

### 2. Resolve the paper source
Try in order, using whatever your environment provides:

- **Reference manager** (Zotero MCP is the supported adapter): search, then metadata, then fulltext. Sequence and search gotchas in `references/INGEST-WORKFLOW.md`.
- **Publisher XML tables** (open-access in PMC): if the DOI has a PMCID, tables can be pulled cell by cell from Europe PMC JATS, independent of the PDF text layer: `python <kit>/tools/pmc_tables.py <DOI> --out _temp/<stem>_pmc.md --body` (exit 2 means no PMCID). Check table numbers against the JATS before opening the page image; on a JATS-versus-PDF discrepancy the printed PDF wins and the discrepancy is noted. No PMCID: use the PDF. The header it prints also gives authors, venue, volume, issue, pages and the PMID (Europe PMC): copy bibliographic fields from there, never from memory. When there is no PDF, the publisher full text counts as the full text for quotes and numbers: say so in `source_verification` and seal with `"source": "publisher XML"` (see `docs/SEALS.md`).
- **PubMed MCP** (paper not in the reference manager): search by keywords, then fetch by **PMID** (a DOI can return an empty `full_text`). Store the PMID in the paper note `notes:` field. Use only for biomedical papers and after the user confirms it is not in their library. In an unattended run (headless or batch: no human is available to answer questions), skip PubMed: the PMID is in the `pmc_tables.py` header.
- **DOI only**: note it; do not fabricate metadata.
- **Web article** (open-access HTML/URL): convert to clean markdown first with a web-to-markdown tool (for example the `defuddle` skill), then treat the output as abstract and body. Use the URL as citation source when there is no DOI.
- **Manual**: the user pastes abstract or text. Extract metadata and flag what is unknown.

Where the PDF lives matters: the note must never cite a working folder (`Downloads/`, a scratch dir) that will be cleaned up. Organise the PDF in the library location your group uses **before** writing the note, and record it in `source_verification`. If the paper is not in the library, or the right collection is unclear, ask the user before moving anything. With no PDF and no library (open-access text only, or an unattended run), skip this step and record that in `source_verification`.

### 3. Determine the paper note filename
Format: `FirstAuthor_Year_Keyword.md`
- FirstAuthor = last name of the first author (ASCII only, no accents, no spaces)
- Year = 4 digits
- Keyword = 1 to 3 word descriptor (CamelCase or underscores, no spaces)
- Example: `Smith_2023_Eccentric_Training.md`

**Duplicate and identity check (run before any write; it guards against silent data loss):**

1. Confirm existence with a content search for the basename, or `test -f "<wiki_root>/papers/{filename}.md"`. Do NOT trust a single glob returning "no files found": file-glob tools have returned false negatives for notes that existed, and a blind `Write` afterwards would overwrite a fully propagated note. If `Write` errors with "File has not been read yet", that is proof the note exists: read it and update in place, never rewrite from scratch.
2. **If the existing note is `status: stub`, do not assume it is the same paper.** Stubs created from another paper's citation context carry provisional metadata and are sometimes a different paper (wrong year, paper versus book chapter, two sibling papers conflated). Resolve the real source first and compare authors, year and journal against both the stub and the citing note's reference list. If it is a different paper, ingest it as a NEW note and keep or improve the stub.
3. If confirmed the same paper, update in place; never create a duplicate. The filename may legitimately change to a more descriptive keyword once you have the fulltext. If so, re-link every `[[OldName]]` and delete the orphan stub, then re-run `wiki-lint` to confirm no broken links remain.
4. **Citekey identity guard.** Two notes for the same paper can carry different filenames, so a clean basename probe proves nothing about identity. Once the reference manager has resolved the item, search `papers/` for the **exact** citekey you are about to write (`grep -l '^citekey: "\?{citekey}"\?$' papers/*.md`). A hit on a different filename means the paper is already ingested: update that note instead. Exact string match, so no false positives.

### 4. Create or update the paper note
Write `<wiki_root>/papers/{filename}.md` from `templates/paper.md`. Fill every frontmatter field from the resolved metadata. Set `last_verified` to today's date (ingest is a verification event). Assign `research_lines` from the taxonomy slugs in `WIKI_SCHEMA.md`.

### 5. Extract and assess
One pass over abstract, results and discussion, doing all of this at once:

- **Identify** 3 to 8 domain concepts (empirical constructs, variables) and 1 to 4 primary methods. Heuristics in `references/INGEST-WORKFLOW.md`.
- **Classify `evidence_level`**: the study design, from the controlled vocabulary in `WIKI_SCHEMA.md` (`SR-MA`, `RCT`, `cohort`, ...). This is the *design* axis that the living-synthesis layer weights. The *measurement-quality* axis stays **inline in each finding** when relevant (`(MRI)`, `(anthropometric estimate)`), never in frontmatter.
- **Research line routing**: match the paper to the research lines in `WIKI_SCHEMA.md`. If relevant content has no matching line, add one to the schema before propagating (append a slug + label pair; never rename or remove existing lines). The same goes for `field` and `subfield`: if none fits, add the field slug to the Taxonomy section of `WIKI_SCHEMA.md` and to `field_titlecase_map` in `wiki.config.json`, or append the subfield slug under its field, and report it. If borderline, use the closest line and flag it in the report.
- **Concept versus method routing**: empirical findings go to `concepts/`; statistical tools, study designs and measurement protocols go to `methods/`. Decide here.
- **Purely methodological shortcut**: if the paper makes no empirical claims, skip step 6 and go to step 7.

### 5b. Evidence table, before any propagation
For every finding that will reach a note in `concepts/` or `methods/` (including a claim under "Papers Using This Method"), write one row in a scratch file (never in the wiki):

| Target note | Finding, as it will be written | Verbatim quote from the source | Page (PDF / printed) | Section, table or figure |

- **The source is the PDF**, or the publisher full text (JATS) when there is no PDF; table cells come from the JATS first. Abstract-only or no PDF: mark the finding `abstract only` in its text and say so in the report.
- **Every specific needs its quote**: each figure, population, device, mechanism, named entity and verb of strength. Split the finding, or use several quotes, until all are covered.
- **Read the whole paragraph or table row around the hit**, not just the matching number.
- **Tables, figures, signs, CIs and ±: render the page** and look at it. Text extraction is a hypothesis, the image is the proof. Some PDFs lose the minus sign in the text layer (`-5.2%` extracts as `25.2%`), producing a plausible false number.
- **No PDF**: write `n/a` in the page column and cite the section, table or figure from the publisher text. A figure that exists only as an image is not a source: use no number that appears only there, and say so in `source_verification`.
- **Absence needs a positive search**, in both layout and non-layout text and with spelling variants, before anything is written as "the paper does not...".

### 5c. Check the table before writing
Read every row against its quote before any note is touched. If a subagent extracted the paper, re-read every row in the PDF, not only rows with a figure or sign. Defect classes to judge by: inference beyond the source, attribution error, wrong number, lost hedge, unsupported superlative, wrong entity, invented detail, omission.

- A row whose quote does not support it is **reworded down to what the quote says, or dropped**. The source note is not evidence: it comes from the same extraction.
- **Keep the source's hedge** ("may", "it seems", "could be due to") and its population.
- **The wiki's own reading is labelled as the wiki's**; never write it as the source's act or conclusion.

Only rows that survive go to steps 6 and 7.

### 6. Propagate to concept notes
For each concept from step 5:
1. Check whether `concepts/{Concept_Name}.md` exists.
2. **Exists**: append the finding with a `[[paper_note]]` backlink under "Key Findings". Update `related_concepts` if new links emerge.
3. **Does not exist**: apply the creation rules in `references/CONCEPT-PROPAGATION.md` first.

### 7. Propagate to method notes
For each method from step 5:
1. Check whether `methods/{Method_Name}.md` exists.
2. **Exists**: add the paper under "Papers Using This Method".
3. **Does not exist**: create from `templates/method.md`.

### 8. Update paper note frontmatter
Fill `concepts_touched` with the concept and method notes created or updated.

**Verify-after-write**: every name in `concepts_touched` MUST resolve to an existing note in `concepts/` or `methods/`. After writing, re-check each basename. If one does not resolve, either create the missing stub now or remove the name. Dangling references become silent lint drift.

### 8b. Seal the source note
Record the verification in the paper note's `source_verification` (one line: reference-manager key, date, what was checked against what). Then seal each (note, work) pair that received a finding and whose rows passed 5c: write a small JSON spec and run `python <kit>/tools/seal.py spec.json --dry-run`, then without `--dry-run` (format and rules in `docs/SEALS.md`). A work checked only against its abstract gets no seal. Take dates from the system clock (`date +%F`), never estimate them.

### 9. Closeout
Three edits, then the report. Use `field_titlecase_map` from `wiki.config.json` to find the correct subsection for each new concept or method; never append to a dated catch-all block at the end of a section.

- **`index.md`**: if the index embeds Obsidian Bases views (`index_mode: bases` in the config), do NOT maintain per-note lists; only bump the curated `## Quick Stats` counts and the relevant `## Coverage by Field` row, then re-read the tables (a fresh wiki has neither section: skip this, nothing drifts until you add them). In `manual` mode, add the note to the right alphabetical slot. Never touch a frozen legacy index.
- **Sub-MOC routing** (see `WIKI_SCHEMA.md`, Sub-MOC Architecture): resolve the note's `field` + `subfield`, compute `fields/{field-slug}/MOC_{Title_Case_Underscore(subfield)}.md` (kebab-case to Title_Case, deterministic, no map needed). If it does not exist, create it from `templates/submoc.md` and add a line to the field MOC's Sub-MOCs section; if the field MOC does not exist, create it from `templates/moc.md` (named `MOC_` plus the display title in `field_titlecase_map`, spaces as underscores) and link it from `fields/MOC_Wiki.md`. Add the note under the right section of the sub-MOC (Concept Notes, Method Notes, Papers, Books), never in the field MOC. Concept and method notes are routed by their own `field` and `subfield`; a paper has neither, so list it under the sub-MOC of its main concept or method note. Entries are **append-ordered**: add at the END of the section.
- **Check 13 hits** (an alias of a note used unlinked in another): link the alias in the note it fired on; it is informational, but a fresh wiki accumulates them on the first ingest.
- **`log.md`**: append
  ```
  ## [YYYY-MM-DD] ingest | {Paper Title}

  - Created/Updated: papers/{filename}.md
  - Created/Updated concepts: concepts/Concept_A.md, ...
  - Created/Updated methods: methods/Method_X.md
  - Reference key: {key} | DOI: {doi}
  ```
- **Rename reconciliation** (only if this ingest renamed a pre-existing stub): (1) search the wiki for `[[OldName]]` (typically book chapters), change each to `[[NewName]]` and drop any "pending ingest" marker; (2) delete the orphan stub; (3) re-run `wiki-lint` and confirm broken-link and index-coverage checks are clean.
- **Check 12 self-heal** (bidirectional `concepts_touched` and target-note backlinks): steps 6 and 7 already write the backlink, so a correct ingest is symmetric. As a safety net, run the `wiki-lint` Check 12 autofix and confirm the follow-up lint reports `Check 12: 0`. This is a workflow step, not a hook: Claude Code hooks fire on tool events, never on skill completion.
- **Check 15 blind spot**: its `stale` test compares dates by day with a strict `>`, so a touched note whose `## State of Knowledge` carries the same date as this source note's `last_verified` stays silent. List those notes by hand in the report as `wiki-synthesize` candidates.
- **Report**: paper note (path, created or updated), concepts and methods (created versus updated), rename reconciliation (if any), evidence table (rows checked, rows reworded or dropped in 5c), seals written, and warnings (DOI not found, reference manager unavailable, borderline research line).

## Safety Rules

- **Never invent** titles, DOIs, authors, years or **citekeys**. If metadata is unavailable, flag it. The citekey is not derivable from author + year: copy it verbatim from the reference manager's `Citation Key:` line, and leave the field empty if the paper is not in the library. A plausible-looking invented key cannot be told from a real one later.
- **One canonical note per paper.** Confirm existence with a content search or `test -f`, not a glob alone; if it exists, update in place.
- **Claims need sources.** Every finding added to a concept note cites the paper note via `[[wikilink]]`.
- **No propagation without a checked quote** (steps 5b and 5c). A fulltext seal on a source note does not protect what another note says about that work; in a past audit of this method roughly 4 in 10 sampled note-to-source note pairs had a defect, some substantive, and some errors sat in the source note itself.
- **No placeholder concept notes.** Create concept notes only under `references/CONCEPT-PROPAGATION.md`.
- **Do not delete** existing findings in concept notes. Append only (or move to Controversies).
- **Write notes in the wiki language** (`note_language` in the config, default English), whatever the language of the source. This covers prose, headings, callouts and verification seals. Deliberate exceptions: `aliases:` (the bilingual synonym bridge; `_VOCABULARY.md` is generated from it), verbatim quotes from sources in another language (copied as printed, never translated), and `log.md` (operational prose, outside lint scope). The rule binds hardest where the note stops quoting and starts judging, because that is the writer's own voice and slips into the writer's native language: relevance-gloss labels under "Relevance", self-correction asides, and code-switched extraction (an English sentence with foreign verbs spliced in). Lint Check 14 is the radar for the rest (off by default: turn it on with `examples/languages/es.json` or your own lists in `lint.language_radar`), but it cannot see words with no accent or stopword, so the rule written here is the only defence.

## References

- `references/INGEST-WORKFLOW.md`: reference-manager sequence, fallbacks, extraction heuristics, evidence-level decision table
- `references/CONCEPT-PROPAGATION.md`: concept note creation, update and conflict rules
- `references/INGEST-PITFALLS.md`: recurring errors; read before every ingest
- `references/VERIFY-DIFF-MODE.md`: verify mode contract
