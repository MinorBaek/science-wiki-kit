"""Regressions from the 2026-11 audit: script entry points and lint checks on small synthetic wikis."""
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from wikikit.config import load_config  # noqa: E402
from wikikit import synthesis  # noqa: E402
from wikikit.lint import checks_content, checks_integrity, checks_structure  # noqa: E402
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

    def test_replace_writes_a_clean_block_and_refuses_a_dirty_one(self):
        with_block = NOTE.replace("## Key Findings", (BLOCK % "12") + "\n## Key Findings")
        write_text(self.note, with_block)
        blk = self.root / "b.md"
        write_text(blk, (BLOCK % "99").replace("2026-11-17", "2026-11-18"))  # 99 is not in the note
        args = (SYNTH / "synth_write.py", "--vault-root", self.root, "--note", "concepts/X_Concept",
                "--block", blk, "--replace")
        r = run(*args)
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("V2", r.stdout + r.stderr)
        self.assertEqual(read_text(self.note), with_block)
        write_text(blk, (BLOCK % "12").replace("2026-11-17", "2026-11-18").replace("resolved", "settled"))
        r = run(*args, "--dry-run")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("+> - ✅ **Q - settled.**", r.stdout)
        self.assertEqual(read_text(self.note), with_block)
        r = run(*args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("updated 2026-11-18", read_text(self.note))
        self.assertEqual(read_text(self.note).count("## State of Knowledge"), 1)

    def test_replace_refuses_a_note_without_a_block(self):
        blk = self.root / "b.md"
        write_text(blk, BLOCK % "12")
        r = run(SYNTH / "synth_write.py", "--vault-root", self.root, "--note", "concepts/X_Concept",
                "--block", blk, "--replace")
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("no `## State of Knowledge` block", r.stdout + r.stderr)
        self.assertEqual(read_text(self.note), NOTE)

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


class SetKitDir(unittest.TestCase):
    def test_accepts_a_config_saved_with_a_bom(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "wiki.config.json"
            cfg.write_bytes(b'\xef\xbb\xbf{\n  "wiki_root": "wiki"\n}\n')  # Windows PowerShell 5.1 Set-Content
            r = run(ROOT / "tools" / "set_kit_dir.py", cfg, d)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn('"kit_dir"', read_text(cfg))
            self.assertIn('"wiki_root": "wiki"', read_text(cfg))


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


class AdoptionAuditFixes(Wiki):
    """Defects found while migrating a large existing wiki onto the kit (2026-11-18)."""

    def test_es_example_guards_con_next_to_ecc(self):
        # "knee ext con 2.68 / ecc 3.92": concentric/eccentric abbreviations, not the Spanish preposition
        lint = json.loads(read_text(ROOT / "examples" / "languages" / "es.json"))["lint"]
        write_text(self.root / "wiki.config.json", json.dumps({"lint": lint}))
        write_text(self.note, NOTE + "".join("- knee ext con 2.%d / ecc 3.9 Nm/kg\n" % i for i in range(10)))
        self.assertEqual(checks_content.check14(self.ctx()).counters["check14"], 0)
        write_text(self.note, NOTE + "".join("- knee ext con 2.%d Nm/kg\n" % i for i in range(10)))
        self.assertEqual(checks_content.check14(self.ctx()).counters["check14"], 1)  # the radar still bites

    def test_spanish_heading_lists_hold_no_english_heading(self):
        english = {"methods", "results", "discussion", "introduction", "references", "summary"}
        for path in (ROOT / "examples" / "languages" / "es.json",
                     ROOT / "tests" / "fixtures" / "lint" / "vault" / "wiki.config.json"):
            with self.subTest(path.name):
                headings = set(json.loads(read_text(path))["lint"]["language_radar"]["headings"])
                self.assertEqual(headings & english, set())

    def test_confidence_levels_agree_across_the_docs(self):
        def labels(path, marker):
            line = next(ln for ln in read_text(path).splitlines() if marker in ln)
            return [x for x in re.findall(r"`([^`]+)`", line) if re.match(r"(High|Moderate|Low)\b", x)]
        schema = labels(ROOT / "docs" / "WIKI_SCHEMA.md", "**Confidence**")
        workflow = labels(ROOT / "skills" / "wiki-synthesize" / "references" / "SYNTHESIS-WORKFLOW.md",
                          "**Confidence:**")
        self.assertEqual(schema, workflow)
        self.assertEqual(len(workflow), 5)

    def test_a_seal_starting_with_abstract_is_below_fulltext(self):
        # Check 17 already treats any value starting with "abstract" as no seal; Check 21 and V4 must agree.
        self.assertTrue(synthesis.below_fulltext("abstract only (no PDF found)"))
        self.assertTrue(synthesis.below_fulltext("abstract"))
        self.assertFalse(synthesis.below_fulltext("[2026-11-18, T, X] Checked against PDF: abstract and tables"))
        write_text(self.root / "wiki.config.json", '{"synthesis": {"prefulltext_cutoff": "2026-06-01"}}')
        write_text(self.wiki / "papers" / "Old_2001_Abs.md", '---\ntype: paper\nstatus: read\ndate: 2026-01-10\n'
                   'source_verification: "abstract only (no PDF found)"\n---\n# p\n')
        out = checks_content.check21(self.ctx()).files["wiki_check21_prefulltext_cohort.txt"]
        self.assertEqual(out, ["Old_2001_Abs"])


if __name__ == "__main__":
    unittest.main()
