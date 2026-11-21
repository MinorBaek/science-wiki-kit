#!/usr/bin/env python3
"""wiki-lint repair tools. Standard library only.

  python fix.py index [--out _temp/wiki_index_additions.md]
      Propose index.md entries for what Check 7 found missing (needs a prior lint run with index_mode
      `manual`, which writes wiki_check7_index_missing.txt into --out-dir). Read-only: writes a proposal.

  python fix.py check12 [--dry-run]
      Insert the missing [[paper]] backlink into every target of a Check 12 asymmetry (computed live).
      Logged to --out-dir/check12_autofix_<timestamp>.md. --dry-run logs without writing.

  python fix.py promote LISTFILE [--status final]
      Flip `status: draft` to --status in each listed note (one path or note name per line).
      Logged to --out-dir/wiki_promotion_log.md.

Run from the vault (or pass --vault-root). Only what a tool reports is touched; line endings are kept.
"""
import argparse
import datetime
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

from wikikit.config import require_config  # noqa: E402
from wikikit.lint import fixes  # noqa: E402
from wikikit.lint.context import Context  # noqa: E402
from wikikit.textio import read_text, write_text  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault-root", default=".")
    ap.add_argument("--out-dir", default=None, help="default: _temp next to wiki.config.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("index")
    p.add_argument("--out", default=None)
    p = sub.add_parser("check12")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--log", default=None)
    p = sub.add_parser("promote")
    p.add_argument("listfile")
    p.add_argument("--status", default="final")
    p.add_argument("--log", default=None)
    a = ap.parse_args()

    root, cfg = require_config(a.vault_root)
    ctx = Context(root, cfg)
    out_dir = Path(a.out_dir) if a.out_dir else Path(root) / "_temp"

    if a.cmd == "index":
        missing = out_dir / "wiki_check7_index_missing.txt"
        if not missing.is_file():
            sys.exit("Run `lint.py --only 7` first (with index_mode `manual`) to produce %s" % missing)
        text, (np_, nb, nc, nm) = fixes.index_proposal(ctx, read_text(missing).splitlines())
        out = Path(a.out) if a.out else out_dir / "wiki_index_additions.md"
        write_text(out, text)
        print("Wrote %s\nPapers: %d, Books: %d, Concept groups: %d, Method groups: %d" % (out, np_, nb, nc, nm))
    elif a.cmd == "check12":
        log = a.log or out_dir / ("check12_autofix_%s.md" % datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        r = fixes.fix_check12(ctx, dry_run=a.dry_run, log_file=log)
        print("Check 12 auto-fix [%s]: notes=%d, backlinks added=%d, skipped=%d. Log: %s"
              % (r["mode"], r["touched"], r["added"], r["skipped"], log))
    else:
        log = a.log or out_dir / "wiki_promotion_log.md"
        r = fixes.promote(ctx, a.listfile, new_status=a.status, log_file=log)
        print("Promoted %d of %d listed. Log: %s" % (r["changed"], r["listed"], log))
    return 0


if __name__ == "__main__":
    sys.exit(main())
