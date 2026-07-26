#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Scribe's Workbench — QUARANTINED WORLD-FACING EDGE. Project Namirha.
#
# READ edge/README.md FIRST. This component is NOT part of the frozen core:
#   - It FACES THE WORLD and inherits churn (§4.7) — it can never be frozen.
#   - It is provider-specific and fragile by nature — ChatGPT's DOM changes.
#   - Its dependency (Playwright/Chromium) is heavy and lives ONLY here.
# The frozen pile+tangler (../scribe.py) never imports this and never depends on it.
#
# GATE 3 ruling = B: EXTRACTION-ONLY, fed by saved HTML. There is no live browser drive
# in Scribe. `extract_turns` / `turns_to_blocks` (and the CLI) do pure stdlib DOM slicing:
# read saved ChatGPT HTML, hand each message turn's inner HTML to the FROZEN CORE's
# capture_html (pandoc + MathML-annotation LaTeX recovery + aria-hidden strip + the
# separate loss-auditor). No browser is required or used.
#
# The world-facing controlled-browser discovery was preserved (generalized to a
# non-authenticated URL reader) in
# ../FUTURE-FORK_url-text-reader_playwright-discovery.md — for a separate future fork,
# not for Scribe.
#
# §3.3 / §3.4 GUARD (see FORBIDDEN-PATTERN-CASESTUDY.md): the edge is a WITNESS. It reads
# the DOM the render was built from and emits INERT TEXT inward. It never scores, ranks,
# steers, or executes captured content — captured text (even the "health-field / logit
# shaping" specimen) is a data string, never code and never a control signal. Processing
# belongs at the edge; only inert text passes inward (§4.8).

import html.parser
import os
import sys

# Import the FROZEN CORE. The edge depends on the core; the core NEVER depends on the edge.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scribe  # noqa: E402

# ChatGPT marks each message turn with this attribute on its container div. This is the
# single provider-specific fact the adapter encodes; when ChatGPT changes it, ONLY this
# adapter breaks (Poverty / isolation — the core and other adapters are untouched).
ROLE_ATTR = "data-message-author-role"


class _TurnSplitter(html.parser.HTMLParser):
    """Slice a page into (role, inner_html) turns by the message-container attribute,
    reconstructing each turn's inner HTML from parser events. Pure stdlib; no browser."""

    def __init__(self, role_attr=ROLE_ATTR):
        super().__init__(convert_charrefs=False)
        self.role_attr = role_attr
        self.turns = []          # list of (role, inner_html)
        self._cap = None         # [role, container_depth, buf] while capturing
        self._depth = 0

    @staticmethod
    def _emit_start(tag, attrs, selfclose=False):
        a = "".join((f' {k}="{v}"' if v is not None else f" {k}") for k, v in attrs)
        return f"<{tag}{a}{'/' if selfclose else ''}>"

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if self._cap is None and self.role_attr in d:
            self._cap = [d[self.role_attr] or "unknown", self._depth, []]
            self._depth += 1
            return
        if self._cap is not None:
            self._cap[2].append(self._emit_start(tag, attrs))
        self._depth += 1

    def handle_startendtag(self, tag, attrs):
        if self._cap is not None:
            self._cap[2].append(self._emit_start(tag, attrs, selfclose=True))

    def handle_endtag(self, tag):
        self._depth -= 1
        if self._cap is not None:
            if self._depth == self._cap[1]:
                self.turns.append((self._cap[0], "".join(self._cap[2])))
                self._cap = None
            else:
                self._cap[2].append(f"</{tag}>")

    def handle_data(self, data):
        if self._cap is not None:
            self._cap[2].append(data)

    def handle_entityref(self, name):
        if self._cap is not None:
            self._cap[2].append(f"&{name};")

    def handle_charref(self, name):
        if self._cap is not None:
            self._cap[2].append(f"&#{name};")


def extract_turns(html_text, role_attr=ROLE_ATTR):
    """Return [(role, inner_html), ...] for each message container in the page."""
    p = _TurnSplitter(role_attr=role_attr)
    p.feed(html_text)
    return p.turns


def turns_to_blocks(html_text, roles=("assistant",), ts=None):
    """DOM -> canonical blocks, via the FROZEN CORE. Each selected turn's inner HTML is
    run through scribe.capture_html (standards-based MathML recovery + fluff strip) and
    scribe.make_block (with the separate loss-auditor). Returns [(Block, findings), ...].
    The edge does provider-specific DOM slicing ONLY; all reduction is the core's."""
    out = []
    for role, frag in extract_turns(html_text):
        if roles and role not in roles:
            continue
        body, annotations = scribe.capture_html(frag)
        block, findings = scribe.make_block(
            body, [("source", "chatgpt"), ("role", role)], "chatgpt",
            ts=ts, annotations=annotations)
        out.append((block, findings))
    return out


# ---------------------------------------------------------------------------
# TRANSPORT — deliberately NOT here.
#
# GATE 3 ruling = B: this edge is EXTRACTION-ONLY, fed by saved HTML. No live browser
# drive lives in Scribe. The world-facing controlled-browser → inert-text discovery was
# preserved, generalized to a non-authenticated URL reader, in
#   ../FUTURE-FORK_url-text-reader_playwright-discovery.md
# for a separate future fork (the boundary-architecture text web reader). Do not
# re-add a live transport to Scribe without a new ruling.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# CLI (extraction only — the safe, provable path)
# ---------------------------------------------------------------------------

def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(
        prog="chatgpt_adapter",
        description="ChatGPT capture edge (extraction). Turns saved ChatGPT HTML into "
                    "canonical pile blocks via the frozen core. World-facing live drive "
                    "is guarded — see edge/README.md.")
    ap.add_argument("html", help="saved ChatGPT page HTML (the live drive is guarded)")
    ap.add_argument("--roles", default="assistant",
                    help="comma list of roles to capture (default: assistant; use "
                         "'user,assistant' for both)")
    ap.add_argument("--append", metavar="PILE", help="append captured blocks to PILE")
    ap.add_argument("--ts", help="override timestamp (testing)")
    args = ap.parse_args(argv)

    with open(args.html, "r", encoding="utf-8") as fh:
        page = fh.read()
    roles = tuple(r.strip() for r in args.roles.split(",") if r.strip())

    n = 0
    for role, frag in extract_turns(page):
        if roles and role not in roles:
            continue
        body, annotations = scribe.capture_html(frag)
        block, findings = scribe.make_block(
            body, [("source", "chatgpt"), ("role", role)], "chatgpt",
            ts=args.ts, annotations=annotations)
        out = scribe.serialize_block(block)
        if args.append:
            with open(args.append, "a", encoding="utf-8") as fh:
                fh.write(("\n\n" if os.path.getsize(args.append) else "") + out + "\n")
        else:
            sys.stdout.write(out + "\n\n")
        n += 1
        sys.stderr.write(f"turn {n}: {role} #{block.id} "
                         f"({len(findings)} loss marker(s))\n")
    sys.stderr.write(f"{n} turn(s) captured\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
