#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Scribe's Workbench — Project Namirha. Sovereign author: Schnee B. Tabanic.
# Phase 1: the canonical pile + capture-from-handed-input (paste / saved HTML).
#
# Design law (Charter, enforced structurally, not by prose):
#   §4.3  The pile is truth; every view is a disposable derived cache (Phase 2).
#   §3.8  A lossy reduction names its loss IN-BAND; absence never looks like a value.
#   §3.6  Hard-fail / mark loudly over silent degradation.
#   §3.1/§3.3  The tool witnesses and marks; it never silently alters the sovereign's
#         text and never decides for him.
#   §4.6  Poverty: one stdlib-only file; shell out to pandoc only for the HTML path.
#   Candidate 5 (actor/auditor separation): the loss-checker `loss_check()` is a
#         SEPARATE deterministic pass that audits the capturer's OUTPUT. The reducer
#         (`capture_*`) never certifies its own reduction.
#   Candidate 4 (co-location is not derivation): capture EXTRACTS/MARKS; it never
#         fabricates structure it cannot prove, and never claims to derive meaning.
#
# stdlib only. Optional external process: `pandoc` (HTML path only), shelled to.
#
# v1.1.0 — "unfreeze the keys" (the v1.0-frozen record is preserved intact in
# PROVENANCE.md; this is a named new version, not a silent edit — §5.8). Five welds
# to one key were removed and one silent-loss path was closed:
#   - a tag value the format cannot carry is REFUSED on write (§3.6) and ANNOUNCED
#     on read (§3.8); it used to be written by `capture` itself, reported as success,
#     and swallow the block on the next read.
#   - the table of contents takes `--by <key>` and NAMES its axis and its loss (§3.13/§3.8).
#   - `--tag key:value` writes any key; the CLI no longer holds an opinion about which
#     vocabulary is expressible (§3.1 — the vocabulary is the sovereign's).
#   - `@state:` is declared RETIRED and announced wherever met; the undisclosed
#     recency-ordering that was welded to it is removed and every view now states
#     its order (§3.8, order-is-a-value).
#   - `scribe keys` reports what the vocabulary has actually become.

import argparse
import hashlib
import html.parser
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

VERSION = "1.1.0"

# The one external process the HTML path shells to. Recorded for provenance (§4.4); the
# tool discloses the running pandoc via `scribe doctor` and hard-fails if it is absent.
PANDOC_PINNED = "3.1.11.1"

# ---------------------------------------------------------------------------
# The canonical pile format
#
#   @@ #<id> <ISO-timestamp> @key:value [@key:value ...]
#   <body — verbatim canonical text, any number of lines, until the next @@ or EOF>
#
# Line-order is honest to ONE axis only: arrival time. Every other ordering is a
# derived view (Phase 2), never the file's physical order.
# ---------------------------------------------------------------------------

# A block boundary: `@@ ` at column 0. Verified collision-free against the sovereign's
# real material (his separators are rows of '#', never '@@').
HEADER_RE = re.compile(r"^@@ +#(?P<id>\S+) +(?P<ts>\S+)(?P<tags>(?: +@[^\s:]+:[^\s]+)*)\s*$")
TAG_RE = re.compile(r"@(?P<key>[^\s:]+):(?P<val>[^\s]+)")

# The in-band loss marker. Plain-text readable, greppable (`grep scribe:loss`), and
# visibly NOT the sovereign's content. Sits on its own line just above what it marks.
LOSS_PREFIX = "[[scribe:loss"

# The in-band marker for a header line the parser could not read. Same shape and same
# greppability as the loss marker — scribe already obeyed the name-your-loss law on the
# way IN (capture) and not on the way OUT (read/derive). This closes that direction.
MALFORMED_PREFIX = "[[scribe:malformed-header"

# Exit code for "the command ran and completed, AND has findings to disclose". Distinct
# from 1 (the command failed) so a caller can tell a refusal from a loud success.
EXIT_FINDINGS = 2

# Keys RETIRED from the vocabulary, and what replaced each. §3.8: a retired thing must
# never look identical to a live one, so the tool announces one wherever it meets one —
# on write, on read, in a pile. It does not refuse: a retired key is a *classification*,
# not a fault. (Prior art the project already adopted once, for the tag-validator's
# third verdict tier: Debian lintian's classification tag + `Show-Always` — a finding
# formally separate from an error, emitted every time, and therefore countable.)
RETIRED_KEYS = {"state": "aspect"}

# A line that is an INTENDED header but did not parse. Deliberately narrower than
# "starts with @@": a pasted unified-diff hunk (`@@ -1,4 +1,4 @@`) is legitimate body
# text and must not be reported as a broken header, so the id sigil `#` is required.
# NAMED LIMIT (§3.8): a header whose `#` itself is missing or mistyped is NOT caught
# by this check — the write-side refusal below is what covers that case.
INTENDED_HEADER_RE = re.compile(r"^@@ +#\S")


# ---------------------------------------------------------------------------
# The pile stamp — a pile carries its own reading instructions, in-band.
#
# RULED by the sovereign 2026-07-28, for a reason wider than this tool: piles will
# sit on a drive that an AI assistant may be asked to search. Any reader — human or
# model, with or without scribe — must meet the instruction IN THE ARTIFACT rather
# than in someone's config or memory. §5.4 (structural fixes over prompt hacks): an
# instruction living in a skills file can be skipped, and skipped SILENTLY, which is
# the failure mode §3.8 refuses everywhere else. Prior art: Debian's `README.Debian`
# — the package explains its own local deviation to whoever opens it.
#
# WHERE IT SITS: the preamble (before the first `@@`). parse_pile already preserves
# preamble text as a Block with id="" and every count/index already excludes it, so
# the stamp costs the format nothing.
#
# WHEN IT IS WRITTEN: only when `capture --append` CREATES a pile, or when the human
# runs `scribe stamp` by hand. Never added to an existing pile behind his back, and —
# because capture only stamps at birth — deleting it means it stays deleted (§3.1).
#
# WHAT IT MAY NOT SAY. A first draft closed with "the tags are written by this file's
# author." That is a FILE-LEVEL claim about a property the tag vocabulary already
# handles PER BLOCK, and the bench sheet had already ruled the distinction finer than
# the stamp was using it: `@source:` (which mind said it), `@origin:` (human or ai —
# "the axis that lets the pile be split into the human's programme and the AI's
# programme later; cheap to write now, impossible to reconstruct afterwards"), and
# `@attests:` ("who vouches for this, which is not always who wrote it — author and
# guarantor are different jobs"). A pile is a MIXTURE by construction, so one sentence
# at the top cannot be true of all of it, and a reader — human or model — who trusts it
# inherits a false attribution for every block it does not fit. The stamp therefore
# makes no provenance claim at all: it says where provenance lives and that an absent
# tag means UNKNOWN (§3.8 — a missing value and a deliberate one must never look the
# same). Same shape as the fix that closed Frog & The Seed: do not assert a property,
# point at the record; and where there is no record, say so.
# ---------------------------------------------------------------------------

