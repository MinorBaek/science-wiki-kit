# Gotchas: operating notes for ingest, synthesis and lint

> Read this before a batch of `/wiki-ingest`, `/wiki-ingest-book`, `/wiki-synthesize` or `/wiki-lint`.
> Every item here was paid for with a real defect in a research wiki of a few thousand notes. Names,
> dates and exact counts are left out; the magnitudes that matter are kept. The motive of each lint
> check lives in `skills/wiki-lint/references/check-origins.md`; this file is about what to do and what
> not to trust.
>
> **Which sections to read first**
> - Before `wiki-ingest` or `wiki-ingest-book`: sections 1, 2, 3 and 5.
> - Before `wiki-synthesize`: sections 1, 4 and 6; for the evidence check against the PDF, also sections 2 and 3.
> - Before `wiki-lint`, or when a batch of corrections has just landed: sections 4, 5 and 7.
>
> Items tagged **[Windows]** apply only to that platform. Items that mention a reference manager are about
> Zotero-style tools in general; substitute your own. "Source note" means the note of one paper or book chapter.

## 1. Ground rules (the epistemics behind everything else)

- **A tool's silence is a hypothesis about the tool, not a fact about the world.** `0 hits`, a 404, an
  empty glob and "no data in the library" all say only that *that query* returned nothing. In one audit,
  of twenty notes that asserted an absence ("no attachment", "no fulltext"), nine were already false when
  written. Never write "the paper does not...", "no PDF" or "not indexed" without a **positive check**:
  search another way, with spelling variants, and confirm the tool can find something you know is there.
- **The zero of a screen belongs to the detector until proven otherwise.** A screen that reads 0 said "my
  condition was not met", not "the wiki is clean". Before writing a zero in a log, a wave closeout or a
  seal, **inject a positive case and watch it fire** (through the same code path that produced the zero).
  Typical ways a zero lies: a fixed-length prefix in a regex (`.{60}term` rejects a term at the start of a
  line, which is where bullets put it), a decimal point where the source writes a comma, a term split
  across a line break, text decoded with the wrong codec.
- **Validate a pattern by counting, not by reading it.** A pattern that looks right and silently omits one
  variant is the commonest bug in triage: you count 7 where the tool says 8. Count, then compare.
- **A declared correction is not an applied one.** A seal can say "removed two columns" while both are
  still in the table; a seal can name the note it wants updated and be ignored; a seal can record having
  propagated a fix to one of the several notes that cite it, which makes the log look closed. Check the
  artefact, not the changelog.
- **A seal certifies only what it enumerates.** "Checked all rows of the results table" says another table
  (reliability, say) was never read. When a figure you need is missing, read WHAT the seal says it covered,
  not just whether it says clean. And a "not found in the source note" points at the source note before it points at the
  note: with the grep done right, the figure was in the fulltext both times it was checked.
- **A correct figure can still be the wrong claim.** Three families defeat every value-based check: the
  right number bound to the wrong variable, the right number from the wrong object (a result of study Y cited
  as evidence about X), and a right claim hung on a source that is not its source. Only reading what the
  study measured catches them.

## 2. Acquiring and reading sources

**Finding the fulltext**
- The reference manager's fulltext can fail while the PDF exists: HTTP 404 means its fulltext index was not
  built for that attachment; "no suitable attachment" means a metadata-only item. Locate the PDF in your
  library storage before degrading to abstract-only.
- **Locate PDFs by listing and grepping** (`find <dir> -iname "*.pdf" | grep -i <author>`), never with
  `find -iname "*author*"` and never with a glob tool: both have returned false negatives for files that exist
  (network and cloud-synced drives). The same goes for notes: confirm a note exists with a content search or
  `test -f`, not a glob. A `Write` that fails with "file has not been read yet" is proof the file exists.
