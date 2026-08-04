#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Phase 1 tests for the Scribe's Workbench. stdlib unittest only.
#
# Each test maps to a Phase-1 gate requirement from the brief / GATE 0 rulings.

import hashlib
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
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
    """Identity. A block is a NOMINAL object: two blocks reading `agreed` are two sayings,
    not one saying stored twice (ruled 2026-08-01).

    REWRITTEN 2026-08-05. These tests used to pin `gen_mint`, which is retired. They pin the
    same PROPERTIES against the thing that now carries identity — the handle — plus the one
    property that is new and is the whole point: identity is not derived from the body."""

    def test_identity_does_NOT_depend_on_the_body(self):
        """THE SIGNATURE TEST OF THE 2026-08-05 CHANGE, and it is the inverse of what the
        old suite pinned. An identity answers *which thing is this*; an integrity check
        answers *is this thing as it was*. Fusing them made every correction an identity
        event, which is what made the pile feel like it was corralling its keeper. Same
        declaring moment, different body, SAME identity — because correcting a word does not
        make a block a different block."""
        ts = "2026-01-01T00:00:00.123456"
        self.assertEqual(scribe.gen_handle(ts), scribe.gen_handle(ts))
        a, _ = scribe.make_block("the quik brown fox", [], "self", ts=ts)
        b, _ = scribe.make_block("the quick brown fox", [], "self", ts=ts)
        self.assertEqual(a.id, b.id, "a typo fix must not change which block this is")

    def test_identity_does_not_depend_on_the_pile_either(self):
        """The mint folded the pile's genesis in, buying global uniqueness at 64 unreadable
        characters per block forever. The handle's coordinates are THE PILE AND THE NAME —
        `#2644` in this pile, `RIPE-LEDGER#2644` across piles, exactly as a directory
        namespaces a filename. So `gen_handle` takes no genesis and there is nothing left
        for a pile to diverge."""
        import inspect
        self.assertNotIn("genesis", inspect.signature(scribe.gen_handle).parameters)

    def test_handle_deterministic(self):
        """Determinism survives the change — the property the old scheme was built for is
        not the property that was wrong. No RNG in a records tool."""
        self.assertEqual(scribe.gen_handle("2026-01-01T00:00:00.000001"),
                         scribe.gen_handle("2026-01-01T00:00:00.000001"))

    def test_different_moment_diverges(self):
        """The `act` half — the fact `timespec='minutes'` used to discard, and now the only
        fact identity rests on."""
        a = scribe.gen_handle("2026-01-01T00:00:00.000001")
        b = scribe.gen_handle("2026-01-01T00:00:00.000002")
        self.assertNotEqual(a, b)

    def test_the_handle_is_re_derivable_from_the_timestamp_beside_it(self):
        """WHY THE DECLARED MOMENT AND NOT RANDOMNESS. A handle taken from the digits of the
        timestamp printed on the same line can be checked BY EYE with no stored digest: a
        fabricated handle does not match its own timestamp. That is a free, weak check that
        costs the header nothing, and it is what a random handle would have thrown away."""
        ts = "2026-08-05T00:18:12.522644"
        h = scribe.gen_handle(ts)
        self.assertTrue(re.sub(r"\D", "", ts).endswith(h),
                        f"handle {h} is not a tail of the moment it claims")

    def test_now_ts_carries_microseconds(self):
        """The encounter: two `agreed`s in the same minute collided because the tool had
        thrown away what distinguished them. Now load-bearing twice over — the microseconds
        are what keep two same-second captures apart."""
        self.assertRegex(scribe.now_ts(), r"T\d\d:\d\d:\d\d\.\d{6}$")

    def test_handle_extends_on_collision(self):
        """Knuth's rule at issue time (`Literate-Programming-Knuth.txt:827`): abbreviate only
        as far as still identifies uniquely — and PERFORM the check. Extended and visible,
        never renamed away (row 29). The handle extends LEFTWARD now, taking in another digit
        of the same moment, so the longer form is still a tail of its own timestamp."""
        ts = "2026-01-01T00:00:00.123456"
        first = scribe.gen_handle(ts)
        second = scribe.gen_handle(ts, taken={first})
        self.assertEqual(len(first), scribe.HANDLE_MIN)
        self.assertNotEqual(first, second)
        self.assertTrue(second.endswith(first))

    def test_collision_exhaustion_is_declared_not_duplicated(self):
        """The end of the road, which only a pinned `--ts` can reach. When every tail of the
        moment is taken the issuer must not hand back a duplicate — a silent collision is the
        original 2026-08-01 defect. It appends a visible discriminator instead."""
        ts = "2026-01-01T00:00:00.123456"
        digits = re.sub(r"\D", "", ts)
        taken = {digits[-n:] for n in range(scribe.HANDLE_MIN, len(digits))}
        out = scribe.gen_handle(ts, taken=taken)
        self.assertNotIn(out, taken)

    def test_handle_floor_matches_the_ruled_spec(self):
        """SPEC-VS-IMPLEMENTATION DRIFT, now guarded (§3.13). The ruled proposal's worked
        examples (PHASE-0-RECON-AND-PROPOSAL.md:206-215) show six-character ids; the code
        shipped four, and nothing in the repo compared them. This test is that comparison.
        It pins the floor deliberately at 4 — every existing pile is full of 4-char
        handles — and exists so the next change to it is a DECISION, not a drift."""
        self.assertEqual(scribe.HANDLE_MIN, 4)
        spec = pathlib.Path(__file__).with_name("PHASE-0-RECON-AND-PROPOSAL.md")
        if not spec.exists():
            # §3.8, applied to this suite itself: a skipped check and a passing check must
            # never look the same. `if spec.exists():` made this one PASS SILENTLY wherever
            # the spec is absent — which is every published clone, since the spec is part of
            # the withheld development history. The suite reported OK and this guard had not
            # run. It is now a COUNTED, NAMED skip: the runner prints `OK (skipped=N)` and
            # says which check did not run and why. Same shape as the tag-validator's third
            # verdict tier — a witness formally separate from a fault, and countable.
            raise unittest.SkipTest(
                f"CHECK NOT RUN — {spec.name} is not present in this tree (it is part of "
                f"the withheld development history, so this is EXPECTED in a published "
                f"clone and is not a failure). The spec-vs-implementation comparison this "
                f"test exists to perform did NOT happen here; run it in the development "
                f"repository, where the spec is present.")
        examples = re.findall(r"^@@ #([0-9a-f]+) ", spec.read_text(), re.M)
        self.assertTrue(examples, "spec worked examples not found — guard is blind")
        self.assertTrue(
            all(len(e) >= scribe.HANDLE_MIN for e in examples),
            f"spec examples {examples} are shorter than HANDLE_MIN")

    def test_no_dead_guard_parameter_remains(self):
        """The docstring was the most dangerous artifact: the old gen_id claimed to
        'extend length on the rare collision (§3.8)' while make_block never passed the
        `taken` set, so the guard was dead code CITING THE CLAUSE ITS ABSENCE BROKE. A
        false claim of compliance stops the next reader looking. Guard the class of
        defect, not just the instance: every collision-guard entry point must be reached
        by the live path."""
        self.assertFalse(hasattr(scribe, "gen_id"),
                         "gen_id survived — the dead guard is back")
        self.assertFalse(hasattr(scribe, "gen_mint"),
                         "gen_mint survived its own retirement")
        # make_block must actually thread a taken-set into the handle issuer.
        src = pathlib.Path(scribe.__file__).read_text()
        self.assertIn("gen_handle(ts, taken)", src)



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
    """`push` APPENDS A SUPERSEDING BLOCK — it never overwrites one (ruled 2026-08-02).

    The tool binds itself to append-only; it does not bind the human, who may always edit a
    block directly and keep that history in restic instead of in the pile. Two doorways,
    chosen per act (§3.1)."""

    def test_edit_in_view_appends_a_superseding_block(self):
        """A thought developed in a view lands as a NEW block that replaces the old one by
        id; the old block and every other block keep their bodies (the detangle round-trip,
        now append-only)."""
        blocks = scribe.parse_pile(PILE)
        view_text, _ = scribe.render_view(blocks, "topic", "nas")
        edited = view_text.replace("Checksumming detects bitrot.",
                                   "Checksumming detects bitrot. ADDED IN VIEW.")
        blocks, report = scribe.push_view(edited, blocks, genesis="g" * 64)
        self.assertEqual([old for old, _ in report["superseded"]], ["n1"])
        new_id = report["superseded"][0][1]
        by_id = {b.id: b for b in blocks}
        # the NEW block carries the edit and points back
        self.assertIn("ADDED IN VIEW", by_id[new_id].body)
        self.assertIn(("replaces", "#n1"), by_id[new_id].tags)
        # the OLD block still says exactly what it said
        self.assertNotIn("ADDED IN VIEW", by_id["n1"].body)
        self.assertIn(("superseded", f"#{new_id}"), by_id["n1"].tags)
        self.assertNotIn("ADDED IN VIEW", by_id["g1"].body)     # others untouched
        self.assertEqual(report["missing"], [])

    def test_superseding_block_inherits_the_vocabulary(self):
        """A supersession that fell out of its own topic would be a silent loss: the view
        you pushed from would stop showing your own edit."""
        blocks = scribe.parse_pile(PILE)
        view = "@@ #n1 2026-03-22T09:00 @topic:nas @topic:zfs @source:gemini\nrewritten\n"
        blocks, report = scribe.push_view(view, blocks, genesis="g" * 64)
        new_id = report["superseded"][0][1]
        self.assertIn(new_id, [b.id for b in scribe.select_blocks(blocks, "topic", "nas")])

    def test_status_tag_precedes_the_mint_so_it_is_actually_read(self):
        """The whole reason the marker is WRITTEN into the file rather than derived is that
        a tool-off reader must MEET it. Parked after 64 hex characters, it would not be."""
        blocks = scribe.parse_pile(
            "@@ #a1 2026-01-01T00:00 @topic:x @source:s @mint:" + "f" * 64 + "\nold\n")
        blocks, report = scribe.push_view(
            "@@ #a1 2026-01-01T00:00 @topic:x @source:s\nnew\n", blocks, genesis="g" * 64)
        line = scribe.serialize_block(blocks[0]).splitlines()[0]
        self.assertLess(line.index("@superseded:"), line.index("@mint:"))

    def test_push_applies_body_only_discloses_tag_drift(self):
        """Push carries BODY only; a header-tag change in the view is disclosed, not
        silently applied (§3.7). The superseding block inherits the OLD block's tags."""
        blocks = scribe.parse_pile(PILE)
        view = ("@@ #n1 2026-03-22T09:00 @topic:nas @topic:zfs @topic:NEWTAG @source:gemini\n"
                "new body text\n")
        blocks, report = scribe.push_view(view, blocks, genesis="g" * 64)
        new_id = report["superseded"][0][1]
        by_id = {b.id: b for b in blocks}
        self.assertEqual(by_id[new_id].body, "new body text")        # body carried
        self.assertNotIn(("topic", "NEWTAG"), by_id[new_id].tags)    # tag NOT applied
        self.assertIn("n1", report["tag_drift"])                     # but disclosed

    def test_pushing_a_stale_view_twice_refuses_to_fork_the_chain(self):
        blocks = scribe.parse_pile(PILE)
        view = "@@ #n1 2026-03-22T09:00 @topic:nas @source:gemini\nrewritten\n"
        blocks, first = scribe.push_view(view, blocks, genesis="g" * 64)
        blocks, second = scribe.push_view(view, blocks, genesis="g" * 64)
        self.assertEqual(second["superseded"], [])
        self.assertEqual(second["already_superseded"],
                         [("n1", first["superseded"][0][1])])

    def test_no_body_change_writes_nothing(self):
        blocks = scribe.parse_pile(PILE)
        view_text, _ = scribe.render_view(blocks, "topic", "nas")
        before = scribe.serialize_pile(blocks)
        blocks, report = scribe.push_view(view_text, blocks, genesis="g" * 64)
        self.assertEqual(report["superseded"], [])
        self.assertEqual(scribe.serialize_pile(blocks), before)

    def test_INVIOLABLE_bodies_and_identities(self):
        """The ruling in one assertion: bodies and identities are inviolable. Across a push,
        no pre-existing block's body changes, no @mint: changes, and no handle changes. The
        ONLY permitted difference on an existing block is the addition of @superseded:."""
        blocks = scribe.parse_pile(PILE)
        before = {b.id: (b.body, dict(b.tags).get(scribe.MINT_KEY), list(b.tags))
                  for b in blocks if b.id}
        view = "@@ #n1 2026-03-22T09:00 @topic:nas @source:gemini\ntotally rewritten\n"
        blocks, report = scribe.push_view(view, blocks, genesis="g" * 64)
        for b in blocks:
            if not b.id or b.id not in before:
                continue                                   # the appended block
            old_body, old_mint, old_tags = before[b.id]
            self.assertEqual(b.body, old_body, f"#{b.id} body was altered")
            self.assertEqual(dict(b.tags).get(scribe.MINT_KEY), old_mint,
                             f"#{b.id} identity was altered")
            added = [t for t in b.tags if t not in old_tags]
            self.assertTrue(all(k == scribe.SUPERSEDED_KEY for k, _ in added),
                            f"#{b.id} gained a tag other than @superseded:: {added}")
            self.assertLessEqual(len(added), 1, f"#{b.id} gained more than one tag")

    def test_views_disclose_supersession_and_never_hide_it_by_default(self):
        """Appending rather than overwriting means a view can now contain both an old
        saying and the one that replaced it. Hiding the old one by default would be an
        undisclosed exclusion (§3.8) — so it is SHOWN and the fact is declared in the
        view's own header, in band, where an editor will meet it."""
        blocks = scribe.parse_pile(PILE)
        view = "@@ #n1 2026-03-22T09:00 @topic:nas @source:gemini\nrewritten\n"
        blocks, report = scribe.push_view(view, blocks, genesis="g" * 64)
        text, chosen = scribe.render_view(blocks, "topic", "nas")
        self.assertIn("n1", [b.id for b in chosen])          # shown, not dropped
        self.assertIn("@superseded:", text)
        self.assertIn("Shown, not hidden", text)

    def test_current_flag_hides_them_and_declares_that_it_did(self):
        blocks = scribe.parse_pile(PILE)
        view = "@@ #n1 2026-03-22T09:00 @topic:nas @source:gemini\nrewritten\n"
        blocks, report = scribe.push_view(view, blocks, genesis="g" * 64)
        text, chosen = scribe.render_view(blocks, "topic", "nas", current=True)
        self.assertNotIn("n1", [b.id for b in chosen])
        self.assertIn("HIDDEN from this view", text)
        self.assertIn("still in the pile", text)

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

    def test_added_tags_land_BEFORE_the_mint_not_after_it(self):
        """@mint: is placed last at capture so the human's eye meets the vocabulary first
        and the 64 hex trail off the end of the line (§4.6, argued at make_block). `push`
        already honoured that for its status tag; `add_tags` did not, so every tag a human
        added by hand landed PAST the wall of hex — quietly undoing the ruling for exactly
        the tags most meant to be read. FOUND LIVE, not by reading: tagging a real block in
        STANDING-PROCEDURES.txt put @act: — the most load-bearing key on the bench sheet —
        after the mint."""
        pile = ("@@ #z1 2026-08-02T10:00:00.000001 @topic:x "
                "@mint:" + "d" * 64 + "\nbody\n")
        blocks = scribe.parse_pile(pile)
        ok, b = scribe.add_tags(blocks, "z1", add=[("act", "keeps-the-thread-alive"),
                                                   ("path", "toward-being-read")])
        self.assertTrue(ok)
        keys = [k for k, _ in b.tags]
        self.assertEqual(keys[-1], scribe.MINT_KEY,
                         f"@mint: must stay last in the tag run; got {keys}")
        self.assertEqual(keys, ["topic", "act", "path", scribe.MINT_KEY],
                         "added tags must keep their order, before the mint")
        # And the header the human actually reads must show it that way.
        self.assertNotIn("d" * 64 + " @act:", scribe.serialize_block(b))

    def test_a_legacy_block_with_no_mint_still_appends_normally(self):
        """The insertion point is 'before @mint:, or at the end if there is none'. A block
        captured before the identity split has no @mint:, and must not be disturbed by the
        rule that exists for blocks that do."""
        blocks = scribe.parse_pile("@@ #z2 2026-01-01T00:00 @topic:x\nbody\n")
        ok, b = scribe.add_tags(blocks, "z2", add=[("act", "still-works")])
        self.assertTrue(ok)
        self.assertEqual([k for k, _ in b.tags], ["topic", "act"])


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


