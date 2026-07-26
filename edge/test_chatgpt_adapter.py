#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Tests for the ChatGPT capture edge — EXTRACTION layer only (no browser needed).
# The world-facing transport (fetch_live) is guarded and not tested live here.

import os
import shutil
import unittest

import chatgpt_adapter as cg

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "chatgpt_sample.html")


class TestTurnSplitting(unittest.TestCase):
    def setUp(self):
        with open(FIXTURE, "r", encoding="utf-8") as fh:
            self.html = fh.read()

    def test_splits_into_role_turns(self):
        turns = cg.extract_turns(self.html)
        roles = [r for r, _ in turns]
        self.assertEqual(roles, ["user", "assistant"])

    def test_assistant_inner_html_captured(self):
        turns = dict((r, h) for r, h in cg.extract_turns(self.html))
        # the assistant turn's inner html must carry the code and the annotation
        self.assertIn("language-python", turns["assistant"])
        self.assertIn("application/x-tex", turns["assistant"])
        # ...but NOT the container tag itself (we want inner html)
        self.assertNotIn("data-message-author-role", turns["assistant"])


class TestExtractionOnly(unittest.TestCase):
    def test_no_live_transport_in_scribe_edge(self):
        """GATE 3 ruling B: the edge is extraction-only. No live browser drive lives in
        Scribe (the discovery was preserved for a separate future fork)."""
        self.assertFalse(hasattr(cg, "fetch_live"))


@unittest.skipUnless(shutil.which("pandoc"), "pandoc not on PATH")
class TestDomToCanonical(unittest.TestCase):
    def setUp(self):
        with open(FIXTURE, "r", encoding="utf-8") as fh:
            self.html = fh.read()

    def test_recovers_what_plaintext_paste_loses(self):
        """The whole point of the edge: from the DOM we recover the code fence + language
        and the clean LaTeX (from the MathML annotation) — exactly what the flattened
        plain-text paste destroys."""
        blocks = cg.turns_to_blocks(self.html, roles=("assistant",), ts="2026-03-08T00:00")
        self.assertEqual(len(blocks), 1)
        block, findings = blocks[0]
        body = block.body
        # code fence + language preserved
        self.assertIn("``` python", body)
        self.assertIn("def energy(mass", body)
        # clean LaTeX recovered from the annotation (not the garbled 'E=mc2' html layer)
        self.assertIn("mc^{2}", body.replace(" ", ""))
        # the rejected-pattern LaTeX is captured too — as INERT TEXT, a specimen
        self.assertIn(r"\Phi_{gov}", body)
        # fluff gone
        self.assertNotIn("__telemetry", body)
        self.assertNotIn("katex-html", body)
        # provenance tag applied
        self.assertIn(("source", "chatgpt"), block.tags)
        self.assertIn(("role", "assistant"), block.tags)

    def test_no_math_not_recovered_finding(self):
        """Both annotations (E=mc^2 and the z'=z-... specimen) survive into the body,
        so the auditor raises no math-not-recovered loss."""
        blocks = cg.turns_to_blocks(self.html, roles=("assistant",), ts="2026-03-08T00:00")
        _, findings = blocks[0]
        self.assertFalse(any(f.kind == "math-not-recovered" for f in findings))

    def test_captured_content_is_inert_text(self):
        """§4.8 guard: the captured forbidden-pattern math is a data string in the pile,
        never executed. Serializing the block yields plain pile text, nothing runnable."""
        blocks = cg.turns_to_blocks(self.html, roles=("assistant",), ts="2026-03-08T00:00")
        text = cg.scribe.serialize_block(blocks[0][0])
        self.assertTrue(text.startswith("@@ #"))
        self.assertIsInstance(text, str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