- **A PDF can have a text layer on page 1 and be image-only inside.** Count words per page on interior
  pages before concluding "no fulltext". If they are empty: find another copy with a text layer, or rasterise
  (`pdftoppm -png -r 200`) and read the images.
- **Resolve by exact citekey or title, not by a free-text query.** Padding the search with descriptive words
  lands on a sibling paper of the same author and year (a three-paper "trilogy" from one study is the
  classic trap) and you ingest the wrong one under the right key. Confirm title, venue and DOI before
  extracting.
- **A year-suffix citekey (`...2019a`) does not reliably map to Part 1 versus Part 2.** Read the real title.
- A hyphen in a reference-manager query can be read as OR; write it as a space. Never use the "search
  everything" mode for a known-item lookup (it returns the attachment, not the article).
- **Matching a PDF folder against the wiki needs the DOI**, not `Author_Year`: the downloaded file carries
  the online-first year and the wiki the issue year. Normalise DOIs (lower case, collapse a printed `//`)
  and beware of a Unicode hyphen (U+2010) in titles.
- A stub is not necessarily the paper you think: it can be a different paper, a book chapter, or two siblings
  conflated. Resolve the real source and compare authors, year and journal against both the stub and the
  citing note's reference list. If it is a different paper, ingest it as a NEW note.
- **The PDF paired with a note can be another work**: a sibling paper of the same group, a complete copy saved
  under another paper's file name, a library record filed under a misspelt author. Check the first page (title,
  authors, venue) every time; a title-similarity score is blind to near-identical titles from one group. Before
  declaring "no PDF", search the library by DOI and by title (the file can hang from another record) and look
  outside the library.
- **The PDF version matters more for quotes than for figures.** Preprints, accepted manuscripts and online-first
  copies are common and often unmarked. Checked figures rarely change between versions, but a verbatim quote can be
  missing from the published one, and a submitted manuscript attached in place of the article can report a
  different number of included studies. Record the version you checked in the seal.
- **Book offsets are per chapter, not per book**: within one book the PDF-to-printed offset ranged over tens of
  pages. Probe the first AND the last page of each chapter (the last PDF page of a chapter can be the next part's
  divider), expect e-books with no printed folios, and do not read an article number in `pages` as a defect.
  Procedure in `wiki-ingest-book` (page-offset calibration).

**Extracting text**
- **Always `pdftotext -enc UTF-8`** (or use a library returning Unicode). Without it some builds emit Latin-1
  and every accented character becomes a replacement glyph, so a search for an accented term silently returns
  zero. If the output contains `�`, it is the encoding, not the PDF.
- **Collapse whitespace before searching a multi-word term** in PDF text: the layout's line break can fall in
  the middle of the term (`PHYSICAL ED-\nUCATION`) and a line-by-line grep never matches.
- Non-ASCII characters in a file name (a Unicode hyphen, an accent) can make some `pdftotext` builds fail with
  "couldn't open file". Copy the PDF to an ASCII name first.
- **For a table, the extractor is a hypothesis and the image is the proof.** Text extraction has produced: a
  minus sign eaten into a digit (`-5.2%` extracted as `25.2%`, a plausible false figure that was copied into
  several notes), a whole row shifted so every value hangs from its neighbour's label, and swapped gene or primer
  identifiers (which no numeric screen can see). When a value looks odd or contradicts the sentence next to it,
  **render the page before reasoning about it**. Prefer the publisher XML (PMC JATS, `<kit>/tools/pmc_tables.py`)
  for tables when the paper has a PMCID. If you only have extracted text, do not propagate the row.
- **Other glyphs get lost besides the minus sign**: the prime (`D′` extracted as `D`, which led a note to claim a
  chapter never mentions `D′`), the degree sign (`°` as `8`), `=`, `≤`, `±`, and ligatures such as `tt` or `fi` that
  break a string match. The layout and non-layout extractions can disagree on the same glyph: grep both, then render.
  A quote matcher's miss is usually the tool (ligatures, interleaved columns, running heads, a reference number or a
  parenthesised p in mid-sentence); two-column PDFs often match only without layout.
