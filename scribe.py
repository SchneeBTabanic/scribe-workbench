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

VERSION = "1.0.0"

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


def render_toc(blocks):
    """Regenerated table of contents (§4.3): topics with their blocks, derived from
    the tags — never hand-kept. Replaces the sovereign's hand-maintained top list."""
    by_topic = {}
    untagged = []
    for b in blocks:
        if not b.id:
            continue
        tops = b.topics()
        if not tops:
            untagged.append(b)
        for t in tops:
            by_topic.setdefault(t, []).append(b)
    lines = ["# Table of contents (derived — do not hand-edit; run `scribe toc`)",
              f"# {sum(1 for b in blocks if b.id)} blocks, {len(by_topic)} topics", ""]
    for topic in sorted(by_topic, key=lambda t: (-len(by_topic[t]), t)):
        lines.append(f"## {topic} ({len(by_topic[topic])})")
        for b in by_topic[topic]:
            lines.append(f"   #{b.id}  {block_title(b)}")
        lines.append("")
    if untagged:
        lines.append(f"## (untagged) ({len(untagged)})")
        for b in untagged:
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
    tags = []
    for t in (args.topic or []):
        tags.append(("topic", t))
    if args.state:
        tags.append(("state", args.state))
    source = args.source or "unknown"
    tags.append(("source", source))

    annotations = None
    if args.html:
        body, annotations = capture_html(text)
    else:
        body = capture_plaintext(text)

    block, findings = make_block(body, tags, source, ts=args.ts, annotations=annotations)
    out = serialize_block(block, tag_form=args.tag_form)

    if args.append:
        with open(args.append, "a", encoding="utf-8") as fh:
            fh.write(("\n\n" if _needs_sep(args.append) else "") + out + "\n")
        _report_findings(findings, block)
    else:
        sys.stdout.write(out + "\n")
        _report_findings(findings, block)
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
    """Parse a pile and list its blocks — proves the format parses and round-trips."""
    text = _read_input(args.file)
    blocks = parse_pile(text)
    n = 0
    for b in blocks:
        if not b.id:
            sys.stdout.write(f"(preamble, {len(b.body.splitlines())} lines)\n")
            continue
        n += 1
        topics = ",".join(b.topics()) or "-"
        sys.stdout.write(f"#{b.id}  {b.ts}  topics={topics}  ({len(b.body.splitlines())} lines)\n")
    sys.stderr.write(f"{n} block(s)\n")
    return 0


def _selector(s):
    """Parse a `key:value` selector, e.g. topic:nas or state:live."""
    if ":" not in s:
        raise SystemExit(f"selector must be key:value (e.g. topic:nas), got {s!r}")
    key, value = s.split(":", 1)
    return key, value


def cmd_view(args):
    blocks = parse_pile(_read_input(args.pile))
    key, value = _selector(args.selector)
    recent = args.recent or key == "state"   # a state/salience view defaults recent-first
    text, chosen = render_view(blocks, key, value, recent=recent, tag_form=args.tag_form)
    sys.stdout.write(text)
    sys.stderr.write(f"{len(chosen)} block(s) in view {key}:{value}"
                     f"{' (most-recent first)' if recent else ''}\n")
    return 0


def cmd_toc(args):
    blocks = parse_pile(_read_input(args.pile))
    sys.stdout.write(render_toc(blocks) + "\n")
    return 0


def cmd_export(args):
    blocks = parse_pile(_read_input(args.pile))
    key, value = _selector(args.selector)
    recent = args.recent or key == "state"
    text, chosen = render_export(blocks, key, value, recent=recent, bare=args.bare)
    sys.stdout.write(text)
    sys.stderr.write(f"exported {len(chosen)} block(s) of {key}:{value}\n")
    return 0


def cmd_push(args):
    view_text = _read_input(args.view)
    with open(args.pile, "r", encoding="utf-8") as fh:
        pile_blocks = parse_pile(fh.read())
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
        blocks = parse_pile(fh.read())
    add = [("topic", t) for t in (args.topic or [])]
    if args.state:
        add.append(("state", args.state))
    if args.source:
        add.append(("source", args.source))
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
    c.add_argument("--topic", action="append", help="topic tag (repeatable)")
    c.add_argument("--state", help="salience tag, e.g. live")
    c.add_argument("--source", help="provenance, e.g. chatgpt")
    c.add_argument("--append", metavar="PILE", help="append the block to PILE")
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
    t.set_defaults(func=cmd_toc)

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
    tg.add_argument("--topic", action="append")
    tg.add_argument("--state")
    tg.add_argument("--source")
    tg.add_argument("--remove", action="append", metavar="key:value",
                    help="remove a tag, e.g. --remove state:live")
    tg.add_argument("--tag-form", choices=["repeated", "comma"], default="repeated")
    tg.set_defaults(func=cmd_tag)

    d = sub.add_parser("doctor", help="disclose the frozen artifact SHA + runtime deps")
    d.set_defaults(func=cmd_doctor)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
