#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Phase 1 tests for the Scribe's Workbench. stdlib unittest only.
#
# Each test maps to a Phase-1 gate requirement from the brief / GATE 0 rulings.

import shutil
import sys
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

    def test_export_default_joiner_unchanged(self):
        """No --joiner given: behaviour is byte-for-byte what it always was."""
        text, _ = scribe.render_export(self.blocks, "topic", "nas", bare=True)
        self.assertIn("\n\n---\n\n", text)

    def test_export_custom_joiner_is_code_safe(self):
        """A '---' line is a Python SyntaxError; a code export needs a different
        join than prose does. Scribe doesn't decide what a body is, only offers it."""
        text, _ = scribe.render_export(self.blocks, "topic", "nas", bare=True, joiner="\n\n")
        self.assertNotIn("---", text)

    def test_export_empty_joiner(self):
        text, chosen = scribe.render_export(self.blocks, "topic", "nas", bare=True, joiner="")
        self.assertEqual(text, "".join(b.body for b in chosen) + "\n")


POINTER_PILE = (
    "@@ #a1 2026-01-01T00:00 @topic:nas @source:s\nAlpha, the original claim.\n\n"
    "@@ #b2 2026-01-01T00:01 @topic:nas @corrects:#a1 @source:s\nBeta corrects Alpha.\n\n"
    "@@ #c3 2026-01-01T00:02 @topic:git @source:s\nGamma, unrelated, nothing points at it.\n"
)


class TestBacklinks(unittest.TestCase):
    """v1.1.2 — the derived reverse index. Ratified 2026-07-31: tagging/TAG-KEYS-
    reference-v1-DRAFT.md (A.4) already said back-references must be derived, never
    hand-written; this is that principle finally built. Confirmed against real prior
    art before writing it: Foam's graph.ts keeps a computed `backlinks` map, Logseq's
    reference.cljs computes get-linked-references the same way. Read-only by
    construction — nothing here is ever written back into a pile."""

    def setUp(self):
        self.blocks = scribe.parse_pile(POINTER_PILE)

    def test_finds_a_real_pointer(self):
        back = scribe.compute_backlinks({"pile.txt": self.blocks})
        out = scribe.render_backlinks("pile.txt", "a1", back)
        self.assertIn("What points at pile.txt#a1 (1):", out)
        self.assertIn("#b2", out)
        self.assertIn("via @corrects:#a1", out)

    def test_absence_is_named_not_silent(self):
        """§3.8 — a block nothing points at must say so, not return empty/nothing."""
        back = scribe.compute_backlinks({"pile.txt": self.blocks})
        out = scribe.render_backlinks("pile.txt", "c3", back)
        self.assertEqual(out, "(nothing points at pile.txt#c3)\n")

    def test_never_reports_a_block_as_pointing_at_itself(self):
        blocks = scribe.parse_pile(
            "@@ #x1 2026-01-01T00:00 @ref:#x1 @source:s\nself-reference, never a backlink\n")
        back = scribe.compute_backlinks({"pile.txt": blocks})
        out = scribe.render_backlinks("pile.txt", "x1", back)
        self.assertEqual(out, "(nothing points at pile.txt#x1)\n")

    def test_a_value_that_is_not_a_real_id_is_not_a_false_positive(self):
        """A '#' in ordinary prose (a hex color, a hashtag-shaped word) must not be
        mistaken for a pointer just because it starts with '#' -- only a value
        matching a REAL block id in the resolved pile counts."""
        blocks = scribe.parse_pile(
            "@@ #d4 2026-01-01T00:00 @topic:colors @swatch:#deadbeef @source:s\nnot a pointer\n")
        back = scribe.compute_backlinks({"pile.txt": blocks})
        self.assertEqual(back, {})

    def test_cross_pile_backlink_resolves_across_two_files(self):
        """Schnee's sovereignty instruction (2026-07-30): relations must work BETWEEN
        piles too, with no database and no new dependency -- `path#id` is a single
        @key:value string, the 30-year-old URL-fragment convention."""
        import os
        import tempfile
        d = tempfile.mkdtemp()
        ledger = os.path.join(d, "LEDGER.txt")
        other = os.path.join(d, "OTHER.txt")
        with open(ledger, "w") as f:
            f.write("@@ #4d2e 2026-01-01T00:00 @topic:x @source:s\nthe ledger entry\n")
        with open(other, "w") as f:
            f.write("@@ #g1tp 2026-01-01T00:01 @ratified-by:LEDGER.txt#4d2e @source:s\n"
                    "a procedure ratified by that ledger entry\n")
        piles = {ledger: scribe.parse_pile(open(ledger).read()),
                 other: scribe.parse_pile(open(other).read())}
        back = scribe.compute_backlinks(piles)
        out = scribe.render_backlinks(ledger, "4d2e", back, same_pile_label="LEDGER.txt")
        self.assertIn("What points at LEDGER.txt#4d2e (1):", out)
        self.assertIn("OTHER.txt#g1tp", out)
        self.assertIn("via @ratified-by:LEDGER.txt#4d2e", out)

    def test_cli_bare_hash_defaults_to_the_first_pile(self):
        import contextlib
        import io
        import os
        import tempfile
        d = tempfile.mkdtemp()
        path = os.path.join(d, "only.txt")
        with open(path, "w") as f:
            f.write(POINTER_PILE)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = scribe.cmd_backlinks(_Args(target="#a1", pile=[path]))
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn(f"What points at {os.path.basename(path)}#a1 (1):", out)
        self.assertIn("#b2", out)

    def test_cli_refuses_a_pile_name_not_given_on_the_command_line(self):
        import contextlib
        import io
        import os
        import tempfile
        d = tempfile.mkdtemp()
        path = os.path.join(d, "only.txt")
        with open(path, "w") as f:
            f.write(POINTER_PILE)
        buf_err = io.StringIO()
        with contextlib.redirect_stderr(buf_err):
            rc = scribe.cmd_backlinks(_Args(target="nope.txt#a1", pile=[path]))
        self.assertEqual(rc, 1)
        self.assertIn("REFUSED", buf_err.getvalue())


