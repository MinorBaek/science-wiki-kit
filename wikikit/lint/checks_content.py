"""Checks 13-21: aliases, language radar, synthesis radar, status vocabulary, provenance and metadata."""
import datetime
import re

from ..synthesis import below_fulltext
from .result import Result
from .text import fm_str as _s
from .text import preprocess_body, remove_diacritics, split_lines

_CHAPTER_SUFFIX = re.compile(r"_Ch\d+[A-Za-z]?$")


def _iso(value):
    """datetime.date from a value starting `YYYY-MM-DD`, else None."""
    m = re.match(r"^\d{4}-\d{2}-\d{2}", _s(value))
    if not m:
        return None
    try:
        return datetime.date.fromisoformat(m.group(0))
    except ValueError:
        return None


def _work_keys(ctx, note):
    """Distinct source works cited by `note` (papers/books targets; book chapters collapse to the book)."""
    works = ctx.source_names()
    return {_CHAPTER_SUFFIX.sub("", t).lower() for t, _, _ in note.wikilinks if t.lower() in works}


# ---------------------------------------------------------------- 13

def check13(ctx):
    """Alias documented in a concept/method note's frontmatter, used in another note's prose WITHOUT a
    link to its canonical note. INFO backlog.

    Distinctive aliases only: an ALL-CAPS/alnum acronym (2-8 chars, at least one letter, case
    sensitive) or a multi-word phrase of at least 6 chars (accent- and case-insensitive). Blockquote
    (verbatim) lines are not searched; the canonical note itself is excluded; `alias_link_stoplist`
    drops ubiquitous acronyms."""
    stop = {s.lower() for s in ctx.lcfg.get("alias_link_stoplist", [])}
    acronyms, phrases = {}, {}
    pool = [n for n in ctx.notes.values() if n.folder.lower() in (ctx.concepts.lower(), ctx.methods.lower())]
    for n in sorted(pool, key=lambda x: x.name):
        al = n.fm.get("aliases")
        if al is None:
            continue
        for a in (al if isinstance(al, list) else [al]):
            a = str(a).strip()
            if not a or a.lower() in stop:
                continue
            if re.fullmatch(r"[A-Z0-9]{2,8}", a) and re.search(r"[A-Z]", a):
                acronyms.setdefault(a, []).append(n.name)
            elif " " in a and len(a) >= 6:
                phrases.setdefault(remove_diacritics(a).lower(), []).append(n.name)

    out = []
    acr = [(a, "/".join(sorted(set(c))), {x.lower() for x in c}) for a, c in acronyms.items()]
    phr = [(k, "/".join(sorted(set(c))), {x.lower() for x in c}, set(re.findall(r"[a-z0-9]+", k)))
           for k, c in phrases.items()]
    for n in pool:
        if ctx.stub_exempt_for(13, n.status):
            continue
        lines = [ln for ln in split_lines(preprocess_body(n.body)) if not ln.lstrip().startswith(">")]
        text = "\n".join(lines)
        linked = {t.lower() for t, _, _ in n.wikilinks}
        me = n.name.lower()
        tokens = set(t for t in re.split(r"[^A-Za-z0-9]+", text) if t)
        for alias, shown, canon_lc in acr:
            if alias in tokens and me not in canon_lc and not (canon_lc & linked):
                out.append("%s|%s|%s" % (n.name, alias, shown))
        if phr:
            folded = remove_diacritics(text).lower()
            words = set(re.findall(r"[a-z0-9]+", folded))
            for key, shown, canon_lc, key_words in phr:
                if key_words <= words and key in folded and me not in canon_lc and not (canon_lc & linked) \
                        and re.search(r"\b" + re.escape(key) + r"\b", folded):
                    out.append("%s|%s|%s" % (n.name, key, shown))
    return Result("alias documented without link, INFO", {"check13": len(out)},
                  {"wiki_check13_alias_no_link.txt": sorted(out)})


# ---------------------------------------------------------------- 14