STAMP_MARK = "# This file is a scribe pile"

PILE_STAMP = f"""{STAMP_MARK} — one canonical file, appended in arrival order.
# Read it plainly: a block begins at a line starting `@@ ` in column 0, carrying
# `#<id> <timestamp> @key:value ...`, and runs until the next such line or the end
# of the file. No tool is needed to read this file. A tool is needed to SEARCH it well.
#
# TO SEARCH IT WELL (human or AI assistant):
#   scribe keys   PILE                  the tag keys and values this pile carries
#   scribe toc    PILE [--by KEY]       contents, grouped by any key you name
#   scribe view   key:value PILE        every block carrying that tag, whole
#   scribe blocks PILE                  every block with its whole tag run
# Views compose — `scribe view a:b PILE | scribe view c:d -` is an AND-query.
#
# WHY NOT JUST grep: a grep over this file returns FRAGMENTS. Match inside a body and
# you get a line with no id, no timestamp and no tags; match a header and you get the
# provenance with none of the claim. It never hands back a whole record. If you must
# grep, read back up to the nearest `@@ ` line before quoting anything from here.
#
# PROVENANCE IS PER BLOCK, NEVER PER FILE. A pile is a mixture by construction: the
# human's own writing, material handed in from elsewhere, and blocks an AI wrote. Do
# not attribute anything here to "the author of this file" — there is no such person.
# Read it off the block's own tags, and say when they are absent rather than guessing:
#   @source:  which mind said it        @origin:  human or ai — which kind made it
#   @attests: who vouches for it, which is NOT always who wrote it
# Untagged means unknown, not mine and not anyone's. (scribe {VERSION})
"""


def is_stamped(text):
    return text.lstrip().startswith(STAMP_MARK)


class TagRefused(ValueError):
    """A tag the pile format cannot carry. Raised on the WRITE side only."""


def validate_tag(key, value):
    """Refuse to write a tag that would produce a header the parser cannot read; return
    a list of non-blocking NOTES to disclose.

    §3.14 — the licence and the encounter, cited beside the check.

    Licensed by §3.6 (*"silent failure is treated as the cardinal engineering sin"*)
    and §7's checklist question *can anything fail silently without announcing it?*
    The encounter that earned it, reproduced on the live machine 2026-07-28 against
    the shipped v1.0.0 — through the sanctioned front door, not by hand-editing:

        $ scribe capture --topic "two words" --append pile.txt
        captured block #ac42                       <- reported success, exit 0
        $ scribe blocks pile.txt
        2 block(s)                                 <- three were captured; #ac42 gone

    The space made HEADER_RE fail, so the header line was absorbed into the PREVIOUS
    block's body: the pile silently got shorter, and a dropped block and a short pile
    are indistinguishable. `capture` never re-parsed what it wrote.

    Refusals here are the write half. The read half is scan_malformed_headers().
    """
    notes = []
    if not key:
        raise TagRefused("empty tag key")
    if not value:
        raise TagRefused(f"empty value for @{key}: — a tag must carry one, and an "
                         f"absent value must be a NAMED value, not an empty one (§3.8)")
    if any(c.isspace() for c in key) or ":" in key:
        raise TagRefused(f"tag key {key!r} contains whitespace or ':' — the header "
                         f"could not be read back")
    if any(c.isspace() for c in value):
        raise TagRefused(
            f"tag value {value!r} for @{key}: contains whitespace. The header would "
            f"not parse and the block would be absorbed into the previous one with no "
            f"error (§3.6). Use hyphens: @{key}:{'-'.join(value.split())}")
    if "," in value:
        notes.append(f"@{key}:{value} contains ',' — the parser reads a comma list, so "
                     f"this will read back as {len(value.split(','))} separate tags")
    if key in RETIRED_KEYS:
        notes.append(f"@{key}: is RETIRED — replaced by @{RETIRED_KEYS[key]}:. Written "
                     f"as asked; nothing was silently substituted")
    return notes


def parse_tag_arg(s):
    """Parse a `--tag key:value` argument (§3.1: the vocabulary is the sovereign's —
    scribe stores whatever key it is given and holds no registry)."""
    if ":" not in s:
        raise TagRefused(f"--tag takes key:value (e.g. --tag act:guards-the-boundary), "
                         f"got {s!r}")
    key, value = s.split(":", 1)
    return key, value


def scan_malformed_headers(text):
    """Find column-0 lines that are intended headers but did not parse.

    `@@` was verified collision-free against the sovereign's real material at GATE 1
    (his separators are rows of '#'), so an `@@ #…` at column 0 is always an intended
    header — there is no legitimate absorbed case. Returns [(lineno, line)], 1-based.
    """
    return [(i, line) for i, line in enumerate(text.split("\n"), 1)
            if INTENDED_HEADER_RE.match(line) and not HEADER_RE.match(line)]


@dataclass
class Block:
    id: str
    ts: str
    tags: list = field(default_factory=list)   # list of (key, value)
    body: str = ""

    def topics(self):
        return [v for (k, v) in self.tags if k == "topic"]

    def get(self, key):
        return [v for (k, v) in self.tags if k == key]


# ---------------------------------------------------------------------------
# Parse / serialize  (round-trip stable — proves the format holds)
# ---------------------------------------------------------------------------

def parse_tags(tagstr):
    """Parse a header tag-run. Accepts BOTH emitted forms so the readability ruling
    is never foreclosed (§5.5):
        @topic:a @topic:b      (repeated key — the ruled default)
        @topic:a,b             (comma list)
    Both normalize to [('topic','a'), ('topic','b')]."""
    tags = []
    for m in TAG_RE.finditer(tagstr or ""):
        key, val = m.group("key"), m.group("val")
        for piece in val.split(","):
            piece = piece.strip()
            if piece:
                tags.append((key, piece))
    return tags


