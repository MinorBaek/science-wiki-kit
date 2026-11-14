"""Checks 22-33: markers, placeholders, schema drift, uncited figures, structure, encoding, seals."""
import fnmatch
import re
import unicodedata
from pathlib import Path

from .. import seals as seal_lib
from ..synthesis import below_fulltext
from ..textio import read_text
from .result import Result
from .text import split_lines, table_cell_count

WARN = "⚠"
_SUBJECT = re.compile(r"\[\[([A-Za-z_0-9\-]+)")


def _s(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value)


def _letter(ch):
    return ch.isalpha()


def _cohort_note(ctx, n):
    return n.folder.lower() in (ctx.concepts.lower(), ctx.methods.lower())


# ---------------------------------------------------------------- 22

def check22(ctx):
    """Stale pre-fulltext marker: a `⚠` in a concept/method note whose OWNING wikilink is a paper that
    already carries a fulltext-level seal. The glyph asserts "unverified source" about a source that
    has been verified. The inverse of Check 21.

    Ownership is POSITIONAL, never regex-chained (the wiki uses both `[[Paper]]⚠` and `⚠[[Paper]]`):
      (1) glued to the following link and detached from the preceding one -> the following link;
      (2) otherwise, if the text to the left ends in `]]` -> that preceding link (this also keeps the
          glued-on-both-sides ambiguity with the preceding link);
      (3) detached on both sides -> the following link, if any.
    A glyph adjacent to no link is a prose caution and is ignored. The glyph's TAIL is then read for
    three exemptions: a prose caveat (the tail, without emphasis marks, starts with a letter), a dated
    italic annotation (`*(corrected 2026-09-06: ...)*`) and `(N src: ...)` confidence notation.
    Has real false positives: never empty the list blind."""
    sealed = set()
    for n in ctx.folder_notes(ctx.papers):
        sv = _s(n.fm.get("source_verification")).strip().strip('"')
        if sv and not below_fulltext(sv):
            sealed.add(n.name.lower())
    out = []
    for n in ctx.notes.values():
        if not _cohort_note(ctx, n):
            continue
        for li, line in enumerate(split_lines(n.body)):
            idx = 0
            while True:
                idx = line.find(WARN, idx)
                if idx < 0:
                    break
                raw_before, raw_after = line[:idx], line[idx + 1:]
                before, after = raw_before.rstrip(), raw_after.lstrip()
                glued_prev, glued_next = raw_before.endswith("]]"), raw_after.startswith("[[")
                owner = None
                if glued_next and not glued_prev:
                    m = re.match(r"^\[\[([A-Za-z_0-9\-]+)\]\]", raw_after)
                    if m:
                        owner = m.group(1)
                if owner is None and before.endswith("]]"):
                    ms = list(re.finditer(r"\[\[([A-Za-z_0-9\-]+)\]\]", before))
                    if ms and ms[-1].end() == len(before):
                        owner = ms[-1].group(1)
                if owner is None:
                    m = re.match(r"^\[\[([A-Za-z_0-9\-]+)\]\]", after)
                    if m:
                        owner = m.group(1)
                tail = raw_after.lstrip()
                bare = tail.lstrip("*_")
                is_caveat = len(bare) > 0 and _letter(bare[0])
                is_annotation = bool(re.match(r"^[*_]+\(\s*[^\W\d_]", tail))
                is_confidence = bool(re.match(r"^\(\s*\d+\s*src", tail))
                if owner is not None and owner.lower() in sealed and not (is_caveat or is_annotation or is_confidence):
                    out.append("%s|L%d|%s" % (n.name, li + 1 + n.body_offset, owner))
                idx += 1
    return Result("stale pre-fulltext marker on a verified paper", {"check22": len(out)},
                  {"wiki_check22_stale_warn.txt": sorted(out)})


# ---------------------------------------------------------------- 23 / 24

