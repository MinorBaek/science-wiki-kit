# Wiki Schema

> The contract that governs how an AI assistant (and a human) operates the wiki. The skills read it before any
> ingest, synthesis or lint run, and `wiki-lint` operationalises it. Copy this file into the root of your
> wiki folder (`<wiki_root>/WIKI_SCHEMA.md`), then adapt the sections marked **ADAPT**. Do not rename the
> section headings: the skills refer to them by name.
>
> Licence: CC-BY 4.0.

## Purpose

The wiki compounds knowledge from scientific literature into reusable, traceable notes, instead of
rediscovering it from raw PDFs on every question.

**Anti-hallucination chain**: `claim -> [[concept note]] -> [[paper note]] -> DOI -> reference manager -> PDF`.
Every factual claim must trace back to a primary source. If no source exists, the claim is flagged as
unverified, never written as fact.

## Conventions

- **Status vocabulary** for `paper`, `concept`, `method`, `book`, `book-chapter` and `synthesis` notes:
  `stub | draft | read | reviewed | final`. For `MOC` and `sub-MOC`: `active | archived`. The lint reads the
  vocabulary from `lint.status_by_type` in `wiki.config.json` (the defaults are in `wikikit/lint/defaults.json`; you only write the key to change it).
- **Frontmatter on every note**: `tags`, `date` (creation), `last_verified` (last check against a source),
  `status`, `type`.
- **Callouts**: `> [!abstract]`, `> [!warning]`, `> [!tip]`, `> [!note]`.
- **Language**: notes are written in `note_language`, whatever the language of the source. Exceptions:
  `aliases:`, verbatim quotes from sources in another language, and the log.
- **A note's `status` lives in its own frontmatter and is never copied into another note's prose.** A MOC bullet
  with a `*(draft)*` marker is a mutable fact written in an immutable place: the note gets promoted and the
  bullet keeps asserting the old value. Prefer no marker. The same rule bans ingest-state markers
  (`*(pending ingest)*`) anywhere in prose; ingest state lives only in a book hub's Table of Contents.
- **Never delete a note**: archive it (move it to an archive folder, with a seal) after a decision.

## Note Types

| Type | Folder (config key) | Purpose | Naming |
|---|---|---|---|
| Paper note | `papers_folder` | One per paper: claims, methods, evidence | `FirstAuthor_Year_Keyword.md` |
| Concept note | `concepts_folder` | One per concept; accumulates claims from many sources | `Concept_Name.md` |
| Method note | `methods_folder` | One per method or technique: how, strengths, limitations | `Method_Name.md` |
| Book note | `books_folder` | One per book: overview, contents, themes | `FirstAuthor_Year_Keyword.md` |
| Chapter note | `books_folder` | One per ingested chapter, same depth as a paper note | `..._ChNN.md` |
| MOC | `fields/` | Map of content of one field: a navigation layer, not knowledge storage | `MOC_Field_Name.md` |
| Sub-MOC | `fields/<field>/` | Map of one subfield | `MOC_Subfield_Name.md` |
| Synthesis | `debates/` | A debate spanning several notes in an active line | free |

Templates for each type are in `templates/` (or in `templates_dir`, with the file names in `template_names`, for a wiki
that already had its own; `<kit>/tools/wiki_paths.py template <kind>` resolves the path). A note keeps the `type:` its
template writes.

## Frontmatter Contracts

All notes carry the conventions above plus the type-specific fields below. Full examples are the templates.

**Paper**: `title`, `authors`, `year`, `venue`, `volume`, `issue`, `pages`, `doi`, `citekey`, `evidence_level`, `source_verification`,
`research_lines`, `concepts_touched`.

**Concept**: `field`, `subfield`, `aliases`, `related_concepts`. **Method**: `field`, `subfield`, `aliases`.

**Book**: `title`, `authors`, `editors`, `year`, `publisher`, `isbn`, `edition`, `doi`, `citekey`,
`research_lines`, `chapters_ingested`, `concepts_touched`.

**Chapter**: as a paper plus `book: "[[Book_Note]]"`, `chapter_number`, `pages`; `evidence_level: textbook`.

**Stub notes.** A stub has a definition (or only metadata) and no sourced findings. It exists to anchor a link or
seed an empty field. It carries `> [!warning] Stub: no sourced findings yet.`, is excluded from coverage counts
and from the orphan, unsourced-claim and index checks, and becomes `draft` when the first sourced finding is added.

### Evidence Level Vocabulary

`evidence_level` records the **study design** of a paper or chapter, the first of two axes the synthesis layer uses
to weight findings. The second axis, **measurement quality**, stays inline in the finding (`(MRI)` versus
`(anthropometric estimate)`) because it is per outcome, not per paper.

