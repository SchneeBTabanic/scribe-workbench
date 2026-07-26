#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Phase 1 tests for the Scribe's Workbench. stdlib unittest only.
#
# Each test maps to a Phase-1 gate requirement from the brief / GATE 0 rulings.

import shutil
import unittest

import scribe


class TestPileFormat(unittest.TestCase):
    def test_roundtrip_stable(self):
        """parse(serialize(blocks)) == blocks — the format holds (§4.3)."""
        pile = (
            "@@ #a1 2026-03-22T19:30 @topic:nas @topic:zfs @source:gemini\n"
            "ZFS vs. ext4: Why Bother?\n"
            "Checksumming, snapshots, RAM hungry.\n\n"
            "@@ #b2 2026-03-22T19:31 @topic:git @topic:rsync @source:self\n"
            "git reset --hard origin/master\n"
        )
        blocks = scribe.parse_pile(pile)
        re_ser = scribe.serialize_pile(blocks)
        re_parsed = scribe.parse_pile(re_ser)
        self.assertEqual(len(blocks), 2)
        self.assertEqual([(b.id, b.ts, b.tags, b.body) for b in blocks],
                         [(b.id, b.ts, b.tags, b.body) for b in re_parsed])
        # EVERY block's body must survive — not just the last. (A symmetric parse bug
        # can pass an equality round-trip while silently dropping earlier bodies, so
        # assert the actual content of the FIRST block explicitly.)
        self.assertIn("ZFS vs. ext4", blocks[0].body)
        self.assertIn("git reset --hard", blocks[1].body)
        self.assertTrue(all(b.body.strip() for b in blocks))

    def test_preamble_preserved(self):
        """Text before the first @@ (a human preamble) survives a round trip —
        nothing in the file is discarded (tool-off-readable invariant)."""
        pile = "# my notes header\nremember to tag things\n\n@@ #a1 2026-03-22T19:30 @topic:x @source:self\nbody\n"
        blocks = scribe.parse_pile(pile)
        self.assertEqual(blocks[0].id, "")
        self.assertIn("my notes header", blocks[0].body)
        self.assertEqual(blocks[1].id, "a1")

    def test_parser_accepts_both_tag_forms(self):
        """Repeated-key (ruled default) AND comma-list both parse identically —
        the readability ruling is never foreclosed (§5.5)."""
        rep = scribe.parse_pile("@@ #a 2026-01-01T00:00 @topic:nas @topic:zfs @source:s\nb\n")[0]
        com = scribe.parse_pile("@@ #a 2026-01-01T00:00 @topic:nas,zfs @source:s\nb\n")[0]
        self.assertEqual(rep.topics(), ["nas", "zfs"])
        self.assertEqual(com.topics(), ["nas", "zfs"])

    def test_emits_repeated_form_by_default(self):
        b = scribe.Block(id="a", ts="2026-01-01T00:00",
                         tags=[("topic", "nas"), ("topic", "zfs"), ("source", "s")], body="x")
        self.assertIn("@topic:nas @topic:zfs", scribe.serialize_block(b))
        self.assertIn("@topic:nas,zfs", scribe.serialize_block(b, tag_form="comma"))

    def test_pile_readable_with_tool_off(self):
        """A captured block, read raw, shows tags as ordinary lines and the body
        verbatim — no tool required to read it (Poverty invariant 1 / Candidate 2)."""
        block, _ = scribe.make_block("hello world\nsecond line",
                                     [("topic", "greeting"), ("source", "self")],
                                     "self", ts="2026-01-01T00:00")
        text = scribe.serialize_block(block)
        self.assertTrue(text.startswith("@@ #"))
        self.assertIn("@topic:greeting", text)
        self.assertIn("hello world", text)     # body verbatim, unaltered
        self.assertIn("second line", text)


class TestCaptureDoesNotAlter(unittest.TestCase):
    def test_plaintext_verbatim(self):
        """Plain-text capture never silently alters the sovereign's text (§3.1/§3.3)."""
        src = "emoji ✅ stays, and so does 🧠 and my prose."
        self.assertEqual(scribe.capture_plaintext(src), src)

    def test_capture_does_not_self_certify(self):
        """The reducer produces raw text; the SEPARATE auditor adds markers
        (Candidate 5). capture_plaintext must not itself insert loss markers."""
        flattened = "def f(x):\n    return x + 1\n    y = x * 2;"
        self.assertNotIn(scribe.LOSS_PREFIX, scribe.capture_plaintext(flattened))