def check14(ctx):
    """Language radar: notes written in a language other than the wiki's.

    A section heading (H2-H6; the H1 is the source's own title) whose first word is in
    `language_radar.headings`, OR at least `prose_threshold` stopword hits in prose, flags the note.
    Disabled unless `language_radar.enabled`. Report-only: it scopes a normalisation pass.

    Guards against known false positives, all configurable: `case_sensitive_tokens` are counted only
    in lower case (a stopword that is also an upper-case acronym), optionally skipped on a line
    matching `line_guards[token]`; `heading_requires_accent` heading words count only when written
    with their accent (the folded form collides with an English word); a stopword written entirely
    in capitals is an acronym and is discounted."""
    lr = ctx.lcfg["language_radar"]
    if not lr.get("enabled"):
        return Result("language radar DISABLED", {"check14": 0}, {"wiki_check14_foreign_language.txt": []})
    fold = lambda s: remove_diacritics(s).lower()  # noqa: E731
    headings = {fold(h) for h in lr["headings"]}
    stop = {fold(s) for s in lr["stopwords"]}
    cs_tokens = {t.lower() for t in lr.get("case_sensitive_tokens", [])}
    guards = {k.lower(): re.compile(v) for k, v in lr.get("line_guards", {}).items()}
    need_accent = {fold(h) for h in lr.get("heading_requires_accent", [])}
    threshold = lr.get("prose_threshold", 8)

    out = []
    for n in ctx.notes.values():
        if ctx.stub_exempt_for(14, n.status):
            continue
        head_hits = stop_hits = 0
        for ln in split_lines(preprocess_body(n.body)):
            t = ln.lstrip()
            h = re.match(r"^(#{1,6})\s+(.+)$", t)
            if h:
                if len(h.group(1)) == 1:
                    continue
                first = h.group(2).strip().split()[0]
                first_fold = re.sub(r"[^a-z0-9]", "", fold(first))
                if first_fold and first_fold in headings:
                    if first_fold not in need_accent or remove_diacritics(first) != first:
                        head_hits += 1
                continue
            if t.startswith("|"):
                continue
            if t.startswith(">"):
                ln = re.sub(r"^[ \t]*(?:>[ \t]?)+", "", ln)
            folded = fold(ln)
            for tok in re.split(r"[^a-z0-9]+", folded):
                if tok and tok not in cs_tokens and tok in stop:
                    stop_hits += 1
            for tok in cs_tokens & stop:
                g = guards.get(tok)
                if g is None or not g.search(ln):
                    stop_hits += len(re.findall(r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(tok), ln))
            for m in re.finditer(r"(?<![A-Za-z0-9])[A-Z]{2,}(?![A-Za-z0-9])", ln):
                u = fold(m.group(0))
                if u not in cs_tokens and u in stop:
                    stop_hits -= 1
        if head_hits >= 1 or stop_hits >= threshold:
            out.append("%s|%s|H=%d|S=%d" % (n.name, n.folder, head_hits, stop_hits))
    return Result("language radar", {"check14": len(out)}, {"wiki_check14_foreign_language.txt": sorted(out)})


# ---------------------------------------------------------------- 15

def check15(ctx):
    """Synthesis radar. Over `final` concept/method notes, two report-only buckets:

    missing: qualifies for a `## State of Knowledge` block (at least `synthesis.min_sources` distinct
             source works, OR one cited source whose `evidence_level` is in `synthesis.sr_levels`)
             but has none: the `/wiki-synthesize` worklist.
    stale:   has a block whose `updated` date predates the newest `last_verified` among its cited works."""
    syn = ctx.cfg["synthesis"]
    min_sources = syn["min_sources"]
    sr = {x.lower() for x in syn["sr_levels"]}
    heading = ctx.lcfg.get("synthesis_block_heading", "## State of Knowledge")
    works = ctx.source_names()
    missing, stale = [], []
    for n in ctx.notes.values():
        if n.folder.lower() not in (ctx.concepts.lower(), ctx.methods.lower()):
            continue
        if n.status.lower() != "final":
            continue
        keys, has_sr, max_lv = set(), False, None
        for t, _, _ in n.wikilinks:
            if t.lower() not in works:
                continue
            keys.add(_CHAPTER_SUFFIX.sub("", t).lower())
            src = ctx.note(t)
            if src is None:
                continue
            ev = _s(src.fm.get("evidence_level"))
            if ev and ev.lower() in sr:
                has_sr = True
            lv = _iso(src.fm.get("last_verified"))
            if lv and (max_lv is None or lv > max_lv):
                max_lv = lv
        if not (len(keys) >= min_sources or has_sr):
            continue
        if not re.search(re.escape(heading), n.body, re.I):
            missing.append("%s|%s|works=%d|srma=%s" % (n.name, n.folder, len(keys), has_sr))
            continue
        m = re.search(r"^>\s*\[!abstract\][^\r\n]*updated\s+(\d{4}-\d{2}-\d{2})", n.body, re.M | re.I)
        upd = None
        if m:
            try:
                upd = datetime.date.fromisoformat(m.group(1))
            except ValueError:
                upd = None
        if max_lv is not None and (upd is None or max_lv > upd):
            stale.append("%s|%s|updated=%s|maxLv=%s" % (n.name, n.folder, upd.isoformat() if upd else "(no date)",
                                                       max_lv.isoformat()))
    return Result("synthesis radar", {"check15_missing": len(missing), "check15_stale": len(stale)},
                  {"wiki_check15_missing.txt": sorted(missing), "wiki_check15_stale.txt": sorted(stale)})