AWAITS_PILE = (
    "@@ #a1 2026-01-01T00:00 @awaits:the-sovereigns-ruling @source:s\n"
    "pile A's own pod, awaiting a ruling.\n\n"
    "@@ #a2 2026-01-01T00:01 @dissolves:the-fix-lands @source:s\n"
    "pile A's own retirement condition.\n"
)
AWAITS_PILE_B = (
    "@@ #b1 2026-01-02T00:00 @awaits:the-sovereigns-ruling @source:s\n"
    "pile B independently awaits the SAME ruling.\n\n"
    "@@ #b2 2026-01-02T00:01 @awaits:something-else @source:s\n"
    "pile B awaits a DIFFERENT condition.\n"
)


class TestActivate(unittest.TestCase):
    """v1.2.0 — the other half of a dpkg trigger. `@awaits:`/`@dissolves:` are
    already this project's `interest` declarations; this is the missing
    on-demand `activate` query: given a condition, who currently awaits it,
    across any piles named. Read-only, never promotes (the human rules every
    promotion, always)."""

    def setUp(self):
        self.a = scribe.parse_pile(AWAITS_PILE)
        self.b = scribe.parse_pile(AWAITS_PILE_B)

    def test_finds_current_waiters_across_piles(self):
        hits = scribe.compute_activations(
            {"pileA.txt": self.a, "pileB.txt": self.b}, "the-sovereigns-ruling")
        self.assertEqual(len(hits), 2)
        ids = sorted(bid for _, bid, _, _, _ in hits)
        self.assertEqual(ids, ["a1", "b1"])

    def test_absence_is_named_not_silent(self):
        """§3.8 — nobody awaiting a condition must say so, not return nothing."""
        hits = scribe.compute_activations({"pileA.txt": self.a}, "no-such-condition")
        out = scribe.render_activate("no-such-condition", hits)
        self.assertEqual(out, "(nothing is @awaits:no-such-condition)\n")

    def test_exact_match_only_not_substring(self):
        """Structural exactness, same discipline as compute_backlinks: a
        condition string that is only a SUBSTRING of a real value must not
        match — no fuzzy/partial matching."""
        hits = scribe.compute_activations({"pileA.txt": self.a}, "sovereigns")
        self.assertEqual(hits, [])

    def test_key_is_choosable_not_hardwired(self):
        """@dissolves: is the other witness-shaped key in this vocabulary
        (the death-condition mirror of @awaits:, per the tag reference) —
        the axis must be choosable, same ruling as toc --by."""
        hits = scribe.compute_activations({"pileA.txt": self.a}, "the-fix-lands",
                                          key="dissolves")
        self.assertEqual([bid for _, bid, _, _, _ in hits], ["a2"])

    def test_cli_reports_across_named_piles(self):
        import contextlib
        import io
        import os
        import tempfile
        d = tempfile.mkdtemp()
        pa, pb = os.path.join(d, "pileA.txt"), os.path.join(d, "pileB.txt")
        with open(pa, "w") as f:
            f.write(AWAITS_PILE)
        with open(pb, "w") as f:
            f.write(AWAITS_PILE_B)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = scribe.cmd_activate(_Args(condition="the-sovereigns-ruling",
                                           pile=[pa, pb], key="awaits"))
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("pileA.txt#a1", out)
        self.assertIn("pileB.txt#b1", out)


