# wiki-synthesize: Batch / Management-by-Exception Mode

Extends the one-note interactive workflow. **Same synthesis contract** (`SYNTHESIS-WORKFLOW.md`), executed in parallel and gated centrally. Adopt it only after the interactive path has produced several notes that needed no corrections. It is NEVER fully autonomous: the evidence check and a deterministic validator gate every write, and 4 triggers escalate to the human. **Subagents (drafting and checking) are proposed to the user before they run**, with their number and model.

## Roles

- **Orchestrator (the main session):** builds priority waves, dispatches subagents, runs the validator, writes clean notes, lints and commits per wave, and presents escalations.
- **Subagent (a capable mid-tier model, isolated context):** synthesizes ONE note by running `SYNTHESIS-WORKFLOW.md` steps 1 to 5, then **returns** a block plus a self-report. It never writes.

## Orchestrator loop

1. **Worklist.** Run `wiki-lint` Check 15 and take `check15_missing`, ordered by priority: fields in `synthesis.priority_fields` first, then by source-work count, descending.
2. **Form a wave** of at most 8 notes. Dispatch in parallel sub-batches of about 4 subagents, one note each, with the SUBAGENT BRIEF below.
3. **Gate and write** per returned note:
   a. Write the returned block to a temp file and run `python <kit>/skills/wiki-synthesize/scripts/synth_validate.py --note concepts/<Name> --block <tmp>`.
   a2. **Evidence check (layer 2):** `SYNTHESIS-WORKFLOW.md` steps 5b and 5c on every entry of the block, with a checking subagent per sub-batch once the user has OK'd it (brief: `CHECK-BRIEF.md`). The drafting subagent does not check its own block. Every defect is re-read in the PDF.
   b. If `RESULT: CLEAN`, the self-report says `escalate: no` **and the check found no defect**: **WRITE** with `synth_write.py` (insert after `## Definition`; absorb Controversies after verifying every bullet mapped), seal the source notes (`<kit>/tools/seal.py`), and append `## [YYYY-MM-DD] synthesize | {Note}` to `log.md`.
   c. Otherwise **QUEUE** (do not write): record the note, the failing check (V1 to V5), the escalation trigger (T1 to T4) and/or the confirmed defects, with a one-line reason.
