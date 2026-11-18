# Seals

A **seal** is the audit trail of "this note's claims about this work were checked against the PDF". It is one segment appended to the `source_verification` frontmatter line of the cited work's note (its *source note*):

```yaml
source_verification: "fulltext, tables checked [2026-11-06, synth Example_Concept, Example_Concept] Checked against PDF: what the block attributes to this work holds up."
last_verified: 2026-11-06
```

There is **one segment per (note, work) pair**: the note is the concept or method note whose block cites the work.

## Format

```
[DATE, TAG, NOTE] Checked against PDF: TEXT
```

- `DATE`: `YYYY-MM-DD`, from `date +%F`. Never estimated.
- `TAG`: free text naming the operation (`ingest Smith_2020_X`, `synth Example_Concept`).
- `NOTE`: the exact note name (without folder or `.md`).
- `TEXT`: exactly `what the block attributes to this work holds up.` when the check found nothing; otherwise `Corrected (<class>): ...` (the note was wrong and was fixed) or `Qualified (<class>): ...` (the note was right but needed a caveat). `<class>` is one of `figure`, `hedge`, `inference`, `attribution`, `entity`, `omission`, `overreach`, `inversion`.
- No double quotes inside `TEXT` (the value lives in a double-quoted YAML string).

## What the check was made against

The segment reads `Checked against PDF:` by default. When the check was made against something else (the publisher's
full text because no PDF was available, a supplement), say so in the spec with a `source` label, and the segment reads
`Checked against publisher XML:`. The label is at most 40 characters (letters, digits, spaces and `.,/()-`). It does not
change how the seal is counted, only what it honestly says.

## Writing seals

```bash
python <kit>/tools/seal.py seals.json --dry-run
python <kit>/tools/seal.py seals.json
```

```json
{"date": "2026-11-06", "tag": "synth Example_Concept", "source": "PDF",
 "seals": [["Example_Concept", "Smith_2020_SR", "what the block attributes to this work holds up."]]}
```

The tool appends to the end of the existing value (an unquoted single-line value is quoted on the way in), sets `last_verified`, preserves the file's line endings, and **writes nothing at all** if any source note is missing, if its `source_verification` is a block scalar or a list, or if a text contains a double quote.

## Writing a seal the next reader can use

A seal is read later by a triage pass, a checker or a human deciding whether a note is wrong. These habits came from
seals that misled them:

- **Name the magnitude you corrected and what the source does support.** An ambiguous seal, or one narrower than the
  source, makes the next triage "correct" what the source does say. Triage applied nearly all proposals that rested
  on clear seals and under half of those that rested on narrow or ambiguous ones.
- **A seal that denies needs a positive search; a seal of exclusivity ("only in group X") needs the other groups
  read.** Test every seal against the abstract, boxes, tables and conclusion, not only the Results. The writer's own
  seals were found wrong again and again; an independent second reading is what catches them.
- **Changing an earlier seal needs the full proof.** A seal rewritten from the text alone had to be reverted in
  several files when the figure backed the old seal. Check doubts about a seal against the PDF before acting on them.
- **A triage package carries the seal as it was when captured.** If the seal is corrected afterwards, capture it again
  before applying, or the proposals come from the old seal. Tags repeat across campaigns: find "already sealed" by
  date and tag together, not by a word in the text.

## Reading seals (what the checks look for)

`wiki-lint` Check 32 asks one question per pair (note, work cited in the note's `## State of Knowledge` block): does the work's `source_verification` carry a seal naming the note?

- A multi-word note name (`Example_Concept`) counts as a whole token anywhere in the value.
- A single-word name (`Detraining`) counts only inside a `[date, ...]` header, because in prose it can be an ordinary word.
- English and Spanish seals are both recognised: what identifies a seal is the `[YYYY-MM-DD, ...]` header plus the note's name, not the words after it. A wiki that wrote its early seals in another language does not need to migrate them.

Pairs without a seal are either **declared debt** (listed in `_lint/seal_debt.txt`, one `Note Work cause` line each, printed every run and never read as verified) or failures.

## What a seal does NOT prove

A seal says the check was done for that pair; it does not say which entries it covered. An entry rewritten with the same works passes the pair check unchecked, so the PDF check (`wiki-synthesize`, steps 5b and 5c) is the only defence, including for manual edits.

A fulltext seal on a source note also does not protect what *another note* says about that work: checking the source note against the PDF and checking a note's claim against the source note are two different checks.

## Seal levels

`source_verification` also records how deep the verification went. The synthesis gate treats a value as **below fulltext** when it is the bare word `abstract`, or contains `abstract-level` / `partial fulltext` and does not contain `UPGRADED TO FULLTEXT`. An upgraded seal keeps its original abstract-level sentence for provenance and appends the upgrade, so tools test for the phrase AND the absence of the marker.
