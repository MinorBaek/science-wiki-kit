---
name: wiki-ingest-book
description: >
  Use when the user asks to ingest a book or book chapter into the scientific wiki.
  Triggers on: "/wiki-ingest-book [title]" (book overview),
  "/wiki-ingest-book [title] > Chapter N" (chapter-level ingest),
  or any request to "add a book to the wiki", "ingest this textbook", "add chapter N of [book]".
---

# wiki-ingest-book

> Before the first ingest, read `docs/GOTCHAS.md` in the kit (operational gotchas, including page-offset calibration for books).

Extends the LLM-wiki ingest pattern to academic books. Books are context-heavy and cannot be ingested in one shot, so this skill uses a **two-phase approach**: a book overview first, then chapters on demand.

## Role and Boundaries

**Does**: create book notes, create chapter notes, propagate findings to concept and method notes, update the index and log.

**Does NOT**: read a full book in one pass (context-limit risk), invent metadata or chapter titles, or duplicate the paper-ingest workflow (chapters follow the same concept-propagation rules as papers).

## Where things live

Paths come from `wiki.config.json` (see `wiki-ingest`). Books and chapters live in `<wiki_root>/books/`. Templates: `templates/book.md` and `templates/chapter.md`. The folder holding your PDF library is `pdf_library_dir` in the config.

## Related skills

- `wiki-ingest`: shares the initial-status decision rules and the `field_titlecase_map` used for index routing.
- `wiki-lint`: run after each chapter ingest. Check 8 (`chapters_ingested` sync) and Check 9 (chapter `book:` frontmatter) catch the most common book-ingest drift.

## Required contracts (must hold after every ingest)

1. **Every chapter note** at `books/{book}_ChNN.md` MUST carry `book: "[[{book_basename}]]"` in frontmatter, and the target must resolve to an existing book note. Verify after writing; if missing, `wiki-lint` Check 9 flags it.
2. **Every chapter ingest** MUST append the chapter number to the parent book note's `chapters_ingested:` list. After the append, list the `{book}_Ch*.md` files that are not `status: stub` (forward-ref stubs from step 9 do not count) and confirm the two sets match; otherwise `wiki-lint` Check 8 flags the drift.
3. **Initial status** follows the `wiki-ingest` status table: `stub` for definition-only, `draft` in progress, and a chapter note reaches `final` with 2 or more sourced findings (a chapter is itself a source). **Derived concept and method notes follow the strict promotion rule**: `final` needs N distinct source works (`min_distinct_sources_for_final`, default 2), so a concept built only from this one book stays `draft` until a second independent source corroborates it.
4. **Index routing** uses `field_titlecase_map` to place new concepts and methods under the correct Title Case field subsection, never in a dated catch-all block.

## Preamble (always, before Mode A or Mode B)

1. Read `WIKI_SCHEMA.md`.
2. Read the template: Mode A uses `templates/book.md`; Mode B uses `templates/chapter.md` (and `templates/book.md` for reference).

> **Tools**: use the host's file tools (Read/Write/Edit) for all vault writes.

---

## Local PDF resolution (preferred for fulltext)

