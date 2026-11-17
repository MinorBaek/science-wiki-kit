"""Checks 6-12: status and promotion, index health, books, drift of declared counts, backlinks."""
import datetime
import re

from ..vault import WIKILINK
from .result import Result
from .text import clean_link_item, split_lines

_LINK = WIKILINK
_CHAPTER_SUFFIX = re.compile(r"_Ch\d+$", re.I)


def _index_lines(ctx):
    from .. import frontmatter
    from ..textio import read_text
    _, body = frontmatter.parse(read_text(ctx.index_path))
    return split_lines(body)


def _cells(row):
    """Non-empty trimmed cells of a markdown table row. An escaped `\\|` (a wikilink alias) does not delimit."""
    return [c.strip() for c in re.split(r"(?<!\\)\|", row) if c.strip() != ""]


# ---------------------------------------------------------------- 6

def check6(ctx):
    """Draft notes: promote-to-final candidates and stale drafts.

    Sources are counted as DISTINCT source works: only papers/books targets count, repeated citations
    collapse, and a book parent plus its chapters (`X`, `X_Ch03`) collapse to one work. A draft with
    at least `min_distinct_sources_for_final` works is a promote candidate; below it, a draft older
    than `stale_days` (or with no parseable date) is stale."""
    min_sources = ctx.cfg["min_distinct_sources_for_final"]
    stale_days = ctx.lcfg["defaults"]["stale_days"]
    works = {n.name.lower() for n in ctx.folder_notes(ctx.papers, ctx.books)}
    stale, promote = [], []
    for n in ctx.notes.values():
        if n.status.lower() != "draft":
            continue
        keys = {re.sub(r"_Ch\d+[A-Za-z]?$", "", t).lower() for t, _, _ in n.wikilinks if t.lower() in works}
        count = len(keys)
        if count >= min_sources:
            promote.append("%s|%d" % (n.name, count))
            continue
        date_str = n.fm.get("date")
        dt = None
        m = re.match(r"^\d{4}-\d{2}-\d{2}", date_str) if isinstance(date_str, str) else None
        if m:
            try:
                dt = datetime.date.fromisoformat(m.group(0))
            except ValueError:
                dt = None
        if dt is not None and (ctx.today - dt).days >= stale_days:
            stale.append("%s|%s|%d" % (n.name, dt.isoformat(), count))
        elif dt is None:
            stale.append("%s|(no date)|%d" % (n.name, count))
    return Result("drafts", {"check6_stale": len(stale), "check6_promote": len(promote)},
                  {"wiki_check6_stale.txt": sorted(stale), "wiki_check6_promote.txt": sorted(promote)})


# ---------------------------------------------------------------- 7 / 7b

def check7(ctx):
    """Index coverage: a note whose basename is not a wikilink in index.md.

    Skipped when `index_mode` is `bases` (the index embeds Obsidian Bases views instead of per-note
    lists, so every note would false-flag). Stubs are listed separately."""
    if ctx.index_is_bases:
        return Result("index coverage SKIPPED (index_mode=bases)", {"check7_missing": 0, "check7_stubs": 0},
                      {"wiki_check7_index_missing.txt": [], "wiki_check7_stubs.txt": []})
    indexed = {t.lower() for t in ctx.index_targets}
    exempt = [re.compile(p, re.I) for p in ctx.lcfg.get("index_exempt_patterns", [])]
    missing, stubs = [], []
    for n in ctx.notes.values():
        if n.folder.lower() == "fields" or any(r.search(n.name) for r in exempt):
            continue
        if n.name.lower() not in indexed:
            (stubs if ctx.stub_exempt_for(7, n.status) else missing).append("%s|%s" % (n.name, n.folder))
    return Result("index coverage", {"check7_missing": len(missing), "check7_stubs": len(stubs)},
                  {"wiki_check7_index_missing.txt": sorted(missing), "wiki_check7_stubs.txt": sorted(stubs)})


def check7b(ctx):
    """Index section misplacement: a `- [[X]]` one-liner under the wrong `##` section.

    Check 7 only proves a basename appears SOMEWHERE in the index; a paper listed under `## Books`
    passes it. Only targets resolving to a section-mapped folder are judged (concepts and methods may
    be referenced under any section) and only level-2 headings delimit sections."""
    out = []
    if ctx.index_path.is_file() and not ctx.index_is_bases:
        sections = ctx.index_sections()
        mapped = {v.lower() for v in sections.values()}
        cur_folder, cur_section = None, None
        for ln in _index_lines(ctx):
            t = ln.lstrip()
            h = re.match(r"^##\s+(.+)$", t)
            if h:
                cur_section = h.group(1).strip()
                cur_folder = None
                for k, folder in sections.items():
                    if re.match(r"^" + re.escape(k) + r"\b", cur_section, re.I):
                        cur_folder = folder
                        break
                continue
            if cur_folder is None or not re.match(r"^[-*]\s", t):
                continue
            m = _LINK.search(ln)
            if not m:
                continue
            target = m.group(1).strip().split("/")[-1]
            note = ctx.note(target)
            if note is None or note.folder.lower() not in mapped:
                continue
            if note.folder.lower() != cur_folder.lower():
                out.append("%s|%s|%s" % (target, note.folder, cur_section))
    return Result("misplaced in index", {"check7_misplaced": len(out)},
                  {"wiki_check7_misplaced.txt": sorted(out)})