def check23(ctx):
    """Unfilled claim placeholder: a list entry that names a source via wikilink but whose claim text
    was never written (`- [[Paper_2018]] - [pending claim]`). It LOOKS like support (the wikilink counts
    as a source for Checks 1, 4 and 6) while asserting nothing. Every wiki folder. Patterns are config."""
    pats = [re.compile(p, re.I) for p in ctx.lcfg.get("unfilled_claim_patterns", [])]
    out = []
    if pats:
        for n in ctx.notes.values():
            for li, line in enumerate(split_lines(n.body)):
                if any(p.search(line) for p in pats):
                    m = _SUBJECT.search(line)
                    out.append("%s|L%d|%s" % (n.name, li + 1 + n.body_offset, m.group(1) if m else "-"))
    return Result("unfilled claim placeholder", {"check23": len(out)},
                  {"wiki_check23_unfilled_claim.txt": sorted(out)})


def check24(ctx):
    """Deprecated frontmatter key (`deprecated_frontmatter_keys` maps old -> canonical). Exact key
    match, so it has no false positives by construction. A schema drift that no check watches is
    discovered by whatever tool depends on the canonical key, and then it looks like a bug in the tool."""
    dep = ctx.lcfg.get("deprecated_frontmatter_keys", {})
    out = []
    for n in ctx.notes.values():
        keys = {k.lower() for k in n.fm}
        for old, new in dep.items():
            if old.lower() not in keys:
                continue
            line_no = 0
            for i, raw in enumerate(split_lines(n.text)[:60]):
                if re.match(r"^%s\s*:" % re.escape(old), raw, re.I):
                    line_no = i + 1
                    break
            out.append("%s|L%d|%s->%s" % (n.name, line_no, old, new))
    return Result("deprecated frontmatter key", {"check24": len(out)}, {"wiki_check24_deprecated_key.txt": sorted(out)})


# ---------------------------------------------------------------- 25

def _cite_key(surname, year):
    d = unicodedata.normalize("NFD", surname)
    return "".join(c.lower() for c in d if unicodedata.category(c) != "Mn" and c.isalnum()) + "_" + year


def check25(ctx):
    """Statistical figure asserted in prose with no citation inside the +/- `unsourced_radius` window.
    INFO backlog. Check 4 only matches claim VERBS, so `ICC = 0.91 (95% CI 0.84-0.95)` carried no
    verb, no citation and no warning.

    Scope: concept and method notes; blockquotes are skipped (which also excludes the State of
    Knowledge block and Useful Quotes). Dates and block ids are stripped first. Fenced code is tracked
    with a toggle, because the report needs FILE line numbers. Triage class per hit (nothing is exempted:
    exempting a whole field would hide a real figure in silence):
      cited   an author-year in the line names a source the wiki HAS: turn it into a wikilink
      block   the section already attributes to a source outside the radius (and the line itself names
              no unresolvable author-year): repeat the link
      methods the note's field is in `check25_methods_fields` (textbook worked examples)
      domain  the campaign queue"""
    pats = [re.compile(p) for p in ctx.lcfg.get("numeric_claim_patterns", [])]
    radius = ctx.lcfg["defaults"]["unsourced_radius"]
    methods_fields = {f.lower() for f in ctx.lcfg.get("check25_methods_fields", [])}
    cited_rx = re.compile(ctx.lcfg["check25_cited_pattern"]) if ctx.lcfg.get("check25_cited_pattern") else None
    link_rx = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")

    source_keys, source_stems = set(), set()
    for n in ctx.folder_notes(ctx.papers, ctx.books):
        source_stems.add(n.name)
        parts = n.name.split("_")
        if len(parts) >= 2 and re.match(r"^(?:19|20)\d{2}$", parts[1]):
            source_keys.add(_cite_key(parts[0], parts[1]))

    def named(text):
        """[(surname, year)] author-year citations in `text`."""
        out = []
        if cited_rx is None:
            return out
        for m in cited_rx.finditer(text):
            ym = re.search(r"(?:19|20)\d{2}", m.group(0))
            if ym:
                out.append((re.split(r"[\s,(]", m.group(0))[0], ym.group(0)))
        return out

    out, tally = [], {"cited": 0, "block": 0, "methods": 0, "domain": 0}
    if pats:
        for n in ctx.notes.values():
            if not _cohort_note(ctx, n) or ctx.stub_exempt_for(25, n.status):
                continue
            field = _s(n.fm.get("field")).strip().strip('"').strip()
            is_methods = field.lower() in methods_fields
            lines = split_lines(n.body)
            has_link = ["[[" in ln for ln in lines]
            block_of, b = [], 0
            for ln in lines:
                if ln.lstrip().startswith("#"):
                    b += 1
                block_of.append(b)
            block_works = {}
            for i, ln in enumerate(lines):
                works = block_works.setdefault(block_of[i], set())
                for mm in link_rx.finditer(ln):
                    tg = mm.group(1).split("/")[-1].strip()
                    if tg in source_stems:
                        works.add(tg)
                for sur, yr in named(ln):
                    k = _cite_key(sur, yr)
                    if k in source_keys:
                        works.add("ay:" + k)
            in_fence = False
            for li, raw in enumerate(lines):
                t = raw.strip()
                if re.match(r"^(```|~~~)", t):
                    in_fence = not in_fence
                    continue
                if in_fence or not t:
                    continue
                if t.startswith(("#", ">", "|", "---")) or re.match(r"^\s*[a-zA-Z_]+:", t):
                    continue
                probe = re.sub(r"\d{4}-\d{2}-\d{2}", " ", t)
                probe = re.sub(r"\^[A-Za-z0-9_-]+", " ", probe)
                value = None
                for p in pats:
                    m = p.search(probe)
                    if m:
                        value = m.group(0).strip()
                        break
                if value is None:
                    continue
                lo, hi = max(0, li - radius), min(len(lines) - 1, li + radius)
                if any(has_link[lo:hi + 1]):
                    continue
                cites = [_cite_key(s, y) in source_keys for s, y in named(t)]
                cited_resolves = any(cites)
                line_names_ghost = not all(cites) if cites else False
                block_attributed = (not line_names_ghost) and bool(block_works.get(block_of[li]))
                if cited_resolves:
                    cls = "cited"
                elif block_attributed:
                    cls = "block"
                elif is_methods:
                    cls = "methods"
                else:
                    cls = "domain"
                tally[cls] += 1
                out.append("%s|L%d|%s|%s" % (n.name, li + 1 + n.body_offset, value, cls))
    counters = {"check25": len(out)}
    counters.update({"check25_" + k: v for k, v in tally.items()})
    return Result("uncited figure in prose, INFO backlog", counters, {"wiki_check25_uncited_number.txt": sorted(out)})