**Default folder**: `pdf_library_dir` in the config (your reference manager's PDF storage).
**Extractor**: `pdftotext` (poppler) or, for better table fidelity, `docling`. Always run `pdftotext` with `-enc UTF-8`.

**Locate the PDF** by enumerating and grepping the author, NOT with a glob tool and NOT with `find -iname "*<author>*"`; both have documented false negatives for files that exist on some filesystems: `find "<pdf_library_dir>" -iname "*.pdf" | grep -i <first_author_lastname>`. Widen the root to the whole library if the first pass is empty (books also live in thematic subfolders). Exactly 1 match: use it. 0 or more than 1: ask the user for the exact path. If that also fails: fall back to the reference manager's fulltext.

> The **full resolution algorithm, the local-first fulltext cascade and MCP decision table, scanned-PDF detection, and the non-ASCII filename hazard** are in `references/BOOK-INGEST-WORKFLOW.md` (sections 1 and 1bis). Read it before the first extraction of a new book. The body below keeps only the commands used for every chapter.

### Extraction commands

- **TOC / overview** (Mode A): `pdftotext -enc UTF-8 -f 1 -l 20 "<path>" -` (first 20 pages, stdout).
- **Chapter range** (Mode B): `pdftotext -enc UTF-8 -f <pdf_start> -l <pdf_end> "<path>" -`. `-f/-l` take **PDF page numbers, not book page numbers**; convert from the TOC with the offset (next section).
- **Writing the extract to a file you will `Read`**: a long chapter slice may be easier as a file than as stdout. Write it inside the project (for example `_temp/{book}_Ch{NN}.txt`), not to an OS-specific `/tmp` that the Read tool cannot open (Git Bash on Windows maps `/tmp` somewhere Windows tools cannot see).

### Page-offset calibration (book pages are not PDF pages)

A book's TOC lists **book** page numbers; `pdftotext -f/-l` addresses **PDF** pages. They differ by an offset (front matter, plates) that **grows nonlinearly** through the book (figures, tables, part dividers). Passing TOC numbers straight to `pdftotext` extracts the wrong pages, the most common time sink in chapter ingest. Calibrate once per book, before extracting any chapter:

1. Pick a chapter with a known book start page. Estimate `pdf_start = book_page + offset_guess` (front matter is often 20 to 60 pages).
2. Extract just its first page and confirm the chapter title appears. Adjust by up to 5 pages until it lands.
3. **Record the calibrated offset in the book note** (for example `> [!note] PDF offset: book_pg + N = pdf_pg (zone: Part X)` near the TOC) so later chapters reuse it.
4. Re-calibrate per zone or Part on long books: a single fixed offset drifts (for example +36 at Ch 3 and +56 at Ch 21 in one textbook). For text-layer PDFs, splitting the text on form feeds gives a fast page map with exact start pages.

---

## Mode A: Book overview

**Trigger**: `/wiki-ingest-book [title]`

1. **Resolve in the reference manager**: search by title, then fetch metadata (title, authors, editors, year, publisher, ISBN, edition, DOI, citekey).
   - **Year-suffix citekey caveat (multi-volume or Part series)**: a Better BibTeX citekey like `...2019a` / `...2019b` does NOT reliably map to Part 1 versus Part 2 of a same-author, same-year series (the suffix is disambiguation order, not meaning). Always confirm the actual **title** (and subtitle or "Part N") from the metadata before naming the note or trusting which volume you have.
2. **Resolve fulltext for the TOC** (cascade; see "Local PDF resolution"):
   - Primary: `pdftotext -enc UTF-8 -f 1 -l 20 "<local_path>" -` (about 3 to 8k tokens).
   - Fallback 1: reference-manager fulltext, only if the local PDF is unavailable AND output is under 2,000 words.
   - Fallback 2: ask the user to paste the TOC; mark it "Source: user-provided".
   - Fallback 3: model knowledge for well-known textbooks; mark every item with `[!note]`.
3. **Determine the filename**: `FirstAuthor_Year_Keyword.md` (first author's last name, ASCII only; keyword is 1 to 3 words on the book's main topic). If `books/{filename}.md` exists, update in place.
4. **Create or update the book note** at `books/{filename}.md` from `templates/book.md`. Set `last_verified` to today's date.
5. **Fill the TOC** from step 2. If uncertain, mark chapters `?` and note the limitation.
6. **Extract 3 to 5 high-level themes** (book level only, no chapter-specific claims). Light propagation: update `concepts/` notes only if the theme is core to a research line AND 2 or more wiki papers already touch it; otherwise just list it in the book note. A theme that reaches a note follows the evidence-table rule: Mode B steps 6b and 8b.
7. **Governance check**: apply the research-line matching and concept-versus-method routing from `wiki-ingest` step 5. At overview level only note which chapters will likely produce method notes versus concept notes; full propagation happens in Mode B.
8. **`index.md`**: if the index embeds Bases views, do NOT add a book entry; only bump the `## Quick Stats` "Books (ingested)" count when this completes a new parent-book ingest. In `manual` mode, add the entry. Never touch a frozen legacy index.
9. **Append to `log.md`**: `## [YYYY-MM-DD] ingest-book | {Title}: overview`.
10. **Report**: book note path, themes identified, and which chapters are available for deep ingest (`/wiki-ingest-book [title] > Chapter N`).

---

## Mode B: Chapter ingest

**Trigger**: `/wiki-ingest-book [title] > Chapter N` (or `> Chapter: [chapter title]`)

1. **Read the existing book note** at `books/FirstAuthor_Year_Keyword.md`.
   - If it **does not exist**: stop. Run Mode A first, then retry.
   - If the chapter is **not listed in the TOC**: append a row with `status: pending`, note it in the final report, continue.
   - If the chapter is already marked `ingested`: confirm with the user before overwriting (default: update in place, preserving existing `[[wikilinks]]`).
2. **Resolve chapter content** (cascade; see "Local PDF resolution"):
   - Take the chapter page range from the book note TOC and convert book pages to PDF pages with the recorded offset. Ask the user only if the TOC page numbers themselves are unknown.
   - Primary: `pdftotext -enc UTF-8 -f <pdf_start> -l <pdf_end> "<local_path>" -` (a typical chapter is 1k to 8k tokens).
   - Fallback 1: if the chapter is a `bookSection` item with its own library entry, use that item's fulltext.
   - Fallback 2: whole-book fulltext from the reference manager, only if the local PDF is unavailable AND the book is under 5,000 words.
   - Fallback 3: ask the user to paste the chapter text.
   - Fallback 4: model knowledge, with `[!warning]` on every claim. It never reaches a concept or method note and gets no seal.
3. **Chapter filename**: `FirstAuthor_Year_Keyword_ChNN.md` (for example `Knuttgen_1987_Strength_Ch03.md`).
4. **Create the chapter note** at `books/{chapter_filename}.md` from `templates/chapter.md`. Set `last_verified` to today's date.
   - **Required contract**: emit `book: "[[{parent_book_basename}]]"` in frontmatter and verify it resolves. If it does not, the parent was not ingested: run Mode A first.
   - **Initial status**: apply the `wiki-ingest` status table. A scaffold chapter with only the TOC entry filled is `stub`; a chapter with at least 2 sourced findings is `final`.
   - **Evidence level**: `evidence_level: textbook` by default. Override to `SR-MA` or `SR` only if the chapter is itself a standalone systematic review or meta-analysis. Measurement quality stays inline in findings, never in frontmatter.
5. **Extract 3 to 8 concepts and 1 to 4 methods**: same extraction rules as `wiki-ingest` (see `references/BOOK-INGEST-WORKFLOW.md`).
6. **Governance check**: same research-line matching and concept-versus-method routing as `wiki-ingest` step 5. Decide explicitly for this chapter: concept notes (empirical findings), method notes (frameworks, protocols), or both. General pedagogical content typically yields method notes only; do not force concept creation for content that belongs in `methods/`.
6b. **Evidence table and check, before any propagation**: apply `wiki-ingest` steps 5b and 5c to this chapter, with a scratch table for the chapter. Three additions for books:
   - The page column gives **both the PDF page and the printed page**, and the chapter title is confirmed on the page you land on (a wrong offset cites another chapter).
   - A textbook gets the strict reading: check every mechanism and marker the finding names. A chapter's list of causes or criteria is not evidence for each item unless the item is on the page.
   - Say who speaks: a claim the chapter hands to another author is written "X, as reported by [[chapter]]", and a chapter's clinical opinion is not written as a trial result.
   Only rows that pass go to steps 7 and 8. Read signs from the rendered page.
7. **Propagate to concept notes**, identical to paper ingest: append the finding with a `[[chapter_note]]` backlink to the existing `concepts/{Concept}.md`, or create a new one from `templates/concept.md` under the same creation rules as `wiki-ingest/references/CONCEPT-PROPAGATION.md`.
8. **Propagate to method notes** if applicable.
8b. **Seal the chapter note**: apply `wiki-ingest` step 8b with the chapter as the work (record the verification in `source_verification`: library key, ISBN, chapter and pages checked, date).
9. **Forward-ref stubs (automatic)**: after the chapter body is written, materialise any forward-references to sibling chapters that do not exist yet:

   ```
   python skills/wiki-ingest-book/scripts/create_forward_ref_stubs.py \
     <wiki_root>/books/{book}_Ch{NN}.md  <wiki_root>/books/{book}.md   [--dry-run]
   ```

   The script scans the just-ingested chapter for `[[{book}_ChNN]]` links (alias-aware), reads the book hub's `## Table of Contents` table to recover title and pages for each missing chapter, derives DOI and citekey from the hub frontmatter (`{doi_base}_{N}`, `{citekey_base}_ch{N}`), and writes UTF-8 stubs with `status: stub`. Forward-refs without a TOC row are skipped and reported (manual ingest required). Actions are logged to `_temp/wiki_ingest_book_stubs_created.md`. `wiki-lint` Check 8 honours `status: stub`, so these stubs do NOT desynchronise `chapters_ingested`, which stays the canonical list of *actually ingested* chapters.

   > ⚠️ **Never write an ingest-state marker in a chapter's prose.** No `*(pending ingest)*`, no "not yet ingested" next to a sibling chapter, in `## Related Papers`, in a *see also* bullet, or anywhere else. Ingest state is **mutable** and has exactly one home: the book hub's `## Table of Contents` row, which step 11 flips from `pending` to `ingested`. A marker copied into prose duplicates a mutable fact into an immutable place: the sibling gets ingested, the TOC updates, and the prose keeps asserting the opposite forever. In one audit this produced 68 stale marks across 58 notes, every dependency already ingested. No lint check sees this class, because each file stays coherent with itself and the contradiction exists only between files. Just link the sibling; if a work is outside the wiki, name it in plain text.

10. **Missing-concept report (automatic)**: after the stubs, scan the chapter for concept-shaped wikilinks that do not resolve:

    ```
    python skills/wiki-ingest-book/scripts/report_missing_concepts.py \
      <wiki_root>/books/{book}_Ch{NN}.md
    ```

    The script builds a note index by walking the vault (honouring `vault_ignore_dirs`), extracts every `[[target]]` from the chapter body (alias- and anchor-aware), and surfaces only targets that BOTH do not resolve AND are not chapter forward-refs (`_ChNN`) or external papers (`Author_YYYY...`). Output goes to stdout plus an append-only log at `_temp/wiki_ingest_book_missing_concepts.md`. **Nothing is auto-created**: concept creation is a human judgement (distinct construct versus duplicate), and external citations are out of scope. Treat the report as a review queue: for each entry, (i) create `concepts/{Name}.md` with `status: stub`, (ii) link to an existing concept through aliases, or (iii) ignore.

11. **Closeout**: four edits, then verify, then report.
   - **Book note** (`books/{book}.md`): append the chapter number to `chapters_ingested:`; add its concepts to `concepts_touched`; flip the TOC row from `pending` to `ingested` with a link to the chapter note. **After writing, list the `{book}_Ch*.md` files that are not `status: stub` and confirm the set matches `chapters_ingested:`**; emit `OK chapters_ingested in sync` or fail loudly (Check 8 contract).
   - **`index.md`**: with Bases views, do NOT insert chapter bullets, book summaries or one-liners; only bump the `## Quick Stats` counts and the relevant `## Coverage by Field` rows for new concept or method notes, then re-read the tables. In `manual` mode, add the entries.
   - **`fields/MOC_{FieldName}.md`**: add new notes to their subfield sections.
   - **`log.md`**: append `## [YYYY-MM-DD] ingest-book | {Book Title} > Ch. N: {Chapter Title}` with bullets for created and updated files.
   - **Final verification**: re-read the chapter frontmatter and confirm `book: "[[{parent}]]"` resolves (Check 9). Re-read the parent frontmatter and confirm the chapter is in `chapters_ingested:` (Check 8). Both pass, or the ingest is incomplete.
   - **Report**: chapter note path, concepts and methods created or updated, evidence table (rows checked, reworded, dropped), seals written, and the verification status of Checks 8 and 9.

---

## Naming conventions

| Item | Convention | Example |
|---|---|---|
| Book note | `FirstAuthor_Year_Keyword.md` | `Zatsiorsky_2006_Biomechanics.md` |
| Chapter note | `FirstAuthor_Year_Keyword_ChNN.md` | `Zatsiorsky_2006_Biomechanics_Ch03.md` |
| Chapter citekey | `{book_citekey}_chN` | `zatsiorsky2006_ch3` |

---

## Safety Rules

- **Never read full book text in one pass**; always work chapter by chapter.
- **Never invent** chapter titles, page numbers, ISBN or authors. If uncertain, use `?` and flag it.
- **Claims need sources**: every finding in a concept note cites the chapter note via `[[wikilink]]`.
- **No propagation without a checked quote** (Mode B steps 6b and 8b). Fallback 4 (model knowledge) never reaches a concept or method note and gets no seal.
- **One canonical note per book and per chapter**: check before creating.
- **Append only** to concept notes; never replace existing findings.
- **Local-first fulltext**: for both modes, run `pdftotext` on the local PDF before any MCP fulltext call. Use the reference-manager fulltext only when the local PDF is unavailable or empty (scanned PDF). This keeps entire books out of context.
- **Write notes in the wiki language** (`note_language`, default English), whatever the language of the book. This covers prose, headings, callouts and seals. Deliberate exceptions: `aliases:` (bilingual synonym bridge), verbatim quotes from sources in another language (copied as printed, never translated), `log.md`, and any mirror note that tracks a primary file kept outside the vault (translating a mirror desynchronises it). This is the skill with the demonstrated debt: when the rule was not written down, a whole cohort of book notes came out in the author's native language and needed its own migration wave. `wiki-lint` Check 14 is the radar (off by default: turn it on with `examples/languages/es.json` or your own lists in `lint.language_radar`).
- **The rule binds hardest where the note stops quoting and starts judging**, and the radar does not see that part. Three classes have had to be migrated after the fact, all the writer's own voice: **(a) the relevance-gloss label**, the bold bullet opening an entry under `## Relevance to My Research` (`- **Teaching handball** - ...`); **(b) the self-correction note**, the aside explaining what the note got wrong; **(c) code-switched extraction**, an English sentence with native-language verbs and connectives spliced in. All three go in the wiki language. The template gets filled in English, but a judgement about one's own projects comes out in the language one thinks in. Words with no accent and no stopword are invisible to Check 14, so **the rule written here is the only defence**.

---

## References

- `references/BOOK-INGEST-WORKFLOW.md`: reference-manager sequence for books, naming edge cases, TOC and chapter content strategies, index and log format
- `WIKI_SCHEMA.md`: authoritative schema (concept creation rules, frontmatter contracts, lint rules)
- `skills/wiki-ingest/references/CONCEPT-PROPAGATION.md`: concept creation and update rules (shared)
- `skills/wiki-ingest/references/INGEST-PITFALLS.md`: recurring errors to avoid (shared); read before every ingest
