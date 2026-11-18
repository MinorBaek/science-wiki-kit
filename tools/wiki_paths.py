#!/usr/bin/env python3
"""Print where a MOC or a template lives, honouring the names an existing wiki already uses.

  python wiki_paths.py moc <field-slug> [<subfield-slug>]   # path of the field MOC or sub-MOC
  python wiki_paths.py template <kind>                       # paper, concept, method, book, chapter, moc, submoc

Never compute a MOC name by hand from the rule: `moc_names` in wiki.config.json may override it (acronyms,
legacy names), and a hand-made name creates a duplicate MOC next to the real one. The path is printed
whether or not the file exists yet; the caller decides whether to create it.
Exit code: 0 printed, 2 usage error or no wiki.config.json found.
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
        sys.exit("wikikit not found: run `pip install -e <kit>` or keep the tools inside the kit checkout")

from wikikit import layout  # noqa: E402
from wikikit.config import require_config, wiki_path  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault-root", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("moc")
    p.add_argument("field")
    p.add_argument("subfield", nargs="?")
    p = sub.add_parser("template")
    p.add_argument("kind")
    a = ap.parse_args()

    root, cfg = require_config(a.vault_root)
    if a.cmd == "moc":
        print((wiki_path(root, cfg) / layout.moc_relpath(cfg, a.field, a.subfield)).as_posix())
    else:
        print(layout.template_path(root, cfg, a.kind).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