# ---------------------------------------------------------------- 26 / 27

def check26(ctx):
    """Table column-count mismatch: the only STRUCTURAL check. GFM does not flag a table whose rows have
    a different number of cells than its delimiter row: it drops the surplus and blanks the missing,
    so the note stores content the rendered note never shows. The DELIMITER row is the authority (GFM
    derives the column count from it). Counted on the RAW body: an escaped `\\|` does not delimit, but a
    pipe inside a code span does. Fenced code is skipped by a trimmed toggle, so an example table in a
    code block is not counted. Every folder."""
    out = []
    for n in ctx.notes.values():
        if ctx.stub_exempt_for(26, n.status):
            continue
        lines = split_lines(n.body)
        in_fence, li = False, 0
        while li < len(lines):
            cur = lines[li].strip()
            if re.match(r"^(```|~~~)", cur):
                in_fence = not in_fence
                li += 1
                continue
            if in_fence:
                li += 1
                continue
            has_sep = li + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[li + 1].strip())
            if re.match(r"^\|.*\|$", cur) and has_sep:
                cols = table_cell_count(lines[li + 1])
                head = table_cell_count(lines[li])
                if head != cols:
                    out.append("%s|L%d|%d|%d|header" % (n.name, li + 1 + n.body_offset, cols, head))
                lj = li + 2
                while lj < len(lines) and re.match(r"^\|.*\|$", lines[lj].strip()):
                    got = table_cell_count(lines[lj])
                    if got != cols:
                        out.append("%s|L%d|%d|%d|row" % (n.name, lj + 1 + n.body_offset, cols, got))
                    lj += 1
                li = lj
            else:
                li += 1
    return Result("table column-count mismatch", {"check26": len(out)}, {"wiki_check26_table_columns.txt": sorted(out)})


