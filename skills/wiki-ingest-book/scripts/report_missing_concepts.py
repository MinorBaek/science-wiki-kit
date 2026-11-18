#!/usr/bin/env python3
"""Report concept-shaped wikilinks in a chapter note that do not resolve anywhere in the vault.

Nothing is auto-created: concept creation is a human judgement (distinct construct vs duplicate),
and external paper citations are out of scope. Chapter forward-refs (_ChNN, handled by
create_forward_ref_stubs.py) and `Author_YYYY...` paper links are skipped.

Usage:
  python report_missing_concepts.py CHAPTER.md [--vault-root DIR] [--log _temp/missing_concepts.md]
The vault root defaults to the nearest ancestor holding wiki.config.json (else the current directory).
"""
import argparse
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

try:
    import wikikit  # noqa: F401
except ImportError:  # running from a checkout without `pip install -e .`
    for _p in Path(__file__).resolve().parents:
        if (_p / "wikikit" / "__init__.py").is_file():
            sys.path.insert(0, str(_p))
            break
    else:
        sys.exit("wikikit not found: run `pip install -e <kit>` or keep the skills inside the kit checkout")

from wikikit import frontmatter, vault  # noqa: E402
from wikikit.config import require_config, vault_path  # noqa: E402
from wikikit.textio import append_log, read_text  # noqa: E402

SKIP_CHAPTER = re.compile(r"_Ch\d+$")
SKIP_PAPER = re.compile(r"^[^\W\d_]+_\d{4}(_|$)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("chapter")
    ap.add_argument("--vault-root")
    ap.add_argument("--log", default="_temp/wiki_ingest_book_missing_concepts.md")
    a = ap.parse_args()

    chapter = Path(a.chapter)
    root, cfg = require_config(a.vault_root or chapter.parent)
    if not chapter.is_file():
        sys.exit(f"Chapter file not found: {chapter}")
    known = vault.note_basenames(vault_path(root, cfg), cfg["vault_ignore_dirs"])

    _, body = frontmatter.parse(read_text(chapter))
    counts = Counter()
    for m in vault.WIKILINK.finditer(body):
        target = m.group(1).strip().rstrip("\\")
        if not target:
            continue
        target = target.split("/")[-1]  # [[folder/Note]] syntax
        if target.lower() in known or SKIP_CHAPTER.search(target) or SKIP_PAPER.match(target):
            continue
        counts[target] += 1

    if not counts:
        print(f"No missing concept candidates in {chapter.stem}")
        return
    names = sorted(counts)
    print(f"\nMissing concept candidates referenced by {chapter.stem}:")
    print("(NOT auto-created. Review and ingest only if relevant to active research lines.)")
    for k in names:
        print(f"  - [[{k}]]" + (f"  ({counts[k]} mentions)" if counts[k] > 1 else ""))
    lines = [f"## {datetime.now():%Y-%m-%d %H:%M} - {chapter.stem}"]
    lines += [f"- [[{k}]]" + (f" ({counts[k]} mentions)" if counts[k] > 1 else "") for k in names]
    header = ("# Missing Concept Candidates: review queue\n\nConcept-shaped wikilinks referenced by ingested "
              "chapters but not present in the vault. Review each and decide: create as `status: stub`, "
              "link to an existing concept through aliases, or ignore as out of scope.")
    append_log(a.log, header, lines)
    print(f"\nLog: {a.log} (appended {len(names)} entries)")


if __name__ == "__main__":
    main()
