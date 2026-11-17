#!/usr/bin/env python3
"""The write gate (V1-V5) for a `## State of Knowledge` block, and a sweep over the whole wiki.

  # gate one block before writing it (block from a file or inline):
  python synth_validate.py --note concepts/Example_Concept --block _temp/Example_Concept.block.md

  # re-check every block already written (the gate is a WRITE gate, not an invariant: a corrected
  # finding or a re-verified source can strand a number or a citation that was anchored the day the
  # block was written):
  python synth_validate.py --sweep

Exit code: 0 CLEAN, 1 ESCALATE (or any failing block in a sweep), 2 usage error.
V1 source fabrication, V2 number fabrication, V3 zero information loss, V4 pre-fulltext flagging,
V5 format. See wikikit/synthesis.py for the exact rules. Run from the vault (or pass --vault-root).
"""
import argparse
import sys
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

from wikikit import sections, synthesis  # noqa: E402
from wikikit.config import load_config, wiki_path  # noqa: E402
from wikikit.textio import read_text  # noqa: E402


def report(name, r):
    print("%s: %s  [%s]" % (name, r["RESULT"], " ".join("%s=%s" % (k, r[k][0]) for k in ("V1", "V2", "V3", "V4", "V5"))))
    if r["v1_bad"]:
        print("  V1 fabricated source: " + ", ".join(r["v1_bad"]))
    if r["v2_bad"]:
        print("  V2 fabricated number: " + ", ".join(r["v2_bad"]))
    if r["v3_bad"]:
        print("  V3 dropped controversy link: " + ", ".join(r["v3_bad"]))
    if r["v4_bad"]:
        print("  V4 entries missing the warning glyph: %d" % len(r["v4_bad"]))
        for line in r["v4_bad"][:3]:
            print("     " + line[:140])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault-root", default=".")
    ap.add_argument("--note", help="note path relative to the wiki, without .md (e.g. concepts/X)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--block", help="file holding the block to validate")
    g.add_argument("--block-text", help="the block text itself")
    ap.add_argument("--sweep", action="store_true", help="validate every existing block in the wiki")
    a = ap.parse_args()

    root, cfg = load_config(a.vault_root)
    wiki = wiki_path(root, cfg)
    sources = synthesis.source_stems(wiki, cfg)

    if a.sweep:
        total, bad = 0, 0
        for folder in cfg["concept_folders"]:
            d = wiki / folder
            for p in sorted(d.glob("*.md")) if d.is_dir() else []:
                text = read_text(p)
                block = sections.get_section(text, synthesis.BLOCK_HEADING)
                if not block.strip():
                    continue
                total += 1
                r = synthesis.validate(text, block, wiki, cfg, sources)
                if r["RESULT"] != "CLEAN":
                    bad += 1
                    report("%s/%s" % (folder, p.stem), r)
        print("sweep: %d blocks, %d clean, %d failing" % (total, total - bad, bad))
        return 1 if bad else 0

    if not a.note:
        ap.error("need --note (with --block or --block-text to gate a new block), or --sweep")
    note_path = wiki / (a.note + ".md")
    if not note_path.is_file():
        sys.exit("no such note: %s" % note_path)
    text = read_text(note_path)
    # Without --block, re-check the block the note already carries (the closeout step after a write).
    block = a.block_text or (read_text(a.block) if a.block else sections.get_section(text, synthesis.BLOCK_HEADING))
    if not block.strip():
        sys.exit("%s has no `## %s` block: pass --block to gate a new one" % (a.note, synthesis.BLOCK_HEADING))
    r = synthesis.validate(text, block, wiki, cfg, sources)
    report(a.note, r)
    return 0 if r["RESULT"] == "CLEAN" else 1


if __name__ == "__main__":
    sys.exit(main())
