"""What an existing wiki needs to adopt the kit: config guards, MOC and template names, nested notes, JSON counters."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from wikikit import layout, synthesis, vault  # noqa: E402
from wikikit.config import load_config  # noqa: E402
from wikikit.lint import engine  # noqa: E402
from wikikit.lint.context import Context  # noqa: E402
from wikikit.textio import write_text  # noqa: E402

SCRIPTS = ROOT / "skills"


def run(*args, cwd=None):
    return subprocess.run([sys.executable, "-I", *map(str, args)], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8")


class RefuseWithoutConfig(unittest.TestCase):
    """Without wiki.config.json the defaults point at an empty `wiki/` tree: every tool must stop with 2,
    not write into it or report it clean."""

    def test_every_entry_point_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            calls = {
                "fix": [SCRIPTS / "wiki-lint/scripts/fix.py", "--vault-root", d, "index"],
                "synth_validate": [SCRIPTS / "wiki-synthesize/scripts/synth_validate.py", "--vault-root", d, "--sweep"],
                "synth_write": [SCRIPTS / "wiki-synthesize/scripts/synth_write.py", "--vault-root", d,
                                "--note", "concepts/X", "--block", Path(d) / "b.md", "--absorbed", "0"],
                "seal": [ROOT / "tools/seal.py", Path(d) / "spec.txt", "--vault-root", d],
                "build_vocabulary": [SCRIPTS / "vocabulary-update/scripts/build_vocabulary.py", "--vault-root", d],
                "report_missing_concepts": [SCRIPTS / "wiki-ingest-book/scripts/report_missing_concepts.py",
                                            Path(d) / "Book_Ch01.md", "--vault-root", d],
                "wiki_paths": [ROOT / "tools/wiki_paths.py", "--vault-root", d, "moc", "biomechanics"],
            }
            for name, args in calls.items():
                with self.subTest(name):
                    r = run(*args)
                    self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
                    self.assertIn("wiki.config.json", r.stdout + r.stderr)
            self.assertFalse((Path(d) / "wiki").exists(), "a tool wrote into the default tree")


class MocAndTemplateNames(unittest.TestCase):
    CFG = {"field_titlecase_map": {"strength-conditioning": "Strength & Conditioning"},
           "templates_dir": "templates", "template_names": {}, "moc_names": {}}

    def cfg(self, **over):
        return dict(self.CFG, **over)

    def test_default_rules(self):
        c = self.cfg()
        self.assertEqual(layout.moc_stem(c, "strength-conditioning"), "MOC_Strength_&_Conditioning")
        self.assertEqual(layout.moc_stem(c, "applied-technology", "ml-sport"), "MOC_Ml_Sport")
        self.assertEqual(layout.moc_relpath(c, "applied-technology", "ml-sport"),
                         "fields/applied-technology/MOC_Ml_Sport.md")
        self.assertEqual(layout.moc_relpath(c, "strength-conditioning"), "fields/MOC_Strength_&_Conditioning.md")

    def test_overrides_win(self):
        c = self.cfg(moc_names={"strength-conditioning": "MOC_Strength_Conditioning",
                                "applied-technology/ml-sport": "MOC_ML_Sport"})
        self.assertEqual(layout.moc_stem(c, "strength-conditioning"), "MOC_Strength_Conditioning")
        self.assertEqual(layout.moc_stem(c, "applied-technology", "ml-sport"), "MOC_ML_Sport")
        self.assertEqual(layout.moc_stem(c, "applied-technology", "ml-healthcare"), "MOC_Ml_Healthcare")

    def test_template_path(self):
        root = Path("/v")
        c = self.cfg(vault_root="MyVault")
        self.assertEqual(layout.template_path(root, c, "concept"), root / "MyVault" / "templates" / "concept.md")
        c = self.cfg(vault_root="MyVault", templates_dir="Templates",
                     template_names={"concept": "Concept_Note_Template.md"})
        self.assertEqual(layout.template_path(root, c, "concept"),
                         root / "MyVault" / "Templates" / "Concept_Note_Template.md")
        self.assertEqual(layout.template_path(root, c, "method"), root / "MyVault" / "Templates" / "method.md")

    def test_cli_prints_the_configured_name(self):
        with tempfile.TemporaryDirectory() as d:
            write_text(Path(d) / "wiki.config.json", json.dumps(
                {"moc_names": {"applied-technology/ml-sport": "MOC_ML_Sport"}}))
            r = run(ROOT / "tools/wiki_paths.py", "--vault-root", d, "moc", "applied-technology", "ml-sport")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.strip().endswith("fields/applied-technology/MOC_ML_Sport.md"), r.stdout)


class NestedNotes(unittest.TestCase):
    """A note under a recursive folder (fields/<field>/MOC_X.md) exists: V1 must not call it invented."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        write_text(self.root / "wiki.config.json", "{}")
        self.wiki = self.root / "wiki"
        write_text(self.wiki / "fields" / "biomechanics" / "MOC_Kinetics.md", "---\ntype: sub-MOC\n---\n# k\n")
        write_text(self.wiki / "papers" / "Smith_2020_Real.md",
                   '---\ntype: paper\nstatus: final\nsource_verification: "fulltext"\n---\n# p\n')

    def tearDown(self):
        self.tmp.cleanup()

    def test_find_note_descends_only_into_recursive_folders(self):
        self.assertIsNone(vault.find_note(self.wiki, ["fields"], "MOC_Kinetics"))
        self.assertEqual(vault.find_note(self.wiki, ["fields"], "MOC_Kinetics", recursive=["fields"]),
                         self.wiki / "fields" / "biomechanics" / "MOC_Kinetics.md")

    def test_v1_accepts_a_link_to_a_nested_note(self):
        root, cfg = load_config(self.root)
        note = ("---\ntype: concept\nstatus: final\n---\n# T\n## Definition\nd\n"
                "## Key Findings\n- gain [[Smith_2020_Real]]\n")
        block = ("## State of Knowledge\n\n> [!abstract] Synthesis · updated 2026-11-18\n"
                 "> - ✅ **Q - resolved.** gain [[Smith_2020_Real]], see [[MOC_Kinetics]] (1 src: RCT; Low).\n")
        r = synthesis.validate(note, block, self.wiki, cfg, {"Smith_2020_Real"})
        self.assertEqual(r["v1_bad"], [])
        r = synthesis.validate(note, block.replace("MOC_Kinetics", "MOC_Invented"), self.wiki, cfg,
                               {"Smith_2020_Real"})
        self.assertEqual(r["v1_bad"], ["MOC_Invented"])  # the guard still bites


class JsonCounters(unittest.TestCase):
    def test_json_matches_the_counters_of_a_run(self):
        vault_dir = ROOT / "tests" / "fixtures" / "lint" / "vault"
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "counters.json"
            r = run(SCRIPTS / "wiki-lint/scripts/lint.py", "--vault-root", vault_dir, "--out-dir", Path(d) / "lists",
                    "--json", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            got = json.loads(out.read_text(encoding="utf-8"))
            root, cfg = load_config(vault_dir)
            want = engine.run(Context(root, cfg), out_dir=Path(d) / "lists2", quiet=True)
        self.assertEqual(got, want)
        self.assertTrue(any(v > 0 for v in got.values()), "a fixture run with no hit cannot prove the parser")


if __name__ == "__main__":
    unittest.main()
