# wiki-synthesize: rules for the drafting subagent

Given together with the subagent brief of `BATCH-WORKFLOW.md` to every drafting subagent, and read by the orchestrator before it drafts a block itself. Every rule below was paid for by a defect that reached a block, most of them found only when the block was checked against the PDF. The drafting subagent works from the note and its source notes, not from the fulltext: where a rule needs the PDF, the subagent **reports** and the orchestrator (or the checking subagent, `CHECK-BRIEF.md`) settles it.

"Source note" means the note of one cited paper or chapter; "the note" is the concept or method note being synthesized.

## 1. Rules 1–13 and A–S

1. **Exact string, never round.** Figures (R² 0.389 is not 0.39), words inside quotation marks, names of rules, devices, models and brands, and protocol details (position, sets × reps, units, order of a list) are copied letter by letter. A rounded figure also fires the orphan-figure screen.
2. **Anchor in the NOTE, not in the source note.** Block wording comes from the note body. Source-note material the note does not state (a comparator clause, an elaboration, a named outcome) is a SIDE-FINDING, never block text.
3. **No acronym, term, theory or eponym that no cited work uses.** The wiki's own labels put in a source's mouth ("motor abundance", a named theory the source never cites) are written as the wiki's reading or left out.
4. **Do not fuse endpoints that are not commensurable** (two outcomes, two instruments, two scales) into one figure or one verdict.
5. **A no-attribution warning in the note overrides the proximity of a wikilink.** Material the note flags as unsourced does not become sourced because a link sits nearby.
6. **Do not flatten a distinction the note makes** (phases, subgroups, the general direction and its exception).
7. **Coverage with explicit `omitted:`.** Every unit of the findings store maps to an entry or to `omitted: <reason>` (RETURN item 7).
8. **No double counting.** One claim from two sources is one entry citing both; one dataset reported in two papers is one piece of evidence.
9. **Two answers are not `resolved`, and a ⚖️ needs a dispute.** Before writing ⚖️, check that both sides answer the same question: two populations, two frames, two metrics or two time points are two questions. One source's position or internal ambiguity is not a dispute, nor are two chapters of one book that differ (report it with each chapter's attribution), nor two studies reported by one review (one review is one source).
10. **No absence claim about the wiki without a positive check.** "No study", "unavailable", "not established" is checked against the note's own sources before it is absorbed.
11. **Report the OLD form verbatim** for every correction you find, so the orchestrator can measure its scope (RETURN item 8).
12. **A framing the source note has already corrected is escalated by T3, not written.**
13. **When measuring scope, grep ALL spellings**, including headings, callouts and the very file that declares the correction (the old form survives most often there), and every note that cites the work, not only the note the seal names.
- **A.** **A "not found in the source note" points at the SOURCE NOTE before the note**, and you must say WHICH WORK the figure hangs from. Across many waves, nearly every figure reported absent from a source note was verbatim in the PDF.
- **B.** **A seal that ENUMERATES which table it verified is saying another table exists that it did not.**
- **C.** **Rule 2 covers QUALITATIVE clauses too**, the only ones the gate cannot see: no hardening of "may", "many", "most", "suggest" or "is associated with" (a correlation is not a prediction; a call for future research is not a recommendation; a conditional is not a law), no qualifier imported from the source note that the note does not state, no qualifier dropped. A hedge can be hardened twice, in the source note and again in the note.
- **D.** **Table versus prose: the table wins**, but if the seal declares a COMPLETE audit its silence is informative. Read a table's symbols against its own legend. A misprint of the source is quoted as printed and flagged, never silently corrected.
- **E.** **A retained block expires in its ABSTENTION, not in its figure.** Stale bookkeeping ("single source so far", "both wiki sources", a design label a source note has corrected) is reported, never carried into the block: a count of the wiki's own sources is always rechecked against the current body.
- **F.** **OMISSION is as much a defect as invention, and no screen sees it.** Walk every section of the store and ask which one has no entry. A caveat that qualifies a sourced entry travels into it, and so does a method's defining feature and the evidence against a stated mechanism.
- **G.** **When you catch a misattributed figure, read WHAT ELSE ITS BULLET SAYS** (and the sentence after it in the source note).
- **H.** **Rule A is the ORDER OF SUSPICION, not a verdict.** Only the fulltext settles it; the source note can misquote too. You do not read fulltext: report.
- **I.** **Fusing two sources fabricates a specificity nobody wrote**, and so does joining two conditions, two methods of one paper, or turning a single-arm finding into a contrast the source never tested.
- **J.** **Before writing a range, check its endpoints are the same CATEGORY, not just the same magnitude**: same outcome, same time point, same method, same label. Two measurements are not a range.
- **K.** **A source's numbering can skip an ordinal.**
- **L.** (Orchestrator-side.) **When a source note is refilled, use the spelling the screens search** (the same decimal mark and notation as the note).
- **M.** **A declared correction escapes through its FRAMING** (scope, dataset, population, comparator, setting, addressee, metric) even when its values are right. A dropped "compared with" manufactures a contradiction between two sources that agree.
- **N.** **The CAVEAT a seal asks to be cited IS a correction**, even if the same seal says "no corrections needed": grep the seal for `caveat` and for "not currently in the note". A qualifier on which analysis a result holds in (% versus absolute, one test, one subgroup) travels with the figure.
- **O.** **A misattributed citation can be the NEIGHBOUR in the reference list.** A secondary citation, or a work's own background (Introduction, Discussion context), is reported as "Y, as reported by X", never promoted to X's finding. A primacy claim is written as the authors' ("the authors state").
- **P.** **A trailer, lead-in or heading that points to a textbook chapter does NOT certify what it covers.** Being a trusted anchor for the pre-fulltext guard is not fidelity: compare the SPECIFICS of the scope (numbers, named studies, named methods, caveats) with that work's source note and report what is missing. Rule P is a checklist, not a presumption of guilt: say so plainly when the source note does carry the specific.
- **Q.** **The two coordinates of one point are not two ends of a range, and a worked example must satisfy the formula it illustrates.**
- **R.** **Re-attributing is not copying the old sentence under a new link**: it is rewritten in the words of the destination source.
- **S.** **A conclusion can be INVERTED against its source**: the sentence after the numbers can negate what the note reads into them ("of the ten studies, seven used X, so there is no clear pattern"). When the note says X moderates, explains, drives or predicts Y, check that the source note states that conclusion and that REASON, not only the numbers. A sentence that explains a pattern by joining several studies is checked against each of them.

