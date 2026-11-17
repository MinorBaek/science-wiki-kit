"""Regressions from the 2026-11 audit: script entry points and lint checks on small synthetic wikis."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from wikikit.config import load_config  # noqa: E402
from wikikit.lint import checks_integrity, checks_structure  # noqa: E402
from wikikit.lint.context import Context  # noqa: E402
from wikikit.textio import read_text, write_text  # noqa: E402

SYNTH = ROOT / "skills" / "wiki-synthesize" / "scripts"
LINT = ROOT / "skills" / "wiki-lint" / "scripts" / "lint.py"

NOTE = ("---\ntype: concept\nstatus: final\n---\n# T\n## Definition\nd\n"
        "## Key Findings\n- gain of 12 % [[Smith_2020_Real]]\n")
BLOCK = ("## State of Knowledge\n\n> [!abstract] Synthesis · updated 2026-11-17\n"
         "> - ✅ **Q - resolved.** gain of %s %% [[Smith_2020_Real]] (1 src: RCT; Low).\n")


def run(*args, cwd=None):
    return subprocess.run([sys.executable, "-I", *map(str, args)], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8")


class Wiki(unittest.TestCase):
    """A throwaway wiki with one paper and one concept note."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        write_text(self.root / "wiki.config.json", "{}")
        self.wiki = self.root / "wiki"
        write_text(self.wiki / "papers" / "Smith_2020_Real.md",
                   '---\ntype: paper\nstatus: final\nsource_verification: "fulltext, tables"\n---\n# p\n')
        self.note = self.wiki / "concepts" / "X_Concept.md"
        write_text(self.note, NOTE)

    def tearDown(self):
        self.tmp.cleanup()

    def ctx(self):
        root, cfg = load_config(self.root)
        return Context(root, cfg)


class SynthScripts(Wiki):
    def test_write_refuses_a_block_the_gate_rejects(self):
        blk = self.root / "b.md"
        write_text(blk, BLOCK % "99")  # 99 is not in the note
        r = run(SYNTH / "synth_write.py", "--vault-root", self.root, "--note", "concepts/X_Concept",
                "--block", blk, "--absorbed", "0")
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("V2", r.stdout + r.stderr)
        self.assertEqual(read_text(self.note), NOTE)

    def test_write_accepts_a_clean_block(self):
        blk = self.root / "b.md"
        write_text(blk, BLOCK % "12")
        r = run(SYNTH / "synth_write.py", "--vault-root", self.root, "--note", "concepts/X_Concept",
                "--block", blk, "--absorbed", "0")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("## State of Knowledge", read_text(self.note))

    def test_validate_rechecks_a_note_that_already_has_its_block(self):
        write_text(self.note, NOTE.replace("## Key Findings", (BLOCK % "12") + "\n## Key Findings"))
        r = run(SYNTH / "synth_validate.py", "--vault-root", self.root, "--note", "concepts/X_Concept")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("CLEAN", r.stdout)


class LintEntryPoint(unittest.TestCase):
    def test_refuses_to_run_without_a_config(self):
        with tempfile.TemporaryDirectory() as d:
            r = run(LINT, "--vault-root", d, "--out-dir", Path(d) / "out")
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("wiki.config.json", r.stdout + r.stderr)

    def test_self_test_does_not_write_into_the_current_folder(self):
        with tempfile.TemporaryDirectory() as d:
            r = run(LINT, "--self-test", cwd=d)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertFalse((Path(d) / "_temp").exists())


class Checks(Wiki):
    def test_check22_sees_a_paper_name_with_an_accent(self):
        write_text(self.wiki / "papers" / "Muñoz_2020_Hombro.md",
                   '---\ntype: paper\nstatus: final\nsource_verification: "fulltext, tables"\n---\n# p\n')
        write_text(self.note, NOTE + "- y 9 % ⚠[[Muñoz_2020_Hombro]]\n")
        out = checks_integrity.check22(self.ctx()).files["wiki_check22_stale_warn.txt"]
        self.assertEqual([r.split("|")[2] for r in out], ["Muñoz_2020_Hombro"])

    def test_check11_reads_an_aliased_or_path_prefixed_moc_link(self):
        write_text(self.root / "wiki.config.json", '{"field_titlecase_map": {"f": "F"}}')
        write_text(self.note, NOTE.replace("status: final", "status: final\nfield: f\nsubfield: sub-a"))
        index = ("# Index\n\n## Coverage by Field\n\n| Field | MOC | Concepts | Methods |\n|---|---|---|---|\n"
                 "| F | [[MOC_F]] | 1 | 0 |\n| -> Sub A | [[f/MOC_Sub_A\\|Sub A]] | 1 | 0 |\n")  # alias pipe escaped, as in any table
        write_text(self.wiki / "index.md", index)
        out = checks_structure.check11(self.ctx()).files["wiki_check11_coverage.txt"]
        self.assertEqual(out, [])


if __name__ == "__main__":
    unittest.main()