# ---------------------------------------------------------------- 8 / 9

def check8(ctx):
    """Book chapters_ingested sync: the declared set must equal the `{book}_ChNN.md` files on disk
    (chapter stubs are skipped)."""
    out = []
    book_files = {n.name.lower(): n for n in ctx.files.get(ctx.books, [])}
    for pb in ctx.folder_notes(ctx.books):
        if _CHAPTER_SUFFIX.search(pb.name):
            continue
        ci = pb.fm.get("chapters_ingested")
        if ci is None:
            continue
        declared = set()
        if isinstance(ci, list):
            for entry in ci:
                clean = clean_link_item(str(entry))
                m = re.search(r"Ch(\d+)", clean, re.I)
                if m:
                    declared.add(int(m.group(1)))
                elif re.match(r"^\d+$", clean):
                    declared.add(int(clean))
        on_disk = set()
        prefix = (pb.name + "_Ch").lower()
        for lname, f in book_files.items():
            if not lname.startswith(prefix):
                continue
            m = re.search(r"Ch(\d+)$", f.name, re.I)
            if m and not ctx.stub_exempt_for(8, f.status):
                on_disk.add(int(m.group(1)))
        if declared != on_disk:
            only_decl = sorted(declared - on_disk)
            only_fs = sorted(on_disk - declared)
            out.append("%s|declared-only:[%s] fs-only:[%s]" % (
                pb.name, ",".join(map(str, only_decl)), ",".join(map(str, only_fs))))
    return Result("book sync", {"check8": len(out)}, {"wiki_check8_book_sync.txt": sorted(out)})


def check9(ctx):
    """Chapter notes (`*_ChNN`) whose `book:` frontmatter does not link to a real vault note."""
    out = []
    for c in ctx.folder_notes(ctx.books):
        if not _CHAPTER_SUFFIX.search(c.name):
            continue
        field = c.fm.get("book")
        if isinstance(field, list):
            field = " ".join(field)
        ok = False
        if field:
            m = _LINK.search(field)
            if m and ctx.in_vault(m.group(1).strip().split("/")[-1]):
                ok = True
        if not ok:
            out.append(c.name)
    return Result("missing book frontmatter", {"check9": len(out)},
                  {"wiki_check9_chapter_book_fm.txt": sorted(out)})


# ---------------------------------------------------------------- 10 / 11

def check10(ctx):
    """Quick Stats drift: a declared count in index.md's `## Quick Stats` table differs from the
    live number of `*.md` files in the mapped folder."""
    out = []
    labels = ctx.quick_stats_labels()
    if labels and ctx.index_path.is_file():
        fs = {label: ctx.fs_count(folder) for label, folder in labels.items()}
        in_quick = False
        for ln in _index_lines(ctx):
            t = ln.lstrip()
            h = re.match(r"^##\s+(.+)$", t)
            if h:
                in_quick = bool(re.match(r"^Quick Stats", h.group(1).strip(), re.I))
                continue
            if not in_quick or not t.startswith("|"):
                continue
            cells = _cells(t)
            if len(cells) < 2 or cells[0] not in fs or not re.match(r"^\d+$", cells[1]):
                continue
            if int(cells[1]) != fs[cells[0]]:
                out.append("%s|declared=%s|fs=%d" % (cells[0], int(cells[1]), fs[cells[0]]))
    return Result("quick-stats drift", {"check10": len(out)}, {"wiki_check10_quickstats.txt": sorted(out)})