## 2. Rules distilled from later waves (14–27)

14. **Say which quantity each number is.** Which side of a comparison, which arm, species, model or procedure, which subgroup (a pooled R printed in the text is not the subgroup R of the figure), which time point, which comparison a p or a d belongs to (a heterogeneity p is not the effect's p; a parenthesised p can be the alpha from the Methods), the unit of a summary statistic, and what an interval predicts. A figure in the abstract can belong to another comparison in the Results, and a table the note labels with the source's number may not be that table.
15. **A derived value is the wiki's arithmetic.** A share, ratio or percentage change the source note does not print is suspect twice (it was absent from the source and often mis-rounded): search the source's own percentage first, and write a derived value only if the note marks it as the wiki's calculation.
16. **Anachronism.** A function, tool or later development credited to an earlier source (a method a paper calls "under development"; later libraries credited to an older textbook; a review commenting on a law passed after it). Check the source note dates it to that source.
17. **The neighbouring chapter or book.** A claim hung on the right book's wrong chapter, or on another book on the same topic, or a method standard in the field attributed to a chapter that never describes it. When a chapter's source note lacks the claim, grep the sibling chapters' and the other books' source notes and name the one that carries it.
18. **Procedure order and stage are content.** What is done to training versus validation data, before or after a split; which step of a selection funnel a number belongs to; whether a figure sits under a protocol's progression criteria or its goals; which level of a staged framework a step belongs to; whether an intervention was added to usual training or replaced part of it; whether a quality score was an inclusion criterion or only reported.
19. **A work presented as an application of a method must name it** (or a member of its family). A study that reports reference values is not an example of reference intervals unless it says so.
20. **Count what the note enumerates.** A source's reasons, rules, steps, criteria or list members, a count of studies or a design label: if the source does not state the count and the label, they are the wiki's. Numbering in a heading is a claim too.
21. **Verdicts from a check done before launch.** When the orchestrator gives verdicts (correct form, defective form) from a PDF check done before drafting, a form flagged defective is unwritable even if the note still carries it. The verdicts are not exhaustive: keep checking every clause.
22. **Definitions are claims.** Check whether a threshold DEFINES a term or RECOMMENDS a practice, and which step of a procedure each cut-off belongs to. A definition can be inverted in one word: read definitional sentences as carefully as numbers.
23. **A value from one illustrative subject, or read off a figure, carries that label**, the panel and the condition. It is not a sample estimate.
24. **A reference-list title is not a claim of the source.** An entity, a definition or a finding that appears only in the title of a cited reference does not belong to the citing work. A study cited without description is written as cited, not described.
25. (Orchestrator-side.) **Side-findings are claims too.** Every side-finding is checked in the PDF before it is applied, in both directions: a side-finding can be false, and can be half right (the two versions may describe different outcomes).
26. (Orchestrator-side.) **A seal is not proof of its own correction.** When a seal re-attributes or re-files a finding, read the passage it names in the source; an earlier correction can be the error. The orchestrator's own seals are checked against the source note after every pass.
27. **Escalate only on the triggers.** An unsourced Controversies bullet is `omitted: unsourced`, not a T2. A tension the note already records, or two sources answering different questions, is not a new contradiction and not a T3.

## 3. Format: the gate fails on these

- **Header** exactly `> [!abstract] Synthesis · updated <today>`. No calendar dates inside entries.
- **Every bullet starts with a state glyph** (✅ ⚖️ 🚫 🌱). "resolved" in prose without the glyph fails V5.
- **🌱 means genuinely emerging knowledge, not "single source".** Thin corroboration lives in the confidence. **🚫 superseded** requires the newer evidence to measure THE SAME thing.
- **A gap is its own 🌱 entry**, with "open gap" as its state word, and an uncontested claim does not go inside a neighbouring ⚖️.
- **The tally closes the bullet**, after the sources, in the format of `docs/WIKI_SCHEMA.md` (Living-Synthesis Layer): no word "confidence", no commentary inside the parentheses, no closing period after it. Cross-references to other concept or method notes are carried in prose and not counted.
- **V2 tokenises every digit** in the block and requires the exact string in the note body. Write a count in words when it is yours, write each figure exactly as the body writes it (`.040` does not match `0.040`), and keep chapter numbers out of the block (they read as figures).
- **V1:** every `[[link]]` in the block must already be in the note body.
- **No bookkeeping in entries** ("this section under-scopes", "not independently verified here", "a coverage gap"): it goes to SIDE-FINDINGS.
- **Do not write "not ingested" about a third-party work.** Say it "has no note of its own".
- **Material without a source.** A store section with no attribution at all (no bullet wikilink, trailer, lead-in, heading link or `## Sources` line naming it) is not anchored to a nearby source by proximity (rules 5 and I): leave it out with `omitted: unsourced`, or use it in an entry that cites nothing and say so in TRACE. Short blocks are the correct result for thin material; do not pad. The note's own editorial comments hung on a source are not carried either.
- **Attribution scopes.** A trailer `— [[X]]` on its own line closes the list or paragraph above it; a lead-in `...[[X]]:` covers the list below; a heading that names `[[X]]` covers its section. A bullet with its own wikilink overrides the section attribution. Say in TRACE which scope each trailer has.
- **Double description** (method notes): the same work often appears twice, in a method section and in `## Papers Using This Method`. A mismatch between the two is a SIDE-FINDING.
- **Return literal `>` and `<`**, never HTML-escaped (`&gt;`, `&lt;`, `&amp;`). Escaped returns were the commonest format failure, wave after wave.

## 4. RETURN: two items after the six of the batch brief

7. **COVERAGE:** every section of the findings store, one line each: `<section>` → entry number(s), or `omitted: <reason>`. Coverage is per UNIT (bullet, table row group, callout), not per section: a section marked "covered" once lost half its bullets.
8. **OLD-FORMS:** for every correction found (declared but not applied, framing escaped, caveat missing), the OLD wording or figure verbatim, so the orchestrator can grep its scope. `none` if none.

Keep the whole return compact, with the BLOCK first, verbatim, in a fenced block.