class TestLossAuditor(unittest.TestCase):
    def test_flattened_code_marked_not_fixed(self):
        """Loss-marking FIRES on clearly-flattened code, MARKS in-band, and does not
        fabricate fences (§3.8, Candidate 4)."""
        body = ("Here is the grammar:\n"
                "root ::= executor proxy\n"
                "executor ::= line body\n"
                "line ::= chars\n"
                "That was the grammar.")
        annotated, findings = scribe.loss_check(body)
        self.assertTrue(any(f.kind == "flattened-code" for f in findings))
        self.assertIn(scribe.LOSS_PREFIX, annotated)
        self.assertIn("root ::= executor proxy", annotated)   # content untouched
        self.assertNotIn("```", annotated)                    # no fabricated fence

    def test_broken_math_flagged_loud_not_silent(self):
        """An UNCLOSED display-math delimiter is named, never emitted silently (§3.6).
        (We deliberately do NOT guess on single '$' — too ambiguous with shell/prices.)"""
        body = "Display: $$E = mc^2 and then prose with no closing delimiter"
        _, findings = scribe.loss_check(body)
        self.assertTrue(any(f.kind == "broken-math" for f in findings))

    def test_shell_dollar_is_not_math(self):
        """The probe's false-positive trap: `$(nproc)` is shell, not LaTeX; and a bare
        single '$' must never be guessed as broken math."""
        for body in ("Build it: make -j$(nproc) vessel_engine",
                     "It costs $5 to run.",
                     "The var is $E and the path is $HOME."):
            _, findings = scribe.loss_check(body)
            self.assertFalse(any(f.kind == "broken-math" for f in findings), body)

    def test_clean_prose_not_over_marked(self):
        """Ordinary prose (no lost structure) yields no markers — the auditor is
        conservative, it does not decide the sovereign's prose is broken (§3.1)."""
        body = ("ZFS calculates a fingerprint for every block. If a bit flips on the "
                "disk, ZFS detects it. Snapshots let you roll back in seconds.")
        _, findings = scribe.loss_check(body)
        self.assertEqual(findings, [])


@unittest.skipUnless(shutil.which("pandoc"), "pandoc not on PATH")
class TestHtmlCapture(unittest.TestCase):
    MATHML = (
        "<html><head><style>.katex{color:red}</style>"
        "<script>track()</script></head><body>"
        "<p>Einstein said "
        "<math><semantics>"
        "<mrow><mi>E</mi><mo>=</mo><mi>m</mi><msup><mi>c</mi><mn>2</mn></msup></mrow>"
        "<annotation encoding=\"application/x-tex\">E = mc^2</annotation>"
        "</semantics></math>.</p>"
        "<pre><code class=\"language-python\">def f(x):\n    return x</code></pre>"
        "</body></html>"
    )

    def test_annotation_extractor(self):
        tex = scribe.extract_tex_annotations(self.MATHML)
        self.assertEqual(tex, ["E = mc^2"])

    def test_math_roundtrip_and_fluff_removed(self):
        """rendered chat LaTeX -> recovered canonical; CSS/JS fluff stripped;
        code fences preserved (the whole point of the HTML path)."""
        body, annotations = scribe.capture_html(self.MATHML)
        self.assertEqual(annotations, ["E = mc^2"])
        # fluff gone
        self.assertNotIn("track()", body)
        self.assertNotIn("color:red", body)
        # math recovered as canonical LaTeX (pandoc normalizes mc^2 -> mc^{2}; both are
        # the same math — the auditor's normalized check is the real proof it survived)
        self.assertIn("$", body)
        self.assertIn("mc", body)
        # code structure survived (pandoc keeps the <pre><code> as a fence)
        self.assertIn("def f(x)", body)
        # auditor confirms the annotation survived -> no math-not-recovered finding
        _, findings = scribe.loss_check(body, annotations=annotations)
        self.assertFalse(any(f.kind == "math-not-recovered" for f in findings))

    def test_math_not_recovered_is_named(self):
        """If a MathML annotation's LaTeX does NOT survive into the body, the auditor
        names the loss rather than hiding it (§3.8)."""
        body = "some text with no math at all"
        _, findings = scribe.loss_check(body, annotations=["E = mc^2"])
        self.assertTrue(any(f.kind == "math-not-recovered" for f in findings))