- **Scanned pages and pages in other languages are read on the rendered image.** A noisy OCR layer produced a false
  "not in the source".
- **When abstract, text, table and figure disagree, record both versions** in the source note and the seal, and do
  not "correct" the note toward one side. The table usually wins for a paper's own data, but sometimes the figure or
  the abstract does; impossible statistic/p pairs and internally inconsistent figures are quoted as printed, with the
  discrepancy. A misprint is declared, never fixed in silence. (This extends Source-Fidelity Rule 3 of
  `docs/WIKI_SCHEMA.md`.)
- **[Windows]** Write extracted text to a path the file-reading tool can open: in Git Bash on Windows, `/tmp` is not a path
  Windows tools can see. Use the project temp folder.
- If the reference manager's fulltext exceeds the inline limit it is persisted to a file: read that path, do
  not re-fetch.

## 3. Error patterns in ingested notes

An A-to-Z audit of a 1,300-note wiki found at least one defect in 20% of the notes (274 fixes). They are not
random noise; they are systematic modes, each with a defence. The first seven are caught by the Source-Fidelity
Rules (`docs/WIKI_SCHEMA.md`, applied by `wiki-ingest`); the rest survive a grep of the number.

1. **Pre-fulltext notes: fabricated quotes AND numbers.** Ingest from an abstract or from memory produced
   "quotes" that are paraphrases and effect sizes that are not in the paper (one set was propagated to a dozen
   notes). Risk concentrates in very long papers, classics and books, where the fulltext was too big to handle
   and the quotes were reconstructed. Defence: no fulltext, no quotes and no numbers (`status: draft`).
   Verify quotes by string-matching against the fulltext rather than reading both.
2. **Abstract versus table.** The note followed the abstract (or the Discussion) when the paper's own table
   said otherwise. Extract numbers from tables.
3. **Non-verbatim quotes** (paraphrased, or attributed to the wrong author). The most numerous class.
4. **Loose `evidence_level`.** Single-arm pre/post is `cohort`; groups without randomization are `CT`;
   consensus or opinion is `narrative`.
5. **Missing provenance and metadata.** The single largest fix class: back-fill `source_verification`, volume,
   issue, pages. A bulk back-fill of volume and pages taught four things: (a) the library's PDF can be the version
   before pagination (in one pilot, three of ten had neither volume nor pages anywhere in their text), so a value
   taken from a registry needs a second registry independent of Crossref (PubMed, for example) agreeing field by
   field; (b) when print and registry disagree, print wins and a human resolves the row; (c) each row of a batch
   write declares its own citekey and DOI, and the write aborts if the note's frontmatter does not confirm them
   (asserts that check shape cannot see a reused loop variable stamping one paper's data into other notes; the
   identity guard caught a hand-mistyped DOI); (d) no row is written without a human approving it, and an existing
   field is never overwritten.
6. **A/B swaps.** A value attached to the wrong group, side or variable (left/right, dominant/non-dominant,
   a sign flipped). Label every value with its group.
7. **Propagation to sibling notes.** The error was copied into concepts, MOCs and backlinks.
8. **Right figure, wrong column.** The high number is attributed to the variable the reader expects, not to the
   one that occupies that column (a table with no column for a muscle, quoted for that muscle). Read the
   column header before the row.
9. **Fabricated provenance.** The note attributes a finding to a work that is not in the citing paper's
   reference list (9a: the author has zero occurrences; 9b: a real reference that does not support the
   claim). The most dangerous: the number is right, the quote is verbatim, the table matches, only the origin
   is false, and a citation copied into a manuscript is caught by a reviewer who knows the field. Defence:
   cross every cited author against the **citing paper's reference list**.