# ---------------------------------------------------------------- 16

def check16(ctx):
    """Status vocabulary: a note whose `status` is not in `status_by_type[type]`, that declares no
    status or no type (so it cannot be validated), or that leaked a template line (`draft | final`)."""
    allowed_by_type = {k.lower(): v for k, v in ctx.lcfg["status_by_type"].items()}
    out = []
    for n in ctx.notes.values():
        status = _s(n.fm.get("status")).strip()
        if not status:
            out.append("%s|%s|missing 'status:' (note declares no status)" % (n.name, n.folder))
            continue
        if "|" in status:
            out.append("%s|%s|template-leak: '%s'" % (n.name, n.folder, status))
            continue
        typ = _s(n.fm.get("type")).strip()
        if not typ:
            out.append("%s|%s|missing 'type:' (status '%s' unvalidated)" % (n.name, n.folder, status))
            continue
        allowed = allowed_by_type.get(typ.lower())
        if allowed is None:
            continue
        if status.lower() not in {a.lower() for a in allowed}:
            out.append("%s|%s|invalid '%s' (type=%s; allowed: %s)" % (n.name, n.folder, status, typ, ", ".join(allowed)))
    return Result("status vocabulary violations", {"check16": len(out)},
                  {"wiki_check16_status_vocab.txt": sorted(out)})


# ---------------------------------------------------------------- 17-21 (papers)

def check17(ctx):
    """Missing `source_verification` (provenance backlog, INFO). A value starting with `abstract` is
    NOT a seal: the protocol forbids sealing against an abstract."""
    out = []
    for n in ctx.folder_notes(ctx.papers):
        if ctx.stub_exempt_for(17, n.status):
            continue
        sv = _s(n.fm.get("source_verification"))
        if not sv.strip() or sv.strip().strip("\"'").strip().lower().startswith("abstract"):
            out.append(n.name)
    return Result("no source_verification, INFO backlog", {"check17": len(out)},
                  {"wiki_check17_no_provenance.txt": sorted(out)})


