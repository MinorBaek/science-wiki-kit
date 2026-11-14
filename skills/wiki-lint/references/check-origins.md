# Where each wiki-lint check comes from

> **What this file is for.** A check that produces noise and does not explain why it exists ends up
> disabled or emptied blind. This file keeps the motive of each check: the failure that created it,
> what is lost if it is switched off, and the false positives it is known to have. **Read the entry
> BEFORE disabling or emptying a check.**
>
> The motives come from the research wiki this kit was extracted from (a sport-science wiki of a few
> thousand notes). Note names, dates and exact counts are left out; the magnitudes that matter are kept.

| File | Answers |
|---|---|
| `references/check-origins.md` (this one) | **why** a check exists |
| `SKILL.md` | **what** it does (terse summary of the logic) |
| `wikikit/lint/checks_*.py` | **how** it is implemented |
| `tests/fixtures/lint/expected_counters.txt` | **why the fixture value is what it is** (guarded branch, bisection) |

At the end of a live run, `lint.py` prints the `check-origins.md#check-N` pointer for every check
that fired.

---

## check-1

**Origin.** Synthesis-hub concept notes (created when an SR or scoping review is ingested) are
referenced by sibling concepts and by the MOC, **never by a paper**. With the original logic (backlinks
from papers and books only) every hub was declared an orphan. The check was widened to count
concept-to-concept backlinks (inline links and `related_concepts`).

**If disabled.** False orphans return in the synthesis layer, the layer that is most expensive to build.
A regression in either path moves the fixture counter from 2 to 4.

## check-2

**Origin.** Not documented in the source project (it predates its versioning). Purpose: a method note
that nothing cites and that cites nothing is disconnected from the evidence. A method note is NOT an
orphan if it cites at least one paper or book chapter, even when nothing links back (the one-way
method-to-source reference is enough for navigation; textbook-derived method notes are the canonical case).
Union the paper and book sets when testing the outgoing links: restricting to papers produces false positives.

## check-3

**Origin.** Its name says "empty `concepts_touched`", but its operational role is to be the **canary for
frontmatter corruption in batch ingests**. The frontmatter parser takes the next line starting with `---`
as the closing delimiter: if the real closing `---` is missing, it either grabs a horizontal rule from the
body (parses anyway, no flag) or returns an empty frontmatter (fires here). It is a **partial** canary: in
the incident that revealed this it caught 1 of 5 corruptions.

**If disabled.** You lose the only indicator that a subagent broke frontmatter during a wave. Using
"Check 3 = 0" as a per-wave seal is a sound practice.

## check-4

**Origin.** Not documented in the source project. Purpose: a concept note asserting findings with no
citation nearby is unsourced.