def parse_pile(text):
    """Split pile text into blocks on `@@ ` header lines. Text before the first
    header is preserved as a leading Block with id '' (e.g. a human preamble) so the
    tool-off-readable invariant holds: nothing in the file is discarded on a round trip."""
    lines = text.split("\n")
    blocks = []
    cur = None
    cur_body = []
    preamble = []

    def _finalize():
        # Set the current block's body from its buffered lines before it is stored.
        # (Doing this ONLY at EOF was a real bug: every block but the last lost its body.)
        if cur is not None:
            cur.body = "\n".join(cur_body).strip("\n")
            blocks.append(cur)

    for line in lines:
        m = HEADER_RE.match(line)
        if m:
            if cur is not None:
                _finalize()
            elif preamble and any(p.strip() for p in preamble):
                blocks.append(Block(id="", ts="", tags=[],
                                    body="\n".join(preamble).rstrip("\n")))
            preamble = []
            cur = Block(id=m.group("id"), ts=m.group("ts"),
                        tags=parse_tags(m.group("tags")), body="")
            cur_body = []
        elif cur is not None:
            cur_body.append(line)
        else:
            preamble.append(line)

    if cur is not None:
        _finalize()
    elif preamble and any(p.strip() for p in preamble):
        blocks.append(Block(id="", ts="", tags=[], body="\n".join(preamble).rstrip("\n")))
    return blocks


def serialize_block(b, tag_form="repeated"):
    """Render a block to pile text. Default tag_form 'repeated' is the sovereign's
    ruling; 'comma' is accepted too. Preamble blocks (id == '') render body only."""
    if not b.id:
        return b.body
    if tag_form == "comma":
        by_key = {}
        order = []
        for k, v in b.tags:
            if k not in by_key:
                by_key[k] = []
                order.append(k)
            by_key[k].append(v)
        tagstr = "".join(f" @{k}:{','.join(by_key[k])}" for k in order)
    else:
        tagstr = "".join(f" @{k}:{v}" for k, v in b.tags)
    header = f"@@ #{b.id} {b.ts}{tagstr}"
    return f"{header}\n{b.body}" if b.body else header


def serialize_pile(blocks, tag_form="repeated"):
    return "\n\n".join(serialize_block(b, tag_form) for b in blocks) + "\n"


# ---------------------------------------------------------------------------
# ID + timestamp
# ---------------------------------------------------------------------------

def now_ts():
    return datetime.now().isoformat(timespec="minutes")


def gen_id(ts, body, source, taken=None):
    """Short, stable, content-derived id (deterministic → testable). Extends length
    on the rare collision within a pile rather than silently overwriting (§3.8)."""
    taken = taken or set()
    h = hashlib.sha256(f"{ts}\x00{source}\x00{body}".encode("utf-8")).hexdigest()
    for n in range(4, len(h)):
        cand = h[:n]
        if cand not in taken:
            return cand
    return h


# ---------------------------------------------------------------------------
# Capture — the reducer.  Produces canonical text. Does NOT audit itself.
# ---------------------------------------------------------------------------

def capture_plaintext(text):
    """Plain-text paste: the body IS the paste, verbatim. We never silently alter the
    sovereign's text (§3.1/§3.3). A plain-text paste carries no CSS/HTML to strip; its
    only fluff is content the human owns. Structural loss (e.g. flattened code fences)
    is NOT repaired here — it is MARKED by the separate auditor."""
    return text.strip("\n")


class _TexAnnotationExtractor(html.parser.HTMLParser):
    """Pull the canonical LaTeX out of MathML <annotation encoding="application/x-tex">
    nodes — the standards-based math-recovery path (§4.1). Reads the source the render
    was built from, not the rendered soup."""
    def __init__(self):
        super().__init__()
        self._in = False
        self.tex = []
        self._buf = []

    def handle_starttag(self, tag, attrs):
        if tag == "annotation" and dict(attrs).get("encoding") == "application/x-tex":
            self._in = True
            self._buf = []

    def handle_data(self, data):
        if self._in:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag == "annotation" and self._in:
            self._in = False
            self.tex.append("".join(self._buf).strip())


def extract_tex_annotations(html_text):
    p = _TexAnnotationExtractor()
    try:
        p.feed(html_text)
    except Exception:
        pass
    return [t for t in p.tex if t]


class _AriaHiddenStripper(html.parser.HTMLParser):
    """Drop subtrees marked aria-hidden="true". These are the render's *visual*
    duplicate layers (e.g. KaTeX emits a garbled `E=mc2` span next to the canonical
    MathML). Screen readers ignore them; so must a faithful reduction. This is the
    accessibility-tree-faithful move the pre-brief cited — target the semantic node,
    discard the visual echo. Prevents the doubled/garbled math the plain-text paste
    is infamous for (the ChatGPT specimen)."""
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.out = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if self._skip_depth:
            self._skip_depth += 1
            return
        if dict(attrs).get("aria-hidden") == "true":
            self._skip_depth = 1
            return
        self.out.append(self.get_starttag_text() or "")

    def handle_startendtag(self, tag, attrs):
        if not self._skip_depth:
            self.out.append(self.get_starttag_text() or "")

    def handle_endtag(self, tag):
        if self._skip_depth:
            self._skip_depth -= 1
            return
        self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if not self._skip_depth:
            self.out.append(data)

    def handle_entityref(self, name):
        if not self._skip_depth:
            self.out.append(f"&{name};")

    def handle_charref(self, name):
        if not self._skip_depth:
            self.out.append(f"&#{name};")


def strip_aria_hidden(html_text):
    p = _AriaHiddenStripper()
    p.feed(html_text)
    return "".join(p.out)


def capture_html(html_text):
    """Saved-HTML path: shell to pandoc for structure + math + fluff removal (§4.6
    loose coupling). Returns (markdown_body, annotation_tex_list). Hard-fails loudly if
    pandoc is absent rather than silently degrading to soup-scraping (§3.6).

    Two pre/post choices that matter for faithfulness:
    - aria-hidden subtrees are stripped first (kills the KaTeX visual-duplicate that
      produces garbled/doubled math);
    - pandoc target is `gfm` (GitHub Markdown), which drops HTML class wrappers pandoc's
      own markdown would keep as `[...]{.katex}` / `::: {.prose}` noise."""
    if not shutil.which("pandoc"):
        raise RuntimeError(
            "HTML capture needs pandoc, which is not on PATH. Refusing to silently "
            "fall back to lossy soup-scraping (§3.6). Install/vendor pandoc, or use the "
            "plain-text path.")
    annotations = extract_tex_annotations(html_text)
    cleaned = strip_aria_hidden(html_text)
    proc = subprocess.run(
        ["pandoc", "-f", "html", "-t", "gfm-raw_html", "--wrap=none"],
        input=cleaned, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"pandoc failed: {proc.stderr.strip()}")
    return proc.stdout.strip("\n"), annotations


# ---------------------------------------------------------------------------
# loss_check — the AUDITOR.  Separate deterministic pass over capture's OUTPUT.
# Inserts in-band markers; never rewrites the sovereign's content (Candidate 5, §3.8).
# ---------------------------------------------------------------------------