CONVERGE_PILE_A = (
    "@@ #a1 2026-01-01T00:00 @act:guard-against-drift @path:toward-sovereignty "
    "@source:s\nProject A's own take, citing Section 3.8 in prose but not the sigil.\n\n"
    "@@ #a2 2026-01-01T00:01 @ref:#a1 @swatch:#deadbeef @source:s\n"
    "Cites the Charter directly: see §3.8 and also Clause 47.\n"
)
CONVERGE_PILE_B = (
    "@@ #b1 2026-01-02T00:00 @act:guard-against-drift @source:s\n"
    "Project B converged on the identical act verb, independently. §3.8 again.\n\n"
    "@@ #b2 2026-01-02T00:01 @topic:git @source:s\n"
    "Unrelated to A entirely.\n"
)


class TestConverges(unittest.TestCase):
    """v1.2.0 — a first structural attempt at Design Charter §3.15's still-open
    founding gap: convergence between DIFFERENT piles that was never made
    explicit by a pointer tag. Deliberately NOT semantic/ML similarity (§3.6's
    "borrowing a word" hazard) -- every finding is a LITERAL tag-value or
    citation-substring match, disclosed as a candidate only, never asserted."""

    def setUp(self):
        self.piles = {"pileA.txt": scribe.parse_pile(CONVERGE_PILE_A),
                      "pileB.txt": scribe.parse_pile(CONVERGE_PILE_B)}

    def test_shared_tag_value_across_two_piles_found(self):
        groups = scribe.compute_convergences(self.piles)
        self.assertIn(("act", "guard-against-drift"), groups)
        hits = groups[("act", "guard-against-drift")]
        self.assertEqual({p for p, _, _ in hits}, {"pileA.txt", "pileB.txt"})

    def test_value_used_only_within_one_pile_is_not_reported(self):
        """@path:toward-sovereignty only appears in pile A -- not a cross-pile
        convergence, so it must not appear in the groups at all."""
        groups = scribe.compute_convergences(self.piles)
        self.assertNotIn(("path", "toward-sovereignty"), groups)

    def test_pointer_shaped_values_are_excluded(self):
        """A value shaped like a pointer (contains '#') is already
        compute_backlinks's job -- converges must not double-report it."""
        groups = scribe.compute_convergences(self.piles)
        for (k, v) in groups:
            self.assertNotIn("#", v)

    def test_by_key_restricts_the_scan(self):
        groups = scribe.compute_convergences(self.piles, tag_key="act")
        self.assertEqual(set(groups), {("act", "guard-against-drift")})

    def test_citation_convergence_found_across_piles(self):
        groups = scribe.compute_citation_convergences(self.piles)
        self.assertIn("§3.8", groups)
        self.assertEqual({p for p, _, _ in groups["§3.8"]},
                         {"pileA.txt", "pileB.txt"})

    def test_citation_only_in_one_pile_is_not_reported(self):
        """Clause 47 is cited only in pile A (once) -- not cross-pile, must
        not appear even though it is a real, well-formed citation."""
        groups = scribe.compute_citation_convergences(self.piles)
        self.assertNotIn("Clause 47", groups)

    def test_render_names_absence_in_both_sections(self):
        """§3.8 -- an empty finding set must say so, in both sections, not
        just vanish silently."""
        out = scribe.render_convergences({}, {})
        self.assertIn("(none found)", out)
        self.assertEqual(out.count("(none found)"), 2)

    def test_render_discloses_which_piles_and_ids(self):
        groups = scribe.compute_convergences(self.piles, tag_key="act")
        out = scribe.render_convergences(groups, {})
        self.assertIn("@act:guard-against-drift", out)
        self.assertIn("pileA.txt#a1", out)
        self.assertIn("pileB.txt#b1", out)
        self.assertIn("never asserted", out)   # the disclosure discipline itself