10. **Homonym concept/method pair: the body links the wrong twin.** Where a concept note and a method note
    share a name root (`X` and `X_Testing`), a paper declares one in `concepts_touched` and links the other in
    its body. Check 12 only validates frontmatter-to-backlink symmetry. The tie-break is the frontmatter plus
    reading the entry (a protocol goes to the method), never "which note links back" (a method note keeps an
    exhaustive papers list by design, a concept note only the papers that add theory).
11. **Fabricated method or architecture label on a correct figure.** The score is real and in the right
    place; the name of the model it is attributed to does not appear in the paper. The same finding then
    enters twice under two names, and a synthesis counting sources sees two architectures converging where
    there is one result. Defence: grep the technical term in the fulltext (zero hits = fabricated label).
12. **The venue does not exist as a journal.** Cheap triggers: a repository DOI prefix (Zenodo, preprint
    servers, figshare) presented as a journal article; a journal with volumes but no Crossref DOI; an ISSN that
    does not resolve or resolves to another title; a venue unrelated to the content. A **quality** warning
    ("weak source, cite the primaries") and an **existence** warning ("this went through no editorial process")
    are different, and the second means "do not cite", not "cite with caution".
13. **A fabricated list member displaces a real one.** An enumerated list with a declared total (eleven
    techniques) keeps its count while one member is invented and the real one disappears, so counting detects
    nothing. Compare the list element by element against the paper's.
14. **The right figure of the wrong object.** Covered in section 1: nothing false to grep; the study measured a
    different model than the note is about. Applies most to method notes where several models share a chapter.

Patterns 15–28 come from checking synthesis entries against the PDF, where most entries never checked had at least
one defect. None leaves a value to grep: they are questions to ask while reading, and the checking brief
(`skills/wiki-synthesize/references/CHECK-BRIEF.md`) puts them to the checker.

15. **Within-group change read as a between-group or treatment effect.** The most repeated reading error; one
    study's within-group change reached several notes as the effect of the intervention. Ask for the group × time
    interaction: a within-group d is not an interaction d, a baseline difference between groups (patients versus
    healthy) is not an intervention effect, and the paper's own significance threshold applies.
16. **A null read as equivalence; a correlation read as agreement or prediction.** "Identical", "interchangeable",
    "without sacrificing" written over a non-significant difference, often with a small sample or low power; a high
    r between two methods with different means read as agreement; a correlation written as "predicts". An
    unreported result is not a reported null.
17. **The design read stronger than it is.** Allocation by team, club or school written as an RCT; "randomized or
    quasi-randomized" as RCT; pre/post without control as `CT`. `evidence_level` belongs to the whole work, the tally
    follows the source note's level, and a wrong level is fixed in the source note, not in the tally.
18. **Validity versus reliability, and inherited figures.** Validity credited to a study that only uses a device and
    cites someone else's validation; a reliability study written as "validated"; an ICC or CV that the work quotes
    from an earlier study (sometimes older than the device) hung on the work as its own.
19. **Dependent sources counted as independent.** Reviews that share trials, several works reproducing one original
    study, two papers on one sample or a subset of it, a review cited alongside a trial it contains, papers of one
    group whose samples may overlap, two works citing the same origin. Lower the confidence, and the state if it
    rested on convergence.
20. **The type of work limits what it supports.** A press release, a short commentary, a hypothesis paper, a
    conference abstract or an opinion piece; a reporting guideline read as a methods guideline; a clinical protocol
    read as a dose, or a review's suggested protocol read as the dose its trials used; normative values read as
    thresholds; a review's tables read as its conclusions (find the sentence in its Discussion or Conclusions); a
    review that lists a method as emerging validates nothing.
21. **Advice hardened into a rule.** "Should", "may", "advised", "a rough guide" became "must", "mandatory",
    "never", "superseded", "resolved"; a call for future research became a recommendation; and the direction can
    flip (a minimum read as a ceiling). The `hedge` class at its most consequential.