CODE_SIGNAL = re.compile(
    r"::=|"                                   # grammar rule
    r"[{};]\s*$|"                             # C/JSON line ends
    r"^\s*(def|class|return|import|#include|float|int|void|struct|for|while|if|else)\b|"
    r"^\s*[\w.]+\s*=\s*[^=].*[;{}()\[\]]|"    # assignment with code punctuation
    r"->|=>|\bnew\b"
)

def _looks_like_code(line):
    return bool(line.strip()) and bool(CODE_SIGNAL.search(line))


def _fenced_regions(lines):
    """Indices already inside ``` fences — never flag those."""
    inside = set()
    fence = False
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("```"):
            fence = not fence
            inside.add(i)
            continue
        if fence:
            inside.add(i)
    return inside


@dataclass
class LossFinding:
    line: int      # 1-based line in the body where the marker was placed
    kind: str
    note: str


def loss_check(body, annotations=None):
    """Audit capture output. Returns (annotated_body, findings). Every finding is a
    CONTESTABLE claim (§3.7): a suggestion the sovereign may act on or delete, never a
    silent edit and never a fabrication (§3.1/§3.3/Candidate 4)."""
    lines = body.split("\n")
    fenced = _fenced_regions(lines)
    findings = []
    insert_before = {}   # line index -> list of marker strings

    def mark(idx, kind, note):
        findings.append(LossFinding(idx + 1, kind, note))
        insert_before.setdefault(idx, []).append(f"{LOSS_PREFIX} {kind} — {note}]]")

    # (1) Flattened code: a run of >=3 consecutive code-ish lines, not already fenced.
    #     Conservative on purpose so single shell commands in prose are not flagged.
    i = 0
    while i < len(lines):
        if i in fenced or not _looks_like_code(lines[i]):
            i += 1
            continue
        j = i
        while j < len(lines) and j not in fenced and (_looks_like_code(lines[j]) or not lines[j].strip()):
            j += 1
        run = [k for k in range(i, j) if lines[k].strip()]
        if len(run) >= 3:
            mark(run[0], "flattened-code",
                 "possible code block whose triple-backtick fences were lost in a paste; "
                 "re-fence by hand if so, otherwise delete this marker")
        i = j + 1 if j > i else i + 1

    # (2) Broken math — RELIABLE structural-imbalance signals ONLY. A single '$' is too
    #     ambiguous (shell $VAR, prices like $5) to guess on: per §3.6 an honest silence
    #     beats a false signal, so we do NOT flag single-'$' parity. We flag only
    #     unmistakable unclosed delimiters.
    whole = "\n".join(ln for k, ln in enumerate(lines) if k not in fenced)

    def _first_line_with(substr, pat=False):
        for idx, ln in enumerate(lines):
            if idx in fenced:
                continue
            if (re.search(substr, ln) if pat else substr in ln):
                return idx
        return len(lines) - 1

    if whole.count("$$") % 2 == 1:
        mark(_first_line_with("$$"), "broken-math",
             "unclosed '$$' display-math delimiter — original LaTeX may be truncated")
    if whole.count(r"\[") != whole.count(r"\]"):
        mark(_first_line_with(r"\\\[", pat=True), "broken-math",
             r"unmatched \[ \] display-math delimiters")
    begins, ends = Counter(re.findall(r"\\begin\{(\w+\*?)\}", whole)), \
        Counter(re.findall(r"\\end\{(\w+\*?)\}", whole))
    for env in set(begins) | set(ends):
        if begins[env] != ends[env]:
            mark(_first_line_with(r"\\(begin|end)\{" + re.escape(env) + r"\}", pat=True),
                 "broken-math", f"unbalanced \\begin/\\end for '{env}' environment")

    # (3) The two known Markdown break-points (name, do not fix).
    for idx, ln in enumerate(lines):
        if idx in fenced:
            continue
        if re.match(r"^\s+", ln) and ("$$" in ln) and re.match(r"^\s+([-*+]|\d+\.)\s", ln):
            mark(idx, "nested-list-math",
                 "display math inside a nested list — Markdown indentation may break the "
                 "delimiters; verify rendering")
        if ln.count("|") >= 2 and re.search(r"\\begin\{(matrix|array|aligned?)\}", ln):
            mark(idx, "table-cell-latex",
                 "matrix/array LaTeX inside a table cell — internal newlines break the "
                 "cell; verify")

    # (4) If we came from HTML with MathML annotations, verify math actually SURVIVED.
    #     We compare COUNTS, not exact strings: pandoc re-normalizes LaTeX (mc^2 ->
    #     mc^{2}, z' -> z^{\prime}) so exact-match false-fires; a shortfall in the number
    #     of recovered math spans, however, is a genuine drop worth naming (§3.8).
    if annotations:
        inline = re.findall(r"(?<!\$)\$(?!\$)[^$\n]+?\$(?!\$)", whole)
        display = re.findall(r"\$\$[^$]+?\$\$", whole)
        recovered = len(inline) + len(display)
        if recovered < len(annotations):
            mark(len(lines) - 1, "math-not-recovered",
                 f"{len(annotations)} MathML annotation(s) in source but only {recovered} "
                 f"math span(s) recovered — some LaTeX did not survive")

    if not insert_before:
        return body, findings

    out = []
    for idx, ln in enumerate(lines):
        for marker in insert_before.get(idx, []):
            out.append(marker)
        out.append(ln)
    return "\n".join(out), findings


# ---------------------------------------------------------------------------
# make_block — wire capture -> auditor -> canonical block
# ---------------------------------------------------------------------------

def make_block(raw_body, tags, source, ts=None, annotations=None):
    ts = ts or now_ts()
    audited_body, findings = loss_check(raw_body, annotations=annotations)
    bid = gen_id(ts, audited_body, source)
    return Block(id=bid, ts=ts, tags=tags, body=audited_body), findings


# ---------------------------------------------------------------------------
# Phase 2 — the view-stripper / tangler.
#
# Every view is a DERIVED, disposable projection of the pile (§4.3). The pile is
# never moved or mutated to produce a view. A block with several tags appears in
# several views WITHOUT being duplicated in the pile — adjacency stops carrying
# meaning (the resolution of Problem B). Views EXTRACT and FILTER; they never derive
# meaning (Candidate 4). Working views carry the block's `@@ #id` header as an
# honest back-link so a thought developed in a view can be pushed home by id.
# ---------------------------------------------------------------------------

def select_blocks(blocks, key, value):
    """All real blocks carrying the tag key:value, in pile (arrival) order."""
    return [b for b in blocks if b.id and (key, value) in b.tags]


