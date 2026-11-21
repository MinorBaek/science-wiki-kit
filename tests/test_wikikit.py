"""Unit tests for wikikit (standard library only). Run: python -m unittest discover -s tests -v"""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from wikikit import frontmatter, sections, seals, synthesis, vault  # noqa: E402
from wikikit.config import DEFAULTS  # noqa: E402
from wikikit.textio import read_text, write_text  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "synth"


def cfg_with_cutoff(cutoff="2026-06-01"):
    cfg = copy.deepcopy(DEFAULTS)
    cfg["synthesis"]["prefulltext_cutoff"] = cutoff
    return cfg


class FrontmatterTests(unittest.TestCase):
    def test_parse_inline_and_block_lists(self):
        fm, body = frontmatter.parse("---\naliases: [a, \"b c\"]\ntags:\n  - x\n  - y\nstatus: final\n---\nBody\n")
        self.assertEqual(fm["aliases"], ["a", "b c"])
        self.assertEqual(fm["tags"], ["x", "y"])
        self.assertEqual(fm["status"], "final")
        self.assertEqual(body, "Body\n")

    def test_set_key_is_eol_safe(self):
        for eol in ("\n", "\r\n"):
            t = eol.join(["---", "status: draft", "---", "body"])
            t2 = frontmatter.set_key(t, "last_verified", "2026-11-06")
            # one line was added: 4 line breaks, all of them the file's own EOL
            self.assertEqual(t2.count("\r\n") if eol == "\r\n" else t2.count("\r"), 4 if eol == "\r\n" else 0)
            self.assertEqual(t2.count("\n"), 4)
            self.assertIn("last_verified: 2026-11-06", t2)
            t3 = frontmatter.set_key(t2, "status", "final")
            self.assertEqual(frontmatter.parse(t3)[0]["status"], "final")

    def test_set_key_refuses_without_frontmatter(self):
        with self.assertRaises(ValueError):
            frontmatter.set_key("no frontmatter", "a", "b")


class SectionTests(unittest.TestCase):
    TEXT = "# T\n## A\na1\n## B\nb1\nb2\n## C\nc1"

    def test_get_and_remove(self):
        self.assertEqual(sections.get_section(self.TEXT, "B"), "b1\nb2")
        self.assertNotIn("b1", sections.remove_section(self.TEXT, "B"))
        self.assertIn("c1", sections.remove_section(self.TEXT, "B"))


class NumberTests(unittest.TestCase):
    def test_metadata_is_not_a_number(self):
        block = "> [!abstract] Synthesis · updated 2026-07-16\n> - ✅ **Q** X by 12% [[Smith_2020_SR]] (3+ src: SR; High)."
        self.assertEqual(synthesis.numbers(block, is_block=True), ["12"])

    def test_thousands_separator_but_not_decimal_comma(self):
        self.assertEqual(synthesis.numbers("n = 2,085 and r = 1,44"), ["2085", "1.44"])

    def test_year_in_citation_position_only_on_block_side(self):
        self.assertEqual(synthesis.numbers("Burkhart et al. 2003 found 5", is_block=True), ["5"])
        self.assertEqual(synthesis.numbers("from 2016 to 2019", is_block=True), ["2016", "2019"])
        self.assertIn("2003", synthesis.numbers("Burkhart et al. 2003 found 5"))

    def test_a_capitalised_word_before_a_number_is_not_a_citation(self):
        # A sentence-initial word is not a surname: these figures must reach V2.
        for text, n in (("Overall 2012 athletes improved", "2012"), ("Pooled 1984 players", "1984"),
                        ("From 2016 to 2019, incidence rose", "2016")):
            with self.subTest(text):
                self.assertIn(n, synthesis.numbers(text, is_block=True))
        # Still citations: citation punctuation follows, or the block links a work of that year.
        for text in ("(Smith et al., 2020)", "Smith and Jones 2019;", "though Aruga (2006) found",
                     "Smith 2020 reported it [[Smith_2020_Real]]"):
            with self.subTest(text):
                self.assertNotIn("2020", synthesis.numbers(text, is_block=True))
                self.assertNotIn("2019", synthesis.numbers(text, is_block=True))
                self.assertNotIn("2006", synthesis.numbers(text, is_block=True))


