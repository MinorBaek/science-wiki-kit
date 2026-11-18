# wiki-synthesize: brief for the checking subagent (evidence check, layer 2)

Given to the subagent that reads synthesis entries against the PDFs of the works they cite: `SYNTHESIS-WORKFLOW.md` step 5b when the scope has more than 3 works, `BATCH-WORKFLOW.md` step 3a2, and a retroactive check of blocks written before the check existed. It is not the drafting brief: the drafting subagent never checks its own block.

**Why it exists.** In one retroactive campaign, most entries that had never been checked against the PDF carried at least one defect, and the rate did not fall with practice. The checker's job is to find them; the orchestrator's job is to re-read every reported defect in the PDF before anything changes (step 5c).

## Orchestrator: before dispatching

- **One subagent per note, or per pair of notes that share works.** Split a large note **by works, not by entries**, so each work is read once by one checker.
- Give each subagent: the note path, a scratch folder, and per cited work the PDF path(s) and the printed page range of a book chapter. Pass the PDF the source note's seal names when there are several candidates.
- Two modes, same method: **block mode** (every entry of the block against every work it cites) and **pair mode** (a list of (note, work) pairs, for example the pairs declared in `_lint/seal_debt.txt`; judge only the listed entries of each pair).
- **Declared limit:** the checker's `ok` rows are not re-read. A campaign's clean rate depends on what each checker saw, and nothing proves the right PDF was opened except the identity line of the report.

## The brief (given verbatim)

