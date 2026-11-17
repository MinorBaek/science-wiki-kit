#!/usr/bin/env python3
"""Write a validated `## State of Knowledge` block into its note.

  - inserts the block right AFTER `## Definition` (or `## Description`, how most method notes title it);
  - ABSORBS `## Controversies or Gaps` by RETITLING it to `## Open Questions and Caveats`, never deleting
    it, and only if you declare its bullets already mapped (`--absorbed N` must equal the bullet count);
  - stamps `last_verified` if the note lacks it; preserves the file's line endings.

  python synth_write.py --note concepts/X --block _temp/X.block.md --absorbed 3
  python synth_write.py --note concepts/X --block _temp/X.block.md --absorbed 0 --dry-run

Use --after "<Section>" only for a note with neither `## Definition` nor `## Description`.
--purge-absorbed deletes the section instead of retitling it; do not use it unless you checked that no
block figure or wikilink lives only in that section (it would fail V2 on the next sweep).
Run from the vault (or pass --vault-root). Write the block through synth_validate.py first.
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

from wikikit import synthesis  # noqa: E402
from wikikit.config import load_config, wiki_path  # noqa: E402
from wikikit.textio import read_text, write_text  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault-root", default=".")
    ap.add_argument("--note", required=True, help="folder/name inside the wiki, without .md")
    ap.add_argument("--block", required=True)
    ap.add_argument("--absorbed", type=int, required=True,
                    help="bullets of `Controversies or Gaps` already mapped to a block entry")
    ap.add_argument("--after", metavar="SECTION")
    ap.add_argument("--purge-absorbed", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    root, cfg = load_config(a.vault_root)
    wiki = wiki_path(root, cfg)
    path = wiki / (a.note + ".md")
    if not path.is_file():
        sys.exit("no such note: %s" % path)
    raw, block = read_text(path), read_text(a.block)
    # The gate runs here too: a block that skipped synth_validate.py must not reach the note.
    gate = synthesis.validate(raw, block, wiki, cfg, synthesis.source_stems(wiki, cfg))
    if gate["RESULT"] != "CLEAN":
        failed = ", ".join(k for k in ("V1", "V2", "V3", "V4", "V5") if gate[k] == "FAIL")
        sys.exit("REFUSED: the gate says %s (%s). Run synth_validate.py, fix the block, never the gate."
                 % (gate["RESULT"], failed))
    try:
        new, rep = synthesis.insert_block(raw, block, a.absorbed, after=a.after, purge_absorbed=a.purge_absorbed)
    except synthesis.SynthError as exc:
        sys.exit("REFUSED: %s" % exc)
    print("%-44s inserts %d lines after `## %s` (line %d)%s; %s" % (
        a.note, rep["block_lines"], rep["anchor"], rep["line"],
        "; absorbs %d bullets of Controversies or Gaps and %s" % (rep["absorbed"], rep["action"]) if rep["action"] else "",
        rep["stamp"]))
    if a.dry_run:
        return 0
    write_text(path, new)
    print("  written (EOL %s preserved)" % rep["eol"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