class TestIdStability(unittest.TestCase):
    def test_id_deterministic(self):
        a = scribe.gen_id("2026-01-01T00:00", "same body", "self")
        b = scribe.gen_id("2026-01-01T00:00", "same body", "self")
        self.assertEqual(a, b)

    def test_id_collision_extends(self):
        first = scribe.gen_id("2026-01-01T00:00", "body", "self")
        second = scribe.gen_id("2026-01-01T00:00", "body", "self", taken={first})
        self.assertNotEqual(first, second)
        self.assertTrue(second.startswith(first))


PILE = (
    "@@ #n1 2026-03-22T09:00 @topic:nas @topic:zfs @state:live @source:gemini\n"
    "ZFS vs. ext4: Why Bother? Checksumming detects bitrot.\n\n"
    "@@ #n2 2026-03-22T10:00 @topic:nas @topic:backup @source:gemini\n"
    "How Backup and Access Work: push vs pull.\n\n"
    "@@ #g1 2026-03-22T11:00 @topic:git @topic:rsync @state:live @source:self\n"
    "git reset --hard then rsync to deploy.\n\n"
    "@@ #m1 2026-03-22T08:00 @topic:markdown @source:chatgpt\n"
    "Markdown is the lingua franca for AI agents.\n"
)


class TestViews(unittest.TestCase):
    def setUp(self):
        self.blocks = scribe.parse_pile(PILE)

    def test_multi_tag_appears_in_both_views_unduplicated_unmoved(self):
        """The core Problem-B resolution: a block with two topics appears in BOTH
        topic views, once each, and the pile is not mutated (§4.3)."""
        nas = scribe.select_blocks(self.blocks, "topic", "nas")
        zfs = scribe.select_blocks(self.blocks, "topic", "zfs")
        self.assertEqual([b.id for b in nas], ["n1", "n2"])
        self.assertEqual([b.id for b in zfs], ["n1"])          # n1 in both, once each
        self.assertEqual(nas.count(self.blocks[0]), 1)         # not duplicated
        # pile bytes unchanged by deriving views (views are read-only wrt the pile)
        self.assertEqual(scribe.serialize_pile(self.blocks),
                         scribe.serialize_pile(scribe.parse_pile(PILE)))

    def test_view_carries_backlink_id(self):
        text, chosen = scribe.render_view(self.blocks, "topic", "nas")
        self.assertIn("@@ #n1", text)   # the back-link the pushback keys on
        self.assertIn("@@ #n2", text)

    def test_salience_view_recent_first(self):
        """state:live view surfaces the live blocks, most-recent first."""
        _, chosen = scribe.render_view(self.blocks, "state", "live", recent=True)
        self.assertEqual([b.id for b in chosen], ["g1", "n1"])   # 11:00 before 09:00

    def test_toc_matches_pile(self):
        toc = scribe.render_toc(self.blocks)
        # nas has 2 blocks; counts must match the pile exactly
        self.assertIn("## nas (2)", toc)
        self.assertIn("## git (1)", toc)
        self.assertIn("#n1", toc)
        self.assertIn("ZFS vs. ext4", toc)      # derived title
        # topic count line reflects reality
        self.assertIn("4 blocks", toc)

    def test_export_bare_has_no_headers_or_manifest(self):
        text, _ = scribe.render_export(self.blocks, "topic", "nas", bare=True)
        self.assertNotIn("@@ #", text)          # clean for pasting onward
        self.assertNotIn("scribe export", text)
        self.assertIn("ZFS vs. ext4", text)

    def test_export_default_has_unobtrusive_manifest(self):
        text, _ = scribe.render_export(self.blocks, "topic", "nas")
        self.assertNotIn("@@ #", text)
        self.assertIn("#n1", text)              # back-link survives, out of the way
        self.assertIn("<!-- scribe export", text)