def check11(ctx):
    """Coverage by Field drift: the Concepts/Methods columns of `## Coverage by Field` versus the live
    number of NON-STUB notes.

    FIELD rows are counted by `field:` and matched by the label in cell 0 (`field_titlecase_map`);
    SUBFIELD rows (`->` or arrow) are counted by `subfield:` and keyed off the `[[MOC_*]]` link in
    cell 1, because a display label does not slugify to the subfield. A subfield with live notes and
    no row at all is reported as MISSING-ROW. Notes with an empty or unknown `field:` are INFO
    (unfielded), never a mismatch."""
    out, unfielded = [], []
    field_map = ctx.cfg.get("field_titlecase_map") or {}
    if field_map and ctx.index_path.is_file():
        slug_to_label = dict(field_map)
        label_to_slug = {v.lower(): k for k, v in field_map.items()}
        by_field = {ctx.concepts: {}, ctx.methods: {}}
        by_sub = {ctx.concepts: {}, ctx.methods: {}}
        for folder in (ctx.concepts, ctx.methods):
            for n in ctx.files.get(folder, []):
                if n.status.lower() == "stub":
                    continue
                sub = n.fm.get("subfield")
                sub = re.sub(r"[\"']", "", str(sub)).strip() if sub is not None else ""
                if sub:
                    by_sub[folder][sub] = by_sub[folder].get(sub, 0) + 1
                fld = n.fm.get("field")
                fld = re.sub(r"[\"']", "", str(fld)).strip() if fld is not None else ""
                if not fld or fld not in slug_to_label:
                    unfielded.append("%s|%s|%s" % (folder, n.name, fld or "(none)"))
                    continue
                by_field[folder][fld] = by_field[folder].get(fld, 0) + 1

        seen_sub = set()
        in_cov = False
        has_cov = False
        for ln in _index_lines(ctx):
            t = ln.lstrip()
            h = re.match(r"^##\s+(.+)$", t)
            if h:
                in_cov = bool(re.match(r"^Coverage by Field", h.group(1).strip(), re.I))
                has_cov = has_cov or in_cov
                continue
            if not in_cov or not t.startswith("|"):
                continue
            cells = _cells(t)
            if len(cells) < 4:
                continue
            label, decl_c, decl_m = cells[0], cells[2], cells[3]
            if label.lower() in label_to_slug:
                slug = label_to_slug[label.lower()]
                for col, decl, folder in (("Concepts", decl_c, ctx.concepts), ("Methods", decl_m, ctx.methods)):
                    if re.match(r"^\d+$", decl):
                        fs = by_field[folder].get(slug, 0)
                        if int(decl) != fs:
                            out.append("%s|%s|declared=%s|fs=%d" % (label, col, decl, fs))
                continue
            if not re.match(r"^(→|->)", label):
                continue
            moc = re.search(r"\[\[(?:[^\]|#]*/)?MOC_([A-Za-z0-9_]+)(?:\\?\|[^\]]*)?\]\]", cells[1])
            if not moc:
                continue
            sub_slug = moc.group(1).lower().replace("_", "-")
            seen_sub.add(sub_slug)
            shown = re.sub(r"^(→|->)\s*", "", label)
            for col, decl, folder in (("Concepts", decl_c, ctx.concepts), ("Methods", decl_m, ctx.methods)):
                if re.match(r"^\d+$", decl):
                    fs = by_sub[folder].get(sub_slug, 0)
                    if int(decl) != fs:
                        out.append("-> %s|%s|declared=%s|fs=%d" % (shown, col, decl, fs))
        # An index with no `## Coverage by Field` section declares nothing to drift from: a fresh wiki
        # must not be told every subfield is a missing row.
        for s in sorted(set(by_sub[ctx.concepts]) | set(by_sub[ctx.methods])) if has_cov else []:
            if s in seen_sub:
                continue
            out.append("MISSING-ROW|%s|fs_concepts=%d|fs_methods=%d" % (
                s, by_sub[ctx.concepts].get(s, 0), by_sub[ctx.methods].get(s, 0)))
    return Result("coverage-by-field drift", {"check11": len(out), "check11_unfielded": len(unfielded)},
                  {"wiki_check11_coverage.txt": sorted(out), "wiki_check11_unfielded.txt": sorted(unfielded)})


# ---------------------------------------------------------------- 12

def check12(ctx):
    """Bidirectional `concepts_touched`: for every `paper -> concepts_touched[token]` edge the target
    note (concepts or methods) must link back `[[paper]]` in its body.

    `asymmetry` = the target exists but carries no backlink (auto-fixable); `missing_target` = the
    token resolves to no note (report-only, triage the token). A leading `folder/` prefix is stripped.
    Forward scope is papers only."""
    concepts = {n.name.lower() for n in ctx.folder_notes(ctx.concepts)}
    methods = {n.name.lower() for n in ctx.folder_notes(ctx.methods)}
    asym, missing = [], []
    for n in ctx.folder_notes(ctx.papers):
        ct = n.fm.get("concepts_touched")
        if ct is None:
            continue
        if not isinstance(ct, list):
            ct = [ct]
        for tok in ct:
            t = clean_link_item(str(tok))
            if t == "":
                continue
            t = t.split("/")[-1]
            if t.lower() in concepts:
                folder = ctx.concepts
            elif t.lower() in methods:
                folder = ctx.methods
            else:
                missing.append("%s|%s" % (n.name, t))
                continue
            target = ctx.note(t)
            if not any(w.lower() == n.name.lower() for w, _, _ in target.wikilinks):
                asym.append("%s|%s|%s" % (n.name, t, folder))
    return Result("concepts_touched asymmetry", {"check12": len(asym), "check12_missing": len(missing)},
                  {"wiki_check12_asymmetry.txt": sorted(asym), "wiki_check12_missing_target.txt": sorted(missing)})


CHECKS = [(6, check6), (7, check7), (7, check7b), (8, check8), (9, check9), (10, check10), (11, check11), (12, check12)]