class TestExportVerify(unittest.TestCase):
    """v1.2.0 -- the joiner-method's missing half: does a saved/derived view
    match the pile it was extracted from, right now? Never repairs -- MATCH
    or DRIFT only (§3.10)."""

    def setUp(self):
        self.blocks = scribe.parse_pile(PILE)

    def test_export_manifest_carries_a_fingerprint(self):
        text, _ = scribe.render_export(self.blocks, "topic", "nas")
        self.assertIn("content:sha256:", text)

    def test_bare_export_carries_no_manifest_to_verify(self):
        text, _ = scribe.render_export(self.blocks, "topic", "nas", bare=True)
        self.assertIsNone(scribe.find_export_manifest(text))

    def test_fingerprint_is_independent_of_order(self):
        """Same blocks, different presentation order (arrival vs --recent):
        the fingerprint is an identity-and-content check, not a text hash, so
        it must not depend on the joiner or the chosen order."""
        chosen_a = scribe.order_blocks(
            scribe.select_blocks(self.blocks, "topic", "nas"), recent=False)
        chosen_b = scribe.order_blocks(
            scribe.select_blocks(self.blocks, "topic", "nas"), recent=True)
        self.assertEqual(scribe.content_fingerprint(chosen_a),
                         scribe.content_fingerprint(chosen_b))

    def test_verify_export_reports_match_when_pile_is_unchanged(self):
        text, _ = scribe.render_export(self.blocks, "topic", "nas")
        manifest = scribe.find_export_manifest(text)
        out = scribe.render_verify_export(manifest, self.blocks, "topic", "nas")
        self.assertTrue(out.startswith("MATCH"))

    def test_verify_export_reports_drift_and_names_what_changed(self):
        text, _ = scribe.render_export(self.blocks, "topic", "nas")
        manifest = scribe.find_export_manifest(text)
        edited = scribe.parse_pile(PILE)
        for b in edited:
            if b.id == "n1":
                b.body = b.body + " EDITED AFTER EXPORT."
        out = scribe.render_verify_export(manifest, edited, "topic", "nas")
        self.assertTrue(out.startswith("DRIFT"))
        self.assertIn("body content changed", out)

    def test_verify_export_names_added_and_removed_ids(self):
        text, _ = scribe.render_export(self.blocks, "topic", "nas")
        manifest = scribe.find_export_manifest(text)
        retagged = scribe.parse_pile(PILE)
        scribe.add_tags(retagged, "n1", remove=[])
        retagged = [b for b in retagged if b.id != "n1"]   # n1 no longer matches
        out = scribe.render_verify_export(manifest, retagged, "topic", "nas")
        self.assertTrue(out.startswith("DRIFT"))
        self.assertIn("no longer matches", out)
        self.assertIn("#n1", out)

    def test_no_manifest_is_named_not_mistaken_for_a_match(self):
        out = scribe.render_verify_export(None, self.blocks, "topic", "nas")
        self.assertTrue(out.startswith("NO MANIFEST"))

    def test_cli_verify_export_round_trip(self):
        import contextlib
        import io
        import os
        import tempfile
        d = tempfile.mkdtemp()
        pile_path = os.path.join(d, "p.txt")
        with open(pile_path, "w") as f:
            f.write(PILE)
        export_path = os.path.join(d, "export.txt")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            scribe.cmd_export(_Args(pile=pile_path, selector="topic:nas",
                                    recent=False, bare=False, joiner=None))
        with open(export_path, "w") as f:
            f.write(buf.getvalue())
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            rc = scribe.cmd_verify_export(_Args(exported=export_path,
                                                selector="topic:nas",
                                                pile=pile_path, recent=False))
        self.assertEqual(rc, 0)
        self.assertTrue(buf2.getvalue().startswith("MATCH"))


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