class GateTests(unittest.TestCase):
    EXPECT = {"note_clean": "CLEAN", "note_fab_source": "ESCALATE", "note_fab_number": "ESCALATE",
              "note_dropped_contr": "ESCALATE", "note_missing_warn": "ESCALATE"}

    def test_fixtures(self):
        cfg = cfg_with_cutoff()
        sources = synthesis.source_stems(FIX, cfg)
        for name, want in self.EXPECT.items():
            with self.subTest(note=name):
                text = read_text(FIX / (name + ".md"))
                block = sections.get_section(text, "State of Knowledge")
                got = synthesis.validate(text, block, FIX, cfg, sources)
                self.assertEqual(got["RESULT"], want, got)

    def test_v1_flags_a_cited_work_that_has_no_note_anywhere(self):
        cfg = cfg_with_cutoff()
        text = read_text(FIX / "note_clean.md")
        block = sections.get_section(text, "State of Knowledge")
        block = block.replace("]]", "]] [[Invented_2021_Study]]", 1)
        got = synthesis.validate(text, block, FIX, cfg, synthesis.source_stems(FIX, cfg))
        self.assertEqual(got["V1"], "FAIL", got)
        self.assertIn("Invented_2021_Study", got["v1_bad"])

    def test_without_cutoff_only_weak_seals_are_prefulltext(self):
        cfg = cfg_with_cutoff(None)
        self.assertFalse(synthesis.is_prefulltext("Pre_2026_CT", FIX, cfg))

    def test_seal_levels(self):
        self.assertTrue(synthesis.below_fulltext("abstract"))
        self.assertTrue(synthesis.below_fulltext("verified at abstract-level only"))
        self.assertFalse(synthesis.below_fulltext("abstract-level. UPGRADED TO FULLTEXT 2026-08-01"))
        self.assertFalse(synthesis.below_fulltext("fulltext, tables checked"))


class InsertBlockTests(unittest.TestCase):
    NOTE = "---\ntype: concept\nstatus: final\n---\n# T\n## Definition\nd\n## Key Findings\n- x 5 [[P_2020_A]]\n## Controversies or Gaps\n- gap [[P_2020_A]]\n- gap2\n"
    BLOCK = "## State of Knowledge\n\n> [!abstract] Synthesis · updated 2026-11-06\n> - ✅ **Q**: x 5 [[P_2020_A]] (1 src: RCT; Low).\n"

    def test_insert_and_retitle(self):
        out, rep = synthesis.insert_block(self.NOTE, self.BLOCK, absorbed=2, today="2026-11-06")
        self.assertLess(out.index("## State of Knowledge"), out.index("## Key Findings"))
        self.assertIn("## Open Questions and Caveats", out)
        self.assertNotIn("## Controversies or Gaps", out)
        self.assertIn("- gap2", out)  # nothing lost
        self.assertIn("last_verified: 2026-11-06", out)

    def test_refuses_wrong_absorbed_count_and_existing_block(self):
        with self.assertRaises(synthesis.SynthError):
            synthesis.insert_block(self.NOTE, self.BLOCK, absorbed=1)
        out, _ = synthesis.insert_block(self.NOTE, self.BLOCK, absorbed=2)
        with self.assertRaises(synthesis.SynthError):
            synthesis.insert_block(out, self.BLOCK, absorbed=0)

    def test_controversies_above_the_anchor_is_retitled_without_losing_a_line(self):
        note = ("---\nstatus: final\n---\n# T\n## Controversies or Gaps\n- gap one\n"
                "## Definition\nDEF LINE\n## Key Findings\n- KEEP 5 [[P_2020_A]]\n")
        out, _ = synthesis.insert_block(note, self.BLOCK, absorbed=1, today="2026-11-06")
        self.assertIn("DEF LINE", out)  # the offset used to overwrite this line with the new heading
        self.assertIn("- gap one", out)
        self.assertNotIn("## Controversies or Gaps", out)
        self.assertEqual(out.count("## Open Questions and Caveats"), 1)

    def test_crlf_preserved(self):
        crlf = self.NOTE.replace("\n", "\r\n")
        out, rep = synthesis.insert_block(crlf, self.BLOCK, absorbed=2)
        self.assertEqual(rep["eol"], "CRLF")
        self.assertEqual(out.count("\n"), out.count("\r\n"))


