---
tags: [wiki, index, vocabulary]
date: 2026-08-14
status: active
type: index
---

# Fixture Vocabulary

Exercises Check 30 (vocabulary sync radar). Lists every fixture concept/methods
EXCEPT Fixture_Orphan (-> check30_missing = 1) plus one row whose note does not exist
(Fixture_Ghost_Concept -> check30_ghost = 1). The 'Fixture Café Concept' row is written
in Unicode NFD on purpose (the filename is NFC): it guards names with spaces, accents and
a different normalization. Do not retype it, or it becomes NFC and stops guarding.

MAINTENANCE COUPLING: adding a new concept/ or methods/ fixture requires adding its
row to this table, or check30_missing bumps and the self-test fails. This mirrors the
index.md fixture coupling (Quick Stats) that every new paper fixture already maintains.

| Canonical | Aliases (EN; ES) | Note | Field | Source hint |
|---|---|---|---|---|
| Fixture_Concept_A | FCA | [[Fixture_Concept_A]] | research-methods | Smith_2024_FakePaper |
| Fixture_Hub_Inline | hub inline | [[Fixture_Hub_Inline]] | fixture | Smith_2024_FakePaper |
| Fixture_Hub_RC | hub rc | [[Fixture_Hub_RC]] | fixture | Smith_2024_FakePaper |
| Fixture_Stub | stub fixture | [[Fixture_Stub]] | fixture | Smith_2024_FakePaper |
| Fixture Café Concept | cafe concept | [[Fixture Café Concept]] | fixture | Smith_2024_FakePaper |
| Fixture_Unsourced | unsourced fixture | [[Fixture_Unsourced]] | fixture | Smith_2024_FakePaper |
| Fixture_Draft_MultiSource | draft multi | [[Fixture_Draft_MultiSource]] | research-methods | Smith_2024_FakePaper |
| Fixture_Draft_SingleSource | draft single | [[Fixture_Draft_SingleSource]] | research-methods | Fixture_Book |
| Fixture_Method_A | method a | [[Fixture_Method_A]] | research-methods | Smith_2024_FakePaper |
| Fixture_Ghost_Concept | ghost | [[Fixture_Ghost_Concept]] | fixture | Smith_2024_FakePaper |