# ---------------------------------------------------------------------------
# v1.1.0 — "unfreeze the keys". Each test below pins one of the five welds that
# were removed, or the silent-loss path that was closed. The encounter that
# earned the first class is reproduced in `validate_tag`'s docstring.
# ---------------------------------------------------------------------------

class TestSilentBlockLoss(unittest.TestCase):
    """The cardinal sin (§3.6): capture used to WRITE a header it could not read back,
    report success, and lose the block on the next read."""

    def _run(self, argv, stdin_text):
        import contextlib
        import io
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
            old, sys.stdin = sys.stdin, io.StringIO(stdin_text)
            try:
                rc = scribe.main(argv)
            finally:
                sys.stdin = old
        return rc, buf_out.getvalue(), buf_err.getvalue()

    def test_capture_refuses_a_value_that_would_swallow_the_block(self):
        """The exact reproduction from v1.0.0: `--topic "two words"` reported
        `captured block #ac42` at exit 0, and the block was gone on the next read."""
        rc, out, err = self._run(["capture", "--topic", "two words", "-"], "body\n")
        self.assertEqual(rc, 1)                      # refused, not "captured"
        self.assertIn("REFUSED", err)
        self.assertIn("two-words", err)              # names the fix, does not apply it
        self.assertNotIn("@@ ", out)                 # nothing written

    def test_generic_tag_flag_is_validated_too(self):
        """The new front door must not re-open the old hole (any key, any value)."""
        rc, _, err = self._run(["capture", "--tag", "path:away from loss", "-"], "b\n")
        self.assertEqual(rc, 1)
        self.assertIn("REFUSED", err)

    def test_a_good_value_still_captures(self):
        rc, out, _ = self._run(
            ["capture", "--tag", "act:guards-the-boundary", "-"], "b\n")
        self.assertEqual(rc, 0)
        self.assertIn("@act:guards-the-boundary", out)

    def test_read_announces_a_malformed_header_and_never_refuses(self):
        """The read/write ruling: a read ANNOUNCES loudly and still hands over the
        material (§3.1 — a pile with one bad line must not become unopenable), with a
        non-zero exit so nothing mistakes it for a clean run."""
        pile = ("@@ #a1 2026-01-01T00:00 @topic:ok @source:s\nbody one\n\n"
                "@@ #b2 2026-01-01T00:01 @path:two words\nbody two\n")
        bad = scribe.scan_malformed_headers(pile)
        self.assertEqual([n for n, _ in bad], [4])
        self.assertEqual(len(scribe.parse_pile(pile)), 1)   # the loss itself, unchanged

    def test_a_pasted_diff_hunk_is_not_a_false_alarm(self):
        """`@@ -1,4 +1,4 @@` at column 0 is legitimate body text. The check requires
        the `#` id sigil precisely so a pasted patch never reports as a broken header."""
        pile = ("@@ #a1 2026-01-01T00:00 @topic:patch @source:s\n"
                "@@ -1,4 +1,4 @@\n-old\n+new\n")
        self.assertEqual(scribe.scan_malformed_headers(pile), [])

    def test_write_back_refuses_over_a_broken_pile(self):
        """`tag`/`push` rewrite the whole pile; doing that over an unparsed header
        would cement the swallowed block into its neighbour's body for good."""
        import os
        import tempfile
        d = tempfile.mkdtemp()
        path = os.path.join(d, "p.txt")
        with open(path, "w") as fh:
            fh.write("@@ #a1 2026-01-01T00:00 @topic:ok @source:s\nb\n\n"
                     "@@ #b2 2026-01-01T00:01 @path:two words\nb2\n")
        with open(path) as fh:
            before = fh.read()
        import contextlib
        import io
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            scribe.cmd_tag(_Args(id="a1", pile=path, tag=["aspect:manifesting"],
                                 topic=None, state=None, source=None, remove=None,
                                 tag_form="repeated"))
        with open(path) as fh:
            self.assertEqual(fh.read(), before)       # untouched


