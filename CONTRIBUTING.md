# Contributing

Thanks for helping. The kit is small on purpose: standard-library Python, markdown instructions, no build step.

## Run the tests

From the repository root, on any platform (Python 3.10 or newer):

```
python -I -m unittest discover -s tests
python -I skills/wiki-lint/scripts/lint.py --self-test
```

The first runs the unit tests (including the worked example, which must lint clean). The second runs the linter
against the synthetic mini-wiki in `tests/fixtures/lint/` with a frozen clock and compares 43 counters with
`tests/fixtures/lint/expected_counters.txt`. CI runs both on Windows, macOS and Linux.

## The rule for a check

Every lint check is guarded by a fixture with **a positive and a guard**:

1. **Positive**: a note that must trigger the check.
2. **Guard**: a near-miss that must **not** trigger it (an escaped pipe, a code span, an exempt type).
3. Update `expected_counters.txt` and write a comment saying why the value is what it is.
4. **Prove the fixture discriminates**: change the check's logic, run the self-test, and see it fail. A fixture
   that passes both before and after a change guards nothing. Then restore the logic.

A zero from a check measures the detector, not the wiki; that is why step 4 exists. The reasoning behind each check
is in `skills/wiki-lint/references/check-origins.md`, and the same idea runs through `docs/GOTCHAS.md`.

New checks go in `wikikit/lint/` (`checks_*.py`), are registered in `engine.ALL_CHECKS`, and read their thresholds
from `wikikit/lint/defaults.json` so a wiki can override them in its `wiki.config.json`.

## Other conventions

- **No personal data, paths or names of real notes** in code, docs or fixtures. Fixtures use invented names
  (`Fixture_*`, `Smith_2024_FakePaper`).
- **Line endings**: the code reads and writes through `wikikit.textio`, which keeps each file's EOL. Do not use
  `open(..., "w")` on wiki notes.
- **Docs and skills are in English.** A language-specific behaviour goes in an `examples/languages/` file, not in the
  code.
- **Skills**: keep a `SKILL.md` short and move detail to `references/`. Refer to the kit's tools as
  `<kit>/tools/...`.
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`), one change per commit.

## Reporting a problem

Use the issue templates. For a wrong lint finding, say which check, and include the smallest note that reproduces it
(anonymised). For a skill that misbehaved with your agent, say which agent and which step of the skill.

## Licences

By contributing you agree that code is released under the MIT licence and documentation, schema, templates and
examples under CC BY 4.0 (see `LICENSE` and `LICENSE-DOCS`).