4. **Post-wave verification.** Run `synth_validate.py --sweep` (the whole wiki, not only this wave's notes) and `wiki-lint`. Confirm the link checks are stable and Check 15 `missing` dropped by the written count. Spot-check one or two written blocks by reading them against their findings store.
5. **Stale close-out (a fixed step).** Every source note the wave re-dated (a seal, a source note completed or corrected against the PDF) re-flags, through its `last_verified`, every block that cites it, so a wave that closes without this step leaves Check 15 `stale` growing. A block reviewed against its re-dated source note **raises its `updated`**, because the source note's new content comes from a more reliable extraction.
   a. List the note-source note pairs whose source note was re-dated in this wave and classify each source note by reading its WHOLE `source_verification` (a "Corrected" marker comes BEFORE the date).
   b. Triage only the pairs whose source note was re-dated **with a correction**. Pure fills and clean seals get their `updated` raised without reading.
   c. For each correction, search the OLD form wiki-wide: in the citing notes, **inside the correcting source note itself** (the old form survives most often in the very file that declares the fix), and in MOCs and indexes. **Matching the source note is not the same as clean**: a phrase can agree with a source note that is itself wrong.
   d. Raise the dates (note `updated` and, for notes you read or corrected, `last_verified`; never lower a date, never add a field a note lacks).
   e. Re-measure Check 15: `stale` must close at 0.
6. **Commit the wave** (`docs(wiki): synthesize batch, wave N (M notes)`).
7. **Present the QUEUE** to the user in one batch (per note: the block and why it escalated). Apply their calls, write the resolved ones, then start the next wave.

## Optional screens

A wave tends to surface old debt, not subagent invention: figures already in the note body get promoted into view by the new block. **A screen hit is a reading to open, not a verdict**: a figure can be (a) false, (b) true with the source note incomplete, or (c) true but used to say something the source does not say. Only the fulltext separates the three.

The kit ships the gate and the seal check (`wiki-lint` Check 32). Other cross-file screens are worth adding as your wiki grows, and each one catches a class that no per-file check can see:

| screen | what it catches |
|---|---|
| orphan figure | block figures with no backing in the cited paper's source note |
| entity | entities the block names that no cited work names |
| corrected value | a correction propagated to some notes but not all |
| mutable state | a state written into another note's prose (`pending ingest` on a chapter already ingested, `draft` on a note already `final`) |
| line endings | files with mixed CRLF and LF |

## Absorbing retitles the section, it does not delete it

`synth_write.py` renames `## Controversies or Gaps` to `## Open Questions and Caveats` in place and stamps it, leaving every line where it was. The gate (V2) requires every block figure to be anchored in the note BODY and runs BEFORE the write, while the section still exists; deleting the section would strand any figure that lived only there, so the block would pass at write time and fail a second later. `--purge-absorbed` restores deletion and should not be used without checking by hand that no figure or wikilink lives only in that section.

- **Read the WHOLE section before absorbing, not just its bullets.** Anything in there is now presented under the new heading: a `> [!note]` scope caveat that belongs with the definition reads oddly under "Open Questions and Caveats". Relocate such content to the end of `## Definition` before running the writer. V3 cannot see it, because V3 only tracks wikilinks.
- **A non-canonical heading means `--absorbed 0`, not a rename.** If a note calls the section `## Gaps in Current Evidence`, the writer leaves it alone: write the block, keep the section, note it. Do not rename headings to make the absorber fire.

## Subagent brief (given verbatim to each drafting subagent)

Give `BRIEF-RULES.md` with it (the drafting rules from past waves and RETURN items 7 and 8); for a note that already has a block (Check 15 `stale`), add `RESYNTHESIS-BRIEF.md`.

> You are synthesizing ONE wiki note's living-synthesis block. Follow `skills/wiki-synthesize/references/SYNTHESIS-WORKFLOW.md` steps 1 to 5 EXACTLY: read `WIKI_SCHEMA.md` (Living-Synthesis Layer); resolve the note with an exact `test -f` or content search (never a glob alone); apply the threshold gate; apply the pre-fulltext guard; cluster the note's FINDINGS STORE (and any `## Controversies or Gaps`) into sub-questions and draft the `## State of Knowledge` block. The findings store is `## Key Findings` in a concept note and the claim-bearing sections in a method note (`## Papers Using This Method`, `## Strengths`, `## Limitations`, `## Typical Parameters`, `## When to Use`). Never assume the heading; read the note's own section list first.
> RULES: never invent. Every entry traces to an existing claim in that store; no fulltext, no new numbers. (You draft from the store; the evidence check against the PDF is a separate step.) Do NOT touch the findings store. Do NOT write any file. Note path: `<PATH>`.
> Pre-fulltext guard: a cited PAPER is in the cohort if its note `date` is before `<CUTOFF>` AND it does not carry a FULLTEXT-level seal. Such a paper gets an inline `⚠` and lowered confidence on its entry; keep the verdict if a clean corroborator anchors it. Book chapters are trusted anchors, with ONE exception: a chapter whose own `status:` is `draft` or `stub` is NOT trusted and needs its `⚠` (a note with `status: draft` was written without the fulltext in front). A fulltext-level `source_verification` overrides the status. **The exit door is the LEVEL of the seal, not the presence of the field**: a value that is the bare word `abstract`, or that says `abstract-level` / `partial fulltext` without the marker `UPGRADED TO FULLTEXT`, is BELOW fulltext and the paper still needs its `⚠`. An upgraded seal keeps its original abstract-level sentence for provenance and appends the upgrade, so test for the phrase AND the absence of the upgrade marker, never for the phrase alone. Any other seal value is fulltext-verified: no `⚠`. You MUST read each cited paper's `source_verification` VALUE before flagging it.
> RETURN exactly this structure (nothing written to disk):
> 1) BLOCK: the `## State of Knowledge` block (callout format; states ✅/⚖️/🚫/🌱; sources as `[[wikilinks]]`; each bullet ends `(<N> src: <dominant design>; <confidence>)`). The header stamp `> [!abstract] Synthesis · updated YYYY-MM-DD` with today's date is REQUIRED (V5 fails without it). Do NOT put a calendar date in an entry's prose; say "fulltext-verified" plainly.
> 2) TRACE: per entry, the cited `[[sources]]`, the finding line(s) it derives from, and each key number.
> 3) CHECK-PREFULLTEXT: which cited papers are pre-fulltext (per the level test above); for each, whether a CLEAN corroborator anchors the verdict (if yes: keep `⚠`, lower confidence, do NOT escalate). Fulltext-sealed papers are never listed here; papers sealed only at abstract level ARE.
> 4) CONTROVERSY-MAP: each `## Controversies or Gaps` bullet mapped to the entry that absorbs it, and confirm every wikilink of that section reappears in your block. A wikilink there can be a CROSS-REFERENCE rather than a source ("see the divergence documented in [[Concept]]"): carry it into the absorbing entry in prose, without counting it in the `(<N> src: ...)` tally. A dropped link fails V3.
> 5) ESCALATE: `no`, or `yes` plus trigger(s) and a one-line reason. It MUST be `yes` if ANY of: (T1) a verdict hinges on a number found only in a pre-fulltext paper without a fulltext-level seal and with NO clean corroborator; (T2) a Controversies bullet does not map cleanly to any entry; (T3) structural anomaly: an EMPTY findings store (no claim-bearing section at all), an existing `## State of Knowledge` block, a concept-and-method pair on the same topic, or a NEW contradiction not already in `## Controversies or Gaps`; (T4) you cannot confidently assign a state or a confidence level.
> 6) SIDE-FINDINGS: anything wrong you noticed that is NOT a trigger, one line each, or `none`. **Do not fix any of it and do not escalate on it**: synthesize from the store as written and list it here. Treat each cited work's seal as a checklist, not as prose:
>    (i) grep each cited work's `source_verification` for `corrected` / `retracted` / `refined` and, for each correction it announces, check whether **the NOTE carries the corrected version** (a seal can name the very note it wants updated and be ignored, or record having propagated a fix to ONE of the notes that cite it);
>    (ii) **does the FICHA ITSELF carry the correction? A declared correction is not an applied one.** Check the artefact, not the changelog;
>    (iii) when a source note says it corrected "a range", check WHICH ROW the range belongs to before calling the note's version wrong (two different rows of the same table can both be right);
>    (iv) **if the note REPLICATES a table from a cited work, compare the two tables** and report rows dropped, columns dropped and which cell each version emphasises. This class is invisible to screens, because the defect is an absence. Truncation is not itself a defect (an explicitly labelled selection is fine): report it and let the orchestrator adjudicate;
>    (v) **report every SUPERLATIVE whose comparison set is the wiki's own collection** ("the highest ICC in the cluster", "the only trial in the wiki that..."). Nothing re-checks them when a new work is ingested, and the usual origin is scope creep: the paper's own Results say "ranged from X to Y", and the ingest widens "highest in this study" to "highest in the series". Say which set it was true of; do not fix it.

