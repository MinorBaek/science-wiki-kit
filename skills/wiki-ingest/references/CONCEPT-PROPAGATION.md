# Concept Propagation Rules

## When to CREATE a new concept note

Create a concept note ONLY when at least one of these is true:

1. **Taxonomy concept**: the concept falls within a field or subfield of this wiki's taxonomy (see `WIKI_SCHEMA.md` → Taxonomy) AND is relevant to the user's active research, teaching or career trajectory. The taxonomy is defined per wiki; for an example of a complete one see `examples/sport-science/taxonomy.md`.
2. **Repeated concept**: two or more papers already in the wiki (or the current paper plus one other the user can confirm) address the same concept.

**Stub rule**: if a concept is foundational for a field but has no sourced finding yet, create it with `status: stub`: a Definition and the stub warning callout, no Key Findings. As soon as it has one cited finding it is a `draft` (a single-source `draft` until a second independent work corroborates it).

Do NOT create a concept note for:
- Generic terms well covered in textbooks, with no wiki-specific findings
- Concepts that appear only once and fall outside the taxonomy relevance criteria
- Statistical methods, measurement protocols or research-design frameworks: use `methods/` instead

## Concept note filename

- CamelCase with underscores between words
- English
- Examples: `Eccentric_Training.md`, `Force_Velocity_Relationship.md`

## Updating an existing concept note

When a new paper adds evidence to an existing concept:

1. Open `concepts/{Concept}.md`.
2. Under **Key Findings**, APPEND (never replace):
   ```
   - [New finding from paper] — [[FirstAuthor_Year_Keyword]]
   ```
3. If the new paper **contradicts** an existing finding, move the contradiction to **Controversies or Gaps**
   (once the note carries a `## State of Knowledge` block, put it in the relevant `contested` or `superseded`
   entry of the block instead, per `WIKI_SCHEMA.md`; do not recreate the absorbed section):
   ```
   - [Finding A] — [[Paper_A]] vs. [Contradicting finding] — [[New_Paper]]
   ```
4. Update `related_concepts` if new concept-to-concept links emerge.
5. Do NOT delete existing findings. Append only.

## Creating a new concept note

Use `templates/concept.md`. Fill:

1. **Frontmatter**: `date` = today, `tags` includes the field slug, `aliases` for alternate names (including the second language if your wiki is bilingual), and **`field:`** and **`subfield:`** per the taxonomy in `WIKI_SCHEMA.md`.
2. **Definition**: 1 to 2 sentence working definition citing the current paper.
3. **Key Findings**: at least the finding(s) that triggered the note.
4. **Implications**: a brief note on why this matters to the user's work.

Minimum content bar: a concept note without at least one cited finding is not ready. Leave `status: draft` until it cites **N distinct source works** (`min_distinct_sources_for_final`, default 2): independent papers or books, where a book parent note and its chapter notes count as **one** work. Canonical table: `wiki-ingest/SKILL.md`, "Initial status decision".

## Concept name disambiguation

If a concept could be confused with another:
- Add an `aliases` entry for the alternative name.
- Add a disambiguating note at the top of the Definition section.
- Example: `Eccentric_Training` might carry the alias "negative training", with the distinction noted in the Definition.

## Relationship between concepts

After creating or updating concept notes, check:
- Should any existing note's `related_concepts` be updated?
- Is there a hierarchy (for example `External_Rotation_Strength` as a subtype of `Shoulder_Biomechanics`)?
- Update both notes to reflect the relationship.
