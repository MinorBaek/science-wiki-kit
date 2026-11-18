"""Living-synthesis layer: the write gate (V1-V5) and the block writer.

The "## State of Knowledge" block of a concept or method note restructures findings the note
already carries. This module holds the two deterministic pieces around it:

  validate()      the write gate. Five mechanical checks, no judgement:
                    V1 source fabrication   a source the block cites is not used anywhere in the note
                    V2 number fabrication   a number in the block's prose is not in the note body
                    V3 zero information loss  a `Controversies or Gaps` link does not reach the block
                    V4 pre-fulltext flagging  an entry cites a pre-fulltext paper without a warning glyph
                    V5 format               header with `updated <date>`; every bullet has a state glyph
  insert_block()  place a validated block after `## Definition` (or `## Description`) and absorb
                  `## Controversies or Gaps` by RETITLING it, never deleting it.

Why absorbing retitles instead of deleting: V2 requires every figure in the block to be anchored in
the note BODY, and the gate runs before the write, while the section still exists. Deleting the
section strands any figure that lived only there: the block passes V2 at write time and violates it
a second later. Retitling keeps every line where it was, so the invariant holds by construction.
The block is the living verdict; the body is the store that anchors it.
"""
import re
from datetime import date as _date

from . import frontmatter, sections, vault

BLOCK_HEADING = "State of Knowledge"
ABSORBED_HEADING = "## Open Questions and Caveats"
ANCHORS = ("Definition", "Description")
GLYPHS = ("✅", "⚖", "🚫", "🌱")

# A seal below fulltext level, and the marker an upgraded seal appends. An upgraded seal KEEPS its
# original abstract-level sentence for provenance, so the test is "phrase present WITHOUT the
# upgrade marker", never the phrase alone. Spanish forms are accepted for wikis that wrote them.
_BELOW = re.compile(r"abstract-level|abstract level|partial fulltext|NIVEL DE ABSTRACT|fulltext PARCIAL", re.I)
_UPGRADED = re.compile(r"UPGRADED TO FULLTEXT|AMPLIADO A FULLTEXT", re.I)
_BARE_ABSTRACT = re.compile(r"^abstract$", re.I)


class SynthError(Exception):
    """A refusal to write (the message says why)."""


# ---------------------------------------------------------------- numbers

def numbers(text, is_block=False):
    """Numbers a piece of prose asserts, as strings, unique, in order.

    Citekeys, the weight tag `(N src: ...)`, ISO dates and (block side only) a year in citation
    position are identifiers, not claims, so they are not numbers.
    """
    t = re.sub(r"\[\[[^\]]*\]\]", "", text)
    t = re.sub(r"\(\s*\d+\+?\s*src[^)]*\)", "", t)  # `7+ src` is a floor, still metadata
    t = re.sub(r"\d{4}-\d{2}-\d{2}", "", t)
    if is_block:
        # A year glued to a surname, "et al." or "&" is an identifier. Applied to the block ONLY:
        # subtracting on the note side deletes anchors and accuses blocks of figures the note holds.
        nm = r"[A-Z][A-Za-z’'\-]{1,25}"
        t = re.sub(r"\b(%s(?:\s+et\s+al\.?)?(?:\s*&\s*%s)?(?:’s|'s)?[,:]?\s*\(?)(?:19|20)\d\d\b" % (nm, nm), r"\1", t)
    # English thousands separator "2,085" -> "2085", without biting a decimal comma ("1,44", "0,004").
    t = re.sub(r"(?<!\d)([1-9]\d{0,2})(?:,\d{3})+(?!\d)", lambda m: m.group(0).replace(",", ""), t)
    t = re.sub(r"[,·]", ".", t)
    seen, out = set(), []
    for n in re.findall(r"\d+(?:\.\d+)?", t):
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


# ---------------------------------------------------------------- cohort