| Value | Design | Synthesis weight |
|---|---|---|
| `SR-MA` | Systematic review **with** meta-analysis | Highest |
| `SR` | Systematic or scoping review, no pooled MA | Very high |
| `RCT` | Randomized controlled trial (parallel groups) | High |
| `RCT-crossover` | Randomized crossover trial | High |
| `CT` | Controlled trial, non-randomized (**needs a separate control arm**) | Moderate |
| `cohort` | Prospective or longitudinal cohort, **including uncontrolled single-group pre-post** | Moderate |
| `cross-sectional` | Cross-sectional or correlational | Low to moderate |
| `case-series` | Case series or case study | Low |
| `pilot` | Pilot or feasibility study | Low |
| `narrative` | Narrative review or expert opinion | Low (framing) |
| `animal` | Animal, in-vitro or preclinical | Low (indirect) |
| `cadaveric` | Cadaveric or specimen study (human tissue) | Low (indirect) |
| `textbook` | Book chapter or textbook | Framing, not primary evidence |

The vocabulary is a list in `wiki.config.json` (`lint.evidence_level_vocab`); **ADAPT** it to your field
(a clinical wiki might add `registry`, a computational one `benchmark`).

Rules:
- One primary value per note. If the design is mixed, record the strongest applicable and note the nuance in the body.
- Book and chapter notes default to `textbook`, unless the chapter is itself a standalone SR/MA.
- **Single-group pre-post with no control arm is `cohort`**, not `CT` and not `case-series`. Stratifying one
  intervention cohort into subgroups that all get the same intervention does not create a control arm. Exception:
  honour a formal self-classification of the source as a case series.
- **Groups compared without real randomization are `CT`. Delphi or expert consensus is `narrative`.**
- Mixed or translational designs (an animal arm and a human arm): tag the arm most relevant to this wiki and add
  an inline `(also: <other design>)` note in the body.
- An engineering or device proof of concept is `pilot` plus a one-line caveat.
- `evidence_level` is descriptive; it does not change `status` or propagation. It is consumed by the synthesis layer.

## Source-Fidelity Rules (mandatory)

They apply to every ingest and re-verification. The motive of each is in `docs/GOTCHAS.md`.

1. **No fulltext, no numbers or quotes.** Never write Useful Quotes or table numbers without the fulltext in front of
   you. Without it: `status: draft`, an explicit inline flag, and only metadata and abstract-level claims marked as such.
2. **Verbatim is mandatory.** Useful Quotes are copied and pasted from the fulltext, never typed or paraphrased.
   Elisions use `...`, insertions use `[ ]`.
3. **Tables over abstract.** When the abstract and a table disagree, the table rules; document the discrepancy inline.
4. **Provenance is mandatory.** Every paper note carries `source_verification` (reference-manager key, date `YYYY-MM-DD`,
   what was verified) and complete metadata (`volume/issue/pages`, or a mark such as `online-first` or `no DOI`).
5. **`evidence_level` is a closed vocabulary** (above).
6. **Label every value with its group or side** when extracting (group A versus B, dominant versus non-dominant), to
   prevent swaps. Read the column header before the row.
7. **Anti-propagation.** When you correct a value, `grep` it across the whole wiki, and also grep the **shape** of the
   claim, not only its text (a third copy said "in the cluster" where the others named the cluster). After correcting a
   figure, re-derive anything computed from it.