> ### 0. What you do
>
> You read entries of a note's `## State of Knowledge` block against the PDF of each work they cite, and say whether the source supports what the entry attributes to it.
>
> - **Scope:** only the bullets of the `> [!abstract] Synthesis` callout (block mode) or the entries listed for each pair (pair mode). Not the rest of the note. Read a source note only to find a page, a table or the PDF; it is never evidence for or against the entry, because it may carry the same error.
> - **Judge only the part of each entry attributed to that work.** If an entry cites three works, each gets its own verdict for its own clause. If you cannot tell whose clause it is, say so: a figure that looks wrong for one work may belong to the other work of the same entry.
> - **Check the works that are already sealed too.** A seal on the source note does not cover what this note says about the work.
> - **Most pairs will be fine.** Report what the source supports as plainly as what it does not. Never stretch a paraphrase into a defect.
> - Do not skip a pair. You write NOTHING in the wiki; the only place you may create files is your scratch folder (text dumps, page renders).
>
> ### 1. How to read the source
>
> 1. **Identity first.** The first page must match the source note (title, authors, venue, year). A sibling paper of the same group, or a full copy saved under another paper's name, is a common mismatch. If the first page is another work, or there is no PDF, report `no-pdf`; never adjudicate from the source note.
> 2. **Grep locates, reading decides.** Read the entry first, then open the source; `grep` locates a passage, it does not read it. Read the whole paragraph or table row around every hit: a cut grep produced false defects (a recommendation that had two grades).
> 3. **Every specific counts:** each figure, population, device, mechanism, named entity, eponym and verb of strength. Locate each one; do not stop at the first matching number.
> 4. **Tables, figures, signs, arrows, CIs, ± and row assignments: render the page** (`pdftoppm -f N -l N -png -r 160 <pdf> <scratch>/pN`) and look at it. The extracted text is a hypothesis, the image is the proof: extraction has shifted a whole row to the wrong label without changing a digit, and loses the minus sign, the prime, the degree sign and ligatures. Read a table's symbols against its own legend.
> 5. **Extract with `pdftotext -enc UTF-8`**, with and without `-layout` (two-column PDFs often match only without it). Grep both.
> 6. **Absence needs a positive search.** Before you say a source does not name something: grep both extractions, try spelling, hyphen and plural variants and a term split across lines, and look at the rendered figures. Report what the source DOES say next to what it does not.
> 7. **Book chapters:** the PDF is the whole book. Calibrate the printed-to-PDF offset with one probe page for THIS chapter (offsets change from chapter to chapter), and confirm the chapter title on the page you land on.
> 8. **Narrative reviews and textbook chapters get the strict reading.** Check every mechanism, marker and named method the entry hangs on them; a targeted check of one claim missed several more unsupported clauses in the same review.
> 9. **Note the PDF version** when it is not the published one (preprint, accepted manuscript, ahead of print): a quote can be absent from one version and present in the other.
>
> ### 2. Defect classes
>
> | class | what it is | example |
> |---|---|---|
> | `inference` | the wiki's inference written as the source's claim or act | "consistent with progressive accumulation"; a trial "formalising" a rule its protocol never uses |
> | `attribution` | wrong owner: the neighbouring reference, a secondary citation promoted to the work's own finding, the wrong grade of a recommendation | a tempo called a professional body's standard when it is one author's suggestion |
> | `figure` | a figure or range wrong, or a range built from two measurements, outcomes or groups | "I² 65–90%" that was 65% for one outcome and 90% for another |
> | `hedge` | a hedge hardened or a modal or quantifier changed | "limited ability to predict" written "does not predict"; "may" as "is"; "many" as "most"; "advised" as "mandatory" |
> | `overreach` | a superlative, exclusivity or generality the source does not state | "the field's best-replicated finding" |
> | `entity` | a method, study, term, marker, population or sport the source never names | markers listed as the source's when none occurs in its text or figures (the biology may be true; the attribution is not) |
> | `inversion` | the conclusion inverted against the source | "largely ignored" where the source reports "a significant interest" |
> | `omission` | the entry drops a condition, caveat or population that changes the claim | "no third injection" without "if no improvement after two" |
>
> **Not defects:** a paraphrase that keeps the claim, its strength and its owner; a confidence or tally you disagree with (a side-finding at most).
>
> ### 3. What to ask while reading
>
> The patterns below survive every value check; ask each question where it applies. The reasons are in `docs/GOTCHAS.md`, section 3, patterns 14–28.
>
> - Is this the right number of the right object (arm, species, model, procedure, subgroup, time point, comparison)? Which comparison does each p and each d belong to (group × time interaction, time main effect, heterogeneity)?
> - Is a within-group change, or a baseline group difference, being read as the effect of the intervention?
> - Is a non-significant difference read as equivalence? A correlation read as agreement or as prediction? An unreported result read as a reported null?
> - Is the design read stronger than it is (allocation by club or team as an RCT, pre/post without control as controlled)?
> - Is validity credited for a study that only used the device? Is a reliability or validity figure the work's own, or cited from an earlier study?
> - Are two cited works really independent (shared trials, same sample, one review containing the other's trial, same group)?
> - Can this type of work support the claim (press release, commentary, conference abstract, opinion, reporting guideline read as a methods guideline, protocol read as a dose, normative values read as thresholds, a review's table read as its conclusion)?
> - Has advice become a rule, a call for research a recommendation, a minimum a ceiling?
> - Is the claim in THIS chapter, or in a sibling chapter or another book? Is a named term, theory or eponym in the source's text, or only in the title of one of its references?
> - Does the source give the reason, mechanism or explanation the entry gives?
> - **Clinical threshold:** does the entry claim that an outcome improved, or that it crossed a threshold (MCID, MDC, SWC), and for how many arms exactly? An exclusivity or universality word ("only", "all arms", "both groups", "no other") next to a threshold is where the two get fused, in either direction.
> - **Secondary citation:** did the work measure this figure, or does it cite it from other studies (a marker such as "(Author et al., year)", "reported by", "according to")? A cited figure is written "Y, as reported by X", never as X's finding.
>
> ### 4. Calibration: three defects of the kind you are looking for
>
> - `inference`, a false claim about the source's methods. Entry: "a condition absent from its Methods (the muscle was tested eccentrically only)". Source: the abstract tests both concentric and eccentric modes, and Table 1 gives concentric ratios.
> - `entity`, entities the source never names. Entry: a pathway "stabilises protein A and induces protein B". Source: neither protein appears in its text or figures.
> - `inference`, the wiki's reading as the source's act. Entry: an RCT "formalises the rule". Source: the protocol compares two cut-offs and never uses that rule.
>
> Also watch for a reason for caution that is not the authors' reason, and a limitation the authors state presented as the wiki's inference, or the reverse.
>
> ### 5. RETURN
>
> Write the full report to `<scratch>/report.md`, one block per pair (or per entry in block mode), in the order given. Use literal `>` and `<`, never HTML-escaped.
>
> ```
> ### P<k>: <Note> <- <Work>   [PDF version if not the published one]
> #### E<n>: <first 8-10 words of the entry, verbatim>
> - ok | DEFECT <class> | no-pdf | not-located
>   - note says: "<the exact clause attributed to this work>"
>   - source says (p. <PDF>/<printed>, <section/table/figure>): "<verbatim quote; for a DEFECT the whole relevant paragraph or row>"
>   - fix (DEFECT only): <the minimal rewording the source supports>
>   - severity (DEFECT only): substantive (false or unsupported) | minor (nuance, hedge, reason)
>   - in source note (DEFECT only): yes, <where> | no
> ```
>
> - Every `ok` carries a short quote and its page: an unquoted ok cannot be audited.
> - `not-located` says what you searched (terms, pages). It is not a defect: an absence points first at your search, then at the source note, last at the entry.
> - End with `## SIDE-FINDINGS` (source-note errors seen in passing, the same defect in the note's body, a seal that contradicts the PDF) and `## TALLY` (pairs and entries: ok / with defect / no-pdf; defects by class and severity).
>
> **Your final message** is short: the report path, the tally, and one line per DEFECT (pair, class, severity, what is wrong).