def block_title(b, width=66):
    """First non-empty body line, minus any leading Markdown heading marker and any
    loss-marker line — a derived label for the TOC. Extraction, not interpretation."""
    for ln in b.body.split("\n"):
        s = ln.strip()
        if not s or s.startswith(LOSS_PREFIX):
            continue
        s = re.sub(r"^#+\s*", "", s)
        return s if len(s) <= width else s[: width - 1] + "…"
    return "(empty)"


def order_blocks(blocks, recent=False):
    """Arrival order by default; most-recent-first for the salience/desktop view.
    Stable: ties keep pile order (Python sort is stable)."""
    if recent:
        return sorted(blocks, key=lambda b: b.ts, reverse=True)
    return list(blocks)


def render_view(blocks, key, value, recent=False, tag_form="repeated"):
    """A working view: the matching blocks, each with its `@@ #id` header (the
    back-link), ready to read, edit, and `push` home. It IS a mini-pile."""
    chosen = order_blocks(select_blocks(blocks, key, value), recent=recent)
    header = f"# view {key}:{value}" + ("  (most-recent first)" if recent else "")
    note = ("# derived view — disposable. Edit a body and `scribe push` it home by #id.\n"
            "# the pile is the truth; regenerate this any time.")
    body = "\n\n".join(serialize_block(b, tag_form) for b in chosen)
    return f"{header}\n{note}\n\n{body}\n", chosen


def render_toc(blocks, key="topic"):
    """Regenerated table of contents (§4.3): blocks grouped by ONE chosen key, derived
    from the tags — never hand-kept. Replaces the sovereign's hand-maintained top list.

    The axis is CHOOSEABLE and NAMED. Two laws licence the change (§3.14):

    §3.13 — deriving a **non-governing** view from the canonical source is the earned
      half of that split; a table of contents governs nothing. Until v1.1.0 this was
      the one ordering in a tool whose founding law is *arrival is the only physical
      ordering, every other ordering is derived* that could not be chosen — which
      quietly made `@topic:` load-bearing whatever any bench sheet said.

    §3.8 — an index that reads one key is lossy BY CONSTRUCTION, so it states its axis
      and lists the keys present in the pile that it does not show. Those lines are
      emitted ALWAYS, including when there is nothing to report, so that "this index
      saw everything" and "this index dropped things" can never look the same.

    Deliberately NOT done (§3.3): the tool never picks the axis that groups most
    tidily. That would be a measurement taking the wheel. The human names the key,
    every time.
    """
    grouped = {}
    unkeyed = []
    other = Counter()
    n_blocks = 0
    for b in blocks:
        if not b.id:
            continue
        n_blocks += 1
        vals = b.get(key)
        if not vals:
            unkeyed.append(b)
        for v in vals:
            grouped.setdefault(v, []).append(b)
        for k, _ in b.tags:
            if k != key:
                other[k] += 1
    lines = ["# Table of contents (derived — do not hand-edit; run `scribe toc`)",
             f"# grouped by @{key}: — {n_blocks} blocks, {len(grouped)} distinct "
             f"@{key}: values"]
    # The always-emitted loss line (§3.8). Absent findings still get a line.
    if other:
        shown = " ".join(f"@{k}:({n})" for k, n in
                         sorted(other.items(), key=lambda kv: (-kv[1], kv[0])))
        lines.append(f"# NOT shown by this index: {shown}  "
                     f"— re-run with `--by <key>` to see any of them")
    else:
        lines.append("# NOT shown by this index: (no other keys present in this pile)")
    if unkeyed:
        lines.append(f"# {len(unkeyed)} of {n_blocks} blocks carry no @{key}: "
                     f"— listed under (no @{key}:) below")
    else:
        lines.append(f"# every block carries @{key}: — nothing fell out of this index")
    lines.append("")
    for val in sorted(grouped, key=lambda t: (-len(grouped[t]), t)):
        lines.append(f"## {val} ({len(grouped[val])})")
        for b in grouped[val]:
            lines.append(f"   #{b.id}  {block_title(b)}")
        lines.append("")
    if unkeyed:
        lines.append(f"## (no @{key}:) ({len(unkeyed)})")
        for b in unkeyed:
            lines.append(f"   #{b.id}  {block_title(b)}")
        lines.append("")
    return "\n".join(lines)


def render_export(blocks, key, value, recent=False, bare=False):
    """A clean export to paste into the next mind: bodies only, no `@@` headers to
    scroll-and-delete. Back-links survive as an unobtrusive trailing manifest unless
    --bare (§3.7: disclosed, not hidden; but out of the way for the paste target)."""
    chosen = order_blocks(select_blocks(blocks, key, value), recent=recent)
    parts = [b.body for b in chosen]
    out = "\n\n---\n\n".join(parts)
    if not bare and chosen:
        manifest = " ".join(f"#{b.id}" for b in chosen)
        out += f"\n\n<!-- scribe export of {key}:{value} — source blocks: {manifest} -->"
    return out + "\n", chosen


def push_view(view_text, pile_blocks):
    """Push edits made in a working view back into the canonical pile by #id (the
    detangle round-trip). Updates BODY only — deterministic, id-keyed, never fuzzy
    (Candidate 4). Tag/timestamp edits are NOT applied here (do them with `tag` or by
    hand) and any header-tag divergence is DISCLOSED, never silently applied."""
    view_blocks = [b for b in parse_pile(view_text) if b.id]
    by_id = {b.id: b for b in pile_blocks}
    updated, missing, tag_drift = [], [], []
    for vb in view_blocks:
        pb = by_id.get(vb.id)
        if pb is None:
            missing.append(vb.id)
            continue
        if vb.tags and vb.tags != pb.tags:
            tag_drift.append(vb.id)
        if vb.body != pb.body:
            pb.body = vb.body
            updated.append(vb.id)
    return pile_blocks, {"updated": updated, "missing": missing, "tag_drift": tag_drift}


