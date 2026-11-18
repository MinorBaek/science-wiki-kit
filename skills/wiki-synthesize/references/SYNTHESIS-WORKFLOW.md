# wiki-synthesize: Workflow

Detailed procedure for the `/wiki-synthesize` skill. The design of the layer lives in `WIKI_SCHEMA.md` (Living-Synthesis Layer). A minimal example of the format is `tests/fixtures/synth/note_clean.md` in the kit.

## The block (target output)

`## State of Knowledge`, placed **immediately after `## Definition` (or after `## Description`, which is how most method notes title it) and before the findings store**:

```
## State of Knowledge

> [!abstract] Synthesis · updated YYYY-MM-DD
> - <icon> **<sub-question> — <state>.** <one-line verdict> — [[Source_A]] [[Source_B]] (<N> src: <dominant design>; <confidence>).
```

- **State icons and words:** `✅ resolved` · `⚖️ contested` · `🚫 superseded` · `🌱 emerging`. Order entries resolved, superseded, contested, emerging.
- **Verdict:** one declarative line grounded in the findings store and checked against the PDF (steps 5b and 5c). No new claims.
- **Sources:** each bullet cites its source notes as `[[wikilinks]]`, which keeps the block link-checkable and directly retrievable when drafting a Discussion.
- **Weight:** the count of **distinct source works** plus the **dominant study design** read from their `evidence_level` (for example `3 src: SR + 2 textbook`). `7+ src` is allowed when the count is a floor.
- **Confidence:** qualitative (`High`, `Moderate–High`, `Moderate`, `Low–moderate`, `Low`; the two hybrids exactly so, with an en dash) = the evidence pyramid (`evidence_level`) crossed with the inline **measurement quality** (MRI versus estimate; replicated versus single proof of concept).
- **Freshness:** one block-level `updated YYYY-MM-DD`. `wiki-lint` Check 15 compares it with the source notes' `last_verified` to flag staleness. There is no separate stale field.
- **Dates:** the header stamp is REQUIRED (V5 fails without it). Calendar dates inside an entry's prose are not allowed (V2 would read the day number as a fabricated figure); say "fulltext-verified" plainly.

## Procedure

1. **Read contracts:** `WIKI_SCHEMA.md` (Living-Synthesis Layer).
2. **Resolve the note** with an exact `test -f` or content search (never a glob alone: false negatives), in `concepts/` or `methods/`.
3. **Threshold gate:** `status: final` AND qualifies (`min_sources` distinct source works OR at least one cited source with `evidence_level` in `sr_levels`), exactly Check 15's test. Otherwise report and STOP.
4. **Pre-fulltext guard:** for each cited source, check whether it is in the pre-fulltext cohort (a paper dated before `synthesis.prefulltext_cutoff`, or sealed only below fulltext level, or a book chapter whose own `status` is `draft`/`stub`). Default: **lower the affected entry's confidence and add an inline `⚠ unverified source`**. Pause or omit the entry only if the specific number it hinges on is itself unverifiable. Never silence the issue. **Read each cited work's `source_verification` value before flagging it**: most pre-cutoff papers are properly verified, and flagging those is the main source of false escalations.
5. **Read the findings store** (plus any `## Controversies or Gaps`); cluster it into **sub-questions**; for each assign state, verdict, weight (distinct sources plus dominant `evidence_level`) and confidence (design crossed with inline measurement).
5b. **Evidence check against the PDF (layer 2).** The scope is every **new or changed** entry: the whole block when there is none yet; in a re-synthesis, each entry whose text or cited works change. Each (entry, work) pair gets a row in a scratch file: the clause attributed to that work, the verbatim quote, the PDF and printed page, and the verdict (`ok` or a defect class).
    - **Method:** judge only the part of the entry attributed to that work. Render tables, figures, signs and CIs and look at them. Absence needs a positive search. The defect classes are `figure`, `hedge`, `inference`, `attribution`, `entity`, `omission`, `overreach`, `inversion`.
    - **Which PDF:** with several candidates, check the one the source note's seal names, comparing version and page count. An accepted manuscript can lack what the published version carries (a reporting-guideline paper checked in a deposit without its Explanation and Elaboration produced three false defects in one audit).
    - **Who:** up to 3 distinct works in the scope, the orchestrator. More than 3, **propose a subagent** (a capable mid-tier model is enough) with the brief restricted to the diff (`CHECK-BRIEF.md`), say why and how many, and **wait for the user's OK**. The subagent writes nothing in the vault and returns the table as text.
    - **No PDF, or abstract only:** the entry cannot go in as checked. Say so at step 6; do not seal that pair.
