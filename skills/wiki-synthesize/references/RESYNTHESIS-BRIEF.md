# wiki-synthesize: addendum for re-synthesis (a note that already has a block)

Given to a drafting subagent, on top of the batch brief (`BATCH-WORKFLOW.md`) and `BRIEF-RULES.md`, when the note is in Check 15's `stale` bucket: the block exists, its entries were checked against the PDFs, and one or more works ingested since then sit in the findings store without being in the block. Where this addendum and the batch brief disagree, this addendum wins for a `stale` note. It is the subagent form of `SYNTHESIS-WORKFLOW.md` step 9.

The orchestrator names the new works in the prompt.

## The addendum (given verbatim)

> ### 1. What changes from the standard brief
>
> - **An existing `## State of Knowledge` block is expected here. It is NOT a T3 trigger.**
> - **Scope = the NEW works named in your prompt, and nothing else.** For each one, find every line of the findings store that cites it (grep its wikilink across the whole note, all sections) and decide ONE of:
>   - (a) **corroborates an existing entry**: add its `[[wikilink]]` to that entry and recount the tally; change the confidence only if the new work moves the evidence pyramid or the measurement quality;
>   - (b) **changes an existing entry's verdict or state** (a contradiction, a boundary condition, a population the entry did not cover): rewrite that entry and state the change explicitly;
>   - (c) **opens a sub-question no entry covers**: add ONE new entry, placed by state order (resolved, superseded, contested, emerging);
>   - (d) **adds nothing the block should carry**: say why (for example "a protocol detail, it lives in the protocol section"). Coverage with explicit `omitted:` (rule 7 of `BRIEF-RULES.md`) applies to these works.
> - **Untouched entries stay VERBATIM**, byte for byte, including their tallies. If you think an untouched entry is wrong, it goes to SIDE-FINDINGS, not into the block.
> - **Prefer (a) over (c).** Mature blocks are already long; a new work that fits an existing sub-question goes there, even if it adds a nuance in a subordinate clause.
> - **Tally:** recount every entry you touch from scratch, per `docs/WIKI_SCHEMA.md` (one `src` per distinct `[[wikilink]]`, per-type counts from each source's `evidence_level`, closed vocabulary only). Never increment the old number.
> - **Header date:** replace the old date with today's: `> [!abstract] Synthesis · updated <today>`.
> - **A new work that contradicts an existing entry is the point of re-synthesis, not an escalation.** Handle it with (b) and list it first in the DIFF. Escalate only on T1, T2, T4, or an empty findings store.
>
> ### 2. RETURN (item 0 is added; items 2 to 8 apply to the touched entries only)
>
> 0) **DIFF**, first, one block per touched entry:
>    - `E<k> (a|b|c)`, then `OLD:` the entry verbatim, or `new`; `NEW:` the entry as you propose it; `WHY:` which new work, which store line(s), what changed (state, verdict, tally, confidence).
>    - Then one line per new work handled by (d), with the reason.
>    - State or confidence changes go at the top.
> 1) **BLOCK:** the full updated block, ready to replace the old one.
> 2) to 8) as in the batch brief and `BRIEF-RULES.md`, restricted to the touched entries (TRACE gives the store line(s) and every key number for each touched entry and each new work).

## Orchestrator, after the return

The evidence check (`SYNTHESIS-WORKFLOW.md` steps 5b and 5c, brief in `CHECK-BRIEF.md`) covers the touched entries only, and the human sees the DIFF before anything is written. The user's manual edits to untouched entries survive because those entries are copied verbatim; compare the returned block with the current one and confirm that only the entries in the DIFF changed.