def add_tags(blocks, block_id, add=None, remove=None):
    """Add/remove tags on a block in place, by id. The human can equally hand-edit the
    header line; this is the named-verb convenience (§3.9). Returns (ok, block)."""
    add = add or []
    remove = set(remove or [])
    for b in blocks:
        if b.id == block_id:
            b.tags = [(k, v) for (k, v) in b.tags if f"{k}:{v}" not in remove]
            for (k, v) in add:
                if (k, v) not in b.tags:
                    b.tags.append((k, v))
            return True, b
    return False, None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _read_input(path):
    if path in (None, "-"):
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _announce_malformed(text, where):
    """READ side: announce every unparsed header, always, and carry on.

    The read/write asymmetry is a ruling, not an accident. Refusing to open a pile
    that has one bad line would put the sovereign's own material out of his reach —
    a worse harm than a loud read (§3.1). So a read ANNOUNCES and continues, with a
    non-zero exit so nothing downstream can mistake it for a clean run; a write-back
    REFUSES (see `_refuse_if_malformed`). §3.6 permits a fallback only when declared,
    never assumed — this is the declaration.

    Returns the number of findings.
    """
    bad = scan_malformed_headers(text)
    for n, line in bad:
        sys.stderr.write(f"{MALFORMED_PREFIX} {where}:{n}]] not read as a header — "
                         f"absorbed into the PREVIOUS block's body: "
                         f"{line.strip()[:72]}\n")
    if bad:
        sys.stderr.write(
            f"  {len(bad)} malformed header line(s): any block count reported here is "
            f"SHORT by that many. Usual cause: a space inside a tag value. "
            f"Fix the line(s) above, then re-run.\n")
    return len(bad)


def _refuse_if_malformed(text, where):
    """WRITE-BACK side: refuse to rewrite a pile whose headers do not all parse.

    `tag` and `push` serialize the whole pile back to disk. Doing that over an
    unparsed header would cement a swallowed block into its neighbour's body as
    though it had always been there. Hard-fail instead (§3.6)."""
    bad = scan_malformed_headers(text)
    if bad:
        _announce_malformed(text, where)
        raise SystemExit(f"REFUSED: will not rewrite {where} while {len(bad)} header "
                         f"line(s) do not parse — a rewrite would make the loss "
                         f"permanent. Fix the line(s) above first.")


def _announce_retired_keys(blocks, where):
    """Announce any RETIRED key found in a pile (§3.8: a retired thing must not look
    identical to a live one). A classification, never a fault: it does not block and
    does not change the exit code."""
    found = Counter(k for b in blocks for k, _ in b.tags if k in RETIRED_KEYS)
    for k, n in sorted(found.items()):
        sys.stderr.write(f"  NOTE: {where} carries the RETIRED key @{k}: on {n} tag(s)"
                         f" — replaced by @{RETIRED_KEYS[k]}:\n")


def _emit_tag_notes(notes):
    for n in notes:
        sys.stderr.write(f"  NOTE: {n}\n")


def _collect_tags(args):
    """Build the tag list for capture/tag from the specific flags AND the generic
    `--tag key:value`, then validate every one before anything is written (§3.6).
    Raises TagRefused; returns (tags, notes)."""
    tags = []
    for t in (getattr(args, "topic", None) or []):
        tags.append(("topic", t))
    if getattr(args, "state", None):
        tags.append(("state", args.state))
    for s in (getattr(args, "tag", None) or []):
        tags.append(parse_tag_arg(s))
    notes = []
    for k, v in tags:
        notes.extend(validate_tag(k, v))
    return tags, notes


def _atomic_write(path, text):
    """Crash-safe write of the canonical pile: write a temp file in the same directory,
    fsync it, then atomically rename over the target (§4.3 — never risk the truth on a
    half-write; a crash leaves either the old pile or the new, never a truncated one)."""
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".scribe-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def cmd_capture(args):
    text = _read_input(args.file)
    # Validate BEFORE reducing or writing: a tag the format cannot carry must never
    # reach the file, because nothing downstream re-parses what capture wrote (§3.6).
    tags, notes = _collect_tags(args)
    source = args.source or "unknown"
    notes.extend(validate_tag("source", source))
    tags.append(("source", source))
    _emit_tag_notes(notes)

    annotations = None
    if args.html:
        body, annotations = capture_html(text)
    else:
        body = capture_plaintext(text)

    block, findings = make_block(body, tags, source, ts=args.ts, annotations=annotations)
    out = serialize_block(block, tag_form=args.tag_form)

    if args.append:
        # A pile is stamped at BIRTH only — never bolted onto an existing one, so that
        # deleting the stamp keeps it deleted (§3.1). Declared, never assumed (§3.6):
        # the stamping is reported, and --no-stamp declines it.
        stamped = False
        if not args.no_stamp and not _pile_exists_nonempty(args.append):
            with open(args.append, "w", encoding="utf-8") as fh:
                fh.write(PILE_STAMP)
            stamped = True
        with open(args.append, "a", encoding="utf-8") as fh:
            fh.write(("\n\n" if _needs_sep(args.append) else "") + out + "\n")
        if stamped:
            sys.stderr.write(f"  new pile {args.append} — stamped with how to read and "
                             f"search it (delete the header block if you don't want it; "
                             f"it is never re-added)\n")
        _report_findings(findings, block)
    else:
        sys.stdout.write(out + "\n")
        _report_findings(findings, block)
    return 0


def _pile_exists_nonempty(path):
    try:
        return os.path.getsize(path) > 0
    except OSError:
        return False


def cmd_stamp(args):
    """Put the pile's own reading instructions at the top of an EXISTING pile.

    The retro-fit half of the stamp: `capture --append` stamps a pile at birth, this
    stamps one that already exists. A named verb the human takes deliberately (§3.9),
    never a thing the tool does to his file on its own (§3.1). Idempotent: on an
    already-stamped pile it reports and changes nothing — it never rewrites a stamp
    the human may have edited."""
    if args.show:
        sys.stdout.write(PILE_STAMP)
        return 0
    with open(args.pile, "r", encoding="utf-8") as fh:
        text = fh.read()
    if is_stamped(text):
        sys.stderr.write(f"{args.pile} is already stamped — unchanged\n")
        return 0
    _refuse_if_malformed(text, args.pile)
    _atomic_write(args.pile, PILE_STAMP + "\n" + text.lstrip("\n"))
    sys.stderr.write(f"{args.pile} stamped — {len(PILE_STAMP.splitlines())} comment "
                     f"lines added above the first block; no block was touched\n")
    return 0


def _needs_sep(path):
    try:
        with open(path, "rb") as fh:
            fh.seek(0, 2)
            if fh.tell() == 0:
                return False
        return True
    except FileNotFoundError:
        return False


def _report_findings(findings, block):
    # Disclosure to stderr so it never contaminates the canonical stdout (§3.7).
    sys.stderr.write(f"captured block #{block.id} ({len(block.body.splitlines())} lines)\n")
    if findings:
        sys.stderr.write(f"  {len(findings)} loss marker(s) placed in-band:\n")
        for f in findings:
            sys.stderr.write(f"    line {f.line}: {f.kind} — {f.note}\n")
    else:
        sys.stderr.write("  no loss markers (auditor found nothing to flag)\n")