def _raw_value(text, key):
    v = frontmatter.get_raw(text, key)
    return None if v is None else v.strip().strip('"')


def below_fulltext(seal):
    """True when a `source_verification` value is a seal BELOW fulltext level."""
    if _BARE_ABSTRACT.match(seal):
        return True
    return bool(_BELOW.search(seal)) and not _UPGRADED.search(seal)


def is_prefulltext(name, wiki, cfg):
    """Is the cited work in the risk cohort (needs a warning glyph on its entry)?

    Papers: a fulltext-level seal is the exit door (trusted). Otherwise the paper is in the cohort
    when its `date` is before `synthesis.prefulltext_cutoff`; with no cutoff configured, a paper
    sealed only below fulltext level is in the cohort (nothing else can date it).
    Book chapters: trusted unless the chapter's own `status` is draft or stub, which is the note
    stating it was written without the fulltext; a fulltext-level seal overrides the status.
    """
    cutoff = cfg["synthesis"].get("prefulltext_cutoff")
    p = vault.find_note(wiki, [cfg["papers_folder"]], name)
    if p is not None:
        text = p.read_bytes().decode("utf-8", errors="replace")
        seal = _raw_value(text, "source_verification")
        weak = False
        if seal is not None:
            if not below_fulltext(seal):
                return False
            weak = True
        if cutoff:
            d = re.search(r"^[ \t]*date[ \t]*:[ \t]*(\d{4}-\d{2}-\d{2})", text, re.M)
            return bool(d) and d.group(1) < cutoff
        return weak
    b = vault.find_note(wiki, [cfg["books_folder"]], name)
    if b is not None:
        text = b.read_bytes().decode("utf-8", errors="replace")
        seal = _raw_value(text, "source_verification")
        if seal is not None and not below_fulltext(seal):
            return False
        status = _raw_value(text, "status")
        return bool(status) and status.lower() in ("draft", "stub")
    return False


# ---------------------------------------------------------------- gate

def validate(note_text, block, wiki, cfg, sources):
    """Run V1-V5. `sources` = set of paper/book stems. Returns a dict with the verdicts and the offenders."""
    contr = sections.get_section(note_text, "Controversies or Gaps")
    body = sections.remove_section(note_text, BLOCK_HEADING)  # the findings store: whole note minus the block
    block_links = vault.links(block)
    body_links = set(vault.links(body))

    # A source the note never uses, or a link that resolves to no note at all (an invented work has no note).
    note_folders = cfg.get("folders") or [cfg[k] for k in ("papers_folder", "books_folder", "concepts_folder",
                                                            "methods_folder")]
    v1_bad = [s for s in block_links if s not in body_links
              and (s in sources or vault.find_note(wiki, note_folders, s, cfg.get("recursive_folders", ())) is None)]
    body_nums = set(numbers(body))
    v2_bad = [n for n in numbers(block, is_block=True) if n not in body_nums]
    v3_bad = [l for l in vault.links(contr) if l not in set(block_links)]

    v4_bad = []
    for line in block.split("\n"):
        if not re.match(r"^\s*>?\s*-\s", line):
            continue
        cited = [s for s in vault.links(line) if s in sources]
        if any(is_prefulltext(s, wiki, cfg) for s in cited) and "⚠" not in line:
            v4_bad.append(line.strip())

    v5 = True
    if not re.search(r"\[!abstract\]\s*Synthesis.*updated\s+\d{4}-\d{2}-\d{2}", block, re.I):
        v5 = False
    for line in block.split("\n"):
        if re.match(r"^\s*>\s*-\s", line) and not any(g in line for g in GLYPHS):
            v5 = False

    verdict = {"V1": not v1_bad, "V2": not v2_bad, "V3": not v3_bad, "V4": not v4_bad, "V5": v5}
    return {
        **{k: ("PASS" if ok else "FAIL") for k, ok in verdict.items()},
        "RESULT": "CLEAN" if all(verdict.values()) else "ESCALATE",
        "v1_bad": v1_bad, "v2_bad": v2_bad, "v3_bad": v3_bad, "v4_bad": v4_bad,
    }