5c. **Re-read every defect in the PDF before changing anything**, including those a subagent reports. Reports carry false positives: a clause that belongs to another work of the same entry, an "absent" term that is in the PDF, a sign the extraction ate. Reword the entry down to what the source supports. If the findings store or the source note carries the same error, list it for correction at step 6: this is the one case in which the findings store changes.
6. **Propose the block in chat** with a per-entry source trace, the quote and page of each checked clause, and the defects found. Changes of state or confidence go first. **DO NOT WRITE.**
7. **The user ratifies or edits** line by line.
7b. **Gate the block:** `python <kit>/skills/wiki-synthesize/scripts/synth_validate.py --note concepts/X --block <file>`. It must say `CLEAN` (V1 to V5). Any FAIL: fix the block, never the gate.
8. **Write:** `python <kit>/skills/wiki-synthesize/scripts/synth_write.py --note concepts/X --block <file> --absorbed N` (use `--dry-run` first). It inserts `## State of Knowledge` after `## Definition`, **absorbs `## Controversies or Gaps` by retitling it** (it refuses unless `--absorbed` equals the section's bullet count, so you must have mapped every bullet first, which guarantees zero loss), and stamps `last_verified` when the note lacks it.
8b. **Seal the source notes.** One seal per checked pair, through `<kit>/tools/seal.py` (spec format in the tool's docstring and in `docs/SEALS.md`). The text is exactly the CLEAN text, or `Corrected (<class>): ...` / `Qualified (<class>): ...`. Use `--dry-run` first. Take the date from `date +%F`.
9. **Re-synthesis** (the note already has a block; Check 15 `stale` bucket): update entries and bump `updated`, **preserving the user's manual edits**; present a diff of the proposed changes before writing. Write with `synth_write.py --note concepts/X --block <file> --replace` (`--dry-run` first): it runs the same gate on the new block, swaps only the old block's lines, prints the diff, and refuses a note without a block or an `updated` date earlier than the current one. Never paste the block by hand: nothing would tie the validated block to the bytes in the note. Steps 5b, 5c and 8b apply to the entries that change. A subagent that drafts a re-synthesis gets `RESYNTHESIS-BRIEF.md` on top of the drafting brief.
10. **Closeout:** append to `log.md` (`## [YYYY-MM-DD] synthesize | {Note}` with the entries created or updated). Re-run `synth_validate.py` on the note, then `wiki-lint` (Check 15 must drop the note from `missing`; Check 32 must show its pairs sealed). Report.

## What the seal check does not see

`wiki-lint` Check 32 asks only whether a pair (note, work cited in its block) has a seal naming the note. **An entry rewritten with the same works passes it unchecked**, so steps 5b and 5c are the only defence, including for a manual edit. If a block grows or changes without the check, record the note as declared debt (`_lint/seal_debt.txt`, one `Note Work cause` line per pair) so it is not read as verified until the check is done. Debt is declared, never silent.

## Pitfalls

- A single rich source (SR/SR-MA or textbook) can *qualify* a note through the SR branch, but its weight and confidence must still reflect that it is one source. Do not overstate.
- `debates/` promotion (a debate that crosses several concepts AND sits in an active line) is **out of scope** here: flag it as a candidate in the report; do not create the note.
- **Do not touch the findings store.** Synthesis only restructures `## Controversies or Gaps`; the detailed findings stay intact (append-only, per the schema). The exception is a defect that step 5c confirmed in the PDF, corrected after the user's OK.
- ⚠ **The findings store is not always `## Key Findings`.** That heading is a concept-note convention. In method notes the claims live in sections such as `## Papers Using This Method`, `## Strengths`, `## Limitations`, `## Typical Parameters` and `## When to Use`. **Read the note's own section list before looking for a heading.** The absence of one particular heading is not an anomaly; an empty store is. Details in `BATCH-WORKFLOW.md`, "Where the findings store lives".
- Keep the block **self-contained prose**. The model reads it raw when drafting, so do not rely on Obsidian-only rendering (transclusion is optional and additive, never the sole carrier of a claim).
- The worklist can be large but is **non-gating**: synthesize by priority, not all at once.