8. **A superlative about the wiki's own corpus names its statistic, its term and its subset, or it is written covered.**
   "The highest ICC in the X cluster" is a claim the wiki makes about its own collection: nobody revalidates it when a new
   work enters, and no screen can see it. Name the statistic ("interaction d", not "d"), name the subset actually
   compared, check that the comparison exists (a superlative copied from a source inherits that source's scope), and when
   in doubt write "one of the largest". A verified superlative is sealed with the date and the corpus.
9. **`## Limitations` is the wiki's own appraisal, not the authors' voice.** It holds judgments the source does not make,
   facts later than the publication, and caveats no author signs. Never cite it as "the authors acknowledge that...".
   A bullet that reproduces a limitation the authors declare ends with `- *authors' own*`; without the mark, it is the
   wiki's appraisal.

## Ingest Protocol

1. Resolve the source: reference manager, then DOI lookup, then manual input.
2. Create or update the paper note (update in place; never duplicate).
3. Extract 3 to 8 concepts and the primary methods.
4. For each concept: update an existing note (append under Key Findings with a backlink) or create one from the template,
   under the creation rules below. Same for methods.
5. Fill `concepts_touched` in the paper note, with the same names the body lists.
6. Update the index, append to the log, and report every action taken.

Books go chapter by chapter (`wiki-ingest-book`), never in one pass.

## Anti-Hallucination Rules

1. Every factual statement in a concept or method note cites at least one paper note with a `[[wikilink]]`.
2. Unsourced claims are flagged: `> [!warning] No verified source in wiki. Verify before citing.`
3. Never invent a citation, DOI or title. If a paper is not in the reference manager, say so.
4. Concept notes are derived: they summarise what papers claim, not what is generally true.
5. When answering from the wiki, attribute: "According to [[paper_note]]...", and say which parts come from the wiki and
   which from the model's own knowledge.

## Concept Note Creation Rules

A concept note is created when at least one holds:
1. **Taxonomy concept**: it falls inside a subfield of this wiki's taxonomy and is relevant to the wiki's purpose
   (**ADAPT**: this threshold decides how fast the wiki grows).
2. **Repeated concept**: two or more sources address it.
3. **Scaffold stub**: seeding an empty field with a definition only.

No concept note for: a pure statistical procedure (use a method note), or a one-off mention in a single source.
Several concepts from one paper are fine if they are distinct constructs.

**Concept expansion rule**: append under Key Findings; never delete or replace. A contradiction goes under
Controversies or Gaps with both papers cited, or, once the note carries a State of Knowledge block, into the relevant
`contested` or `superseded` entry there.

**Concept and method pairs.** When a topic has both a theoretical and a protocol dimension, both notes may coexist:
the construct keeps the bare name (`X`), the method is renamed `X_Testing`, and a `companion_note` frontmatter field
cross-links them. A paper that applies the method has `X_Testing` in `concepts_touched`; one that contributes findings
has `X`. When the overlap exceeds about 50 percent, merge instead.

## Living-Synthesis Layer: the `## State of Knowledge` block

It captures the flow of the evidence on a topic (what is resolved, contested, superseded or emerging), which otherwise
sits dispersed and inline. Generated by `/wiki-synthesize`, **human-ratified, never autonomous**: every entry traces
to an existing Key Finding.

**Where.** One `## State of Knowledge` section immediately after `## Definition` and before `## Key Findings`. It
absorbs `## Controversies or Gaps`: the section is retitled, never deleted, and every existing bullet must land as an
entry (zero information loss).

**Who gets one.** Concept and method notes at the threshold: `status: final` and either at least `synthesis.min_sources`
distinct sources or at least one SR/MA of quality.

**Format.**

```
## State of Knowledge

> [!abstract] Synthesis · updated YYYY-MM-DD
> - <icon> **<sub-question> - <state>.** <one-line verdict> - [[Source_A]] [[Source_B]] (<N> src: <design>; <confidence>).
```

- **State vocabulary**: `✅ resolved`, `⚖️ contested`, `🚫 superseded`, `🌱 emerging`. Order: resolved, superseded,
  contested, emerging.
- **Verdict**: one declarative line grounded in the Key Findings, no new claims.
- **Sources**: each bullet cites its source notes as wikilinks.
- **Tally**: the unit is the source NOTE, one per distinct `[[wikilink]]` the entry cites; five chapters of one book are
  five sources here. This differs on purpose from the qualification unit of lint Check 15, which collapses chapters
  into their book: the tally asks how well one sentence is backed, Check 15 asks whether the note rests on enough
  distinct works to deserve a block.
- **Design slot**: the closed `evidence_level` vocabulary and nothing else. No synonyms, no slash-compounds, no
  `-dominant` suffix; write per-type counts (`4 src: 2 RCT + 1 CT + 1 cohort`). A bare type with no number means all of
  them. Naming only the dominant design is allowed, but not when the omitted designs are weaker than the one named.
  An entry that cites nothing writes `(0 src: <reason>; n/a)`.
- **A qualifier the vocabulary cannot express** (a practice guideline, a consensus statement, a preprint) goes in the
  entry's prose, never in the tally.
- **Confidence**: `High`, `Moderate–High`, `Moderate`, `Low–moderate` or `Low` (the two hybrids exactly so, with an
  en dash), combining design and the inline measurement-quality axis.
- **Freshness**: one block-level `updated` date. Check 15 compares it with the sources' `last_verified`.
- A debate spanning several notes and belonging to an active line is promoted to a `debates/` synthesis note.

## Query Protocol

1. Resolve the term through the vocabulary file (synonyms to the canonical name).
2. Find the field and subfield through the sub-MOCs.
3. Search concept, method, paper and book notes for the canonical name and aliases; follow outgoing wikilinks (at most
   two hops); prioritise by `evidence_level`.
4. Flag which parts come from the wiki and which from model knowledge.
5. If the wiki has no information, say so and suggest an ingest. Do not fill gaps silently.

## Lint Rules and Intentional Design Exceptions

The checks are listed in `skills/wiki-lint/SKILL.md`. Do not flag:

- **Method to paper links are one-directional by design.** A method note lists its papers; papers do not link back to
  the method note. A method note is not orphaned because no paper links to it.
- **General method definitions without a wikilink are acceptable** (standard textbook knowledge). Only unsourced claims
  in Key Findings of concept notes are flagged.
- **Book chapters count as valid sources for method notes**, as do papers.
- **Stub notes are exempt** from the coverage and index checks and from the empty `concepts_touched` check.

## Sub-MOC Architecture

When a field grows, its map of content is split by subfield, the axis every concept and method note already declares.

- One sub-MOC per subfield; the field MOC (`fields/MOC_<Field>.md`) becomes an **index of sub-MOCs** with no inline note
  lists. Sub-MOCs are created lazily: one is born with its first note.
- **Deterministic routing**: a note with `field: F` and `subfield: S` maps to `fields/F/MOC_<Title_Case_Underscore(S)>.md`,
  heading `# <Human Title> - Sub-Map of Content`. Template: `templates/submoc.md`.
- **Field MOC name**: `fields/MOC_<display title>.md`, where the display title is the value in `field_titlecase_map` with
  spaces turned into underscores and used verbatim (`Strength and Conditioning` gives `MOC_Strength_and_Conditioning.md`;
  do not re-derive it from the slug, `and` and `And` would differ). Template: `templates/moc.md`. Every field MOC is linked
  from the hub `fields/MOC_Wiki.md`, which the installer creates.
- **Existing names win.** `moc_names` in `wiki.config.json` maps a `field-slug` or `field-slug/subfield-slug` to the
  MOC stem the wiki already uses (acronyms such as `MOC_ML_Sport`, or a field MOC named before its display title).
  `<kit>/tools/wiki_paths.py moc <field> [<subfield>]` applies the map and the rules above; use it instead of
  composing a name by hand, which would create a second MOC next to the real one.
- If two fields share a sub-MOC basename, disambiguate with a path-prefixed wikilink (`[[field/MOC_X]]`); the lint
  resolver strips the path prefix.
- `fields/` is enumerated recursively (`recursive_folders`). MOCs and sub-MOCs are exempt from the orphan and
  index-coverage checks.
- The marker rule from Conventions applies: no status marker next to a MOC entry. The marker attaches to the bullet's
  subject (its first wikilink), not to the source citation that ends the line.

## Taxonomy (ADAPT)

Define here the fields and subfield slugs of your discipline, one block per field, in kebab-case. They are the values
allowed in `field:` and `subfield:`, and the keys of `field_titlecase_map` in `wiki.config.json`. A complete example
(twelve fields) is in `examples/sport-science/taxonomy.md`. Keep a short list of **routing rulings** next to it for
near-duplicate constructs that must not be merged (route by the function measured, not by surface name; see
`examples/sport-science/routing-disambiguations.md`).

Write it as a list, a field slug with its display title and then its subfield slugs:

```
strength-and-conditioning: Strength and Conditioning
  subfields: resistance-training, eccentric-training, periodization
```

A field slug is the kebab-case of its display title (`&` written as `and`). **New fields and subfields are added here**
(and the field to `field_titlecase_map`) the first time a paper needs one: append, never rename or remove (the `your-field-slug` placeholder in the shipped config is the one entry you replace). The example
taxonomy lists display titles and subfield slugs; derive the field slug with the rule above.

### Research lines (ADAPT)

`research_lines` in a paper note is a list of the active lines of work the paper serves (kebab-case slugs, for
example `hamstring-injury`, `strength-testing`). Keep the list here, one `slug: label` per line, and add a new one
here before using it. A line is a purpose ("what I am working on"); a field is a place in the discipline ("where
the knowledge lives"). They overlap often but are not the same axis.

Registered research lines (the line below is an example: replace it with your own):

```
your-line-slug: Your line label
```

## Adapting this schema

| To change | Edit |
|---|---|
| Folder names | `papers_folder`, `concepts_folder`, `methods_folder`, `books_folder`, `folders` in `wiki.config.json` |
| Status vocabulary per type | `lint.status_by_type` |
| Evidence-level vocabulary | `lint.evidence_level_vocab` (and the table above) |
| Fields and subfields | the Taxonomy section and `field_titlecase_map` |
| Synthesis threshold | `synthesis.min_sources`, `synthesis.sr_levels` |
| Note language | `note_language` and, to police it, `lint.language_radar` (see `examples/languages/es.json`) |