## Where the findings store lives

`## Key Findings` is a **concept-note convention**. Method notes usually have no such heading: their claims live in `## Papers Using This Method`, `## When to Use`, `## Limitations`, `## Strengths` and `## Typical Parameters`. In a real wiki, concept notes without a block almost always have `## Key Findings`, and most method notes do not, so treating the absence of that heading as a structural anomaly would escalate the whole method half of the worklist for nothing. The shape of a section does not say whether the data exists.

**Operating rule:** read the note's section list BEFORE looking for a particular heading. T3 fires only if there is NO section with claims, not if one particular heading is missing. The validator already works this way (V1 and V2 read the whole body minus the block), and `synth_write.py` anchors on `## Definition` **or** `## Description`.

## Verify-on-escalation brief (given verbatim when a genuine T1 or T4 needs fulltext)

When the user chooses "verify" for escalated entries, dispatch verification subagents (at most 5 papers each) with the papers and the EXACT claims or numbers each block entry depends on. They confirm against fulltext and report; sealing goes through `<kit>/tools/seal.py`.

> You verify specific claims for the listed papers against their ACTUAL fulltext. Process papers ONE AT A TIME (reference-manager MCP calls can time out under parallel use). For EACH paper:
> 1. Read `<wiki_root>/papers/<citekey>.md` for its DOI and title.
> 2. Acquire the fulltext: the reference manager's fulltext by title or DOI; on 404, no attachment or error, retry once, then fetch the DOI if open access. If acquisition FAILED, do NOT report the paper as verified: report ACQUISITION-FAILED.
> 3. Verify each target claim: ✅ CONFIRMED (verbatim or number matches) / ⚠ PARTIAL / ❌ CONTRADICTED (give the correct value).
> RETURN: (1) ACQUISITION, per paper, the route used or FAILED; (2) VERIFICATION TABLE, per paper, each claim with its verdict and the verbatim quote or number; (3) DISCREPANCIES, every ❌ or ⚠ the orchestrator must reflect in the block (re-attribute or drop the affected clause), or "none". Do not edit any note.