DUPE_PILE = (
    "@@ #a8eb 2026-08-01T10:00 @topic:x @source:claude\n"
    "first saying\n\n"
    "@@ #a8eb 2026-08-01T10:00 @topic:x @source:claude\n"
    "second saying\n\n"
    "@@ #c0de 2026-08-01T10:01 @topic:x @source:claude\n"
    "a block with a handle of its own\n"
)


class TestAmbiguityIsRefused(unittest.TestCase):
    """PHASE 0 — the live data loss, independent of any theory of identity.

    push_view built `{b.id: b}` (a dict), so on a duplicate handle the LAST block
    silently won and quietly received an edit meant for the FIRST, while add_tags
    scanned for the FIRST match. Two verbs, silently disagreeing about which block an
    id names. §3.6: silent failure is the cardinal sin, and this was silent
    wrong-TARGET writing."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.pile = os.path.join(self.dir, "dupes.txt")
        with open(self.pile, "w", encoding="utf-8") as fh:
            fh.write(DUPE_PILE)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_duplicate_handles_are_found(self):
        d = scribe.duplicate_handles(scribe.parse_pile(DUPE_PILE))
        self.assertEqual(sorted(d), ["a8eb"])
        self.assertEqual(len(d["a8eb"]), 2)

    def test_resolve_refuses_ambiguity_instead_of_guessing(self):
        blocks = scribe.parse_pile(DUPE_PILE)
        with self.assertRaises(scribe.AmbiguousHandle) as cm:
            scribe.resolve_handle(blocks, "a8eb")
        self.assertIn("2 blocks", str(cm.exception))
        # the unambiguous one still resolves — the guard is not a blanket refusal
        self.assertEqual(scribe.resolve_handle(blocks, "c0de").body,
                         "a block with a handle of its own")

    def test_unique_prefix_resolves_but_ambiguous_prefix_refuses(self):
        """Knuth's rule on LOOKUP: enough text to identify uniquely, and perform the
        check. `#c0` is enough; `#a8` is not."""
        blocks = scribe.parse_pile(DUPE_PILE)
        self.assertEqual(scribe.resolve_handle(blocks, "c0").id, "c0de")
        with self.assertRaises(scribe.AmbiguousHandle):
            scribe.resolve_handle(blocks, "a8")

    def test_push_refuses_and_writes_NOTHING(self):
        """The whole push aborts. A partial push would leave the human unable to tell
        which of his edits landed."""
        before = pathlib.Path(self.pile).read_text()
        view = "@@ #a8eb 2026-08-01T10:00 @topic:x @source:claude\nEDITED IN THE VIEW\n"
        blocks, report = scribe.push_view(view, scribe.parse_pile(before))
        self.assertEqual(report["superseded"], [])
        self.assertIn("a8eb", report["ambiguous"])
        # and the file on disk is byte-identical after the real command
        vpath = os.path.join(self.dir, "view.txt")
        pathlib.Path(vpath).write_text(view)
        rc = _run_cmd(["push", vpath, self.pile])
        self.assertEqual(rc, 1)
        self.assertEqual(pathlib.Path(self.pile).read_text(), before)

    def test_tag_refuses_and_writes_NOTHING(self):
        before = pathlib.Path(self.pile).read_text()
        rc = _run_cmd(["tag", "a8eb", self.pile, "--tag", "topic:new"])
        self.assertEqual(rc, 1)
        self.assertEqual(pathlib.Path(self.pile).read_text(), before)

    def test_tag_still_works_on_an_unambiguous_handle(self):
        rc = _run_cmd(["tag", "c0de", self.pile, "--tag", "topic:new"])
        self.assertEqual(rc, 0)
        self.assertIn("@topic:new", pathlib.Path(self.pile).read_text())

    def test_mint_cannot_be_edited_as_vocabulary(self):
        blocks = scribe.parse_pile(
            "@@ #z1 2026-08-01T10:00 @mint:" + "f" * 64 + " @source:s\nbody\n")
        with self.assertRaises(scribe.TagRefused):
            scribe.add_tags(blocks, "z1", remove=[f"mint:{'f' * 64}"])


class TestCaptureIssuesNominally(unittest.TestCase):
    """PHASE 1 — the encounter, run through the sanctioned front door.

    RENAMED 2026-08-05 from TestCaptureMintsNominally: there is no mint. What is pinned here
    is unchanged in substance — two identical sayings must remain two — and the mechanism
    that keeps them apart moved from CONSTRUCTION to a CHECK."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _capture(self, pile, body, ts=None, extra=()):
        cmd = [sys.executable, "scribe.py", "capture", "--source", "claude",
               "--tag", "topic:x", "--append", pile, *extra]
        if ts:
            cmd += ["--ts", ts]
        return subprocess.run(cmd, input=body, capture_output=True, text=True)

    def test_same_body_same_minute_same_source_now_distinct(self):
        """THE ENCOUNTER. Before: two identical `@@ #a8eb` headers, in one pile, silently.
        The ts is pinned to the same MINUTE for both, so the declaring moment cannot separate
        them either — and they must still be two sayings."""
        pile = os.path.join(self.dir, "same.txt")
        self._capture(pile, "agreed\n", ts="2026-08-01T10:00")
        self._capture(pile, "agreed\n", ts="2026-08-01T10:00")
        blocks = [b for b in scribe.parse_pile(pathlib.Path(pile).read_text()) if b.id]
        self.assertEqual(len(blocks), 2)
        self.assertEqual(len(set(b.id for b in blocks)), 2, "handles collided")
        self.assertEqual(scribe.duplicate_handles(blocks), {})

    def test_THE_OBJECTION_a_pinned_ts_collapses_the_one_field_identity_rests_on(self):
        """THE OBJECTION THE 2026-08-05 CHANGE REVIVES, ANSWERED RATHER THAN DROPPED.

        The old mint kept two identical backdated sayings apart BY CONSTRUCTION: `ordinal` is
        a block's position in an append-only pile, so the second is the (n+1)th however
        identical it is — gForth's `HERE`, which only moves forward. That was a real argument
        and this suite used to pin it (`test_full_precision_ts_ALONE_is_not_sufficient`).

        Identity no longer contains the position, so THE CONSTRUCTION IS GONE and only the
        CHECK remains. That is not a weakening dressed up: it is Knuth's rule stated exactly
        — abbreviate only as far as still identifies uniquely, and PERFORM the check — and
        the whole 2026-08-01 defect was a truncation shipped WITHOUT the check.

        What it does mean is that `taken` is now the only thing standing between the pile and
        a repeat of that defect, so it is load-bearing in a way it was not before. Pinned
        here, through the real CLI, with the timestamp pinned to the microsecond so nothing
        else can be doing the work."""
        pile = os.path.join(self.dir, "pinned.txt")
        ts = "2026-08-01T10:00:00.000000"
        for _ in range(3):
            self._capture(pile, "agreed\n", ts=ts)
        blocks = [b for b in scribe.parse_pile(pathlib.Path(pile).read_text()) if b.id]
        self.assertEqual(len(blocks), 3)
        self.assertEqual(len(set(b.id for b in blocks)), 3,
                         "the check is the ONLY guard now, and it did not hold")
        self.assertEqual(scribe.duplicate_handles(blocks), {})

    def test_two_piles_may_reuse_a_handle_and_that_is_the_model(self):
        """The cross-pile half, and the answer CHANGED on 2026-08-05. The mint bought global
        uniqueness by folding each pile's genesis into every identity — 64 unreadable
        characters per block, forever, to avoid ever writing down which pile you meant.

        Now the PILE IS THE NAMESPACE, as a directory is for a filename, and `backlinks`
        already speaks `pile.txt#id` for exactly this reason. So two piles reusing a handle
        is not a collision to be prevented; it is the naming model working. Pinned as a
        PROPERTY rather than left as an accident, because the next reader will otherwise
        read it as the bug that was fixed on 2026-08-01 — and it is not that bug, which was
        two identical handles INSIDE one pile."""
        a, b = (os.path.join(self.dir, n) for n in ("a.txt", "b.txt"))
        ts = "2026-08-01T10:00:00.000000"
        self._capture(a, "the same thought\n", ts=ts)
        self._capture(b, "a different thought\n", ts=ts)
        ida = [x for x in scribe.parse_pile(pathlib.Path(a).read_text()) if x.id][0].id
        idb = [x for x in scribe.parse_pile(pathlib.Path(b).read_text()) if x.id][0].id
        self.assertEqual(ida, idb, "same moment, different piles — the handle is the same "
                                   "and the pile is what tells them apart")

    def test_new_pile_is_born_with_a_genesis(self):
        pile = os.path.join(self.dir, "born.txt")
        self._capture(pile, "first\n")
        text = pathlib.Path(pile).read_text()
        genesis, declared = scribe.genesis_of(text, pile)
        self.assertTrue(declared, "a pile born today must carry its own genesis")
        self.assertEqual(len(genesis), 64)

    def test_legacy_pile_is_NAMED_not_silently_upgraded(self):
        """A pile from before 2026-08-01 has no genesis. It keeps working, the difference is
        DISCLOSED, and nothing is rewritten behind the human (§3.8). What the disclosure SAYS
        changed on 2026-08-05 — the genesis no longer feeds identity, so the note now reports
        a fact about the pile's history rather than a weaker guarantee."""
        pile = os.path.join(self.dir, "legacy.txt")
        pathlib.Path(pile).write_text(
            "@@ #old1 2026-07-01T09:00 @topic:x @source:s\nan older saying\n")
        r = self._capture(pile, "a new one\n")
        self.assertIn("no @genesis:", r.stderr)
        self.assertIn("#old1", pathlib.Path(pile).read_text())

    def test_handle_extension_is_announced(self):
        """Row 29: declare the collision, do not rename it away."""
        pile = os.path.join(self.dir, "ext.txt")
        ts = "2026-08-01T10:00:00.000000"
        self._capture(pile, "one\n", ts=ts)
        r = self._capture(pile, "two\n", ts=ts)
        self.assertIn("handle extended", r.stderr)

    def test_an_ordinary_header_carries_NO_DIGEST_AT_ALL(self):
        """§4.3, and it is the change a human actually SEES. Every header used to end in 64
        hex; sealing is opt-in, so an ordinary block's header is now entirely readable
        vocabulary. The poverty objection raised on 2026-08-01 — 'a pile's whole virtue is
        being readable in an editor with the tool off, and 64 hex per block is identity noise
        in front of the human's eyes' — was answered then by MOVING the hash to the end of
        the line. It is answered now by not writing one."""
        block, _ = scribe.make_block("body", [("topic", "x"), ("source", "s")], "s",
                                     ts="2026-01-01T00:00:00.000000")
        line = scribe.serialize_block(block).splitlines()[0]
        self.assertNotIn("@mint:", line)
        self.assertNotIn("@sealed:", line)
        self.assertNotRegex(line, r"[0-9a-f]{64}")

    def test_a_seal_is_opt_in_and_trails_the_vocabulary(self):
        """When a digest IS asked for it keeps the placement ruling the mint held: the eye
        meets the tags it came for, and the 64 hex trail off the line end."""
        block, _ = scribe.make_block("body", [("topic", "x"), ("source", "s")], "s",
                                     ts="2026-01-01T00:00:00.000000", seal=True)
        self.assertEqual(block.tags[-1][0], scribe.SEAL_KEY)
        line = scribe.serialize_block(block).splitlines()[0]
        self.assertLess(line.index("@topic:"), line.index("@sealed:"))



