# Book Ingest Workflow: Detailed Reference

Companion to `wiki-ingest-book/SKILL.md`. Read this when the main steps need more detail, especially reference-manager resolution, naming edge cases and chapter content strategies.

---

## 1. Reference-manager sequence for books (Zotero MCP)

Books have `itemType: book`, or `itemType: bookSection` for edited volumes with individual chapter entries.

### Step 1: Search
```
zotero_search_items(query="{book title}", qmode="titleCreatorYear", limit=5)
```
Books may appear alongside papers. Identify the correct item by `itemType`. (Search semantics and the hyphen-as-OR gotcha: `wiki-ingest/references/INGEST-WORKFLOW.md`.)

### Step 2: Metadata
```
zotero_item_metadata(item_key)
```

| Library field | Frontmatter field | Notes |
|---|---|---|
| `title` | `title` | Full title including subtitle |
| `author` | `authors` | "Last, First" becomes last name only |
| `editor` | `editors` | Edited volumes only |
| `date` | `year` | 4-digit year |
| `publisher` | `publisher` | Full publisher name |
| `ISBN` | `isbn` | Keep hyphens |
| `edition` | `edition` | "2nd", "3rd", ... |
| `DOI` | `doi` | Some books have DOIs |
| `Citation Key` | `citekey` | Copy verbatim from the metadata; never construct one |
| `abstractNote` | used for Key Themes | Often absent for books |

### Step 3: Fulltext (cascade, local-first)

1. **`pdftotext -enc UTF-8` on the local PDF** (default `pdf_library_dir`)
   - Mode A: `-f 1 -l 20` (TOC and early pages)
   - Mode B: `-f <chapter_start> -l <chapter_end>`
2. **Reference-manager fulltext**: only if local extraction failed
3. **User paste**: only if both of the above failed
4. **Model knowledge**: last resort, every claim flagged `[!warning]`

**MCP fulltext decision table (only when reached as fallback 2):**

| Fulltext result | Action |
|---|---|
| under 2,000 words | Use directly |
| 2,000 to 5,000 words | Mode A only; Mode B needs a page range, so request a paste |
| over 5,000 words or multi-chapter | Skip; ask for a paste |
| Empty or scan only | Model knowledge with `[!warning]` |
| `bookSection` item | Use directly for Mode B |

---

## 1bis. Local PDF resolution

### Filename pattern (Zotero default export)
`{First Author Last Name} - {YEAR} - {Title}.pdf`

Examples: `Haff - 2016 - Essentials of strength training and conditioning.pdf`, `Hastie et al. - 2009 - The elements of statistical learning.pdf`.

### Resolution algorithm

```bash
# 1. Enumerate PDFs and grep the author. Do NOT use a glob tool or `find -iname "*<author>*"`:
#    both have documented false negatives for files that exist (network and cloud-synced drives).
find "<pdf_library_dir>" -iname "*.pdf" | grep -i "<first_author_lastname>"
#    The book may live in a thematic subfolder outside the books folder; if the first pass is
#    empty, widen the search root to the whole library.

# 2. Branch on results
#    Exactly 1 match  -> use it
#    0 or >1 matches  -> ask the user: "I could not find the PDF of '{book title}' by author.
#                        What is the exact path?"
#    User-provided path fails -> fall back to the cascade (reference-manager fulltext, paste, model knowledge)
```

### Extraction commands

```bash
# Mode A: TOC and front matter
pdftotext -enc UTF-8 -f 1 -l 20 "<book.pdf>" -

# Mode B: a specific chapter (for example PDF pages 87 to 114)
pdftotext -enc UTF-8 -f 87 -l 114 "<book.pdf>" -
```

On Windows, `pdftotext` is not on the PATH by default (it ships with poppler); either add it or call it by full path. Without `-enc UTF-8` it emits Latin-1 there, accents break, and a search for an accented term returns a false zero.

### Detecting scanned PDFs
If `pdftotext` returns under 100 characters for a 20-page slice, the PDF is scanned. Also check *interior* pages, not just page 1: a PDF can carry a text layer on the first page but be image-only inside (words per page near 0). Confirm with `pdftotext -f <p> -l <p> "<book.pdf>" - | wc -w` on a few interior pages. If they are empty, drop to fallback 2 or rasterise (`pdftoppm -png -r 200 -f N -l M "<book.pdf>" out`) and read the PNGs, or OCR with docling.

### Non-ASCII filename hazard
If the PDF path contains a Unicode hyphen, dash or accent, `pdftotext` may fail with `Couldn't open file` (the binary receives the name mangled). Copy the PDF to an ASCII name in a temp folder first and run `pdftotext` on the copy.

---

## 2. Filename conventions

### Book notes
`FirstAuthor_Year_Keyword.md`

- **FirstAuthor**: last name of the first author or first editor (ASCII only, no spaces): Zuñiga becomes Zuniga, García becomes Garcia.
- **Year**: 4-digit year of the edition being ingested.
- **Keyword**: 1 to 3 words on the book's core topic, not its full title.
  - "Science and Practice of Strength Training" becomes `Zatsiorsky_2006_StrengthTraining`
  - "Essentials of Strength Training and Conditioning" becomes `Haff_2016_StrengthConditioning`

### Chapter notes
`FirstAuthor_Year_Keyword_ChNN.md`