def check27(ctx):
    """Mojibake: a body line that literally stores `RÂ²`, `MuÃ±oz`, `â€”`: UTF-8 bytes that were read as
    cp1252 and re-saved. DETECTION IS THE REPAIR: if `line.encode('cp1252').decode('utf-8')` succeeds and
    the result differs, the line was corrupted and the result is the correct text. Both steps are STRICT
    (no `?` substitution, no U+FFFD), so a legitimate `é` or `—` raises and is left alone. A round trip,
    not a character range: the commonest sequence carries a `€` that a range misses. No status exemption."""
    out = []
    for n in ctx.notes.values():
        for li, line in enumerate(split_lines(n.body)):
            if not line:
                continue
            try:
                fixed = line.encode("cp1252").decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
            if fixed != line:
                out.append("%s|L%d" % (n.name, li + 1 + n.body_offset))
    return Result("mojibake", {"check27": len(out)}, {"wiki_check27_mojibake.txt": sorted(out)})


# ---------------------------------------------------------------- 28 / 29

def check28(ctx):
    """Sealed work missing `last_verified`. The seal protocol writes `source_verification` AND
    `last_verified` together; a seal without the date is invisible to Check 15's `stale` bucket, so
    synthesis blocks citing the work never re-flag after a correction. Papers and books. INFO."""
    out = []
    for n in ctx.folder_notes(ctx.papers, ctx.books):
        if _s(n.fm.get("source_verification")).strip() and not _s(n.fm.get("last_verified")).strip():
            out.append(n.name)
    return Result("sealed but no last_verified", {"check28": len(out)},
                  {"wiki_check28_seal_no_lastverified.txt": sorted(out)})


def check29(ctx):
    """Wikilink pointing at an out-of-vault slug (`memory_slug_prefixes`), e.g. the files of an AI
    agent's memory. Such a slug is never a valid target: Obsidian would create a phantom note. VAULT
    WIDE on purpose (the live defects sit in project and diary folders that folder-scoped checks never
    look at). A slug in inline code or a fence does not render as a link, so it is skipped. Basenames
    in `memory_slug_exempt_files` (wildcards) are exempt: historical logs quote slugs. Disabled when
    `memory_slug_prefixes` is empty (the default)."""
    prefixes = ctx.lcfg.get("memory_slug_prefixes", [])
    out = []
    if prefixes:
        exempt = [p.lower() for p in ctx.lcfg.get("memory_slug_exempt_files", [])]
        rx = re.compile(r"\[\[((?:" + "|".join(re.escape(p) for p in prefixes) + r")[A-Za-z0-9_-]+)")
        ignore = set(ctx.cfg["vault_ignore_dirs"])
        for p in sorted(ctx.vault.rglob("*.md")):
            rel_parts = p.relative_to(ctx.vault).parts
            if any(part in ignore for part in rel_parts[:-1]):
                continue
            if any(fnmatch.fnmatchcase(p.stem.lower(), pat) for pat in exempt):
                continue
            text = read_text(p)
            if "[[" not in text:
                continue
            rel = "/".join(rel_parts)[:-3]
            in_fence = False
            for li, ln in enumerate(split_lines(text)):
                if re.match(r"^\s*(```|~~~)", ln):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                for m in rx.finditer(ln):
                    if ln[:m.start()].count("`") % 2 == 1:
                        continue
                    out.append("%s|L%d|%s" % (rel, li + 1, m.group(1)))
    return Result("wikilink to an out-of-vault slug", {"check29": len(out)},
                  {"wiki_check29_memory_slug_link.txt": sorted(out)})


# ---------------------------------------------------------------- 30 / 31