class TestSealAudit(unittest.TestCase):
    """`scribe verify` — the pile auditing itself at rest, OPT-IN since 2026-08-05.

    REWRITTEN from TestMintAudit. The old class pinned an audit that covered every block by
    re-deriving its `@mint:`. That check was retired for the reason gathered before the
    change and not after: across all four of the sovereign's real piles — 76 blocks — it had
    reported `edited in place` ZERO times, and 45 of those 76 carried no mint at all. What it
    cost was paid every day; what it caught was nothing.

    Gone with it: the DELETION-SIGNATURE search. Because the old identity contained a block's
    ordinal, removing one block from the middle made every later block re-derive wrong, so
    the audit had to look for a trailing run verifying at one constant offset and report
    "K blocks removed" instead of a wave of false alarm. That machinery was correct and it
    existed ONLY to defend the choice to put position inside identity. An identity that is
    issued and never recomputed cannot drift when its neighbours move. Most of what these
    tests stopped needing was not the feature — it was the scaffolding the feature required."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.g = "a" * 64

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _pile(self, bodies, seal=True):
        blocks = []
        for i, body in enumerate(bodies):
            b, _ = scribe.make_block(body, [("topic", "t"), ("source", "self")], "self",
                                     ts=f"2026-08-02T10:00:0{i}.00000{i}",
                                     taken={x.id for x in blocks}, seal=seal)
            blocks.append(b)
        return blocks

    def test_untouched_sealed_pile_is_all_as_sealed(self):
        rep = scribe.audit_seals(self._pile(["one", "two", "three"]))
        self.assertEqual(rep["states"], [scribe.AS_SEALED] * 3)
        self.assertEqual(rep["unsealed"], 0)

    def test_a_sealed_body_edited_in_place_is_named_and_only_that_one(self):
        blocks = self._pile(["one", "two", "three"])
        blocks[1].body = "two, with the final sentence rewritten"
        rep = scribe.audit_seals(blocks)
        self.assertEqual(rep["states"],
                         [scribe.AS_SEALED, scribe.CHANGED_SINCE_SEAL, scribe.AS_SEALED])

    def test_editing_the_TIMESTAMP_is_caught_too(self):
        """A seal covers the declaring moment, so backdating a sealed block says so."""
        blocks = self._pile(["one"])
        blocks[0].ts = "2020-01-01T00:00:00.000000"
        self.assertEqual(scribe.audit_seals(blocks)["states"], [scribe.CHANGED_SINCE_SEAL])

    def test_ONLY_source_is_sealed_of_the_tags(self):
        """DECLARED CONSEQUENCE (§3.8), carried over from the mint unchanged because the
        reasoning was right: re-attributing a saying is a significant act and should be
        visible, so `@source:` is inside the seal — but the rest of the vocabulary is how a
        pile is re-interrogated as thinking moves, and sealing it would make ordinary
        re-filing look like tampering."""
        blocks = self._pile(["one"])
        blocks[0].tags = [("topic", "COMPLETELY-DIFFERENT"), ("source", "self")] + \
                         [t for t in blocks[0].tags if t[0] == scribe.SEAL_KEY]
        self.assertEqual(scribe.audit_seals(blocks)["states"], [scribe.AS_SEALED],
                         "re-filing must not read as tampering")
        blocks[0].tags = [("topic", "t"), ("source", "someone-else")] + \
                         [t for t in blocks[0].tags if t[0] == scribe.SEAL_KEY]
        self.assertEqual(scribe.audit_seals(blocks)["states"], [scribe.CHANGED_SINCE_SEAL],
                         "re-attribution must not be silent")

    def test_a_DELETED_middle_block_disturbs_NOTHING(self):
        """THE SCAFFOLDING THAT IS NO LONGER NEEDED, pinned as a property. Cutting a block
        out of the middle of a pile used to make every later block re-derive wrong, and the
        audit needed a whole offset-search to report that truthfully. Identity and seals now
        contain no position, so removing a block is invisible to every other block — which
        is what an append-only store of independent sayings should have meant all along."""
        blocks = self._pile(["one", "two", "three", "four"])
        del blocks[1]
        self.assertEqual(scribe.audit_seals(blocks)["states"], [scribe.AS_SEALED] * 3)

    def test_a_block_moved_in_from_elsewhere_still_verifies(self):
        """NAMED LIMIT, and its sign flipped. A mint folded in the pile's genesis, so a block
        carried in from another pile read as edited — which was defensible but meant a seal
        was partly a statement about WHERE a block sat. A seal is now a statement about the
        BLOCK, so it travels with it. That is the property `@formed:` has in the gForth
        build, reached here from the other direction."""
        blocks = self._pile(["one"])
        self.assertEqual(scribe.audit_seals(blocks, genesis="z" * 64)["states"],
                         [scribe.AS_SEALED])

    def test_an_unsealed_block_says_THE_CHECK_DID_NOT_RUN(self):
        """§3.8. A check that did not run must never be reported like one that passed —
        and under opt-in sealing that is the ORDINARY condition, so it is stated every time
        rather than left to the silence."""
        import contextlib, io
        path = os.path.join(self.dir, "u.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(scribe.serialize_pile(self._pile(["one", "two"], seal=False)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = scribe.main(["verify", path])
        out = buf.getvalue()
        self.assertIn("2 not sealed", out)
        self.assertIn("CHECK DID", out)
        self.assertEqual(rc, 0, "a question nobody asked is not an unanswered question")

    def test_exit_2_ONLY_when_a_seal_was_broken(self):
        """The exit code carries one fact and no others. Neither an unsealed block nor a
        legacy `@mint:` sets it — both are permanent conditions of ordinary piles, and an
        alarm that always fires defeats disclosure while satisfying it (§3.7 as amended),
        teaching the reader to stop reading exit codes."""
        import contextlib, io
        clean = os.path.join(self.dir, "clean.txt")
        broken = os.path.join(self.dir, "broken.txt")
        legacy = os.path.join(self.dir, "legacy.txt")
        with open(clean, "w", encoding="utf-8") as fh:
            fh.write(scribe.serialize_pile(self._pile(["one"])))
        blocks = self._pile(["one"])
        blocks[0].body = "changed"
        with open(broken, "w", encoding="utf-8") as fh:
            fh.write(scribe.serialize_pile(blocks))
        with open(legacy, "w", encoding="utf-8") as fh:
            fh.write("@@ #old1 2026-07-01T09:00 @topic:t @source:s @mint:" + "f" * 64
                     + "\nan older saying\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(scribe.main(["verify", clean]), 0)
            self.assertEqual(scribe.main(["verify", broken]), scribe.EXIT_FINDINGS)
            self.assertEqual(scribe.main(["verify", legacy]), 0)

    def test_a_LEGACY_mint_is_reported_as_UNCHECKABLE_not_as_absent(self):
        """The retired scheme stays legible (§3.16 live-vs-frozen). A mint cannot be
        re-derived from what the file alone says — it needed the pile's genesis and the
        block's frozen ordinal — so this verb says exactly that, rather than reporting an
        absence of evidence as evidence."""
        import contextlib, io
        path = os.path.join(self.dir, "legacy.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("@@ #old1 2026-07-01T09:00 @topic:t @source:s @mint:" + "f" * 64
                     + "\nan older saying\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            scribe.main(["verify", path])
        out = buf.getvalue()
        self.assertIn("1 legacy", out)
        self.assertIn("cannot be re-derived", out)
        self.assertIn("RETIRED", out)
        # And the state itself carries the same fact, for anything reading the audit
        # programmatically rather than reading the report.
        rep = scribe.audit_seals(scribe.parse_pile(pathlib.Path(path).read_text()))
        self.assertEqual(rep["states"], [scribe.LEGACY_MINT])

    def test_legacy_blocks_are_summarised_with_the_grep_that_finds_them(self):
        """§4.6, and it is a correction made once the output existed rather than reasoned in
        advance. The first version NAMED every legacy block: nine of them cost eighteen lines
        that said nothing the count had not, and there is no per-block act to take from
        reading them. Summarise the norm, and hand over the means of finding them."""
        import contextlib, io
        path = os.path.join(self.dir, "many.txt")
        with open(path, "w", encoding="utf-8") as fh:
            for i in range(6):
                fh.write(f"@@ #old{i} 2026-07-01T09:0{i} @topic:t @source:s @mint:"
                         + "f" * 64 + f"\nsaying {i}\n\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            scribe.main(["verify", path])
        out = buf.getvalue()
        self.assertIn("NOT LISTED", out)
        self.assertIn("grep", out)
        self.assertNotIn("#old3", out)

    def test_THE_LANGUAGE_GUARD_no_fault_words_anywhere_in_the_output(self):
        """THE LOAD-BEARING TEST, and it guards a RULING rather than a behaviour.

        v1.3.1 ruled the hand-edit a legitimate sovereign act — the second doorway. A verb
        that reported it as MISMATCH/INVALID/at a severity would recast a sanctioned choice
        as a defect, and a sovereign who feels told off for using his own door stops using
        it. `substituted` is a fact, never a fault (the path-sovereignty witness); `[HELD]`
        is the same move in the tag-validator. Prose cannot hold that line across future
        edits — this test can, and it is why it exists."""
        import contextlib, io
        path = os.path.join(self.dir, "p.txt")
        blocks = self._pile(["one", "two", "three"])
        blocks[1].body = "edited by hand"
        plain = scribe.Block(id="old1", ts="2026-01-01T00:00",
                             tags=[("topic", "t"), ("source", "self")], body="no seal here")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(scribe.stamp_for(self.g) + "\n"
                     + scribe.serialize_pile(blocks + [plain]))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            scribe.main(["verify", path])
        out = buf.getvalue().lower()
        for word in ("mismatch", "invalid", "corrupt", "tamper", "unverified", "error",
                     "warning", "severity", "violation", "illegal", "suspicious", "modified"):
            self.assertNotIn(word, out, f"fault-language {word!r} reached the output")
        self.assertIn("as sealed", out)



class TestLegacyIsWhatCARRIESAMintNotWhatLacksOne(unittest.TestCase):
    """A DEFECT FOUND BY BEING ASKED A QUESTION, 2026-08-05, and the class of defect is the
    point rather than the instance.

    `duplicates` decided a block was legacy with `not block.tags.get(MINT_KEY)` — correct
    while a *missing* mint meant a block predated v1.3.0. After v1.4.0 **no capture writes a
    mint at all**, so the predicate silently inverted: a pile of blocks captured today was
    reported, confidently, as *"minted before the identity split"*.

    **A predicate that was true of the past and is now true of the present is the most
    dangerous kind of staleness** — nothing errors, nothing is skipped, and the output is
    simply backwards. No existing test caught it because every test either used fresh blocks
    (where the old code was wrong but nothing asserted the wording) or legacy fixtures. This
    class asserts BOTH DIRECTIONS, which is the only shape that can catch an inversion."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _run(self, path):
        import contextlib, io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            scribe.main(["duplicates", path])
        return buf.getvalue()

    def test_a_pile_captured_TODAY_is_not_called_legacy(self):
        path = os.path.join(self.dir, "fresh.txt")
        blocks = []
        for i in range(3):
            b, _ = scribe.make_block(f"saying {i}", [("topic", "t")], "self",
                                     ts=f"2026-08-05T10:00:0{i}.00000{i}",
                                     taken={x.id for x in blocks})
            blocks.append(b)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(scribe.serialize_pile(blocks))
        out = self._run(path)
        self.assertNotIn("RETIRED", out)
        self.assertNotIn("legacy", out.lower())

    def test_a_pile_of_MINTED_blocks_IS_called_legacy(self):
        path = os.path.join(self.dir, "old.txt")
        with open(path, "w", encoding="utf-8") as fh:
            for i in range(2):
                fh.write(f"@@ #old{i} 2026-08-02T09:0{i} @topic:t @source:s @mint:"
                         + "f" * 64 + f"\nsaying {i}\n\n")
        out = self._run(path)
        self.assertIn("RETIRED @mint:", out)
        self.assertIn("2 block(s)", out)

    def test_two_blocks_sharing_an_id_are_separated_by_their_MOMENT(self):
        """What tells two same-handled blocks apart used to be their distinct mints. It is
        now the declaring moment — which is not a substitute for the mint, it is what the
        mint was mostly made of, read straight off the header instead of through a digest."""
        path = os.path.join(self.dir, "dupe.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("@@ #aaaa 2026-08-05T09:00:00.000001 @topic:t @source:s\nfirst\n\n"
                     "@@ #aaaa 2026-08-05T09:00:00.000002 @topic:t @source:s\nsecond\n")
        out = self._run(path)
        self.assertIn("distinct declaring moments", out)
        self.assertIn("ARE different sayings", out)

    def test_two_blocks_sharing_an_id_AND_a_moment_are_left_to_the_keeper(self):
        path = os.path.join(self.dir, "same.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("@@ #aaaa 2026-08-05T09:00 @topic:t @source:s\nfirst\n\n"
                     "@@ #aaaa 2026-08-05T09:00 @topic:t @source:s\nsecond\n")
        out = self._run(path)
        self.assertIn("cannot be decided by the tool", out)
        self.assertIn("Yours to rule", out)