**Scope note.** Its `verb_list` is ten English verbs, so it is **blind to figures**:
`ICC = 0.91 (95% CI 0.84-0.95)` contains none of them. That gap is covered by [check-25](#check-25), not
by widening this one.

## check-5

**Origin.** Broken links resolved against the **whole vault**, so a link to a project or person note is not
"broken" (a wiki-only index produced a flood of false positives). Enumerating `fields/` recursively
surfaced sub-MOC links that had been invisible. Two conventions exist because of this check: slugs of an
agent's out-of-vault memory are never written as `[[wikilinks]]` (they would break here), and stubs are not
auto-created for every externally cited paper (it would inflate the graph just to silence the check).

**Empty targets.** `[[]]` and `[[|alias]]` are invisible to the wikilink extractor (its pattern needs at
least one character), so the check's zero was the pattern's, not the wiki's: a pass that confused the `|` of
a formula (`r(AB|C)`, `|ad-bc|`) with the alias separator ate text between the `|` and the next `]]` in a
cohort of notes and went unseen for months. They are found separately on the raw body (skipping fences and
code spans, where `[[]]` is quoted text, not a link).

**If disabled.** Placeholders (`[[ChapterNote]]`) stop being distinguishable from truly broken links.

## check-6

**Origin.** A strict promotion policy: `final` requires at least N **distinct source works**
(`min_distinct_sources_for_final`, default 2), and a book parent plus its chapters count as **one** work. The
previous logic counted resolving wikilink occurrences, so a note backed only by one book (parent plus two
chapters = three occurrences) was promoted with a single real source.

**If disabled.** Single-source notes get promoted to `final`, exactly what the evidence criterion exists to prevent.

**Known false positives.** It counts cross-links as sources and does not exempt by `type` or folder. Check
by hand before promoting.

## check-7 / check-7b

**Origin.** Check 7 verifies **presence** of a wikilink in `index.md` and by design cannot see location: a
paper listed under `## Books` passed clean. Check 7b closes exactly that gap.

**Status.** Both are **skipped** with `index_mode = "bases"`: the index embeds Obsidian Bases views instead of
per-note lists, so every note would false-flag. They stay because the mode is configurable.

## check-8

**Origin.** Sync between `chapters_ingested` and the `{book}_Ch*.md` glob. It parses `Ch(\d+)`, that is,
**numeric chapters only**. A convention follows: front-matter chapters with Roman numerals (`_ChV`, `_ChIII`)
are recorded in a separate field, not in `chapters_ingested`, so they do not false-flag here.

**If disabled.** A book can end up with ingested but undeclared chapters (or the reverse), and Check 6
miscounts the distinct source works that depend on that list.

## check-9

**Origin.** Not documented in the source project. Purpose: a chapter note without a resolving `book:` link
is cut off from its parent.

## check-10

**Origin.** `index.md` carries **two counts that measure different things**: `## Quick Stats` counts every
note (stubs included) and `## Coverage by Field` only the non-stub ones. Promoting a stub to draft moves
Coverage and does **not** move Quick Stats, so the drift is silent by construction.

**If disabled.** The index keeps declaring figures that no longer match the disk, and those are the figures
quoted when reporting the wiki's state.

## check-11

**Origin.** Like Check 10 at field-row level. Deliberately scoped to **field-level** rows at first: unfielded
notes are reported as INFO, never as a mismatch, so the check does not turn into noise during a field backfill.

**Widened to subfield rows.** The narrow scope was written in the code, but the index's own footnote claimed
the check validated the `->` rows too. Nobody looked at them because they were advertised as watched, and
once measured, **about half had drifted**, almost all by undercount (the wiki grows and the row stays), and
one subfield had live notes and no row at all. The check now covers both levels and missing rows:

- **field rows**: counted by `field:`, matched by the label in cell 0;
- **`->` rows**: counted by `subfield:`, matched by the **`[[MOC_*]]` link in cell 1, never by the label**
  (a display name does not slugify to the subfield slug);
- **`MISSING-ROW|<slug>`**: a subfield with at least one non-stub note and no row, which is invisible to any
  row-by-row comparison.

The Papers column stays out on purpose: it is a cross-listed membership view, not a partition.

**The lesson that is worth more than the check.** Do not document a guarantee without checking that the engine
provides it. A footnote that promises monitoring **switches off human monitoring**, and drift accumulates
exactly where it was announced it could not.

## check-12

**Origin.** An edge `paper -> concepts_touched[token]` with no backlink leaves the concept invisible from the
graph even though the paper believes it covered it. Two failures that look like one: `asymmetry` (the target
exists, the backlink is missing, auto-repairable with `fix.py check12`) and `missing_target` (the token
resolves to no note, so the token has to be triaged).

**If disabled.** The concept layer disconnects from the paper layer and nothing says so.

## check-13

**Origin.** An alias documented in one concept's frontmatter and used in another concept's prose **without a
link** breaks retrieval whenever `_VOCABULARY.md` is the only synonym bridge (no embedding search). INFO
backlog, not gating.

**Determinism.** When several concepts declare the same alias, which one is "the canonical" used to depend
on the enumeration order of a hash table, so two runs over an untouched tree gave totals that differed by a
few dozen. The kit's version is deterministic: an alias shared by several notes counts as linked if the
note links to **any** of them (or is one of them), and the canonical column lists the candidates joined by `/`.
Nothing is hidden that the old rule did not also hide; it only stops flagging notes that already link one of
the alias's meanings.

**Scope limits, not defects.** Blockquote lines are not searched, so the check sees nothing inside a callout
(State-of-Knowledge blocks included). Never close or block a batch because of a Check 13 delta.

## check-14

**Origin.** A radar for content in a language other than the wiki's, to scope the normalisation pass.
Report-only, and **disabled unless `language_radar.enabled`**; the Spanish lists in
`examples/languages/es.json` are an example, not a default.

**Design points that each came from a measured false positive:**

- The H1 is the title of the note and, for a paper, the real title of the source: a source in another language
  has its title in that language without breaking the rule. Only H2 to H6 count.
- A heading word whose accent-folded form collides with an English word (`conclusion`) counts only if it keeps
  its accent (`heading_requires_accent`).
- A stopword that is also an upper-case acronym is not prose in that language (`con` as the abbreviation of
  *concentric*, `LAS`/`HAS` as arch stiffness). `case_sensitive_tokens` counts such a token only in lower case,
  `line_guards` skips a line where a second acronym shows it is the abbreviation, and any other stopword
  written entirely in capitals is discounted.
- Blockquotes DO count: they were excluded while callouts were still written in the other language, and the
  quote channel turned out to be the one place where it could sit unseen.

**Known false positive, accepted.** Verbatim quotes from sources written in that language are legitimate text in
a correct note. Before reading a movement of this check as a leak, look at which word it comes from.

**Measuring.** Of a measurement of this check only the **delta** is transferable, never the absolute floor: a
floor cited against a base that keeps growing expires on its own. And measure volume **by lines, not by note
size**: big notes are English with one stray line.

## check-15

**Origin.** Synthesis radar over `final` notes: `missing` = qualifies for a `## State of Knowledge` block and has
none (the `/wiki-synthesize` worklist); `stale` = has a block whose date precedes the newest `last_verified` of
its cited works. A progress meter, not a gate.

**Measured blind spot.** `stale` compares **by day, with a strict `>`**. A work ingested the same day as the
block's `updated` does not flag it, and **the silence is permanent**: the next day the dates are still equal, and
it would only fire if the source note were re-verified later. A `stale = 0` therefore does not prove the blocks are
up to date. Moving to `>=` would flag every synthesised note the day its source is verified, which is the normal
flow, so it is not changed; instead the ingest workflow tells you to list those notes by hand. Also, the newest
`last_verified` is taken over the links of the **whole body**, not only the block's: `stale` can mean "there is a
new source in the note", not "the block cites it".

## check-16

**Origin.** Conformance with the `status` vocabulary of the vault contract, plus template leaks
(`status: draft | review | final` never filled in). A note with no `status`, or with no `type`, is itself the
finding: the check used to exit before looking at anything, so notes that declared a status without a type were
exempt from validation for months. **A missing field is the finding, not an excuse to skip.**

## check-17 · check-18 · check-19 · check-20 · check-21

**Common origin.** An audit of source fidelity across a whole wiki. Five complementary checks that split the
provenance problem into non-overlapping pieces:

- **17** papers with no `source_verification`: the provenance backlog. INFO, large by definition until the field
  is universal; its output is the live work queue of a verification campaign.
- **18** papers that *declare* `source_verification` yet still lack `volume`/`pages` and carry no dated exemption:
  "verified but incomplete".
- **19** `evidence_level` outside the closed vocabulary. Papers only: books use `textbook`, so a **paper** tagged
  `textbook` is a genuine mislabel.
- **20** a leaked `]]` inside a blockquote of `## Useful Quotes`. Empty Useful Quotes sections are **not** flagged
  (many notes legitimately have the heading with no quote), and there is no unbalanced-quote heuristic (it is
  false-positive-prone on multi-line quotes).
- **21** the pre-fulltext cohort: papers dated before `synthesis.prefulltext_cutoff` with no fulltext-level seal,
  the re-verification candidates.

**Check 17, amendment.** A value that **starts with `abstract`** is not a seal. The counter used to accept any
non-empty value, so papers verified only against their abstract (which the protocol forbids) counted as sealed.
A blind re-audit also found that a short legacy seal (`fulltext`, 8 characters) hid substantive residues
([check-31](#check-31) is the answer to that).

**Check 18, the exemption is a dated field, not a word in prose.** The first escape was four words inside the
seal (`online-first`, `no doi`, `preprint`, `ahead-of-print`). Two measured defects killed it: (1) **words do not
expire and papers do**: most "online-first" notes audited had been paginated years earlier, and one seal even
instructed "resolve in the Check 18 sweep" while its own word took the note out of Check 18, so the exemption
switched off the only check that would have revisited it; (2) **a sentence written for a human silenced a
machine**: of the notes missing volume or pages that did not show in the check, most were hidden by a word in the
seal, and about a third were real debt. The replacement is `check18_exempt: "YYYY-MM-DD, reason"`: explicit, dated,
auditable. The inventory goes to its own report, and anything older than `check18_exempt_stale_months` counts as
stale, the way `last_verified` ages. **A malformed value does NOT exempt**: it lands in the backlog labelled,
because a broken exemption must be loud. Fail closed, never silent.

**Check 18, conference papers and theses are exempt by venue and shape, not by the seal text.** A proceedings
paper has no volume because none exists, so it added a permanent, uncorrectable +1. The test is: pages present,
volume absent, venue matching `proceedings|conference|symposium|congress`. Two measured design decisions:
(1) **do not match the seal**: a seal may be written in any language (one said "it is a CONGRESS paper" and
contained none of the English words), so matching its prose would have missed the very case that motivated this;
(2) **requiring pages prevents over-exemption**: journals merely *named* "Proceedings of..." do have volumes, and
the ones flagged here were missing both. A thesis has **neither** volume nor pages (so the shape is both absent,
not the conference shape), and the venue pattern is anchored with `\b`, which is not cosmetic: "Research
Synthesis Methods" contains "thesis" inside "Syn-thesis", and unanchored it would silently exempt a real journal
the day one of its notes lost a field.

**Check 21, gotcha.** The date-only version (without also requiring no fulltext seal) over-flagged papers that
were already verified and fired false T1 escalations in synthesis waves. Derived rule: **verify on escalation**;
check `source_verification` first. A seal only exits the cohort if it reaches **fulltext level**: a seal reading
"partial fulltext, verified at abstract level" is below fulltext, and an upgraded seal keeps its abstract
sentence for provenance and appends the upgrade marker, so the test is "abstract wording AND no upgrade marker",
never "abstract wording appears". Checks 21, 22 and the synthesis gate (V4) must agree on this test.

## check-22

**Origin.** A `⚠` glyph (the "unverified source" mark) on a paper that **already carries a fulltext seal**: the
mark asserts something the verification disproved. The inverse of Check 21: 21 counts papers awaiting
verification, 22 counts marks that verification made obsolete. Nothing else saw them, so they accumulated
silently with every closed verification lot (hundreds on the first sweep).

**How the glyph's owner is resolved** is by **adjacency**: the link immediately to its left if the trimmed left
text ends in `]]`, otherwise the link to its right; a glyph adjacent to no link is a prose caution and is
ignored (hundreds of those exist). Three rules in order: (1) glued to the next link and detached from the previous
one: the next link; (2) otherwise, left text ends in `]]`: the previous link; (3) detached on both sides: the next
link.

**A regression worth remembering.** The first logic trimmed the left side first and so gave the preceding link
priority unconditionally. In a chain of prefixed marks (`[[A]] ⚠[[B]] ⚠[[C]]`) every glyph went to the link
**before** it, so the check was blind in exactly the direction that matters: when the intended owner was sealed
the check stayed silent, and genuine stale marks hid behind it. The mirror error (a mark meant for B reported
against a sealed A) is noisier but harmless.

**Forbidden.** Resolving it with two chained regexes (the second eats the neighbouring link's mark and silently
de-flags an unverified source: it destroyed live marks once), or a `(?<!\]\])` lookbehind (it misses
`]] ⚠ [[KEY]]`). Any bulk edit of marks needs a per-citekey census before and after.

**It has false positives; never empty the list blind.** Resolving an owner is necessary but not sufficient: the
glyph's **tail** is then read, and three forms are not stale marks:

| Tail | What it is | Counts? |
|---|---|---|
| starts with a **letter** (any Unicode letter, either case), after stripping a leading `*`/`_` emphasis | a prose caveat the author wrote ABOUT the source; sealing the paper does not expire it | no |
| starts with emphasis + `(` + letter (`*(corrected 2026-09-06: ...)*`) | a dated annotation; the glyph opens a note ABOUT the verification, so removing it would erase that signal | no |
| starts with `(N src` | the confidence notation of a debates layer, not a source mark | no |
| empty, `,`, `;`, `.`, `\|`, a `(` that is not `(N src`, or a `[[` (prefix) | a real mark | yes |

The wide case rule matters: a narrow `^[a-z]` test missed a capitalised caveat. The exemption is deliberately
**narrow**: exempting too little is noise, exempting too much hides a stale mark, which is the failure above.
The `[[A]] ⚠ [[B]]` ambiguity is resolved to **A**, and that is measured, not assumed (two natural experiments in
the history: a marker that was cleaned on a line removed A's and left B's).

**Method lesson.** A pattern is validated by counting, not by reading it: the first triage pattern silently
left out the italic case without parentheses, and only counting 7 where the check said 8 exposed it. The fixture
therefore has TWO lines for the annotation, not one.

## check-23

**Origin.** A list entry that names a source by wikilink but whose claim text was never written
(`- [[Paper_2018]] - [pending claim]`). It **looks** like support (Checks 1, 4 and 6 count the wikilink as a
source) while asserting nothing, so it inflates apparent coverage. Dozens existed after one propagation lot,
concentrated in the two highest-traffic notes of one research line. Nothing else saw them. The text is
configurable (`unfilled_claim_patterns`); `fix.py check12` inserts `claim_placeholder_text`.

## check-24

**Origin.** A handful of notes carried `journal:` where thousands carried `venue:`. Nothing read `journal`, so
the drift was invisible until the sealing tool, which anchors its bibliographic insert on the `venue:` line,
**silently refused to seal one note**.

> A schema drift that no check watches is eventually discovered by a tool that depends on it, and then it looks
> like a bug in the tool.

**Why it is worth having.** Exact key match: no false positives by construction. That is its whole reason.

## check-25

**Origin.** Check 4 hunts *verbs* without a citation. **Nothing in the engine looked at numbers**: a line like
`ICC = 0.91 (95% CI 0.84-0.95) in overhead athletes` has no verb and passed clean. The defect it covers is
documented: notes written before fulltext acquisition contain non-verbatim quotes **and fabricated figures**,
and the only way to catch them was to grep by hand for the wrong value when someone happened to spot it. The most
expensive defect a wiki can have is a fabricated figure that reaches a manuscript.

**Character.** INFO/backlog, not gating. A high volume is expected on the first sweep.

**Deliberately narrow in v1.** Blockquotes are skipped, which also excludes `## State of Knowledge` and
`## Useful Quotes`. Synthesis blocks do contain figures that should be cited, but they use the `(N src: ...)`
convention and cite on the same line, so including them in the first pass would have drowned the signal. Widening
it is a conscious decision (measure the added noise first), not an oversight.

**The patterns are not "any number".** Only statistics with a value: ICC, `r`/`d`/`g`/`z`/`t`/`F` with a decimal,
`p`, `n =`, a percentage, `±`. ISO dates and block ids are stripped first. The value is reported **in full**
(`ICC = 0.91`, not `ICC = 0`): a truncated value reads as a different figure and sends triage the wrong way.

### First-sweep calibration

The first version had about a third false positives in manual sampling, right at the threshold below which a
check enters the workflow. Two systematic classes, both fixed:

1. **`N% CI` is boilerplate, not a claim.** "95% CI" is fixed terminology; a line like "always report 95%
   confidence intervals alongside the ICC point estimate" contains no figure to verify. The pattern was removed
   and the generic percentage pattern carries a negative lookahead for `% CI`, `% confidence`, `% IC`. When a line
   does carry a real interval, the ICC pattern catches it, and that is the one that names the figure that matters.
2. **`p` is not always a p-value.** In statistical-methodology notes `p` is a variable (`n x p > 5` is the normal
   approximation condition). The pattern now requires a **decimal or scientific notation**.

**Known remaining false positives** (accepted): conventional thresholds, rules of thumb and mathematical
identities written as percentages, and explicitly fictional worked examples. Telling a convention from empirical
data requires **reading the sentence**, so the check does not try. That, not volume, is why it is INFO.

### Triage classes (nothing is exempted)

Each finding is written as `note|Lnn|value|class`:

| Class | What it is | Fix |
|---|---|---|
| `cited` | an author-year in the line names a source **the wiki HAS a note for** | turn it into a `[[wikilink]]`; the cheapest fix |
| `block` | the attribution exists but outside the radius: a section heading, a lead-in line, or a closing `- [[Work]]` line | repeat the link inside the radius; nothing to verify |
| `methods` | the note's field is in `check25_methods_fields`: textbook worked examples and formula constants | none: not claims about the world |
| `domain` | a domain note with no named source | the real campaign queue: locate and verify |
| *(orthogonal axis)* percentage | derivable from the value; where the noise lives | triage the strong-statistic subset first |

Precedence `cited > block > methods > domain`. **Nothing is exempted by field**: a real empirical figure inside a
methods note would stop being seen **silently**, exactly the pathology of Check 22. A field that mixes ML notes
(figures are architecture specs from the paper) with measurement notes (an IMU's ICC is empirical data) is not a
methods field: its findings land in `domain` and stay visible.

**`cited` must name a source the wiki actually has.** It originally tested only the SHAPE of the line (an
author-year anywhere in it), and advertised as one-line fixes rows whose named source is an **internal citation of
an already-ingested textbook** with no note of its own, so there was nothing to link to. Requiring that the
author-year **resolves** to a paper or book note dropped `cited` by more than an order of magnitude with the total
unchanged; the rows fell to `methods` or `domain` by the ordinary rule. Resolution key: first surname + `_` +
year, diacritics and punctuation stripped, against the note stems (`Surname_Year_Slug`). Accepted false negative:
a surname with a lowercase particle (`de Hond 2022`) keys as `hond_2022` while the stem is `deHond_2022`.

**The `block` class, and why it is a re-label, not an exemption.** The +/-2-line radius is blind to where a wiki
really puts its attributions. Measured over a sample of strong-statistic rows, about a quarter were already
attributed that way and the radius saw none. Re-labelling keeps the row printed. There are two guards, both found
by running a triage: (1) **mechanised**: if the row's OWN line names an author-year that does not resolve, the
block does not speak for it (otherwise a 2007 figure would be attributed to a 2014 paper); (2) **not
mechanisable**: a line that synthesises ACROSS the block's sources ("n=9-12 per arm across the four studies here")
is not a figure FROM one of them, and no regex separates that from a datum, so the row stays labelled `block` and a
human has to read it. That is the decisive argument against exempting.

**The two precision tiers differ a lot.** Strong statistics (ICC, `r`, `d`, `p`, `n`, `z`, `t`, `F`, SEM, MDC, CV)
sample clean (almost all true positives); a bare percentage is where the noise lives. Two independent manual
samples gave roughly 30% and 50% false positives over the whole set, concentrated in the percentage class. Triage
the strong subset first. The class labels are display metadata and are **not regression-guarded**: the self-test
compares only the total.

**Do not bulk-edit from this list.** Each entry requires locating the source and verifying the figure, or
removing it. It is the same mistake Check 22 punished.

## check-26

**The incident.** A read-only `markdownlint` census over a few thousand notes returned a few dozen
table-column-count findings. **Three were content defects** that had survived synthesis, sealing and
`status: final`:

- a reliability table with a 6-column header and 5-column rows, so everything read shifted: an **ICC fell under
  the "CV (%)" column** and a CV under "Condition";
- a table with a header **narrower** than its rows: the renderer does not split the row, it **drops the last
  cell silently**, hiding verdicts and worked examples;
- a meta-analysis row bound to the wrong outcome: values the paper reports for the **aggregate** landed on one
  jump type, which left the other row empty. **The structural mismatch was the only visible symptom of the
  misattribution.**

**Why none of the other checks saw it.** All the others are semantic (links, backlinks, vocabulary, provenance,
citation radius, index coverage). None looks at Markdown structure; a broken table renders badly or loses data
without a warning.

**Why native instead of calling markdownlint.** By the GFM spec the only special case is the escaped pipe `\|`;
inside a code span a pipe **does** delimit (that is why MD056 flags `escalc(measure="RR"|"OR")`). It is about 20
lines, and shelling out would add a node and network dependency to an offline, self-contained skill. The native
version is also **strictly more sensitive**: it catches headers that disagree with the delimiter row, which
markdownlint cannot report because in GFM that block is not a table and MD056 never evaluates it (a pipe inside a
code span like `P(xi|yq)`, absolute-value bars in `| n | |t| threshold |`). The **delimiter row is the
authority**, not the header: GFM derives the column count from it.

**Do not hand-roll the rule by eye.** An ad-hoc counter written the same day gave about 5 times too many findings
(2.5x false positives overall) because it did not neutralise the escaped `\|` of table aliases. The escape is a
guarded branch of the fixture; if it stops being neutralised, the self-test fails.

**Not a bulk-fix list.** The three classes need different treatment: escaping a pipe touches no data; a header
missing a column only needs naming; a missing cell means going to the source, case by case.

## check-27

**The incident.** A sweep found notes that literally stored `RÂ²`, `NÃºÃ±ez` and `â€”` where they should hold `R²`,
`Núñez` and `—`: **mojibake**, UTF-8 bytes that were once read as cp1252 and re-saved. It broke nothing the other
checks look at: links resolve, frontmatter parses, tables are square, the text is still English. It is seen only
by reading. And in a scientific note the damage is silent and directional: **what gets corrupted are exactly the
superscripts, range dashes and accents** (`R²`, `0.78–0.89`, surnames). A figure with a corrupted unit still
gets cited.

**The method lesson, worth more than the check.** The first detector was a character range, `[ÂÃâ][-¿]`, and it
**counted 4 of 65**: the commonest sequence `â€”` carries a `€` (U+20AC) outside the range. A mojibake detector by
enumerating characters always misses variants, because the variants are as many as there are non-ASCII characters.

**Detection IS the repair.** If `line.encode('cp1252').decode('utf-8')` does not raise and the result differs, the
line was corrupted **and the result is the correct line**. One operation is both test and fix, and covers every
variant at once. **Both steps must be STRICT**: a lenient cp1252 encoder substitutes `?` for what it cannot map
and a lenient UTF-8 decoder yields U+FFFD for invalid bytes, either of which turns a clean line into a fake hit.
With strict codecs a legitimate `é` or `—` **raises** on decode (its lone cp1252 byte is not valid UTF-8) and is
left alone. No `status` exemption: a stub with corrupted bytes is still corrupted.

## check-28

**A seal without a date is a silent reliability leak, not a typo.** An audit found dozens of papers with
`source_verification` and no `last_verified`: seals from before the protocol made the two fields a mandatory
pair. The damage is not cosmetic: Check 15's `stale` bucket compares a synthesis block's `updated` with the
newest `last_verified` of its cited works. A work sealed without a date **can never trigger that stale**: if the
seal corrected a figure, the blocks citing it still look fresh and nobody looks again. No other check saw it
(17 looks at the seal's absence, 18 at bibliographic metadata, none at the date).

**The backfill is NOT mechanical.** The right date is usually printed inside the seal text itself ("fulltext
verified YYYY-MM-DD"): extracting it from there is legitimate; inventing it is not. Meanwhile the counter is
INFO/backlog.

**Extended to books.** The same leak reappeared through another door: PARTIAL chapter seals written by hand
carried only `source_verification`, because they do not go through the sealing tool that writes the pair. Twenty
sealed and corrected chapters could not re-flag the blocks citing them, and Check 15's stale stayed flat when it
should have risen. The check only looked at `papers/`. In the same closing, many papers whose source notes had been
completed or corrected against the fulltext without moving their `last_verified` were dated: **filling in a
source note is also a verification**.

## check-29

**An out-of-vault slug between brackets is a phantom note in waiting.** Slugs naming files of an agent's memory
(outside the vault) are never valid link targets, and the rule is old, but it depended entirely on human memory.
An audit found live wikilinks to such slugs, ALL of them **outside the wiki folder** (projects, teaching, diary),
beyond the scope of the folder-scoped checks. Hence this check's **vault-wide** scope.

**Two subtleties the first sweep taught.** (1) A slug inside backticks is NOT a defect: it is a code span,
Obsidian does not render it as a link, and the backtick guard excludes it. (2) Historical logs cite slugs when
describing past fixes; rewriting a historical file falsifies it, so they are exempt by basename
(`memory_slug_exempt_files`).

It is **disabled by default** (`memory_slug_prefixes` is empty): it only makes sense for a vault that shares a
folder with an AI agent's memory.

## check-30

**The only synonym bridge did not warn when it fell behind.** `_VOCABULARY.md` is a GENERATED artifact (single
source: the `aliases` frontmatter of every note) and, with no embedding search, the ONLY term-to-note bridge. An
audit found it a month stale with hundreds of notes newer than it, and nothing would ever have said so. The honest
nuance: when regenerated, **no alias had changed** (only source hints), so the real damage was smaller than
projected. That is why the check is INFO and measures **content, not mtime**: `missing` (a note with no row) and
`ghost` (a row with no note) are the two drifts that break term resolution; trivial edits do not count. mtime would
also be non-deterministic in fixtures.

**The remedy is `/vocabulary-update`** (regenerate, diff, approve), never hand-editing the table.

**Names in any language (v0.1.3, issue #1).** The row parser first accepted only `[A-Za-z0-9_-]` in the canonical
cell, inherited from a wiki whose canonical names were English slugs. A note named `Fuerza máxima` or even
`Dinamometría` was listed by the generator and still reported as `missing`. The parser now reads the cell up to
the next pipe, and both sides are compared in **NFC**, because a vocabulary generated on macOS can spell the same
name in NFD. Found by a user testing the kit on a Spanish-named synthetic vault: the guarantee "every note the
generator writes is recognised" had never been tested with a non-ASCII name.

## check-31

**Four channels for the same promise, and a large set of seals that satisfy none.** An audit of the method found
that the guarantee "verified against the fulltext" lives in four physical places: the value of
`source_verification` itself (long seals), a `notes:` field starting with "Verified", a `verification_notes:` field,
and a body callout "Re-verified vs fulltext". And a large set of sealed notes carries **none of them**:
`source_verification: fulltext` and nothing else. Neither the lint nor the queue distinguishes that seal from one of
two thousand characters, and a blind re-audit found substantive residues precisely in one of those. This check
counts them as INFO/backlog; the fix is to migrate `source_verification` to a controlled value (for example
`fulltext-v2 | fulltext-legacy | abstract | preprint`), at which point the counter should drop to zero or become
the worklist.

**Rule.** `source_verification` counts as a seal (Check 17), its text is at most 60 chars after stripping quotes,
no `notes:` starting with Verified/Verificad, no `verification_notes`, and no "Re-verified vs fulltext" callout in
the body.

## check-32

**A work could be hung from a synthesis block without anyone checking it for that note.** `/wiki-synthesize` does
not re-read the fulltext, and waves that applied the evidence check by hand were closed. The screen requires that
every pair (note, work cited in the block) has, in the source note, a seal that names the note. When it was first
measured against a large real wiki, a wave map built for the seals of earlier waves accepted only a fraction of the
pairs and many were left unsealed. In a pilot of 15 pairs at random, 6 had a defect and 3 were substantive, **even
with the source note sealed against the fulltext**: **a fulltext seal does not protect the pair.**

**Rule.** See `docs/SEALS.md` for the seal format and `wikikit/seals.py` for the detection. Declared debt
(`seal_debt_file`, lines `Note Work cause`) does not count as a defect and is always printed, because it does not
mean verified. A new pair is never added to the debt by hand: it is checked and sealed. Before emptying this check
for noise, read its limits: a mention of the name counts as a seal, and **it does not see an entry rewritten with
the same works** (only the PDF check in `wiki-synthesize` sees that).

## check-33

**A source note could reach `status: final` with no bibliographic identity.** One note lacked `title`, `authors`, `year`,
`venue` and `citekey`, and its heading was the file name; nobody saw it for months because Check 18 only looks at
`volume` and `pages`. It surfaced while reviewing a linter warning from the sealing tool, which only inserts those
fields after `venue:`; measuring which source notes could lose them found this one among over a thousand.

**Rule.** A `papers/` note, not a stub, with an absent or empty `title` or `venue`. Only those two: `authors`,
`year` and `citekey` are not watched.
