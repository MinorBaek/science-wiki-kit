#!/usr/bin/env python3
"""Seal source notes: record that a note's claims about a work were checked against the PDF.

Input is a JSON file:
  {"date": "2026-11-06", "tag": "synth Example_Concept", "source": "PDF",   (source is optional)
   "seals": [["Example_Concept", "Smith_2020_SR", "what the block attributes to this work holds up."],
             ["Example_Concept", "Jones_2019_RCT", "Corrected (figure): 14% in the block, 12% in Table 2."]]}

For each work it appends one segment per (note, work) pair to the END of the source note's
`source_verification` line, `[DATE, TAG, NOTE] Checked against PDF: TEXT`, and sets `last_verified`.
The text is exactly the CLEAN text when the check found nothing, or `Corrected (<class>): ...` /
`Qualified (<class>): ...` with one of: figure, hedge, inference, attribution, entity, omission,
overreach, inversion. Take the date from `date +%F`, never estimate it.

Writes NOTHING if a source note does not exist, if its `source_verification` is a block scalar or list, or
if a text contains a double quote. Preserves each file's line endings.

  python tools/seal.py seals.json --dry-run
  python tools/seal.py seals.json
"""
import argparse
import json
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
        sys.exit("wikikit not found: run `pip install -e <kit>` or keep the tools inside the kit checkout")

from wikikit import seals  # noqa: E402
from wikikit.config import require_config, wiki_path  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--vault-root", default=".")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    root, cfg = require_config(a.vault_root)
    spec = json.loads(Path(a.spec).read_bytes().decode("utf-8-sig"))
    wiki = wiki_path(root, cfg)
    try:
        done = seals.append_seals(wiki, cfg, [tuple(s) for s in spec["seals"]], spec["date"], spec["tag"],
                                  dry_run=a.dry_run, source=spec.get("source", "PDF"))
    except seals.SealError as exc:
        sys.exit("ABORT (nothing written): %s" % exc)
    for path, eol, n in done:
        print("%s %s (%s, %d segment%s)" % ("would write" if a.dry_run else "ok", path.relative_to(wiki),
                                           "crlf" if eol == "\r\n" else "lf", n, "" if n == 1 else "s"))
    print("source notes %d, segments %d" % (len(done), sum(n for _, _, n in done)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