def cmd_check(args):
    """Run the auditor standalone on text — demonstrates the separate-auditor design
    and lets the sovereign see what would be marked, without capturing anything."""
    text = _read_input(args.file)
    annotated, findings = loss_check(text)
    if args.show:
        sys.stdout.write(annotated + "\n")
    sys.stderr.write(f"{len(findings)} finding(s):\n")
    for f in findings:
        sys.stderr.write(f"  line {f.line}: {f.kind} — {f.note}\n")
    return 0


def cmd_blocks(args):
    """Parse a pile and list its blocks — proves the format parses and round-trips.

    Shows the WHOLE tag run, not just `@topic:`. This listing is the sovereign's
    check that a hand-typed header landed; showing one key would answer that question
    for one key only."""
    text = _read_input(args.file)
    blocks = parse_pile(text)
    n = 0
    for b in blocks:
        if not b.id:
            sys.stdout.write(f"(preamble, {len(b.body.splitlines())} lines)\n")
            continue
        n += 1
        tags = " ".join(f"@{k}:{v}" for k, v in b.tags) or "(no tags)"
        sys.stdout.write(f"#{b.id}  {b.ts}  {tags}  "
                         f"({len(b.body.splitlines())} lines)\n")
    sys.stderr.write(f"{n} block(s)\n")
    bad = _announce_malformed(text, args.file)
    _announce_retired_keys(blocks, args.file)
    return EXIT_FINDINGS if bad else 0


def cmd_keys(args):
    """Report what the vocabulary has actually become: every distinct key in the pile,
    its values, and counts. The companion to `toc --by` — an axis you cannot see is an
    axis you cannot choose. Replaces a `grep | tr | sed | sort -u` pipeline that lived
    in a paragraph of the guide rather than in the tool."""
    text = _read_input(args.pile)
    blocks = parse_pile(text)
    per_key = {}
    for b in blocks:
        for k, v in b.tags:
            per_key.setdefault(k, Counter())[v] += 1
    if not per_key:
        sys.stdout.write("(no tags in this pile)\n")
    for k in sorted(per_key, key=lambda k: (-sum(per_key[k].values()), k)):
        vals = per_key[k]
        retired = f"   [RETIRED — replaced by @{RETIRED_KEYS[k]}:]" if k in RETIRED_KEYS else ""
        sys.stdout.write(f"@{k}:  {sum(vals.values())} tag(s), "
                         f"{len(vals)} distinct value(s){retired}\n")
        if not args.counts_only:
            for v, n in sorted(vals.items(), key=lambda kv: (-kv[1], kv[0])):
                sys.stdout.write(f"    {v}  ({n})\n")
    bad = _announce_malformed(text, args.pile)
    return EXIT_FINDINGS if bad else 0


def _selector(s):
    """Parse a `key:value` selector, e.g. topic:nas or state:live."""
    if ":" not in s:
        raise SystemExit(f"selector must be key:value (e.g. topic:nas), got {s!r}")
    key, value = s.split(":", 1)
    return key, value


# §3.8, order-is-a-value. Until v1.1.0 both `view` and `export` carried
#     recent = args.recent or key == "state"
# — an ordering rule welded to one key and disclosed nowhere. When `@state:` was
# retired the behaviour did NOT move with the vocabulary: `view aspect:manifesting`
# silently ordered differently from the `view state:live` it replaced, and nothing
# announced the change. The implicit rule is removed. Ordering now comes from
# `--recent` alone, and every view STATES the order it used — including arrival order,
# so that an ordering choice is never left to be inferred.

def _order_note(recent):
    return "most-recent first" if recent else "arrival order"


def _note_retired_selector(key):
    if key in RETIRED_KEYS:
        sys.stderr.write(
            f"  NOTE: selector key @{key}: is RETIRED — replaced by "
            f"@{RETIRED_KEYS[key]}:. It also no longer defaults to most-recent-first; "
            f"pass --recent if that is what you want.\n")


def cmd_view(args):
    text_in = _read_input(args.pile)
    blocks = parse_pile(text_in)
    key, value = _selector(args.selector)
    recent = args.recent
    text, chosen = render_view(blocks, key, value, recent=recent, tag_form=args.tag_form)
    sys.stdout.write(text)
    sys.stderr.write(f"{len(chosen)} block(s) in view {key}:{value} "
                     f"({_order_note(recent)})\n")
    _note_retired_selector(key)
    bad = _announce_malformed(text_in, args.pile)
    return EXIT_FINDINGS if bad else 0


def cmd_toc(args):
    text_in = _read_input(args.pile)
    blocks = parse_pile(text_in)
    sys.stdout.write(render_toc(blocks, key=args.by) + "\n")
    bad = _announce_malformed(text_in, args.pile)
    _announce_retired_keys(blocks, args.pile)
    return EXIT_FINDINGS if bad else 0


def cmd_export(args):
    text_in = _read_input(args.pile)
    blocks = parse_pile(text_in)
    key, value = _selector(args.selector)
    recent = args.recent
    text, chosen = render_export(blocks, key, value, recent=recent, bare=args.bare)
    sys.stdout.write(text)
    sys.stderr.write(f"exported {len(chosen)} block(s) of {key}:{value} "
                     f"({_order_note(recent)})\n")
    _note_retired_selector(key)
    bad = _announce_malformed(text_in, args.pile)
    return EXIT_FINDINGS if bad else 0


def cmd_push(args):
    view_text = _read_input(args.view)
    with open(args.pile, "r", encoding="utf-8") as fh:
        pile_text = fh.read()
    _refuse_if_malformed(pile_text, args.pile)
    pile_blocks = parse_pile(pile_text)
    pile_blocks, report = push_view(view_text, pile_blocks)
    # Write the pile back only if something changed; disclose everything (§3.7).
    if report["updated"]:
        _atomic_write(args.pile, serialize_pile(pile_blocks))
    sys.stderr.write(f"pushed home: {len(report['updated'])} block(s) updated "
                     f"({', '.join('#'+i for i in report['updated']) or 'none'})\n")
    if report["missing"]:
        sys.stderr.write(f"  WARNING: {len(report['missing'])} view block(s) had no "
                         f"matching #id in the pile: {', '.join('#'+i for i in report['missing'])}\n")
    if report["tag_drift"]:
        sys.stderr.write(f"  NOTE: header tags differ for {', '.join('#'+i for i in report['tag_drift'])}"
                         " — NOT applied (use `tag` or edit the pile); body only was pushed\n")
    return 0


