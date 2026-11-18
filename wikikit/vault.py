"""Vault-level lookups: note index, wikilinks, finding a note by name."""
import re
from pathlib import Path

WIKILINK = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
# Looser form used when only the target matters (also tolerates a trailing backslash escape).
LINK_TARGET = re.compile(r"\[\[([^\]\|#]+)")


def links(text):
    """Unique wikilink targets of `text`, in order of first appearance."""
    seen, out = set(), []
    for m in LINK_TARGET.finditer(text):
        t = m.group(1).strip().rstrip("\\").split("/")[-1]
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def note_basenames(vault_root, ignore_dirs):
    """Set of lowercase note basenames (no extension) across the vault."""
    ignore = set(ignore_dirs)
    names = set()
    for p in Path(vault_root).rglob("*.md"):
        if any(part in ignore for part in p.relative_to(vault_root).parts[:-1]):
            continue
        names.add(p.stem.lower())
    return names


def stems(folder):
    """Set of note stems directly inside `folder` (empty if it does not exist)."""
    f = Path(folder)
    return {p.stem for p in f.glob("*.md")} if f.is_dir() else set()


def find_note(wiki, folders, stem, recursive=()):
    """Path of `<wiki>/<folder>/<stem>.md` for the first folder that has it, else None. A folder named in
    `recursive` (the config's `recursive_folders`, e.g. `fields`) is searched in its subfolders too.

    Uses an exact `is_file` probe in each directory, never a file glob: file-glob tools have returned false
    negatives for notes that exist.
    """
    deep = {r.lower() for r in recursive}
    for f in folders:
        base = Path(wiki) / f
        dirs = [base] + (sorted(d for d in base.rglob("*") if d.is_dir()) if f.lower() in deep and base.is_dir() else [])
        for d in dirs:
            p = d / (stem + ".md")
            if p.is_file():
                return p
    return None