class TestAmendTheThirdDoorway(unittest.TestCase):
    """`scribe amend` — correction as an act distinct from revision, 2026-08-05.

    Before this there were two doorways and the missing one was the common case: "I wrote
    that five minutes ago and a word is wrong." That is not a revision — nothing moved — so
    the pile should not grow and nothing should be reported, because NOTHING HAPPENED. It
    could not exist while identity contained the body: every correction would have been an
    identity event, so the tool would have had to either change the block's identity
    (breaking every pointer to it) or report it forever as edited.

    So this is not a feature added on top of the identity change. It IS that change, seen
    from the user's side."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.pile = os.path.join(self.dir, "p.txt")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _cap(self, body, extra=()):
        return subprocess.run(
            [sys.executable, "scribe.py", "capture", "--source", "schnee",
             "--tag", "topic:t", "--append", self.pile, *extra],
            input=body, capture_output=True, text=True)

    def _amend(self, handle, body):
        return subprocess.run(
            [sys.executable, "scribe.py", "amend", handle, self.pile],
            input=body, capture_output=True, text=True)

    def _blocks(self):
        return [b for b in scribe.parse_pile(pathlib.Path(self.pile).read_text()) if b.id]

    def test_a_typo_changes_the_body_and_NOTHING_ELSE(self):
        """Identity unchanged, pile the same length, no tag added, no trace. A typo is not
        an event — the gForth build's ruling (`amend-last` records nothing), adopted here."""
        self._cap("the quik brown fox\n")
        h = self._blocks()[0].id
        before_tags = list(self._blocks()[0].tags)
        r = self._amend(h, "the quick brown fox\n")
        self.assertEqual(r.returncode, 0)
        after = self._blocks()
        self.assertEqual(len(after), 1, "the pile grew")
        self.assertEqual(after[0].id, h, "identity moved under a correction")
        self.assertEqual(after[0].body, "the quick brown fox")
        self.assertEqual(after[0].tags, before_tags, "a correction left a trace")

    def test_it_REFUSES_when_something_points_at_the_block(self):
        """THE GUARD, AND IT IS A REFUSAL NOT A WARNING. Someone wrote `@ref:#x` ABOUT the
        wording that is there now; silently changing that wording rewrites their citation.
        That is exactly what `push` exists to protect, so the refusal names it and says so.
        If something points at it, it is no longer only yours to correct."""
        self._cap("the target\n")
        target = self._blocks()[0].id
        self._cap("the pointer\n", extra=["--tag", f"ref:#{target}"])
        before = pathlib.Path(self.pile).read_text()
        r = self._amend(target, "rewritten under a citation\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("REFUSED", r.stderr)
        self.assertIn("push", r.stderr, "the refusal must name the doorway that fits")
        self.assertEqual(pathlib.Path(self.pile).read_text(), before,
                         "a refusal that wrote anyway")

    def test_it_REFUSES_a_sealed_block_which_is_what_makes_seal_mean_anything(self):
        """A seal is a declaration that this body is to be held as it stands. Amending under
        one would either break it silently or reissue it in the keeper's name — the first is
        damage, the second is a tool forging a claim. Neither is the tool's to do."""
        self._cap("held as it stands\n", extra=["--seal"])
        h = self._blocks()[0].id
        before = pathlib.Path(self.pile).read_text()
        r = self._amend(h, "quietly changed\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("@sealed:", r.stderr)
        self.assertEqual(pathlib.Path(self.pile).read_text(), before)

    def test_it_NAMES_the_piles_it_checked_and_offers_how_to_widen(self):
        """§3.8 — a check must say what it did not check, and this one goes one better: it
        names the piles it DID check and hands over the flag that widens it. Ruled 2026-08-05
        after the first build only disclosed the limit: a disclosure a reader can act on is
        worth more than one they can only note."""
        self._cap("the target\n")
        target = self._blocks()[0].id
        self._cap("the pointer\n", extra=["--tag", f"ref:#{target}"])
        r = self._amend(target, "x\n")
        self.assertIn("Checked: 1 pile(s)", r.stderr)
        self.assertIn("p.txt", r.stderr)
        self.assertIn("--also", r.stderr)

    def test_also_widens_the_check_to_a_pointer_in_ANOTHER_pile(self):
        """The hole the disclosure was disclosing. A citation living in a different pile was
        silently rewritable; `--also` closes it for the piles you name. Opt-in, because a
        tool that hunted for related piles by itself would be guessing — and a wrong guess
        here is a wrong REFUSAL, which sends you to `push` for a typo."""
        self._cap("the target\n")
        target = self._blocks()[0].id
        other = os.path.join(self.dir, "other.txt")
        subprocess.run(
            [sys.executable, "scribe.py", "capture", "--source", "schnee", "--tag", "topic:t",
             "--tag", f"ref:p.txt#{target}", "--append", other],
            input="a citation living elsewhere\n", capture_output=True, text=True)
        # without --also the amendment goes through: the other pile is not seen
        self.assertEqual(self._amend(target, "rewritten\n").returncode, 0)
        # with it, the pointer is found, named, and located
        r = subprocess.run(
            [sys.executable, "scribe.py", "amend", target, self.pile, "--also", other],
            input="rewritten again\n", capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("REFUSED", r.stderr)
        self.assertIn("other.txt", r.stderr)
        self.assertIn("Checked: 2 pile(s)", r.stderr)

    def test_an_identical_replacement_writes_nothing_and_says_so(self):
        self._cap("unchanged\n")
        h = self._blocks()[0].id
        r = self._amend(h, "unchanged\n")
        self.assertEqual(r.returncode, 0)
        self.assertIn("unchanged", r.stderr)
        self.assertIn("Nothing written", r.stderr)

    def test_an_empty_replacement_is_refused_because_deletion_is_not_this_verb(self):
        self._cap("real content\n")
        h = self._blocks()[0].id
        r = self._amend(h, "\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("deletion", r.stderr)
        self.assertEqual(self._blocks()[0].body, "real content")

    def test_it_reports_the_act_it_performed_not_the_one_capture_performs(self):
        """A small lie caught by running it: the shared findings-reporter said "captured
        block", and the pile did not grow. The verb is passed in."""
        self._cap("before\n")
        h = self._blocks()[0].id
        r = self._amend(h, "after\n")
        self.assertIn("amended block", r.stderr)
        self.assertNotIn("captured block", r.stderr)



class TestTheMovingName(unittest.TestCase):
    """`@name:` — the Forth dictionary ported, 2026-08-05.

    THE TENSION IT ANSWERS, in the sovereign's words: "it would be corralling my living
    impulses into frozen addended crystallized blocks over and over???"

    Before this, saying one thing better meant `push`: a new block, `@replaces:` on it,
    `@superseded:` written BACK onto the old one, and a chain to keep in step. Say it five
    times and the pile holds five crystals and four bookkeeping writes, and has quietly
    become a record of your revisions rather than of what you think.

    gforth has answered this since 1970: define `foo` twice and it prints `redefined foo`
    and moves on. The old definition stays in the dictionary, unmarked and still findable.
    What moved is not the old thing — it is what THE NAME finds. These tests pin that."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.pile = os.path.join(self.dir, "living.txt")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _say(self, body, name="coupling-law"):
        return subprocess.run(
            [sys.executable, "scribe.py", "capture", "--source", "schnee",
             "--name", name, "--tag", "topic:law", "--append", self.pile],
            input=body, capture_output=True, text=True)

    def _blocks(self):
        return [b for b in scribe.parse_pile(pathlib.Path(self.pile).read_text()) if b.id]

    def test_saying_it_again_MARKS_NOTHING_and_appends_no_bookkeeping(self):
        """THE LOAD-BEARING TEST OF THE WHOLE MECHANISM. Three sayings of one thing produce
        three blocks and NOTHING else: no @superseded:, no @replaces:, no chain, no counter,
        no trace of the act of revising. The pile records what you think, not the history of
        your getting there — which is what restic is for (§3.1, the second doorway)."""
        for body in ("first try\n", "said better\n", "said better still\n"):
            self._say(body)
        blocks = self._blocks()
        self.assertEqual(len(blocks), 3)
        for b in blocks:
            keys = [k for k, _ in b.tags]
            self.assertNotIn(scribe.SUPERSEDED_KEY, keys, "a mark was written back")
            self.assertNotIn(scribe.REPLACES_KEY, keys, "a chain link was written")
        # and the earlier blocks are byte-for-byte what they were
        self.assertEqual(blocks[0].body, "first try")
        self.assertEqual(blocks[1].body, "said better")

    def test_redefinition_is_ANNOUNCED_at_the_moment_of_the_act(self):
        """The placement is the whole of its value, and it is gforth's. A redefinition
        learned about next week is one you have already built on — so it is said in the
        stream you are already reading, unprompted, on the capture that causes it. The first
        capture of a name says nothing, because nothing happened."""
        first = self._say("first try\n")
        self.assertNotIn("redefined", first.stderr)
        second = self._say("said better\n")
        self.assertIn("redefined coupling-law", second.stderr)
        self.assertIn("UNTOUCHED", second.stderr)
        self.assertIn("nothing is owed", second.stderr)

    def test_the_name_finds_the_newest_and_the_rest_still_resolve(self):
        """The dictionary's rule: a name resolves to its most recently ADMITTED definition,
        and the shadowed ones are still there — not deleted, not marked, still executable by
        anything that already holds them. Here: still resolvable by handle."""
        for body in ("first try\n", "said better\n", "said better still\n"):
            self._say(body)
        blocks = self._blocks()
        self.assertEqual(scribe.recall(blocks, "coupling-law").body, "said better still")
        self.assertEqual(len(scribe.definitions_of(blocks, "coupling-law")), 3)
        for b in blocks:
            self.assertIs(scribe.resolve_handle(blocks, b.id), b)

    def test_ARRIVAL_ORDER_decides_the_live_one_NOT_the_timestamp(self):
        """A `--ts` can be pinned or backdated — both are shipped, supported acts. Sorting
        definitions by timestamp would let a backdated capture silently become the live
        definition of a name, which is a thing happening to your pile that you did not ask
        for. The pile is append-only and its order is a FACT about what happened; a stated
        moment is a CLAIM. Where they disagree, the name follows the pile."""
        self._say("said now\n")
        subprocess.run(
            [sys.executable, "scribe.py", "capture", "--source", "schnee",
             "--name", "coupling-law", "--ts", "2020-01-01T00:00:00.000000",
             "--tag", "topic:law", "--append", self.pile],
            input="backdated, but admitted second\n", capture_output=True, text=True)
        self.assertEqual(scribe.recall(self._blocks(), "coupling-law").body,
                         "backdated, but admitted second")

    def test_redefinitions_are_DERIVED_and_never_written_back(self):
        """The identical contract `backlinks` has held since v1.1.2, for the identical
        stated reason. A pile that recorded its own redefinitions would be maintaining a
        chain, and maintaining a chain is the paperwork this exists to abolish. Pinned by
        comparing the file before and after asking the question."""
        for body in ("first try\n", "said better\n"):
            self._say(body)
        before = pathlib.Path(self.pile).read_text()
        rep = scribe.redefinitions(self._blocks())
        self.assertEqual(list(rep), ["coupling-law"])
        self.assertEqual(len(rep["coupling-law"]), 2)
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            scribe.main(["names", self.pile])
        self.assertEqual(pathlib.Path(self.pile).read_text(), before,
                         "asking the question changed the pile")

    def test_recall_SAYS_WHAT_IT_DID_NOT_SHOW(self):
        """§3.8 as amended. Handing back the live definition in silence would make a name
        look as though it had only ever had one — an instrument reporting its blindness as
        an observation. It names the count and the handles it withheld."""
        import contextlib, io
        for body in ("first try\n", "said better\n"):
            self._say(body)
        buf, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            scribe.main(["recall", "coupling-law", self.pile])
        self.assertIn("NOT SHOWN", err.getvalue())
        self.assertIn("1 earlier definition", err.getvalue())
        self.assertIn("said better", buf.getvalue())
        self.assertNotIn("first try", buf.getvalue())

    def test_push_still_writes_its_mark_because_that_is_a_DIFFERENT_ACT(self):
        """WHAT THIS DOES NOT REPLACE, pinned so the next reader does not tidy `push` away.
        Sometimes the supersession IS the saying, and you want the reader who wanders into
        the outdated block to be told IN THE FILE, with the tool off (§4.3) — a property the
        gForth build cannot have at all. The change is that `push` is no longer the ONLY way
        to say a thing again. Four acts; choosing between them is the keeper's."""
        src = pathlib.Path(scribe.__file__).read_text()
        self.assertIn("SUPERSEDED_KEY", src)
        self.assertIn(f'"{scribe.SUPERSEDED_KEY}"', src)
        # and a name never triggers it
        for body in ("first try\n", "said better\n"):
            self._say(body)
        text = pathlib.Path(self.pile).read_text()
        self.assertNotIn("@superseded:", text)



class TestDuplicatesAudit(unittest.TestCase):
    """PHASE 3 — declare, never re-mint. Re-minting existing duplicates would change ids
    that relational tags already point at: breaking the pointer graph to fix a naming
    problem. Reports; changes nothing (§3.5)."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.pile = os.path.join(self.dir, "dupes.txt")
        pathlib.Path(self.pile).write_text(DUPE_PILE)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_audit_reports_and_changes_nothing(self):
        before = pathlib.Path(self.pile).read_text()
        r = subprocess.run([sys.executable, "scribe.py", "duplicates", self.pile],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, scribe.EXIT_FINDINGS)
        self.assertIn("#a8eb", r.stdout)
        self.assertIn("2 blocks", r.stdout)
        # WAS `assertIn("legacy", ...)` for a pile with no @genesis: line. That assertion
        # ENCODED the stale assumption and is why nothing caught the inversion — the test
        # and the code agreed with each other and both were wrong. It now asserts the fact
        # (the line is absent) without the judgement (that this makes the pile old).
        self.assertIn("no @genesis: line", r.stdout)
        self.assertNotIn("legacy", r.stdout)
        self.assertEqual(pathlib.Path(self.pile).read_text(), before)

    def test_clean_pile_reports_none(self):
        clean = os.path.join(self.dir, "clean.txt")
        pathlib.Path(clean).write_text(
            "@@ #a1 2026-08-01T10:00 @topic:x @source:s\none\n")
        r = subprocess.run([sys.executable, "scribe.py", "duplicates", clean],
                           capture_output=True, text=True)
        self.assertIn("no duplicated handles", r.stdout)


class TestIdentityKindGuards(unittest.TestCase):
    """THE GUARD-SET FOR THE PROPOSED §3.16, and the reason it is not a prose guard.

    §3.15 warns that a law nobody can test erodes. You never test a law's metaphysics —
    §3.13 is not testable "as written" either; its drift-guard is its test, and that
    pairing (prose law + named guard) is how candidates 1 and 4 were ratified. What is
    testable is the DUTIES the clause imposes on observable surfaces. Four fall straight
    out of the clause's own sentences, and this class is all four."""

    # `none` added 2026-08-05 with `gen_seal`: an issuing site whose honest declaration is
    # that what it issues is NOT an identity. The lint's duty is that no site inherits a kind
    # by default, and "none, and here is why" satisfies that duty exactly. Its absence from
    # this set is part of how `@mint:` came to be both an identity and an integrity check —
    # there was no way to declare a digest that names nothing, so it was declared an identity.
    LEGAL = ("nominal", "structural", "handle", "none")

    # ---- GUARD 1: the kind-declaration lint ------------------------------------------
    def test_guard1_every_issuing_site_declares_its_kind(self):
        """B's first duty: 'the choice is a ruling to be made, not a default to be
        inherited.' Every site that issues identifiers carries a declared kind, in band.

        This is NOT a registry and does not violate the companion clause's refusal of one:
        it is a per-site, in-band declaration — Unison's 'syntax to declare which kind you
        mean' (`docs/data-types.markdown:7-12`) made a lintable duty. Nothing central holds
        a list of permitted identities; each site simply says what it is.

        The lint is aimed at history: it is what would have caught `gen_id` — an issuing
        site that declared nothing, inherited the structural default, and shipped."""
        import ast
        tree = ast.parse(pathlib.Path(scribe.__file__).read_text())
        issuers = [n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name.startswith("gen_")]
        self.assertTrue(issuers, "no issuing sites found — the lint is blind")
        for fn in issuers:
            doc = ast.get_docstring(fn) or ""
            found = re.search(r"@identity:([a-z-]+)", doc)
            self.assertIsNotNone(
                found, f"{fn.name}() issues an identifier and declares no @identity: kind")
            self.assertIn(found.group(1), self.LEGAL,
                          f"{fn.name}() declares an illegal kind {found.group(1)!r}")

    def test_guard1_module_kind_is_declared_and_legal(self):
        self.assertIn(scribe.IDENTITY_KIND, scribe.IDENTITY_KINDS)

    # ---- GUARD 2: the signature test per kind -----------------------------------------
    def test_guard2_signature_test_matches_the_declared_kind(self):
        """The elegant half: the ruling itself dictates which test the tool must carry.

            nominal    -> the TWINS test: two identical contents, declared twice, yield
                          two DISTINCT identities.
            structural -> the DEDUP test: identical content yields the IDENTICAL identity.

        A tool declaring `nominal` while passing the dedup test IS the scribe bug, and here
        it is a failing assertion rather than a silent wrong answer. The declaration says
        what was ruled; this proves the code enacts it; disagreement is the drift.

        The surface is CAPTURE, not the pure function — `gen_handle` is deterministic given
        its arguments (and must be, for testability). What makes scribe nominal is that the
        pile REFUSES to reissue a handle it has already issued, so two declarings cannot end
        up as one. Testing the function alone would pass a structural tool and prove
        nothing."""
        d = tempfile.mkdtemp()
        try:
            pile = os.path.join(d, "twins.txt")
            for _ in range(2):
                subprocess.run(
                    [sys.executable, "scribe.py", "capture", "--source", "claude",
                     "--ts", "2026-08-01T10:00", "--tag", "topic:x", "--append", pile],
                    input="agreed\n", capture_output=True, text=True)
            blocks = [b for b in scribe.parse_pile(pathlib.Path(pile).read_text()) if b.id]
            ids = [b.id for b in blocks]
            self.assertEqual(len(ids), 2)
            if scribe.IDENTITY_KIND == "nominal":
                self.assertEqual(len(set(ids)), 2,
                                 "declares nominal but passes the DEDUP test — the drift")
            else:
                self.assertEqual(len(set(ids)), 1,
                                 "declares structural but passes the TWINS test — the drift")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    # ---- GUARD 3: the whole-identity check --------------------------------------------
    def test_guard3_the_abbreviation_is_CHECKED_and_ambiguity_refuses(self):
        """REWRITTEN 2026-08-05, and the rewrite is the clause holding while its mechanism
        changed underneath.

        This used to assert `truncate for filing, never for identity` STRUCTURALLY: a whole
        64-hex identity exists, the handle is a prefix of it, the prefix is shorter. That
        shape is gone — there is no long form any more, because the long form was doing
        integrity's job under identity's name.

        What §3.16 actually requires survives intact, and it is the OTHER half of its own
        sentence: an abbreviation must be CHECKED, never assumed. Knuth's WEB rule. So the
        assertable duties are (a) the issuer refuses to reuse a name the pile already holds,
        and (b) the resolver refuses ambiguity rather than guessing. Both are what the
        2026-08-01 defect actually broke; neither depended on there being a longer form.

        The guard that WOULD have been lost is added back as its own test — that identity
        does not depend on the body — which is the duty this change introduced."""
        # (a) the issuer checks, at issue time
        ts = "2026-01-01T00:00:00.123456"
        first = scribe.gen_handle(ts)
        self.assertNotEqual(scribe.gen_handle(ts, taken={first}), first,
                            "the abbreviation was assumed, not checked")
        # (b) the resolver refuses ambiguity rather than guessing
        dupes = scribe.parse_pile(DUPE_PILE)
        with self.assertRaises(scribe.AmbiguousHandle):
            scribe.resolve_handle(dupes, "a8eb")

    # ---- GUARD 4: the unitemised-placeholder guard -------------------------------------
    #
    # Specs known to carry an UNRULED identity placeholder. Named, never silently exempted
    # (§3.8): PHASE-0-RECON-AND-PROPOSAL.md:141 wrote the id as `#<id>` and the ruling
    # request at :288 asked only about the delimiter and the tags — so the id was never
    # ruled on and shipped anyway. That file is the encounter that earned this guard and is
    # a closed historical record; it is listed rather than edited. Adding to this list is a
    # visible, reviewable act, which is the whole point of it being a list.
    # Each entry carries its REASON. A silent exemption would make the lint read as
    # coverage it does not have, which is the failure the lint exists to catch.
    KNOWN_UNRULED = {
        "PHASE-0-RECON-AND-PROPOSAL.md":
            "the encounter that earned this guard — `#<id>` at :141 was unitemised and the "
            "ruling request at :288 covered only the delimiter and tags, so the id shipped "
            "unruled. A closed historical record: listed, never edited.",
        "BRIEF-scribe-identity-mint-and-handle.md":
            "quotes the historical `#<id>` at :181 while DESCRIBING the gap; it does not "
            "introduce a live field. It is also the document that carries the ruling.",
    }
    PLACEHOLDER_RE = re.compile(r"[#<]<(id|uuid|guid|key|hash|handle)>")
    # Deliberately narrow: an explicit kind declaration, NOT the word "ruled". The historical
    # spec says "Nothing is built until these are ruled" and still shipped an unruled id —
    # a marker loose enough to match that sentence would have let the very case through.
    RULING_MARKER_RE = re.compile(r"@identity:(nominal|structural|handle)\b")

    def test_guard4_no_spec_introduces_an_unruled_identity_placeholder(self):
        """Closed at the door it used. A document that introduces an identity-shaped
        placeholder must ALSO declare a kind somewhere in itself; otherwise the field ships
        unruled, and an unruled default is indistinguishable from law once it is in the
        artifact. Per-file, in-band — not a registry."""
        offenders = []
        for md in sorted(pathlib.Path(scribe.__file__).parent.glob("*.md")):
            if md.name in self.KNOWN_UNRULED:
                continue
            text = md.read_text(errors="replace")
            if not self.PLACEHOLDER_RE.search(text):
                continue
            if self.RULING_MARKER_RE.search(text):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if self.PLACEHOLDER_RE.search(line):
                    offenders.append(f"{md.name}:{i}: {line.strip()[:70]}")
        self.assertEqual(offenders, [], "identity placeholder in a doc that declares no "
                         "@identity: kind:\n" + "\n".join(offenders))

    def test_guard4_exemptions_are_named_with_reasons(self):
        """§3.8 applied to the lint itself: an exemption without a reason is a silent one."""
        for name, reason in self.KNOWN_UNRULED.items():
            self.assertTrue(reason.strip(), f"{name} is exempted with no reason given")

    def test_guard4_the_guard_is_not_blind(self):
        """A lint that can never fire is worse than none — it reads as coverage. Prove the
        pattern actually catches the historical specimen it was built from."""
        spec = pathlib.Path(scribe.__file__).parent / "PHASE-0-RECON-AND-PROPOSAL.md"
        if not spec.exists():
            # See test_handle_floor_matches_the_ruled_spec for the full reasoning. A lint
            # that can never fire reads as coverage; a test proving it can fire, which
            # itself silently no-ops, is the same defect one layer up.
            raise unittest.SkipTest(
                f"CHECK NOT RUN — {spec.name} is not present in this tree (withheld "
                f"development history; EXPECTED in a published clone, not a failure). The "
                f"guard-is-not-blind proof did NOT run: nothing here has demonstrated that "
                f"the placeholder pattern still catches the historical specimen it was "
                f"built from. Run it in the development repository.")
        self.assertTrue(self.PLACEHOLDER_RE.search(spec.read_text()),
                        "the guard no longer detects the case that earned it")


def _run_cmd(argv):
    """Run scribe's own main() in-process, swallowing its stderr disclosure."""
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(io.StringIO()):
        return scribe.main(argv)


if __name__ == "__main__":
    unittest.main(verbosity=2)