def cmd_tag(args):
    with open(args.pile, "r", encoding="utf-8") as fh:
        pile_text = fh.read()
    _refuse_if_malformed(pile_text, args.pile)
    blocks = parse_pile(pile_text)
    add, notes = _collect_tags(args)
    if args.source:
        notes.extend(validate_tag("source", args.source))
        add.append(("source", args.source))
    _emit_tag_notes(notes)
    ok, b = add_tags(blocks, args.id.lstrip("#"), add=add, remove=args.remove)
    if not ok:
        sys.stderr.write(f"no block with id #{args.id.lstrip('#')}\n")
        return 1
    _atomic_write(args.pile, serialize_pile(blocks, tag_form=args.tag_form))
    sys.stderr.write(f"#{b.id} tags now: {' '.join(f'@{k}:{v}' for k, v in b.tags)}\n")
    return 0


def cmd_doctor(args):
    """Disclose the frozen artifact and its runtime dependency (§3.7 / §4.4): the
    scribe.py SHA-256 (compare against PROVENANCE.md), the Python version, and the
    pandoc the HTML path would use (or that it is absent)."""
    with open(os.path.abspath(__file__), "rb") as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()
    sys.stdout.write(f"scribe {VERSION}\n")
    sys.stdout.write(f"scribe.py sha256: {sha}\n")
    sys.stdout.write(f"python: {platform.python_version()} ({sys.executable})\n")
    pandoc = shutil.which("pandoc")
    if pandoc:
        ver = subprocess.run(["pandoc", "--version"], capture_output=True, text=True)
        line = (ver.stdout.splitlines() or ["pandoc"])[0]
        note = "" if PANDOC_PINNED in line else f"  [pinned/tested: {PANDOC_PINNED}]"
        sys.stdout.write(f"pandoc: {line} ({pandoc}){note}\n")
    else:
        sys.stdout.write("pandoc: ABSENT — HTML capture unavailable; plain-text path "
                         "and all pile/view/tangle verbs work without it\n")
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        prog="scribe",
        description="Scribe's Workbench: canonical pile + capture + derived views. "
                    "The pile is truth; every view is a disposable derived cache.")
    p.add_argument("--version", action="version", version=f"scribe {VERSION}")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("capture", help="clean+canonicalize handed input into a block")
    c.add_argument("file", nargs="?", default="-", help="input file, or - for stdin")
    c.add_argument("--html", action="store_true", help="treat input as saved HTML (pandoc)")
    c.add_argument("--tag", action="append", metavar="key:value",
                   help="ANY tag, repeatable, e.g. --tag act:guards-the-boundary "
                        "--tag path:away-from-silent-loss")
    c.add_argument("--topic", action="append", help="topic tag (repeatable)")
    c.add_argument("--state", help="RETIRED (writes @state:, replaced by @aspect:) — "
                                   "kept working, announced when used")
    c.add_argument("--source", help="provenance, e.g. chatgpt")
    c.add_argument("--append", metavar="PILE", help="append the block to PILE")
    c.add_argument("--no-stamp", action="store_true",
                   help="do not write the reading-instructions header when --append "
                        "creates a new pile")
    c.add_argument("--tag-form", choices=["repeated", "comma"], default="repeated")
    c.add_argument("--ts", help="override timestamp (testing)")
    c.set_defaults(func=cmd_capture)

    k = sub.add_parser("check", help="run the loss auditor on text (no capture)")
    k.add_argument("file", nargs="?", default="-")
    k.add_argument("--show", action="store_true", help="print the annotated text")
    k.set_defaults(func=cmd_check)

    b = sub.add_parser("blocks", help="parse a pile and list its blocks")
    b.add_argument("file", nargs="?", default="-")
    b.set_defaults(func=cmd_blocks)

    v = sub.add_parser("view", help="derive a working view (topic:/state:) from the pile")
    v.add_argument("selector", help="key:value, e.g. topic:nas or state:live")
    v.add_argument("pile")
    v.add_argument("--recent", action="store_true", help="most-recent first (salience)")
    v.add_argument("--tag-form", choices=["repeated", "comma"], default="repeated")
    v.set_defaults(func=cmd_view)

    t = sub.add_parser("toc", help="regenerate the table of contents from tags")
    t.add_argument("pile")
    t.add_argument("--by", default="topic", metavar="KEY",
                   help="group by this tag key (default: topic). The index names the "
                        "axis it used and the keys it did not show. Run `scribe keys` "
                        "to see what the pile carries.")
    t.set_defaults(func=cmd_toc)

    ky = sub.add_parser("keys", help="list the tag keys and values this pile carries")
    ky.add_argument("pile")
    ky.add_argument("--counts-only", action="store_true",
                    help="keys and counts only, without their values")
    ky.set_defaults(func=cmd_keys)

    e = sub.add_parser("export", help="clean export of a view to paste into the next mind")
    e.add_argument("selector", help="key:value, e.g. topic:nas")
    e.add_argument("pile")
    e.add_argument("--recent", action="store_true")
    e.add_argument("--bare", action="store_true", help="omit the trailing back-link manifest")
    e.set_defaults(func=cmd_export)

    ph = sub.add_parser("push", help="push edits in a view back into the pile by #id")
    ph.add_argument("view", help="the edited view file")
    ph.add_argument("pile")
    ph.set_defaults(func=cmd_push)

    tg = sub.add_parser("tag", help="add/remove tags on a block by id (in place)")
    tg.add_argument("id", help="block id, e.g. 50c1 or #50c1")
    tg.add_argument("pile")
    tg.add_argument("--tag", action="append", metavar="key:value",
                    help="add ANY tag, repeatable, e.g. --tag aspect:manifesting")
    tg.add_argument("--topic", action="append")
    tg.add_argument("--state", help="RETIRED (writes @state:, replaced by @aspect:)")
    tg.add_argument("--source")
    tg.add_argument("--remove", action="append", metavar="key:value",
                    help="remove a tag, e.g. --remove state:live")
    tg.add_argument("--tag-form", choices=["repeated", "comma"], default="repeated")
    tg.set_defaults(func=cmd_tag)

    st = sub.add_parser("stamp", help="add the pile's own reading instructions on top")
    st.add_argument("pile", nargs="?", help="the pile to stamp (omit with --show)")
    st.add_argument("--show", action="store_true",
                    help="print the stamp text without writing anything")
    st.set_defaults(func=cmd_stamp)

    d = sub.add_parser("doctor", help="disclose the frozen artifact SHA + runtime deps")
    d.set_defaults(func=cmd_doctor)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except TagRefused as e:
        # A refusal is exit 1 (the command did not do what was asked). A completed
        # command that has findings to disclose is EXIT_FINDINGS. The two must be
        # distinguishable (§3.8).
        sys.stderr.write(f"REFUSED: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
