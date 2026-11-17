"""Everything the checks read, loaded once: config, vault index, wiki notes, index.md links."""
import datetime
import json
from pathlib import Path

from .. import frontmatter, vault
from ..config import _merge, vault_path, wiki_path
from ..textio import read_text
from .text import extract_wikilinks, split_lines

_DEFAULTS_FILE = Path(__file__).with_name("defaults.json")

# Frozen clock for --self-test. A fixture cannot depend on the calendar: a draft note dated just
# before a threshold crosses it on its own one day and turns the suite red without a code change.
SELFTEST_TODAY = datetime.date(2026, 7, 1)


def lint_config(cfg):
    """Lint settings: the shipped defaults, overridden by wiki.config.json's `lint` section."""
    base = json.loads(_DEFAULTS_FILE.read_bytes().decode("utf-8"))
    return _merge(base, cfg.get("lint", {}))


class Note:
    __slots__ = ("name", "folder", "path", "text", "fm", "body", "body_offset", "wikilinks")

    def __init__(self, name, folder, path, text):
        self.name, self.folder, self.path, self.text = name, folder, path, text
        self.fm, self.body = frontmatter.parse(text)
        # Checks that REPORT a line must add this offset so the number matches the file.
        self.body_offset = len(split_lines(text)) - len(split_lines(self.body))
        self.wikilinks = extract_wikilinks(self.body)

    @property
    def status(self):
        v = self.fm.get("status")
        return v if isinstance(v, str) else ""


class Context:
    def __init__(self, root, cfg, self_test=False, today=None):
        self.root, self.cfg, self.self_test = Path(root), cfg, self_test
        self.lcfg = lint_config(cfg)
        self.vault = vault_path(root, cfg)
        self.wiki = wiki_path(root, cfg)
        self.today = SELFTEST_TODAY if self_test else (today or datetime.date.today())
        # Obsidian Bases embeds replace per-note index lists; --self-test forces manual mode so the
        # fixtures keep exercising the list-based checks (7, 7b).
        self.index_is_bases = (not self_test) and self.lcfg.get("index_mode") == "bases"
        self.stub_exempt = set(self.lcfg["stub_exempt_checks"])

        # folder roles (configured names)
        self.papers = cfg["papers_folder"]
        self.books = cfg["books_folder"]
        self.concepts = cfg["concepts_folder"]
        self.methods = cfg["methods_folder"]

        self.vault_set = vault.note_basenames(self.vault, cfg["vault_ignore_dirs"])
        self.notes = self._load_notes()
        self.index_path = self.wiki / "index.md"
        self.index_wikilinks = []
        if self.index_path.is_file():
            _, ibody = frontmatter.parse(read_text(self.index_path))
            self.index_wikilinks = extract_wikilinks(ibody)
        self.index_targets = sorted({t for t, _, _ in self.index_wikilinks})

    # -- loading ---------------------------------------------------------
    def _load_notes(self):
        """notes: {basename: Note}, one entry per basename (a cross-folder collision keeps the last).
        self.files: {folder: [Note]}, EVERY file, so counts taken per folder never undercount."""
        notes, self.files = {}, {}
        recursive = {f.lower() for f in self.cfg["recursive_folders"]}
        for folder in self.cfg["folders"]:
            d = self.wiki / folder
            self.files[folder] = []
            if not d.is_dir():
                continue
            files = d.rglob("*.md") if folder.lower() in recursive else d.glob("*.md")
            for p in sorted(files):
                if p.is_file():
                    note = Note(p.stem, folder, p, read_text(p))
                    notes[p.stem] = note
                    self.files[folder].append(note)
        self.by_lower = {k.lower(): v for k, v in notes.items()}
        return notes

    def note(self, name):
        """Case-insensitive lookup by basename (the wiki is addressed by wikilink, which is)."""
        return self.by_lower.get(name.lower())

    def source_names(self):
        """Lowercase names of the source works (papers and books): what a source citation resolves to."""
        if not hasattr(self, "_sources"):
            self._sources = {n.name.lower() for n in self.folder_notes(self.papers, self.books)}
        return self._sources

    def fs_count(self, folder):
        """Number of `*.md` files in a wiki folder, straight off the filesystem (recursive if configured)."""
        d = self.wiki / folder
        if not d.is_dir():
            return 0
        recursive = folder.lower() in {f.lower() for f in self.cfg["recursive_folders"]}
        return sum(1 for p in (d.rglob("*.md") if recursive else d.glob("*.md")) if p.is_file())

    def index_sections(self):
        """index.md heading (leading word) -> wiki folder, for Check 7b."""
        return self.lcfg.get("index_sections") or {"Papers": self.papers, "Books": self.books}

    def quick_stats_labels(self):
        """index.md Quick Stats row label -> wiki folder whose file count it must equal (Check 10)."""
        return self.lcfg.get("quick_stats_labels") or {
            "Concept notes": self.concepts, "Method notes": self.methods, "Papers": self.papers}

    # -- helpers ---------------------------------------------------------
    def in_vault(self, name):
        return name.lower() in self.vault_set

    def stub_exempt_for(self, num, status):
        return status.lower() == "stub" and num in self.stub_exempt

    def folder_notes(self, *folders):
        want = {f.lower() for f in folders}
        return [n for n in self.notes.values() if n.folder.lower() in want]