class _Args:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class TestChooseableToc(unittest.TestCase):
    """§3.13/§3.8 — the one ordering that could not be chosen, and could not say so."""

    def setUp(self):
        self.blocks = scribe.parse_pile(
            "@@ #a1 2026-01-01T00:00 @topic:nas @act:keeps-the-pile-readable @source:s\nAlpha\n\n"
            "@@ #b2 2026-01-01T00:01 @topic:nas @act:keeps-the-pile-readable @source:s\nBeta\n\n"
            "@@ #c3 2026-01-01T00:02 @topic:git @source:s\nGamma\n")

    def test_toc_groups_by_any_key(self):
        toc = scribe.render_toc(self.blocks, key="act")
        self.assertIn("## keeps-the-pile-readable (2)", toc)
        self.assertIn("grouped by @act:", toc)

    def test_toc_names_the_keys_it_does_not_show(self):
        toc = scribe.render_toc(self.blocks, key="topic")
        self.assertIn("NOT shown by this index:", toc)
        self.assertIn("@act:", toc)

    def test_the_loss_line_is_emitted_even_when_there_is_no_loss(self):
        """Show-Always: an index that saw everything and an index that dropped things
        must never look the same (§3.8). Silence is not an answer."""
        blocks = scribe.parse_pile("@@ #a1 2026-01-01T00:00 @topic:x\nA\n")
        toc = scribe.render_toc(blocks, key="topic")
        self.assertIn("NOT shown by this index: (no other keys present in this pile)", toc)
        self.assertIn("every block carries @topic:", toc)

    def test_toc_names_the_blocks_that_fell_out(self):
        toc = scribe.render_toc(self.blocks, key="act")
        self.assertIn("1 of 3 blocks carry no @act:", toc)
        self.assertIn("## (no @act:) (1)", toc)


class TestRetiredKeyIsNeverSilent(unittest.TestCase):
    """§3.8 — a retired thing must not look identical to a live one. A classification,
    not a fault: it announces and does not block."""

    def test_writing_the_retired_key_is_announced_not_refused(self):
        notes = scribe.validate_tag("state", "live")
        self.assertTrue(any("RETIRED" in n for n in notes))

    def test_the_replacement_is_named(self):
        self.assertEqual(scribe.RETIRED_KEYS["state"], "aspect")
        notes = scribe.validate_tag("state", "live")
        self.assertTrue(any("@aspect:" in n for n in notes))

    def test_a_live_key_produces_no_note(self):
        self.assertEqual(scribe.validate_tag("aspect", "manifesting"), [])

    def test_comma_in_a_value_is_disclosed_not_silently_split(self):
        notes = scribe.validate_tag("topic", "nas,zfs")
        self.assertTrue(any("2 separate tags" in n for n in notes))