**Orchestrator, after verification returns:** (a) seal the confirmed pairs with `<kit>/tools/seal.py`; (b) remove `⚠` and raise confidence on the now-verified entries; (c) apply every DISCREPANCY: drop or re-attribute the unsupported clause to its true source (the note body usually attributes it correctly and the block over-attributed it, as in the split-attribution pattern where one finding is credited to the wrong author of a pair).

## What the validator checks (the write gate)

| Check | Guard | Fails when |
|---|---|---|
| V1 | source fabrication | a block `[[link]]` that resolves to `papers/` or `books/` is absent from the note body minus the block (the whole body is read, not one section; that is what makes method notes work) |
| V2 | number fabrication | a prose number in the block is absent from the note body (citekeys, dates, the weight tag and a year in citation position are not numbers) |
| V3 | zero information loss | a `## Controversies or Gaps` `[[link]]` does not survive into the block |
| V4 | pre-fulltext flagging | an entry cites a pre-fulltext PAPER (or a draft or stub book chapter) without `⚠` |
| V5 | format | missing `[!abstract] Synthesis · updated <date>` header, or a bullet lacks a state glyph |

Any FAIL means `RESULT: ESCALATE`: the orchestrator queues the note and never writes it.

### The gate is a WRITE gate, not an invariant: sweep it periodically

Two kinds of blocks never sit behind the gate. **Interactive mode** (propose, ratify, write) does not call the validator unless you run step 7b, so a block written without it has never been checked. And a block that *did* pass at write time can fail later, because the gate compares it with the findings store **as it is now**: a rewritten finding, a corrected figure or a re-verified source can strand a number or a citation that was properly anchored the day it was written.

`python <kit>/skills/wiki-synthesize/scripts/synth_validate.py --sweep` runs the gate over every block in `concepts/` and `methods/` and lists the failing ones. The failure rate of blocks written before the gate existed is far higher than of those written behind it, and drifts upward over time, so make the sweep a closing step of every wave. Do not treat a zero as permanent: it is a measurement of a moving target.

## Fallback

Subagent failure or timeout: the orchestrator retries once, then falls back to the interactive one-note path for that note. If a note is edited live in the middle of a wave, re-run the gate on it before writing.