class TestPushHome(unittest.TestCase):
    def test_edit_in_view_lands_in_right_block(self):
        """A thought developed in a view is pushed home to the right canonical block
        by id; other blocks are untouched (the detangle round-trip)."""
        blocks = scribe.parse_pile(PILE)
        view_text, _ = scribe.render_view(blocks, "topic", "nas")
        # edit n1's body inside the view
        edited = view_text.replace("Checksumming detects bitrot.",
                                   "Checksumming detects bitrot. ADDED IN VIEW.")
        blocks, report = scribe.push_view(edited, blocks)
        by_id = {b.id: b for b in blocks}
        self.assertIn("n1", report["updated"])
        self.assertIn("ADDED IN VIEW", by_id["n1"].body)
        self.assertNotIn("ADDED IN VIEW", by_id["g1"].body)     # others untouched
        self.assertEqual(report["missing"], [])

    def test_push_updates_body_only_discloses_tag_drift(self):
        """Push applies BODY only; a header-tag change in the view is disclosed, not
        silently applied (§3.7)."""
        blocks = scribe.parse_pile(PILE)
        view = ("@@ #n1 2026-03-22T09:00 @topic:nas @topic:zfs @topic:NEWTAG @source:gemini\n"
                "new body text\n")
        blocks, report = scribe.push_view(view, blocks)
        by_id = {b.id: b for b in blocks}
        self.assertEqual(by_id["n1"].body, "new body text")     # body applied
        self.assertNotIn(("topic", "NEWTAG"), by_id["n1"].tags)  # tag NOT applied
        self.assertIn("n1", report["tag_drift"])                 # but disclosed

    def test_push_missing_id_is_named(self):
        blocks = scribe.parse_pile(PILE)
        view = "@@ #zzzz 2026-01-01T00:00 @topic:x @source:s\nghost\n"
        blocks, report = scribe.push_view(view, blocks)
        self.assertEqual(report["missing"], ["zzzz"])


class TestTagging(unittest.TestCase):
    def test_add_tag_makes_block_appear_in_view(self):
        blocks = scribe.parse_pile(PILE)
        ok, b = scribe.add_tags(blocks, "m1", add=[("topic", "ai")])
        self.assertTrue(ok)
        self.assertIn("m1", [x.id for x in scribe.select_blocks(blocks, "topic", "ai")])

    def test_remove_tag(self):
        blocks = scribe.parse_pile(PILE)
        scribe.add_tags(blocks, "n1", remove=["state:live"])
        self.assertEqual(scribe.select_blocks(blocks, "state", "live"),
                         [b for b in blocks if b.id == "g1"])

    def test_add_tag_is_idempotent(self):
        blocks = scribe.parse_pile(PILE)
        scribe.add_tags(blocks, "n1", add=[("topic", "nas")])   # already present
        n1 = [b for b in blocks if b.id == "n1"][0]
        self.assertEqual(n1.topics().count("nas"), 1)


class TestAtomicWrite(unittest.TestCase):
    def test_atomic_write_content_and_no_tmp_left(self):
        import glob
        import os
        import tempfile
        d = tempfile.mkdtemp()
        path = os.path.join(d, "my.pile")
        scribe._atomic_write(path, "hello pile\n")
        with open(path) as fh:
            self.assertEqual(fh.read(), "hello pile\n")
        # no stray temp files left behind
        self.assertEqual(glob.glob(os.path.join(d, ".scribe-*.tmp")), [])

    def test_atomic_write_overwrites_existing(self):
        import os
        import tempfile
        d = tempfile.mkdtemp()
        path = os.path.join(d, "my.pile")
        scribe._atomic_write(path, "v1\n")
        scribe._atomic_write(path, "v2\n")
        with open(path) as fh:
            self.assertEqual(fh.read(), "v2\n")


class TestDoctorDisclosure(unittest.TestCase):
    def test_doctor_reports_sha_and_python(self):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            scribe.cmd_doctor(None)
        out = buf.getvalue()
        self.assertIn("scribe.py sha256:", out)
        self.assertIn("python:", out)
        self.assertIn("pandoc", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
