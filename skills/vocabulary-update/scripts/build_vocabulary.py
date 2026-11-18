#!/usr/bin/env python3
"""Generate _VOCABULARY.md from concept and method note frontmatter (stdlib only).

The vocabulary is a GENERATED artifact: its single source is the `aliases` frontmatter of each
concept and method note. This script walks those notes, writes one table per field, and also
reports near-duplicate concepts (same field, 2 or more shared normalised aliases). The duplicate
report is for human review only: this script never merges or edits notes.

Configuration comes from wiki.config.json (found by walking up from --vault-root or the current
directory). Keys used, with defaults:
  wiki_root            "wiki"                       wiki folder, relative to the vault root
  concept_folders      ["concepts", "methods"]      folders scanned for notes
  papers_folder        "papers"                     used to find a "source" hint per note
  books_folder         "books"
  vocabulary_file      "_VOCABULARY.md"
  wiki_title           "Science Wiki"               title shown in the generated header
  field_titlecase_map  {}                           field slug -> display title; its key order is
                                                    the section order. Unknown fields go last.

Usage:
  python build_vocabulary.py [--vault-root DIR] [--out FILE] [--dupes FILE]
"""
import argparse
import datetime
import re
import sys
import unicodedata
from collections import defaultdict
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

from wikikit import frontmatter  # noqa: E402
from wikikit.config import require_config, wiki_path  # noqa: E402


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def cell(s):
    return s.replace("|", r"\|").replace("\n", " ").strip()


def collect(wiki, cfg):
    papers = {p.stem for p in (wiki / cfg["papers_folder"]).glob("*.md")}
    books = {p.stem for p in (wiki / cfg["books_folder"]).glob("*.md")}

    def is_source(name):
        if name in papers or name in books:
            return True
        base = re.match(r"(.+?)_Ch\d+", name)
        return bool(base and base.group(1) in books)

    rows = []
    for folder in cfg["concept_folders"]:
        for path in sorted((wiki / folder).glob("*.md")):
            fm, body = frontmatter.parse(path.read_bytes().decode("utf-8", errors="ignore"))
            hint = ""
            for tgt in re.findall(r"\[\[([^\]|#]+)", body):
                if is_source(tgt.strip()):
                    hint = tgt.strip()
                    break
            rows.append({
                "canonical": path.stem,
                "field": fm.get("field", "") if isinstance(fm.get("field", ""), str) else "",
                "subfield": fm.get("subfield", "") if isinstance(fm.get("subfield", ""), str) else "",
                "aliases": frontmatter.as_list(fm.get("aliases")),
                "source": hint,
            })
    return rows


def render(rows, cfg, today):
    titles = cfg["field_titlecase_map"]
    by_field = defaultdict(list)
    for r in rows:
        by_field[r["field"] or "(unfielded)"].append(r)
    ordered = [f for f in titles if f in by_field]
    ordered += sorted(f for f in by_field if f not in titles and f != "(unfielded)")
    if "(unfielded)" in by_field:
        ordered.append("(unfielded)")

    total = len(rows)
    with_alias = sum(1 for r in rows if r["aliases"])
    out = [
        "---", "tags: [wiki, index, vocabulary]", f"date: {today}", "status: active",
        "type: index", f"last_verified: {today}", "---", "",
        f"# _VOCABULARY: {cfg['wiki_title']}", "",
        "> **Generated file: do not hand-edit.** Rebuilt from concept and method frontmatter `aliases` "
        "by `build_vocabulary.py`. Maintenance: `/vocabulary-update` re-runs it and shows the diff.",
        "> **Purpose:** the canonical synonym bridge for retrieval. A term found in text (in any "
        "language the aliases cover) should resolve to its canonical note. Powers wiki-lint Check 13 "
        "(alias documented without link) and Check 30 (vocabulary sync).",
        "> Exempt from the index-coverage check through the `_` filename prefix; keep the prefix.", "",
        f"**Entries:** {total} ({with_alias} with aliases) · "
        f"**Fields:** {len([f for f in ordered if f != '(unfielded)'])} · **Generated:** {today}", "",
    ]
    for field in ordered:
        items = sorted(by_field[field], key=lambda r: r["canonical"].lower())
        out += [f"## {titles.get(field, field)}", "", f"_{len(items)} entries._", "",
                "| Canonical | Aliases | Note | Subfield | Source |", "|---|---|---|---|---|"]
        for r in items:
            out.append("| {c} | {a} | [[{c}]] | {sf} | {src} |".format(
                c=cell(r["canonical"]), a=cell("; ".join(r["aliases"])) or "-",
                sf=cell(r["subfield"]) or "-", src=cell(r["source"]) or "-"))
        out.append("")
    return "\n".join(out) + "\n", ordered, by_field


def find_dupes(rows):
    groups = defaultdict(list)
    for r in rows:
        s = {norm(a) for a in r["aliases"] if norm(a)}
        s.add(norm(r["canonical"]))
        groups[r["field"]].append((r["canonical"], s))
    dupes = []
    for field, group in groups.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                shared = group[i][1] & group[j][1]
                if len(shared) >= 2:
                    dupes.append((field, group[i][0], group[j][0], sorted(shared)))
    return sorted(dupes)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault-root", default=".")
    ap.add_argument("--out", help="output file (default: <wiki_root>/<vocabulary_file>)")
    ap.add_argument("--dupes", help="duplicate report (default: <wiki_root>/_lint/vocabulary_dupes.txt)")
    a = ap.parse_args()

    root, cfg = require_config(a.vault_root)
    wiki = wiki_path(root, cfg)
    if not wiki.is_dir():
        sys.exit(f"Wiki folder not found: {wiki} (set wiki_root in wiki.config.json)")
    missing = [f for f in cfg["concept_folders"] if not (wiki / f).is_dir()]
    if missing:
        sys.exit(f"Concept folder(s) not found under {wiki}: {', '.join(missing)}")

    today = datetime.date.today().isoformat()
    rows = collect(wiki, cfg)
    if not rows:
        sys.exit("No concept or method notes found; nothing to write.")
    text, ordered, by_field = render(rows, cfg, today)

    out = Path(a.out) if a.out else wiki / cfg["vocabulary_file"]
    dupes_path = Path(a.dupes) if a.dupes else wiki / "_lint" / "vocabulary_dupes.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(text.encode("utf-8"))

    dupes = find_dupes(rows)
    lines = [f"# Near-duplicate concepts (same field, 2+ shared normalised aliases): {today}",
             f"# {len(dupes)} candidate pairs. REVIEW ONLY: no auto-merge.", ""]
    lines += [f"[{f}] {ci}  <->  {cj}   shared: {', '.join(sh)}" for f, ci, cj, sh in dupes]
    dupes_path.parent.mkdir(parents=True, exist_ok=True)
    dupes_path.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))

    with_alias = sum(1 for r in rows if r["aliases"])
    print(f"wrote {out}  ({len(rows)} entries, {with_alias} with aliases)")
    print(f"wrote {dupes_path}  ({len(dupes)} candidate duplicate pairs)")
    print("entries per field:")
    for f in ordered:
        print(f"  {len(by_field[f]):>4}  {cfg['field_titlecase_map'].get(f, f)}")


if __name__ == "__main__":
    main()