def source_stems(wiki, cfg):
    return vault.stems(wiki / cfg["papers_folder"]) | vault.stems(wiki / cfg["books_folder"])


# ---------------------------------------------------------------- writer

def insert_block(raw, block_text, absorbed, today=None, after=None, purge_absorbed=False):
    """Return (new_text, report) with the block inserted and Controversies absorbed.

    `raw` keeps its own line endings and so does the result. Raises SynthError on any refusal
    (existing block, no anchor, `absorbed` not matching the section's bullet count, ...).
    """
    today = today or _date.today().isoformat()
    eol = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(eol)

    if re.search(r"^##\s+State of Knowledge\s*$", raw, re.M):
        raise SynthError("the note already has a block: this is re-synthesis, not insertion")

    anchor, name = None, None
    for cand in ANCHORS:
        anchor = sections.section_bounds(lines, cand)
        if anchor:
            name = cand
            break
    if anchor and after:
        raise SynthError("the note has `## %s`: --after is only a rescue for notes without a canonical anchor" % name)
    if not anchor:
        if not after:
            raise SynthError("no `## Definition` or `## Description`; if the note opens with another "
                             "section (`## Overview`...), pass its exact name with --after")
        anchor = sections.section_bounds(lines, after)
        if not anchor:
            raise SynthError("no `## %s` in the note" % after)
        name = after
    insert_at = anchor[1]

    gaps = sections.section_bounds(lines, "Controversies or Gaps")
    ngaps = 0
    if gaps:
        ngaps = sum(1 for l in lines[gaps[0] + 1:gaps[1]] if re.match(r"^[-*]\s\S", l.rstrip("\r")))
    if ngaps != absorbed:
        raise SynthError("INCOMPLETE ABSORPTION: the section has %d bullets and you declared %d mapped" % (ngaps, absorbed))
    if gaps and not purge_absorbed and sections.section_bounds(lines, ABSORBED_HEADING[3:]):
        raise SynthError("the note already has `%s`: merging two sections is not automated" % ABSORBED_HEADING)

    block = block_text.replace("\r\n", "\n").rstrip("\n").split("\n")
    out = lines[:insert_at] + block + [""] + lines[insert_at:]
    action = ""
    if gaps:
        gs, ge = gaps
        off = len(block) + 1 if gs >= insert_at else 0  # the block only shifts lines BELOW it
        if purge_absorbed:
            out = out[:gs + off] + out[ge + off:]
            action = "DELETED (--purge-absorbed)"
        else:
            out[gs + off] = ABSORBED_HEADING
            out.insert(gs + off + 1, "")
            out.insert(gs + off + 2,
                       "> [!note] Absorbed into the `## State of Knowledge` block on %s. Kept here because the "
                       "block cites it: the synthesis is the living verdict, this section is the store that anchors it."
                       % today)
            action = "RETITLED to `%s`" % ABSORBED_HEADING

    # last_verified is stamped when the block is written: the note was just reviewed against its sources.
    # Line based, never `re.M` over the text (CRLF safe).
    stamp = "already had it"
    if out and out[0].strip() == "---":
        close = next((i for i in range(1, len(out)) if out[i].strip() == "---"), None)
        if close is None:
            stamp = "frontmatter not closed, NOT stamped"
        elif not any(l.startswith("last_verified:") for l in out[1:close]):
            out.insert(close, "last_verified: " + today)
            stamp = "last_verified " + today
    else:
        stamp = "no frontmatter, NOT stamped"

    report = {"anchor": name, "line": insert_at, "block_lines": len(block), "absorbed": ngaps,
              "action": action, "stamp": stamp, "eol": "CRLF" if eol == "\r\n" else "LF"}
    return eol.join(out), report