def _months_before(d, months):
    y, m = divmod(d.year * 12 + d.month - 1 - months, 12)
    m += 1
    import calendar
    return datetime.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def check18(ctx):
    """Verified-but-incomplete metadata: a paper that DECLARES `source_verification` yet lacks `volume`
    or `pages`, with no dated exemption.

    The exemption is `check18_exempt: "YYYY-MM-DD, reason"`: explicit, dated, auditable, and reported
    separately (older than `check18_exempt_stale_months` counts as stale). A malformed value does NOT
    exempt: it lands in the backlog labelled (fail closed). Conference papers (pagination without a
    volume, in a proceedings-like venue) and theses (neither field, venue says thesis/dissertation)
    are exempt by shape, not by the seal's wording, because a seal can be written in any language."""
    stale_months = ctx.lcfg.get("check18_exempt_stale_months", 12)
    limit = _months_before(ctx.today, stale_months)
    out, exempt, exempt_stale = [], [], []
    for n in ctx.folder_notes(ctx.papers):
        if ctx.stub_exempt_for(18, n.status):
            continue
        if not _s(n.fm.get("source_verification")).strip():
            continue  # total-missing is Check 17's
        has_vol = bool(_s(n.fm.get("volume")).strip())
        has_pages = bool(_s(n.fm.get("pages")).strip())
        if has_vol and has_pages:
            continue
        ex = _s(n.fm.get("check18_exempt")).strip()
        if ex:
            ex = ex.strip("\"'").strip()
            m = re.match(r"^(\d{4}-\d{2}-\d{2})\s*,\s*\S", ex)
            if m:
                exempt.append("%s|%s" % (n.name, ex))
                try:
                    if datetime.date.fromisoformat(m.group(1)) < limit:
                        exempt_stale.append("%s|%s" % (n.name, m.group(1)))
                except ValueError:
                    exempt_stale.append("%s|unreadable date: %s" % (n.name, m.group(1)))
                continue
            out.append("%s|check18_exempt malformed (missing ISO date or reason): %s" % (n.name, ex))
            continue
        venue = _s(n.fm.get("venue"))
        if not has_vol and has_pages and re.search(r"proceedings|conference|symposium|congress", venue, re.I):
            continue
        if not has_vol and not has_pages and re.search(r"\b(thesis|dissertation)\b", venue, re.I):
            continue
        out.append("%s|volume=%s pages=%s" % (n.name, has_vol, has_pages))
    return Result("verified but incomplete metadata",
                  {"check18": len(out), "check18_exempt": len(exempt), "check18_exempt_stale": len(exempt_stale)},
                  {"wiki_check18_incomplete_metadata.txt": sorted(out), "wiki_check18_exemptions.txt": sorted(exempt),
                   "wiki_check18_exempt_stale.txt": sorted(exempt_stale)})


def check19(ctx):
    """`evidence_level` outside the closed vocabulary (`evidence_level_vocab`). Papers only: books use
    `textbook`, so a PAPER tagged `textbook` is a genuine mislabel."""
    vocab = {v.lower() for v in ctx.lcfg["evidence_level_vocab"]}
    out = []
    for n in ctx.folder_notes(ctx.papers):
        lvl = _s(n.fm.get("evidence_level")).strip()
        if lvl and lvl.lower() not in vocab:
            out.append("%s|%s" % (n.name, lvl))
    return Result("evidence_level out of vocabulary", {"check19": len(out)},
                  {"wiki_check19_evidence_level.txt": sorted(out)})


def check20(ctx):
    """A blockquote under `## Useful Quotes` carrying a leaked `]]` (a wikilink artifact inside a quote).
    An empty Useful Quotes section is deliberately NOT flagged."""
    out = []
    for n in ctx.folder_notes(ctx.papers):
        in_q = flagged = False
        for ln in split_lines(n.body):
            t = ln.lstrip()
            h = re.match(r"^##\s+(.+)$", t)
            if h:
                in_q = bool(re.match(r"^Useful Quotes", h.group(1).strip(), re.I))
                continue
            if in_q and t.startswith(">") and "]]" in t:
                flagged = True
        if flagged:
            out.append(n.name)
    return Result("Useful Quotes ']]' artifact", {"check20": len(out)}, {"wiki_check20_quote_sanity.txt": sorted(out)})


def check21(ctx):
    """Pre-fulltext cohort (INFO backlog): a paper dated before `synthesis.prefulltext_cutoff` with no
    fulltext-level seal. A seal only exits the cohort if it reaches fulltext (see
    `synthesis.below_fulltext`; keep the checks that use it in step)."""
    cutoff = ctx.cfg["synthesis"].get("prefulltext_cutoff")
    cutoff = datetime.date.fromisoformat(cutoff) if cutoff else None
    out = []
    for n in ctx.folder_notes(ctx.papers):
        if ctx.stub_exempt_for(21, n.status):
            continue
        sv = _s(n.fm.get("source_verification")).strip().strip('"')
        if sv and not below_fulltext(sv):
            continue
        d = _iso(n.fm.get("date"))
        if cutoff and d and d < cutoff:
            out.append(n.name)
    return Result("pre-fulltext cohort, INFO backlog", {"check21": len(out)},
                  {"wiki_check21_prefulltext_cohort.txt": sorted(out)})


CHECKS = [(13, check13), (14, check14), (15, check15), (16, check16), (17, check17), (18, check18),
          (19, check19), (20, check20), (21, check21)]