- `NN` is the zero-padded chapter number: `Ch01`, `Ch03`, `Ch12`.
- If a book uses Parts, keep numbering chapters continuously (`Ch05`, not `Pt02_Ch05`): every tool reads
  `{book}_ChNN`, and a Parts prefix breaks Checks 6, 8 and 15.
- Unnumbered chapters get a short slug: `Intro`, `Appendix_A`.

### Citekey convention
- Book: the reference manager's key (never construct one).
- Chapter: `{book_citekey}_ch{N}`, for example `zatsiorsky2006strength_ch3`.

---

## 3. TOC construction strategies

In priority order:

1. **`pdftotext -f 1 -l 20` on the local PDF**: front matter and TOC are in the first 20 pages.
2. **Reference-manager metadata**: `bookSection` items are individual chapters; search for all items with the same parent.
3. **Reference-manager fulltext**: only if the local PDF is unavailable.
4. **Model knowledge**: for very well-known textbooks the TOC is reliably known. Mark it with `[!note]` as coming from model knowledge.
5. **User provides**: ask the user to paste the TOC. Mark it "Source: user-provided".

In the book note:
```markdown
| Ch. | Title | Pages | Status |
|---|---|---|---|
| 1  | Introduction to Strength Training | 1-24 | pending |
| 2  | Neuromuscular Physiology | 25-60 | pending |
```
`create_forward_ref_stubs.py` accepts several row shapes (chapter number in column 1, or Part in column 1 and chapter number in column 2); the chapter number is the first pure-integer cell.

---

## 4. Chapter content strategies

In priority order:

1. **`pdftotext -f <start> -l <end>` on the local PDF**: primary path, cheapest and most precise (1k to 8k tokens per chapter).
2. **`bookSection` item**: if the chapter has its own library entry, use that item's fulltext directly.
3. **Whole-book fulltext**: only if the local PDF is unavailable AND the book is under 5,000 words.
4. **User pastes the chapter text**: for unavailable PDFs or scan-only books.
5. **Model knowledge**: last resort. Add `[!warning]` to every claim and cite the chapter note as `[model knowledge: full text not available]`.

---

## 4bis. Source-fidelity gate (mandatory before writing the note)

Apply `WIKI_SCHEMA.md` → **Source-Fidelity Rules**, adapted to chapters and books. Checklist (examples in `wiki-ingest/references/INGEST-PITFALLS.md`):

1. **Do I have the chapter text in front of me?** If it is model knowledge or a scan without OCR: `status: draft` or `stub`, no quotes, no numbers, `[!warning]` on every claim. STOP: do not populate Useful Quotes or statistics. (P1)
2. **Quotes** are copy-pasted verbatim from the chapter text, never from memory and never attributed to another chapter or author. (P3)
3. **Numbers** come from the chapter's TABLES and figures, not from the chapter summary or the book overview; discrepancies are documented inline. (P2)
4. **`evidence_level`**: `textbook` by default. If the chapter is itself an SR/MA or another primary design, apply the decision table. (P4)
5. **Provenance**: reference key, ISBN, chapter and pages verified, and date, in `source_verification`. (P5)
6. **Every value is labelled** with its group, side or condition. (P6)
7. If this **corrects a previous value**: search the wrong value across `papers/`, `books/`, `concepts/` and `methods/`. (P7)

---

## 5. Concept extraction rules (books versus papers)

The heuristic is **identical** to papers; use `wiki-ingest/references/CONCEPT-PROPAGATION.md`.

Reminders for books:
- **Book overview (Mode A)**: extract 3 to 5 high-level themes. They map to concepts only if the concept is core to a research line AND 2 or more wiki papers already touch it. Otherwise list the theme in the book note without creating a concept note.
- **Chapter ingest (Mode B)**: full extraction, 3 to 8 concepts and 1 to 4 methods per chapter, same threshold as papers.
- **Do not create a concept note for every topic a textbook mentions**: textbooks cover many topics superficially. Create notes only for topics the chapter treats deeply enough to add a verified finding.

---

## 6. Index and log format

### index.md: Books section
With `index_mode: bases`, the `## Books` section is an embedded Obsidian Bases view (`![[Books.base]]`) that auto-lists every note in `books/` from frontmatter. Do not hand-maintain a book list; only bump the `## Quick Stats` "Books (ingested)" count when a new parent book is completed. In `manual` mode, add a one-line entry per book instead:

```markdown
- [[Zatsiorsky_2006_StrengthTraining]]: comprehensive biomechanics and physiology of strength training; 2/15 chapters ingested
```

### log.md: book entries

```
## [YYYY-MM-DD] ingest-book | {Book Title}: overview

- Created: books/FirstAuthor_Year_Keyword.md
- TOC: N chapters identified
- Key themes: Concept_A, Concept_B
- Reference key: XXXXXXXX | ISBN: 978-...

## [YYYY-MM-DD] ingest-book | {Book Title} > Ch. N: {Chapter Title}

- Created: books/FirstAuthor_Year_Keyword_ChNN.md
- Updated concepts: concepts/Concept_A.md, concepts/Concept_B.md
- Created concepts: concepts/New_Concept.md
- Updated book note: chapters_ingested now includes Ch. N
```

---

## 7. Lint rules for books

`wiki-lint` covers these automatically, but be aware:

- **Book notes without any ingested chapters**: acceptable if recently created, not orphaned.
- **Chapter notes without a `book:` link**: flagged as a broken backlink.
- **Concept notes citing chapter notes**: valid backlinks, treated like paper-note citations.
- **`chapters_ingested` out of sync with the chapter files**: flagged.