class TestPileStamp(unittest.TestCase):
    """A pile carries its own reading instructions in-band, so any reader — human or
    a model asked to search the drive — meets them in the artifact rather than in
    someone's config (§5.4: an instruction in a config can be skipped, silently)."""

    def _pile(self):
        import os
        import tempfile
        return os.path.join(tempfile.mkdtemp(), "p.txt")

    def _capture(self, path, topic, extra=None):
        scribe.cmd_capture(_Args(file=None, html=False, tag=None, topic=[topic],
                                 state=None, source="self", append=path,
                                 no_stamp=bool(extra), tag_form="repeated",
                                 ts="2026-01-01T00:00"))

    def setUp(self):
        import io
        self._stdin, sys.stdin = sys.stdin, io.StringIO("body text\n")
        self._err, sys.stderr = sys.stderr, io.StringIO()

    def tearDown(self):
        sys.stdin, sys.stderr = self._stdin, self._err

    def test_a_new_pile_is_stamped_at_birth(self):
        import io
        p = self._pile()
        self._capture(p, "nas")
        with open(p) as fh:
            text = fh.read()
        self.assertTrue(scribe.is_stamped(text))
        self.assertIn("scribe view", text)
        self.assertIn("FRAGMENTS", text)          # names what grep cannot give back
        sys.stdin = io.StringIO("second body\n")
        self._capture(p, "backup")
        with open(p) as fh:
            self.assertEqual(fh.read().count(scribe.STAMP_MARK), 1)   # not re-stamped

    def test_deleting_the_stamp_keeps_it_deleted(self):
        """capture stamps at BIRTH only, so removing it is a decision that sticks —
        the tool never re-adds a header the human took out (§3.1)."""
        import io
        p = self._pile()
        self._capture(p, "nas")
        with open(p) as fh:
            body = "\n".join(l for l in fh.read().split("\n")
                             if not l.startswith("#")).lstrip("\n")
        with open(p, "w") as fh:
            fh.write(body)
        sys.stdin = io.StringIO("second body\n")
        self._capture(p, "backup")
        with open(p) as fh:
            self.assertFalse(scribe.is_stamped(fh.read()))

    def test_the_stamp_costs_the_format_nothing(self):
        """Every stamp line is a comment in the preamble: no block count, no index and
        no round trip may change because a pile is stamped."""
        pile = ("@@ #a1 2026-01-01T00:00 @topic:nas @source:s\nAlpha\n\n"
                "@@ #b2 2026-01-01T00:01 @topic:git @source:s\nBeta\n")
        plain = scribe.parse_pile(pile)
        stamped = scribe.parse_pile(scribe.PILE_STAMP + "\n" + pile)
        self.assertEqual(len([b for b in plain if b.id]),
                         len([b for b in stamped if b.id]))
        self.assertEqual(scribe.render_toc(plain), scribe.render_toc(stamped))
        # and no stamp line may ever be mistaken for a header
        self.assertEqual(scribe.scan_malformed_headers(scribe.PILE_STAMP), [])

    def test_a_rewrite_preserves_the_stamp(self):
        """`tag`/`push` serialize the WHOLE pile back. A stamp that vanished on the
        first tag edit would be worse than no stamp at all."""
        p = self._pile()
        with open(p, "w") as fh:
            fh.write(scribe.PILE_STAMP + "\n@@ #a1 2026-01-01T00:00 @topic:x\nb\n")
        scribe.cmd_tag(_Args(id="a1", pile=p, tag=["aspect:manifesting"], topic=None,
                             state=None, source=None, remove=None, tag_form="repeated"))
        with open(p) as fh:
            after = fh.read()
        self.assertTrue(scribe.is_stamped(after))
        self.assertIn("@aspect:manifesting", after)

    def test_the_stamp_makes_no_file_level_claim_about_who_wrote_the_blocks(self):
        """A pile is a MIXTURE — the human's writing, material handed in, and blocks an
        AI wrote. Provenance is per block (@source:/@origin:/@attests:), so one sentence
        at the top cannot be true of all of it, and a reader who trusts it inherits a
        false attribution for every block it does not fit. The stamp points at where
        provenance lives and says that an absent tag means UNKNOWN (§3.8). This test
        exists because a first draft did claim it."""
        s = scribe.PILE_STAMP
        self.assertNotIn("this file's author", s)
        self.assertIn("PER BLOCK", s)
        for key in ("@source:", "@origin:", "@attests:"):
            self.assertIn(key, s)
        self.assertIn("unknown", s.lower())      # absence is named, not implied

    def test_stamping_an_existing_pile_is_idempotent_and_keeps_a_human_preamble(self):
        p = self._pile()
        with open(p, "w") as fh:
            fh.write("my own notes header\n\n@@ #a1 2026-01-01T00:00 @topic:x\nb\n")
        scribe.cmd_stamp(_Args(pile=p, show=False))
        scribe.cmd_stamp(_Args(pile=p, show=False))     # second run must change nothing
        with open(p) as fh:
            text = fh.read()
        self.assertEqual(text.count(scribe.STAMP_MARK), 1)
        self.assertIn("my own notes header", text)      # his words untouched


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