class ReplaceBlockTests(unittest.TestCase):
    NOTE = InsertBlockTests.NOTE
    BLOCK = InsertBlockTests.BLOCK
    NEW = BLOCK.replace("2026-11-06", "2026-11-18").replace("**Q**", "**Q, revised**")

    def written(self, eol="\n"):
        out, _ = synthesis.insert_block(self.NOTE, self.BLOCK, absorbed=2, today="2026-11-06")
        return out.replace("\n", eol)

    def test_only_block_lines_change_and_crlf_is_kept(self):
        before = self.written("\r\n")
        out, rep = synthesis.replace_block(before, self.NEW)
        self.assertEqual(rep["eol"], "CRLF")
        self.assertEqual(out.count("\n"), out.count("\r\n"))
        b, a = before.split("\r\n"), out.split("\r\n")
        self.assertEqual(len(b), len(a))  # same block length here, so a line-by-line comparison is exact
        changed = [i for i, (x, y) in enumerate(zip(b, a)) if x != y]
        s = b.index("## State of Knowledge")
        self.assertTrue(changed and all(s < i < s + len(rep["old"]) for i in changed), changed)
        self.assertIn("**Q, revised**", out)
        self.assertEqual((rep["old_date"], rep["new_date"]), ("2026-11-06", "2026-11-18"))

    def test_refuses_a_note_without_a_block(self):
        with self.assertRaises(synthesis.SynthError):
            synthesis.replace_block(self.NOTE, self.NEW)

    def test_refuses_an_earlier_updated_date(self):
        with self.assertRaises(synthesis.SynthError):
            synthesis.replace_block(self.written(), self.BLOCK.replace("2026-11-06", "2026-11-01"))

    def test_refuses_a_block_without_its_heading(self):
        with self.assertRaises(synthesis.SynthError):
            synthesis.replace_block(self.written(), self.NEW.split("\n", 1)[1])


class SealTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.wiki = Path(self.tmp.name)
        (self.wiki / "papers").mkdir()
        self.cfg = copy.deepcopy(DEFAULTS)
        self.ficha = self.wiki / "papers" / "P_2020_A.md"
        write_text(self.ficha, '---\nstatus: final\nsource_verification: "fulltext"\n---\nbody\n')

    def tearDown(self):
        self.tmp.cleanup()

    def test_append_is_idempotent_in_shape_and_sets_last_verified(self):
        seals.append_seals(self.wiki, self.cfg, [("Example_Concept", "P_2020_A", seals.CLEAN_TEXT)],
                           "2026-11-06", "synth Example_Concept")
        t = read_text(self.ficha)
        self.assertIn("[2026-11-06, synth Example_Concept, Example_Concept] Checked against PDF:", t)
        self.assertIn("last_verified: 2026-11-06", t)
        sv = frontmatter.get_raw(t, "source_verification")
        self.assertTrue(seals.names_note(sv, "Example_Concept"))
        self.assertFalse(seals.names_note(sv, "Other_Note"))

    def test_plain_scalar_is_quoted_and_block_scalar_refused(self):
        write_text(self.ficha, "---\nstatus: final\nsource_verification: fulltext\n---\nbody\n")
        seals.append_seals(self.wiki, self.cfg, [("N_One", "P_2020_A", seals.CLEAN_TEXT)], "2026-11-06", "t")
        sv = frontmatter.get_raw(read_text(self.ficha), "source_verification")
        self.assertTrue(sv.startswith('"fulltext [2026-11-06, t, N_One]') and sv.endswith('"'))
        write_text(self.ficha, "---\nstatus: final\nsource_verification: |\n  multi\n---\nbody\n")
        with self.assertRaises(seals.SealError):
            seals.append_seals(self.wiki, self.cfg, [("N_One", "P_2020_A", seals.CLEAN_TEXT)], "2026-11-06", "t")

    def test_block_list_is_refused_and_the_file_untouched(self):
        listed = "---\nstatus: final\nsource_verification:\n  - fulltext\n  - tables\n---\nbody\n"
        write_text(self.ficha, listed)
        with self.assertRaises(seals.SealError):
            seals.append_seals(self.wiki, self.cfg, [("N_One", "P_2020_A", seals.CLEAN_TEXT)], "2026-11-06", "t")
        self.assertEqual(read_text(self.ficha), listed)

    def test_aborts_without_writing(self):
        before = read_text(self.ficha)
        with self.assertRaises(seals.SealError):
            seals.append_seals(self.wiki, self.cfg,
                               [("N", "P_2020_A", "ok"), ("N", "Missing_2020_X", "ok")], "2026-11-06", "t")
        self.assertEqual(read_text(self.ficha), before)
        with self.assertRaises(seals.SealError):
            seals.append_seals(self.wiki, self.cfg, [("N", "P_2020_A", 'has "quote"')], "2026-11-06", "t")

    def test_source_label_changes_the_wording_and_is_validated(self):
        seals.append_seals(self.wiki, self.cfg, [("N_One", "P_2020_A", seals.CLEAN_TEXT)], "2026-11-06", "t",
                           source="publisher XML")
        t = read_text(self.ficha)
        self.assertIn("[2026-11-06, t, N_One] Checked against publisher XML:", t)
        self.assertNotIn("Checked against PDF", t)
        self.assertTrue(seals.names_note(frontmatter.get_raw(t, "source_verification"), "N_One"))  # still a seal
        before = read_text(self.ficha)
        for bad in ('a"b', "x]y", "", "z" * 41):
            with self.assertRaises(seals.SealError):
                seals.append_seals(self.wiki, self.cfg, [("N_Two", "P_2020_A", seals.CLEAN_TEXT)], "2026-11-06", "t",
                                   source=bad)
        self.assertEqual(read_text(self.ficha), before)

    def test_single_word_note_only_counts_in_header(self):
        self.assertFalse(seals.names_note("a paper about Detraining effects", "Detraining"))
        self.assertTrue(seals.names_note("[2026-01-01, tag, Detraining] Checked", "Detraining"))

    def test_spanish_seal_still_detected(self):
        sv = "[2026-10-05, regla P retroactiva, tanda C1, Subgroup_Analysis] Contra el PDF: CLEAN"
        self.assertTrue(seals.names_note(sv, "Subgroup_Analysis"))

    def test_evaluate_pairs(self):
        notes = {"N_One": ["P_2020_A"], "N_Two": ["P_2020_A"]}
        fichas = {"P_2020_A": "[2026-11-06, t, N_One] Checked against PDF: ok"}
        r = seals.evaluate(notes, fichas, debt={("N_Two", "P_2020_A"): "declared"})
        self.assertEqual((len(r["sealed"]), len(r["debt"]), len(r["unsealed"])), (1, 1, 0))
        r2 = seals.evaluate(notes, fichas)
        self.assertEqual(r2["unsealed"], [("N_Two", "P_2020_A")])


class VaultTests(unittest.TestCase):
    def test_links_strip_alias_anchor_and_path(self):
        self.assertEqual(vault.links("[[A|x]] [[B#s]] [[dir/C]] [[A]]"), ["A", "B", "C"])


if __name__ == "__main__":
    unittest.main()
