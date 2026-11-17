# Ingest Pitfalls: do not repeat these errors

> From a full A-to-Z audit of a 1,300-note wiki (274 fixes). Read before every ingest.

- [ ] **P1 No fulltext, no numbers or quotes.** Without the PDF or fulltext, do NOT invent figures or quotes. `status: draft` and flag inline.
- [ ] **P2 Verify against TABLES, not the abstract.** Abstracts round, err, and sometimes contradict their own tables. Extract from the tables of the fulltext.
- [ ] **P3 Quotes verbatim (copy-paste).** Never type a quote from memory or attribute it without checking the author. Copy it from the fulltext. Use `...` to elide and `[ ]` to insert.
- [ ] **P4 `evidence_level` from the decision table** (closed vocabulary). Single-arm pre/post is `cohort`; groups without randomization is `CT`; consensus or opinion is `narrative`.
- [ ] **P5 Provenance always.** `source_verification` (library key + date + what was verified) and volume, issue and pages are mandatory.
- [ ] **P6 Label every value with its group or side.** Prevents A/B swaps, dominant/non-dominant, left/right, and other paired-label mix-ups.
- [ ] **P7 When correcting, search the value across the whole wiki.** Errors propagate to sibling notes of the same author or study, and to concepts and MOCs.
- [ ] **P8 Write the note in the wiki language** (`note_language`, default English), whatever the language of the source. Prose, headings, callouts and seals. Deliberate exceptions: `aliases:` (bilingual synonym bridge), verbatim quotes from sources in another language (copied as printed), and `log.md`. If the rule is not written down, English is habit rather than contract, and habit costs migration campaigns. Radar: `wiki-lint` Check 14 (off by default: turn it on with `examples/languages/es.json` or your own lists in `lint.language_radar`).
