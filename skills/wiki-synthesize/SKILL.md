---
name: wiki-synthesize
description: Drafts or updates the living-synthesis "## State of Knowledge" block of ONE mature concept or method note in a scientific wiki, weighing its findings by the evidence pyramid, checking each new or changed entry against the PDF of every work it cites, and presenting the block for human ratification before writing. Triggered by /wiki-synthesize, "synthesize this concept", "state of knowledge for X". Generative with a human in the loop, never autonomous. Consumes wiki-lint Check 15's worklist.
---

# wiki-synthesize

> Before the first run, read `docs/GOTCHAS.md` in the kit (operational gotchas for ingest, synthesis and lint) and `docs/SEALS.md` (the seal format).

The "surgeon" of the living-synthesis layer. It reorganises a note's already-verified findings store (`## Key Findings` in a concept note; the claim-bearing sections of a method note) into a State-of-Knowledge block that captures the *flow* of the evidence: resolved, contested, superseded, emerging. It NEVER invents claims. Every entry traces to an existing finding, and every new or changed entry is checked against the PDF of each work it cites before the user ratifies it (evidence check, layer 2).

## Modes

- **default:** `/wiki-synthesize <NoteName>` synthesizes one concept or method note.
- **worklist:** `/wiki-synthesize` (no argument) runs `wiki-lint` Check 15, then presents `check15_missing` **prioritised** (fields listed in `synthesis.priority_fields` first, then by source-work count, descending) plus `check15_stale` (re-synthesis candidates), and asks which note to process. The worklist is a **backlog, not a must-do-all-now**. The eligible set is whatever Check 15 reports live; a frozen count written into a doc goes stale.
- **batch:** `/wiki-synthesize --batch [N]` is management-by-exception campaign mode (default wave of 8). It runs Check 15, forms a priority wave, dispatches parallel subagents (each follows `SYNTHESIS-WORKFLOW.md` and **returns** a block plus a self-report, never writing), gates every write with the evidence check and `scripts/synth_validate.py`, writes clean notes, and escalates on 4 triggers (T1 unverifiable key number, T2 information loss, T3 structural anomaly, T4 low subagent confidence) and on any defect the check finds. See `references/BATCH-WORKFLOW.md`. **Propose the subagents of a wave to the user first** (what they do, how many, which model) and wait for the go-ahead.

## Role and boundaries

**Does:** read a note's findings store, weigh by `evidence_level` plus inline measurement, draft the block, check each new or changed entry against the PDF, present for ratification, then write (insert the block and absorb `## Controversies or Gaps`), seal the source notes, run the gate, log.

**Does NOT:** invent numbers or claims, create `debates/` notes (flag candidates in the report instead), touch notes below the synthesis threshold, or write anything before the user ratifies.

## Where things live

Paths come from `wiki.config.json`. Notes: `<wiki_root>/concepts/`, `methods/`, `papers/`, `books/`. **Always read `WIKI_SCHEMA.md` (Living-Synthesis Layer) before starting.**

## Threshold (must hold before synthesizing)

`status: final` AND (`synthesis.min_sources` or more distinct source works (default 3) OR at least one cited source with `evidence_level` in `synthesis.sr_levels` (default `SR-MA`, `SR`)). This is exactly `wiki-lint` Check 15's qualification test. If it does not hold: report and STOP.

## Workflow

Full procedure in `references/SYNTHESIS-WORKFLOW.md`. Summary: read contracts, resolve the note (exact `test -f`/content search, never a glob alone), threshold gate, pre-fulltext guard, cluster findings into sub-questions, **check new or changed entries against the PDF**, propose the block in chat with quotes and pages, ratify, write (`scripts/synth_write.py`: insert after `## Definition`, absorb Controversies, stamp), **seal the source notes** (`<kit>/tools/seal.py`), re-synthesis diff if a block already exists, then log, re-run the gate and re-run Check 15.

## Safety rules

- **Never invent.** Every entry traces to an existing finding; no new numbers from memory or from the source note.
- **Evidence check, layer 2: no new or changed entry without a PDF check.** Up to 3 distinct works, the orchestrator checks them; more, it proposes a subagent with the brief restricted to the diff and waits for the user's OK. Every defect is re-read in the PDF before anything changes, and the source notes are sealed with the note's name. A fulltext seal on a source note does not protect what a note says about that work: in a past audit of this method, roughly 4 in 10 sampled note-to-source note pairs had a defect.
- **Human in the loop.** Interactive modes: propose, ratify, write (no write before the user's OK). Batch mode: `synth_validate.py` gates every write and the 4 triggers escalate; never fully autonomous.
- **Zero information loss.** Every `## Controversies or Gaps` bullet must map to a block entry before that section is absorbed.
- **Pre-fulltext guard.** A cited **paper** in the pre-fulltext cohort (a paper note dated before `synthesis.prefulltext_cutoff` and not fulltext-sealed, or sealed only at abstract level) lowers the affected entry's confidence and gets an inline `⚠` flag; pause the entry only if the number it hinges on is itself unverifiable. Book chapters are trusted anchors **unless their own `status:` is `draft` or `stub`**, which is the note stating it was ingested without the fulltext (a fulltext-level `source_verification` overrides the status). `synth_validate.py` V4 enforces this mechanically.
- **Claims need sources.** Each entry cites `[[wikilinks]]`.
- **Filesystem-first.** Use the host's file tools; no Obsidian plugin or MCP is required.

## Related skills

- `wiki-lint`: Check 15 produces this skill's worklist; Check 32 flags a (note, work) pair with no seal. Run it after synthesizing to confirm no drift (link checks clean, Check 15 drops the note from `missing`).
- `wiki-ingest`: upstream. The findings this skill reorganises were written by ingest.

## References

- `references/SYNTHESIS-WORKFLOW.md`: the detailed procedure, the block template, guard logic, re-synthesis handling.
- `references/BATCH-WORKFLOW.md`: batch mode, the orchestrator loop, the subagent brief, the V1-V5 write gate, the escalation triggers.
- `scripts/synth_validate.py`: the write gate and a whole-wiki sweep; `--note` without `--block` re-checks the block the note already carries. `scripts/synth_write.py`: block insertion; it runs the same gate and refuses anything but CLEAN. `<kit>/tools/seal.py`: sealing.
