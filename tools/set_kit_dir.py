#!/usr/bin/env python3
"""Record the kit's location in a wiki.config.json, as `kit_dir`.

The skills refer to the kit's tools as `<kit>/tools/...`; `kit_dir` tells an agent (or you) what `<kit>`
is when the skills were linked or copied away from the checkout. The installers call this; run it by hand
if you move the kit.

    python set_kit_dir.py path/to/wiki.config.json [kit_dir]     # kit_dir defaults to this checkout

Edits the one line in place (adds it after the opening brace when absent), so the rest of the file keeps its
formatting and key order.
"""
import json
import re
import sys
from pathlib import Path


def main(argv):
    if not argv or len(argv) > 2:
        sys.exit(__doc__)
    cfg = Path(argv[0])
    kit = Path(argv[1] if len(argv) > 1 else Path(__file__).resolve().parent.parent).resolve()
    text = cfg.read_text(encoding="utf-8-sig")  # as load_config: a BOM (Windows PowerShell 5.1) is not an error
    json.loads(text)  # refuse to touch a file that is not valid JSON
    value = json.dumps(kit.as_posix())
    if re.search(r'^\s*"kit_dir"\s*:', text, re.M):
        new = re.sub(r'^(\s*"kit_dir"\s*:\s*)"[^"\n]*"', lambda m: m.group(1) + value, text, count=1, flags=re.M)
    else:
        new = re.sub(r"\{", '{\n  "kit_dir": %s,' % value, text, count=1)
    json.loads(new)
    cfg.write_text(new, encoding="utf-8", newline="")
    print("kit_dir = %s in %s" % (kit.as_posix(), cfg))


if __name__ == "__main__":
    main(sys.argv[1:])