def check30(ctx):
    """Vocabulary sync (INFO): `_VOCABULARY.md` is a GENERATED artifact and the wiki's only synonym
    bridge. Deterministic CONTENT diff (not mtime): `missing` = a live concept/method note absent from
    the table; `ghost` = a table row whose note no longer exists. Remedy: /vocabulary-update.
    The canonical cell is read up to the next pipe, so names with spaces or non-ASCII letters count, and
    both sides are compared in NFC: a vocabulary generated on macOS can spell the name in NFD."""
    vocab = ctx.wiki / ctx.cfg["vocabulary_file"]
    if not vocab.is_file():
        return Result("vocabulary sync SKIPPED (%s not found)" % ctx.cfg["vocabulary_file"],
                      {"check30_missing": 0, "check30_ghost": 0}, {"wiki_check30_vocab_sync.txt": []})
    rx = re.compile(r"^\|\s*([^|\[\]]+?)\s*\|[^|]*\|\s*\[\[")  # the `[[` gate excludes header and separator

    def key(name):
        return unicodedata.normalize("NFC", name).lower()

    in_vocab = {}
    for line in split_lines(read_text(vocab)):
        m = rx.match(line)
        if m:
            in_vocab[key(m.group(1))] = m.group(1)
    live = {key(n.name): n.name for n in ctx.notes.values() if _cohort_note(ctx, n)}
    missing = sorted(v for k, v in live.items() if k not in in_vocab)
    ghost = sorted(v for k, v in in_vocab.items() if k not in live)
    lines = ["missing|%s" % x for x in missing] + ["ghost|%s" % x for x in ghost]
    return Result("vocabulary sync, INFO", {"check30_missing": len(missing), "check30_ghost": len(ghost)},
                  {"wiki_check30_vocab_sync.txt": lines})


def check31(ctx):
    """Sealed paper with NO descriptive verification text in any channel (INFO). A seal counts (Check 17:
    not empty, not `abstract*`) but is at most 60 chars, and there is no text elsewhere: a `notes:` field
    starting with Verified/Verificad, `verification_notes`, or a body callout `Re-verified vs fulltext`.
    `source_verification: fulltext` and nothing else: nobody can tell what that guarantees."""
    out = []
    for n in ctx.folder_notes(ctx.papers):
        sv = _s(n.fm.get("source_verification")).strip().strip("\"'").strip()
        if not sv or sv.lower().startswith("abstract") or len(sv) > 60:
            continue
        if re.match(r"^(Verificad|Verified)", _s(n.fm.get("notes")).strip().strip("\"'"), re.I):
            continue
        if _s(n.fm.get("verification_notes")).strip():
            continue
        if re.search(r"Re-verified vs fulltext|Reverificad", n.body, re.I):
            continue
        out.append(n.name)
    return Result("sealed but no descriptive verification text, INFO", {"check31": len(out)},
                  {"wiki_check31_seal_no_text.txt": sorted(out)})


# ---------------------------------------------------------------- 32 / 33

def check32(ctx):
    """Pair (note, work cited in its `## State of Knowledge` block) whose source-note seal does not name the
    note. Blocking: it must read 0 before a synthesis is closed. Declared debt (`seal_debt_file`, default
    `_lint/seal_debt.txt` in the wiki; one `Note Work cause` per line) does not count as a defect, but it
    is always reported and it is NOT verification. A debt line whose pair is now sealed or gone is
    `stale`. It does not see an entry rewritten with the same works: only the PDF check does."""
    rel = ctx.lcfg.get("seal_debt_file", "_lint/seal_debt.txt")
    debt = seal_lib.load_debt(ctx.wiki / rel)
    notes, fichas = seal_lib.load_pairs(ctx.wiki, ctx.cfg)
    r = seal_lib.evaluate(notes, fichas, debt)
    lines = ["%s|%s" % p for p in r["unsealed"]]
    return Result("note-work pair without a seal naming the note",
                  {"check32": len(r["unsealed"]), "check32_debt": len(r["debt"]), "check32_stale": len(r["stale_debt"])},
                  {"wiki_check32_seal_pairs.txt": lines})


def check33(ctx):
    """Paper without title or venue: a source note could reach `final` with no bibliographic identity at all,
    because Check 18 only looks at `volume` and `pages`. Stubs are exempt."""
    out = []
    for n in ctx.folder_notes(ctx.papers):
        if ctx.stub_exempt_for(33, n.status):
            continue
        miss = [k for k in ("title", "venue") if not _s(n.fm.get(k)).strip().strip("\"'").strip()]
        if miss:
            out.append("%s|%s" % (n.name, ",".join(miss)))
    return Result("paper without title or venue", {"check33": len(out)}, {"wiki_check33_no_title_venue.txt": sorted(out)})


CHECKS = [(22, check22), (23, check23), (24, check24), (25, check25), (26, check26), (27, check27),
          (28, check28), (29, check29), (30, check30), (31, check31), (32, check32), (33, check33)]