22. **A chapter loaded with another work's rules.** Thresholds, corrections or formulas standard in the field,
    attributed to a chapter that never states them (they were in a sibling chapter, another book, or nowhere).
    Search the term in the chapter before attributing it. A table the wiki derived (interpolated, recomputed) is
    marked as the wiki's calculation.
23. **Status labels and settled debates the source does not give.** "Gold standard", "canonical", "consensus",
    "dominant" (for "one of the most used"); an open debate written as resolved; a "gap" the work actually addresses.
24. **Inversions cluster where the wiki already had a story.** "Adaptation" where the source says risk factor,
    "protective" for susceptibility, "masked by compensation" where the source says there is no compensation. Be most
    suspicious of the sentence that best fits the note's theme.
25. **Small slips with large effects.** Animal or in-vitro work given as human; a laboratory's experience or opinion
    given as a rule; one or two subjects given as a norm; an exception stated wider than the source; a figure from the
    neighbouring paragraph, or composed from a table and the text; a reference-list title read as a finding; a model
    validated by windows or records rather than by subject presented as ready for deployment.
26. **The wiki corrects itself wrongly.** An old correction can be the error, and its seal will defend it; the source
    note can keep the old verdict after the seal that corrects it (after sealing, grep the source note for the
    corrected word); a block can be corrected while the body keeps the old form.
27. **A statistical improvement sold as a clinical threshold.** An exclusivity or universality quantifier ("only",
    "all arms", "both groups", "no other") glued to a threshold (MCID, MDC, SWC). Improving and crossing the threshold
    can split the arms in opposite directions: one arm alone crossed the MCID while nearly every arm, the untreated
    control included, improved. Ask of each entry: improvement or crossing, and in how many arms exactly? A screen for
    the co-occurrence is a reading list, never a verdict or a blocking check.
28. **A secondary citation dressed as the work's own finding.** The figure is in the source note, so every value
    check passes; what is false is the provenance the line implies (the work cites the figure from other studies).
    Check whether the work measured it or inherits it. A screen over source notes sees only the provenance a source
    note recorded: its zero means "no source note records an inherited figure", not "no note misattributes", and in
    one trial its top leads were all false positives. A reading list, never a blocking check.

Related: **when the studies included in a review do not match the wiki's source notes for those studies, check the
review's bibliography against Crossref (DOI and title) before propagating any of its figures**, with positive
controls from your own wiki, and record what you measured without attributing a cause.

## 4. Propagation and drift

The common root: **every file stays coherent with itself, and the contradiction exists only between files**, so
no per-file check sees it.

- **A corrected source note does not correct the notes that cite it.** After any source note correction, sweep the notes
  that cite it. A correction reaches more notes than the report names (a sign thought to be in one note was in
  four): count with `grep -rln` before deciding the scope, and write the number in the seal.
- **A partial propagation is as invisible as none, and misleads more.** A seal listing the places it propagated
  to looks closed; the unlisted one kept the old value for weeks.
- **Grep the value-and-label pair, not just the value.** When a source note adjudicates an internal contradiction of
  its source in a callout, the rejected version can live on downstream: the number was right everywhere and the
  condition glued to it was wrong. The callout that adjudicates is not propagated.
- **A sweep navigates by value, so it only reaches defects that have one.** A false sentence, a misplaced bold
  or a missing row has no value to grep. After correcting a source note, also look at which notes REPLICATE its
  tables: there the failure is a row that is gone, an emphasis, or a stale summary sentence. A truncated
  replica is not itself a defect (an explicitly labelled selection is fine); an unlabelled one disables
  any audit of the arithmetic derived from it.
- **A side-finding that is not written down the moment it appears does not exist tomorrow.** Dump the whole list
  into the log in the turn it appears, not at the closeout.
- **When you correct a sign, write the convention too** (a source that computes t as pre minus post makes every
  improvement negative); without the gloss the next reader "fixes" it back.
