"""Seals: the audit trail of "this note's claims about this work were checked against the PDF".

A seal is one segment appended to the `source_verification` frontmatter line of the cited work's
note (its source note):

    [2026-11-06, synth Example_Concept, Example_Concept] Checked against PDF: <text>

There is one segment per (note, work) pair. `<text>` is exactly CLEAN_TEXT when the check found
nothing, or `Corrected (<class>): ...` / `Qualified (<class>): ...` with one of DEFECT_CLASSES.

Detection accepts both English and Spanish seals (a wiki may have written the early ones in its own
language): what identifies a seal is the `[YYYY-MM-DD, ...]` header plus the note's name, not the words.
"""
import re

from . import frontmatter, vault
from .textio import detect_eol, read_text, to_lf, with_eol, write_text

CLEAN_TEXT = "what the block attributes to this work holds up."
DEFECT_CLASSES = ("figure", "hedge", "inference", "attribution", "entity", "omission", "overreach", "inversion")
SEAL_HEADER = re.compile(r"\[\d{4}-\d{2}-\d{2}[^\]]*\]")
_SV_LINE = re.compile(r'^(source_verification: ")(.*)("[ \t]*)$', re.M)
_BLOCK = re.compile(r"^## State of Knowledge[ \t]*\n(.*?)(?=^## |\Z)", re.M | re.S)


class SealError(Exception):
    """Refusal to write anything (the message says why)."""


# ---------------------------------------------------------------- writing

SOURCE_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,/()-]{0,39}$")


def format_segment(date, tag, note, text, source="PDF"):
    """`source` names what the check was made against; the default keeps the standard wording."""
    if not SOURCE_LABEL.match(source):
        raise SealError("bad seal source label %r (letters, digits, spaces and .,/()-, at most 40)" % source)
    return "[%s, %s, %s] Checked against %s: %s" % (date, tag, note, source, text.strip())


def append_seals(wiki, cfg, seals, date, tag, dry_run=False, source="PDF"):
    """Append seal segments to the source notes and set their `last_verified`.

    `seals` = [(note, work, text), ...]. Aborts without writing ANYTHING when a source note does not exist,
    its `source_verification` is not a double-quoted single line, or a text contains a double quote.
    Preserves each file's EOL. Returns [(path, eol, n_segments)].
    """
    segs = {}
    for note, work, text in seals:
        if '"' in text:
            raise SealError("double quote in the seal of %s/%s" % (note, work))
        segs.setdefault(work, []).append(format_segment(date, tag, note, text, source))

    staged = {}
    for work, parts in segs.items():
        path = vault.find_note(wiki, [cfg["papers_folder"], cfg["books_folder"]], work)
        if path is None:
            raise SealError("no source note for %s" % work)
        raw = read_text(path)
        eol = detect_eol(raw)
        t = to_lf(raw)
        head = re.match(r"^---\n.*?\n---\n", t, re.S)
        if not head:
            raise SealError("no frontmatter in the source note of %s" % work)
        fm = head.group(0)
        if _SV_LINE.search(fm):
            fm = _SV_LINE.sub(lambda mm: mm.group(1) + mm.group(2).rstrip() + " " + " ".join(parts) + mm.group(3),
                              fm, count=1)
            t = fm + t[head.end():]
        elif re.search(r"^source_verification:", fm, re.M):
            # An unquoted single-line scalar (`source_verification: fulltext`) is quoted on the way in.
            plain = re.search(r"^source_verification:[ \t]*([^\n]*?)[ \t]*$", fm, re.M).group(1)
            block_list = not plain and re.search(r"^source_verification:[ \t]*\n[ \t]", fm, re.M)
            if block_list or '"' in plain or plain[:1] in ("|", ">", "[", "{", "'", "&", "*") or plain.endswith(":"):
                raise SealError("source_verification is not a plain or double-quoted single line: %s" % work)
            value = (plain + " " if plain else "") + " ".join(parts)
            fm = re.sub(r"^source_verification:[^\n]*$", lambda mm: 'source_verification: "%s"' % value, fm,
                        count=1, flags=re.M)
            t = fm + t[head.end():]
        else:
            t = frontmatter.set_key(t, "source_verification", '"%s"' % " ".join(parts))
        t = frontmatter.set_key(t, "last_verified", date)
        staged[path] = (eol, t, len(parts))

    for path, (eol, t, n) in staged.items():
        if not dry_run:
            write_text(path, with_eol(t, eol))
    return [(p, eol, n) for p, (eol, _, n) in sorted(staged.items(), key=lambda kv: str(kv[0]))]


# ---------------------------------------------------------------- reading

def names_note(seal_value, note):
    """Does a `source_verification` value carry a seal for `note`?

    A multi-word name (`Foo_Bar`) counts as a whole token anywhere. A single-word name (`Detraining`)
    only inside a `[date, ...]` header, because in prose it can be an ordinary word.
    """
    token = re.compile(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(note))
    if "_" in note:
        return bool(token.search(seal_value))
    return any(token.search(h) for h in SEAL_HEADER.findall(seal_value))


def load_pairs(wiki, cfg):
    """(notes, source_notes): notes = {name: [works cited in its block]} for notes WITH a block;
    source_notes = {work: source_verification value}."""
    fichas = {}
    for folder in (cfg["papers_folder"], cfg["books_folder"]):
        d = wiki / folder
        if not d.is_dir():
            continue
        for p in d.glob("*.md"):
            fm_text, _ = frontmatter.split(to_lf(read_text(p)))
            m = re.search(r"^source_verification:[ \t]*(.*)$", fm_text, re.M)
            fichas[p.stem] = m.group(1).strip() if m else ""
    notes = {}
    for folder in cfg["concept_folders"]:
        d = wiki / folder
        if not d.is_dir():
            continue
        for p in d.glob("*.md"):
            blk = _BLOCK.search(to_lf(read_text(p)))
            if blk is None:
                continue
            works = [w for w in vault.links(blk.group(1)) if w in fichas]
            notes[p.stem] = works
    return notes, fichas


def load_debt(path):
    """Declared debt: lines `Note Work [cause]` (whitespace separated, `#` comments). {(note, work): cause}."""
    debt = {}
    try:
        text = read_text(path)
    except OSError:
        return debt
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        if len(parts) >= 2:
            debt[(parts[0], parts[1])] = parts[2] if len(parts) > 2 else ""
    return debt


def evaluate(notes, fichas, debt=None):
    """Classify every (note, work) pair: sealed (a seal names the note), declared debt, or unsealed."""
    debt = debt or {}
    r = {"total": 0, "sealed": [], "debt": [], "unsealed": []}
    for note in sorted(notes):
        for work in notes[note]:
            r["total"] += 1
            pair = (note, work)
            if names_note(fichas[work], note):
                r["sealed"].append(pair)
            elif pair in debt:
                r["debt"].append(pair)
            else:
                r["unsealed"].append(pair)
    r["stale_debt"] = sorted(p for p in debt if p not in set(r["debt"]))
    return r
