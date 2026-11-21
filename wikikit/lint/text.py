"""Text helpers shared by the checks (pre-processing rules that keep link and table checks free of false positives)."""
import re
import unicodedata

from ..vault import WIKILINK as _WIKILINK

_COMMENT = re.compile(r"<!--[\s\S]*?-->")
# Indent-tolerant fences: a fenced block nested in a list carries leading spaces. [ \t]* rather than
# \s*: in multiline mode \s matches newlines, so ^\s* would let the anchor drift across blank lines.
_FENCE_BACKTICK = re.compile(r"^[ \t]*```[\s\S]*?^[ \t]*```\s*$", re.M | re.S)
_FENCE_TILDE = re.compile(r"^[ \t]*~~~[\s\S]*?^[ \t]*~~~\s*$", re.M | re.S)


def split_lines(text):
    return re.split(r"\r?\n", text)


def fm_str(value):
    """frontmatter value as a string (a list collapses to its first item, None to '')."""
    if value is None:
        return ""
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value)


def preprocess_body(body):
    """Strip HTML comments and fenced code, and unescape table pipes. Removes lines, so line numbers
    computed from the result are NOT file line numbers."""
    b = _COMMENT.sub("", body)
    b = _FENCE_BACKTICK.sub("", b)
    b = _FENCE_TILDE.sub("", b)
    return b.replace("\\|", "|")


def extract_wikilinks(body):
    """[(target, line, raw)] from the preprocessed body. `line` is relative to the preprocessed body."""
    out = []
    for i, line in enumerate(split_lines(preprocess_body(body)), 1):
        for m in _WIKILINK.finditer(line):
            t = m.group(1).strip().rstrip("\\")
            if "/" in t:
                t = t.split("/")[-1]
            out.append((t, i, m.group(1)))
    return out


def table_cell_count(row):
    """Cells in a GFM table row; an escaped pipe does not delimit, even inside a code span."""
    r = re.sub(r"\\\|", "", row.strip()).strip("|")
    return 1 if r == "" else r.count("|") + 1


def remove_diacritics(text):
    """Accent-insensitive folding (Spanish radar, phrase aliases)."""
    if not text:
        return text
    d = unicodedata.normalize("NFD", text)
    return unicodedata.normalize("NFC", "".join(c for c in d if unicodedata.category(c) != "Mn"))


def clean_link_item(item):
    """`[[Name]]` or `Name` (as found in concepts_touched / related_concepts) -> `Name`."""
    return item.replace("[[", "").replace("]]", "").strip()