- **The stale claim can sit inside one file.** The corrected figure is written where it hurts and nobody
  searches where else the same file said it. The worst place is frontmatter: a one-line `next_step` that
  grows by accretion (each session appends instead of rewriting) is read at a glance and never re-read.
- **Mirror notes lie.** A decision revised in the canonical note does not travel to the mirror note that is
  consulted for a report or a dossier; a pointer ("details in the canonical note") says where the detail is,
  it does not synchronise figures. Search the OLD figure, not the topic.
- **A line number (`L286`) is mutable state.** Inside a dated seal it is history and harmless; inside a
  synthesis block, which is read as a live claim, it is a defect (it may point at the right line by luck).
- **A generator that lives in a session scratchpad makes its output irreproducible.** If a repo file is
  generated, the generator goes in the repo next to it, in the same pass, and the file says which script
  produces it. Rebuilding by eye from the output does not reproduce it.

## 5. Structure and maintenance of the wiki

- **Renames.** Ingest may rename a stub to a more descriptive filename (the skill picks keywords from the
  fulltext, not from the stub's working title); that is intended. After any batch: delete the orphan stub,
  relink every `[[OldName]]` (typically book chapters) and drop the "pending ingest" marks. A duplicate-stub
  hunt is a `status: stub` grep plus a glob on author and year.
- **Do not auto-create stubs for every externally cited paper.** One chapter ingest would create dozens of
  phantom notes that are never developed. But also **do not tolerate a growing pile of broken links** as
  "cosmetic debt": each deserves a decision (map to an existing canonical note, create a stub for a legitimate
  construct, ingest the paper, or remove the brackets). Intra-book forward references DO get auto-stubs (their
  metadata lives in the hub's TOC).
- **Merging two notes.** Order: merge the body, run `wiki-synthesize` on the survivor, redirect references,
  archive with a seal (never delete), update index counters, log, relint. The reference sweep fails in four
  places: (1) frontmatter lists must be edited by parsing the list, not with a word regex (a lookahead for
  `[[Note]]` skips the bare token that closes a YAML list); (2) mentions inside seal callouts, logs and archived
  indexes are history and must NOT be redirected (exclude them before running the script); (3) the vocabulary is
  generated, so re-run the full generator, not only its second half, or the Check 30 ghost survives looking
  fixed; (4) sub-MOC counters drop when a note is archived. Zero overlap between two notes means two halves of
  one thing, not a duplicate: the merged note grows.
- **The index has two counts that measure different things**: Quick Stats counts every note (stubs included),
  Coverage by Field only the non-stub. Promoting a stub to draft moves Coverage and not Quick Stats. The index
  lists papers alphabetically under their section, and Check 7 sees presence, not placement. With Bases
  views (`index_mode: bases`) nobody maintains per-note lists and Check 7 is skipped; do NOT regenerate a stub
  queue from Check 7 in that mode (it writes an empty list): grep `status: stub`.
- **Synthesis hubs.** Concept notes created after ingesting an SR or scoping review are referenced by sibling
  concepts and the MOC, never by a paper; Check 1 recognises them through concept-to-concept backlinks.
- **Several concepts from one paper are fine** if they are distinct constructs. `final` needs N distinct source
  works, and a book parent plus its chapters is one work.
- **Routing: by the function measured, not by the surface name** (RPE used to prescribe load is a different
  construct from the session-RPE method; two products from the same manufacturer measuring different things
  are different notes). Keep a list of confirmed rulings.
- **A new concept or method note can collide with a note outside the wiki.** Obsidian resolves `[[Name]]` by file
  stem across the whole vault, so a new `concepts/X.md` that shares its stem with a project or manuscript note
  elsewhere in the vault makes every bare `[[X]]` ambiguous, on both sides. Before creating the note, search the
  whole `vault_root`, not only `wiki_root` (command in `wiki-ingest`, step 7), and on a hit stop and ask for a
  distinct name or path-qualified links. This is not the concept/method twin of section 3, pattern 10, which lives
  inside the wiki.
- **The Edit tool and descriptions.** When an edit trims an existing list entry's description and inserts a
  new entry after it, the removed text can reappear glued to the NEXT entry. Include both full descriptions
  in the new text, or re-read the affected lines right after the edit.
- **CRLF.** A multiline `$` regex or a text-mode read-modify-write converts or splits CRLF silently, and
  `git status` may not notice. Edit by lines, preserve the file's EOL, and run an end-of-line screen after bulk
  edits.
- **Run a structural Markdown check (table column counts) after each batch.** The semantic checks cannot see a
  broken table, and a column mismatch was the only visible symptom of three content errors. Do not hand-roll
  the rule (it gives several times too many false positives); use `wiki-lint` Check 26.
- **Run the lint from the vault root** (or pass `--vault-root`): a tool that resolves the vault relative to the
  current directory silently reports zero notes after a stray `cd`.
- **[Windows] Pipelines in Git Bash that start with PowerShell's `*>&1`**: bash expands the `*` as a glob and passes the
  directory listing as arguments. Put the whole pipeline inside one quoted `powershell -Command "..."`.

## 6. The synthesis layer

- **Standing policy for batch mode.** An unverifiable key number (T1) goes to verify-on-escalation; a new
  structural contradiction (T3) keeps the contested state (⚖️); the only thing asked of the human is the
  cluster. Check the seal first before treating a pre-cutoff paper as unverified: most are properly verified.
- **The findings store is not always `## Key Findings`.** That is a concept-note convention; method notes keep
  their claims in other sections. Read the note's section list before looking for a heading. Only an EMPTY
  store is an anomaly.
- **The highest-yield item in a subagent brief is the seal, treated as a checklist.** For each cited work,
  grep its `source_verification` for corrections and, for each one, check the note AND the source note itself
  (section 1). When a seal says it corrected "a range", check which table row the range belongs to before
  deciding the note's version is wrong: two different rows of one table can both be right.
- **The gate (V1) checks the NOTE, not the ENTRY.** A source cited anywhere in the body satisfies V1 for every
  entry of the block, so an entry can hang a figure from the wrong source among its own note's sources, and a
  mis-attributed figure that is also anchored passes all five checks. The PDF check is the only defence.
  Sibling pattern: soldering two independent proportions from one source into a subgroup nobody reports.
- **A defect can live in the body or in the block, not necessarily both.** An inversion was found only in a note's
  body in one case and only in its block in another. Check the block even when the body agrees with the source,
  and the body even when the block does.
- **A checker's false "not found" ends up in the orchestrator's seal.** False absences from subagents kept coming
  (a stem such as `randomi` searched as `randomly`), and once one is in a seal, later proposals inherit it: one
  false seal carried over a dozen coherent proposals with it. Re-read every absence in the PDF before it reaches a
  seal. A subagent can also derive a figure from the means instead of finding the printed one.
- **Brief wording is read literally.** "Judge only against this note" was read as "skip the works already sealed"
  (write "CHECK the already-sealed works too"); subagents told to read whole notes started with `grep` until the
  full read, by line ranges, was ordered in the first prompt; and fitting the prompt to the dominant defect class
  paid ("flag only what contradicts the magnitude the seal states" produced no false positives).
- **Triage proposals need the source paragraph.** Subagents proposing fixes from seals proposed downgrades the
  source contradicts (removing "RCT" from a randomised trial, "significantly" from p < 0.001), inverted adjectives,
  called contradictory a figure that measures something else, and added new figures to blocks. Apply only what the
  seal covers, after re-reading the whole paragraph (see `docs/SEALS.md` for why narrow seals mislead triage).
- **Removing a figure can orphan another that matched it by chance**, so run the screens after applying a batch,
  not before. An orphan figure that the source does print is fixed by filling the source note, not by deleting it
  from the note.
- **A state changes only when the sources disagree or the core claim does not hold.** Otherwise lower the confidence
  and keep the glyph. Every state transition goes to the human, and a change to a claim shared by several notes is
  propagated to all of them.
- **A backlog item written as a fact is a hypothesis.** Items of the form "note X has the wrong figure" failed
  repeatedly when checked, and a backlog reviewed against the PDF often sided with the wiki or with an erratum in
  the source.
- **Tally per source note, not per work.** In `(N src: ...)`, N counts distinct `[[wikilinks]]`; five chapters of one
  book are five sources there and ONE work for Check 15. Both are right because they answer different
  questions (how well the sentence is backed versus whether the note qualifies). A type with no number means
  "all of them". The breakdown may name only the dominant design (a subset is not a defect); naming a design the
  entry does not cite is.
- **`last_verified` is written together with `source_verification`**, including for hand-written partial seals
  and for any source note filled or corrected against the fulltext: filling a source note is a verification. Check 15's
  `stale` reads only `last_verified`; without it a corrected source never re-flags the blocks citing it. `seal.py`
  moves it only with `--source-corrected` (or when the source note has none): a plain pair seal leaves the source
  note's date alone, or every block citing the work would turn `stale` for nothing (issue #5).
  `synth_write.py` adds `last_verified` to the note when it writes the block if the note has none; an existing
  date is left as it is.
- **Check 15 `stale` is blind to equal dates, permanently** (it compares by day with a strict `>`): a block
  dated the day a work was ingested is not flagged even if it does not incorporate that work. List those notes
  by hand after an ingest.
- **With several candidate PDFs, check the one the source note's seal names**, comparing version and page count: an
  accepted manuscript can lack what the published version carries and produce false defects.
- **Do not read a Check 13 delta, and do not quote an absolute floor of Check 14 or 25.** Only the delta is
  transferable for those, and Check 13 is a large slow-moving INFO backlog.
- **Absorbing retitles `Controversies or Gaps`, it does not delete it** (see `wiki-synthesize`); read the whole
  section before absorbing, because anything in it now appears under the new heading.

## 7. Language of the notes

- Write notes in the wiki language (`note_language`) whatever the language of the source. Exceptions:
  `aliases:` (the bilingual bridge), verbatim quotes from sources in another language, and the log.
- **Where it leaks:** in the ANNOTATIONS of a batch of corrections. The side note is written in the language
  you are reasoning in, not the language of the note: a batch that closed a language-normalisation campaign
  produced new foreign-language annotations the same day. After any correction batch, run an accent sweep over
  the files you touched. A correct sweep leaves only proper names.
- **The language radar (Check 14) fails on both sides.** It counts acronyms (`CON` for concentric, `LAS`/`HAS`),
  angle abbreviations and an English heading whose folded form collides with a foreign word as foreign
  language; and it does not see a whole foreign-language paragraph that avoids its stopwords. Closing a folder
  takes two screens: the detector and an accent sweep.
- The class the radar cannot see at all is the writer's own voice: relevance-gloss labels, self-correction
  asides and code-switched sentences. The rule written in the skill is the only defence.

## 8. Operating habits

- **One queue, one list.** Keep a single ingest queue in one note, not one per source of papers; and cross it
  with the wiki before trusting it (pending items that already had a note, retrieval keys that had gone stale).
- **Organise before you write.** Put each paper in its library collection and in its storage folder, with
  an identical checksum, and cite the final location (never a transit folder that will be deleted). Having a
  link is not enough: look at the item's children, because a linked file and a duplicate imported attachment
  can coexist.
- **Take dates from the system clock** (`date +%F`), never estimate them.
- **Delegate to subagents deliberately.** Decide what each does and how many (a subagent starts cold and
  re-derives context the main thread already has), let the human approve the plan, and once a subagent has
  reported, do not redo its work.
