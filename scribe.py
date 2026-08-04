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

VERSION = "1.4.1"

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
# Untagged means unknown, not mine and not anyone's.
#
# THE `#id` AT THE FRONT OF EACH HEADER is that block's identity — issued once when it was
# captured, checked unique in THIS pile, and never recomputed. It is the digits of the
# timestamp beside it, taken from the right, so you can check by eye that a header has not
# been fabricated. It says nothing about what the block contains, on purpose: correcting a
# word does not make a block a different block. Across piles, write `PILE#id` — the pile is
# the namespace, as a directory is for a filename. Do not edit it by hand.
#
# @name: IS A NAME YOU CAN SAY AGAIN. Capture the same @name: later and the name simply
# follows you to the new block; the earlier ones are untouched, unmarked, and still resolve
# by their #id. `scribe recall NAME` finds the live one, `scribe names` lists them all.
# Nothing is superseded and nothing is owed — this is Forth's dictionary, where redefining a
# word announces itself and leaves the old definition standing.
#
# A LONG HEX `@sealed:` AT THE END OF A HEADER, where one appears, is opt-in: someone asked
# for that body to be frozen as it stands, and `scribe verify` will say if it changed. Most
# blocks do not carry one and are meant to be correctable. `@mint:` on an older block is a
# RETIRED identity scheme (2026-08-01..04); it is kept readable and is no longer checked.
# (scribe {VERSION})
"""


def is_stamped(text):
    return text.lstrip().startswith(STAMP_MARK)


def stamp_for(genesis):
    """The stamp, plus this pile's own birth identity. The genesis line is machine-read
    (GENESIS_RE) and human-readable, in-band like everything else — no sidecar, no
    database, no registry. Row 29 refuses registries; this is the alternative it names:
    let the namespace discriminate, and keep the namespace in the artifact."""
    return PILE_STAMP + (
        "#\n"
        "# THIS PILE'S BIRTH MOMENT. Written once, at birth, in-band — no sidecar, no\n"
        "# database, no registry. Since 2026-08-05 nothing depends on it: a block's\n"
        "# identity is issued from its own declaring moment and checked within this pile,\n"
        "# so the pile itself is the namespace. Kept because a record of when a pile began\n"
        "# is worth having on its own account. Do not edit it; losing it breaks nothing.\n"
        f"# @genesis:{genesis}\n")


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

# A scribe block is a NOMINAL object, not a structural one (ruled 2026-08-01).
# Two blocks reading `agreed` are two SAYINGS, not one saying stored twice.
#
# THE ENCOUNTER THAT EARNED THIS, reproduced on the live machine 2026-08-01 against
# shipped v1.2.0, through the sanctioned front door:
#
#     $ echo "agreed" | scribe capture --ts 2026-08-01T10:00 --source claude --append a.txt
#     $ echo "agreed" | scribe capture --ts 2026-08-01T10:00 --source claude --append a.txt
#     $ grep '^@@' a.txt
#     @@ #a8eb 2026-08-01T10:00 @topic:x @source:claude
#     @@ #a8eb 2026-08-01T10:00 @topic:x @source:claude     <- the same id, twice
#
# `push_view` then keyed `{b.id: b}` and the SECOND block silently captured an edit
# meant for the first. That is a name collision silently tolerated — the failure Debian
# ledger row 29 names, and the one §3.8 forbids.
#
# WHY THE OLD SCHEME COULD NOT HELP. It hashed `ts + source + body` and truncated to 4
# hex. Two of those three inputs barely vary (`ts` was minute-resolution; `source` ranges
# over a handful of hands), so the body was the only wide field — and identical bodies are
# exactly what a working pile accumulates (the re-confirmation, the second ruling, the
# "yes" that means something new in a new place). No choice of CONTENT inputs can separate
# two identical utterances; that is what content-addressing MEANS. The fix is therefore not
# a wider hash but a different KIND of identity.
#
# THE BIFURCATION AS FIRST BUILT (2026-08-01), and RETIRED four days later:
#
#   MINT   the identity. Whole, never truncated, frozen at birth, carried as @mint:.
#   HANDLE the name. Short, typeable, `#a8eb`, a prefix of the mint.
#
# WHAT REPLACED IT (2026-08-05), and why the reasoning below survives the mechanism. The
# diagnosis in this section is exactly right and is the reason the change was possible: no
# choice of CONTENT inputs can separate two identical utterances, so the fix is a different
# KIND of identity, not a wider hash. What it got wrong was the SHAPE of the answer. It built
# two values where one would do, and the second value — the long one — kept the body in it,
# which quietly made every correction an identity event and made the pile feel like it was
# corralling its keeper. There is now ONE identity, `#id`, issued from the declaring moment
# and checked within the pile; integrity moved out to an opt-in `@sealed:`.
#
# AND THE PRIOR ART BELOW HAD ALREADY SAID SO, WHICH IS THE PART WORTH REMEMBERING. The
# gForth citation at `:2721` — a redefined word leaves the old definition intact and old
# references still reach the one they meant — was read here as evidence for SEPARATING a
# name from an identity, and it is that. It is also the complete answer to the corralling,
# sitting unused in this file for four days: the dictionary lets you redefine, announces it,
# marks nothing, and moves the NAME rather than the thing. That is now built (`@name:`,
# `recall`, `names`). Charter §3.19: a citation can be present, correct, and unread.
#
# Prior art, unanimous across five systems — every one separates the name you search by
# from the identity references bind to; scribe alone fused them into one 4-char token:
#   * gForth `ebook_gforth-manual.txt:2399` — the dictionary returns an execution token
#     "corresponding to the DEFINITION", not the name; `:2721` — a redefined word leaves
#     the old definition intact and old references still reach the one they meant, because
#     they bound to an address. `:2710`/`debugs.fs:152` — the collision is ANNOUNCED.
#   * Unison `docs/data-types.markdown:7-12` — structural (hash of structure) vs NOMINAL
#     (a GUID minted at the time of declaration), with syntax to declare which you mean.
#   * restic `data-safety/DESIGN.md:99,129` + on-disk `data/2b/2b3c15…` — the full hash is
#     the identity; the 2-char prefix is demoted to a DIRECTORY. Truncate for FILING,
#     never for IDENTITY.
#   * Sovereign Pool `tagio.h:44` — `char out_hex[65]`, the whole digest, with the
#     filename kept separate and renameable.
#   * Debian ledger row 29 — allow the collision, DECLARE it, let the namespace
#     discriminate. Explicitly NO global registry, which is why nothing here scans a
#     directory or keeps a manifest.
# ---------------------------------------------------------------------------

# RETIRED 2026-08-05. `@mint:` was the identity: sha256 over genesis+ordinal+ts+source+body.
# It is no longer ISSUED. It is still READ, because 31 blocks in the sovereign's piles carry
# one and a retired scheme must stay legible rather than become noise (§3.16 live-vs-frozen).
#
# WHY IT WENT, and it is one clause, twice:
#
#   §3.13 one contract, one place. Every ingredient of the mint was ALREADY STATED, readably,
#   on the same header line: genesis is the file you are reading, ordinal is the block's
#   position in it, ts is the timestamp column, source is `@source:`. The mint restated four
#   visible facts in 64 characters no human can read — two copies of one truth, and the
#   unreadable copy was the one called "identity".
#
#   §3.16 one token, one job. It was doing three: identity (which block is this), provenance
#   (where and when and from whom), and integrity (is the body as captured). The three are now
#   three things — the handle, the tags, and `@sealed:` — each nameable and each refusable.
#
# THE EVIDENCE, gathered before the change and not after (the brief demanded it): `verify`
# across all four real piles, 76 blocks, reported `edited in place` ZERO times, and 45 of the
# 76 carried no mint at all. The integrity job the fusion cost so much to serve had never once
# fired. That is why this is a removal and not a trade.
MINT_KEY = "mint"

# `@sealed:` — the integrity job, alone and OPT-IN. sha256 over the body and the header claims
# a seal is worth freezing. Written only when asked for (`capture --seal`), on the blocks that
# warrant it, and `verify` reports plainly which blocks carry one and which do not.
#
# Opt-in is the whole point. A guarantee that covers everything is a guarantee nobody chose,
# and its report fires on every ordinary correction — which §3.7-as-amended names as defeating
# disclosure while satisfying it.
SEAL_KEY = "sealed"

# THE KIND-DECLARATION. A tool that issues identifiers must say which kind it issues, in
# band, rather than inheriting a default — because an unruled default is indistinguishable
# from law once it is in the artifact, which is exactly how the old 4-hex id shipped.
#
#   nominal     a thing is a thing because it was DECLARED. Two identical declarations are
#               TWO things, so identity must carry a fact about the declaring.
#   structural  a thing is what it is made of. Two identical contents are ONE thing, and
#               identity may honestly be computed from content alone.
#
# scribe is NOMINAL: a block is an utterance. A future content-dedup tool over the same
# piles would declare `structural` and would be right to.
#
# This declaration is not decorative — it selects which SIGNATURE TEST the tool must carry
# and pass (test_scribe.py, TestIdentityKindGuards):
#   nominal    -> the twins test:  two identical contents, declared twice, must yield two
#                 DISTINCT identities.
#   structural -> the dedup test:  identical content must yield the IDENTICAL identity.
# A tool declaring `nominal` while passing the dedup test is the scribe bug, expressed as a
# failing assertion. The declaration says what was ruled; the signature test proves the code
# enacts the ruling; disagreement between them is the drift.
IDENTITY_KINDS = ("nominal", "structural")
IDENTITY_KIND = "nominal"

# `@name:` — THE MOVING NAME, ported from the Forth dictionary 2026-08-05.
#
# THE TENSION IT ANSWERS, in the sovereign's words: "it would be corralling my living
# impulses into frozen addended crystallized blocks over and over???" That is the real
# complaint, and `@mint:` was a symptom of it rather than its cause. A living thought is
# CONTINUOUS and restated; a pile is DISCRETE and appended. Every time you say the thing
# better, the tool made you file paperwork — a new block, `@replaces:` on it, `@superseded:`
# written back onto the old one, a chain to maintain. Say it five times and you have five
# crystals and four bookkeeping writes, and the pile has quietly become a record of your
# revisions rather than of what you think.
#
# FORTH DOES NOT DO THIS, AND IT IS THE OLDEST WORKING ANSWER ANYONE HAS. Define `foo`, then
# define `foo` again. gforth does not refuse. It does not make you supersede anything. It
# does not keep a version chain you have to maintain. It prints
#
#     redefined foo
#
# in the stream you are already reading, and moves on. The OLD definition is still in the
# dictionary — still executable, still findable by anything that already resolved to it,
# never deleted and NEVER MARKED. What changed is not the old thing. What changed is what
# THE NAME FINDS, because the dictionary is searched newest-first.
#
# So: the name moves, and the thing stays exactly where it was.
#
#   allowed, not refused           -> capture the same @name: as often as you like
#   announced in the stream        -> said at the moment of the act, unprompted, on stderr
#   the old definition survives    -> the earlier block is untouched and still resolvable
#   nothing marks the old one      -> NO @superseded: is written. No chain exists to keep.
#   search order resolves the name -> `scribe recall` finds the newest; the rest is DERIVED
#
# WHAT THIS DOES NOT REPLACE. `push` still exists and still writes `@superseded:` onto the
# old block, because sometimes the supersession IS the saying — you want the reader who
# wanders into the outdated block to be told, in the file, with the tool off (§4.3). That is
# a real property and the gForth build cannot have it. The change is that it is no longer the
# ONLY way to say a thing again. Four acts now, and choosing between them is the keeper's:
#
#   capture  a new saying
#   amend    a typo. Nothing happened.
#   @name:   I say this better now. The name follows me; nothing is marked; no paperwork.
#   push     a revision whose supersession is itself worth recording, in the file.
#
# WHY THE MARK IS DERIVED AND NOT WRITTEN. `scribe names` computes redefinition fresh from
# the pile every time and never writes back — the identical contract `backlinks` has held
# since v1.1.2, and for the identical reason: "back-references are derived, never
# hand-written" (`tagging/TAG-KEYS-reference-v1-DRAFT.md` A.4, after Knuth).
NAME_KEY = "name"

# The supersession pair. Ruled onto opposite blocks, deliberately and for a stated reason
# (`tagging/TAGS-bench-sheet.md:232`, `:240`):
#   @superseded:#new  goes on the OLD block — "the person who needs telling is the one who
#                     wandered into the outdated block." The ONLY tag `push` may write onto
#                     an existing block, and it touches neither body nor identity.
#   @replaces:#old    goes on the NEW block — "a rewrite of that block, kept as a separate
#                     change rather than an edit over the top."
SUPERSEDED_KEY = "superseded"
REPLACES_KEY = "replaces"


def _tag_value(block, key):
    """First value for `key` on this block, or None. (A block may carry a key more than
    once — `@topic:` routinely does — so this is deliberately 'first', not 'the'.)"""
    for k, v in block.tags:
        if k == key:
            return v
    return None


def _insert_before_digest(tags, new_tag):
    """Place a tag before any digest tag (`@sealed:`, or a legacy `@mint:`), or at the end
    if the block carries neither — which, sealing being opt-in, is now the common case.
    Keeps the human-facing vocabulary, and any status marker, on the readable side of the
    64 hex."""
    for i, (k, _) in enumerate(tags):
        if k in (SEAL_KEY, MINT_KEY):
            return tags[:i] + [new_tag] + tags[i:]
    return tags + [new_tag]

# The pile's genesis, written into the stamp at BIRTH and never afterwards. This is the
# `path` half of the mint: two piles diverge here and can never re-converge, so global
# uniqueness is a CONSEQUENCE of local history rather than a constraint imposed on top by
# a registry. In-band and greppable, like everything else scribe relies on.
GENESIS_RE = re.compile(r"^#\s*@genesis:(?P<hex>[0-9a-f]{64})\s*$", re.M)

# The shortest handle scribe will issue. Historical: the shipped code used exactly 4, and
# every existing pile is full of 4-char handles, so 4 stays the floor and handles only ever
# grow from there. NAMED LIMIT (§3.8): the spec's own worked examples
# (PHASE-0-RECON-AND-PROPOSAL.md:206-215) show SIX characters; the code shipped four and
# nothing guarded the drift. test_scribe.py now pins this constant against that spec.
HANDLE_MIN = 4


def now_ts():
    """The declaration moment at FULL precision — microseconds, not minutes.

    This is the `act` half of the mint, and the fact the old scheme threw away. It was
    `timespec="minutes"`, a resolution chosen before any pile existed and never re-checked;
    two blocks captured in the same minute were indistinguishable to the tool ONLY because
    the tool had discarded what distinguished them. Knuth's rule for an abbreviated name
    (`Literate-Programming-Knuth.txt:827`) is "enough text to identify the remainder
    uniquely" — a truncation licensed BY a check. Neither truncation in this file carried
    one; this one is simply not taken."""
    return datetime.now().isoformat(timespec="microseconds")


def gen_genesis(ts, abspath):
    """@identity:nominal — issues a pile's identity from its own declaring.

    Mint a pile's genesis from two NOMINAL facts about the pile's own declaring: when
    it was born, and where it was born. Deterministic (no randomness, so tests can pin it)
    and unique without coordination — two piles at one path cannot be born at the same
    microsecond, because at one path they are one file.

    NAMED LIMIT (§3.8): two piles born on DIFFERENT machines at the same microsecond under
    the same absolute path would share a genesis. Nothing here detects that. It is named
    rather than defended against, because defending would need a machine registry and row
    29 refuses registries."""
    return hashlib.sha256(f"{ts}\x00{os.path.abspath(abspath)}".encode("utf-8")).hexdigest()


def genesis_of(text, path):
    """Read a pile's genesis out of its own stamp. Returns (genesis_hex, is_declared).

    A pile with no genesis line is LEGACY — every pile that existed before 2026-08-01.
    Its genesis falls back to the path alone, which still separates piles from each other
    but carries no birth moment. That is a weaker guarantee and is DISCLOSED at the call
    site rather than silently substituted (§3.8): a fallback that looks like a real
    genesis is exactly the kind of absence this project refuses to imply."""
    m = GENESIS_RE.search(text or "")
    if m:
        return m.group("hex"), True
    return hashlib.sha256(os.path.abspath(path).encode("utf-8")).hexdigest(), False


def gen_seal(body, ts, source):
    """@identity:none — OPT-IN, and IT IS NOT AN IDENTITY. Issued only when asked for.

    The kind-declaration reads `none` because the lint that reads it (TestIdentityKindGuards,
    guard 1) exists to ensure no issuing site inherits a kind by default — and the honest
    declaration for this site is that it issues no identity at all. `none` was added to the
    legal set on 2026-08-05 for exactly this function, which is the first thing scribe has
    ever issued that is deliberately not an identity. That it needed a new legal value is
    itself the finding: the old vocabulary had no way to say "this is a digest and it names
    nothing", which is how one value came to do both jobs.

    An identity answers *which thing is this*. An integrity check answers *is this thing as
    it was*. Those requirements point in opposite directions — an identity must be stable
    across every correction that leaves the saying intact, and an integrity check must be
    disturbed by exactly those corrections — so §3.16's own reasoning forbids fusing them,
    the same way it forbids fusing a name and an identity. `@mint:` fused them for four days.

    WHAT IT COVERS, and each is a claim someone might want frozen rather than merely stated:
    the body, the declaration moment, and `@source:`. Re-attributing a saying is the act this
    project cares about most (`@origin:`, `@attests:`, the stamp's PROVENANCE IS PER BLOCK),
    and a seal is where a keeper freezes that claim ON PURPOSE rather than having it frozen
    for them.

    WHAT IT DOES NOT COVER: `@topic:`, `@act:`, `@path:`, the whole revisable vocabulary. Tags
    are how a pile is re-interrogated as the keeper's thinking moves; sealing them would make
    re-filing a tamper event.

    NOT TRUNCATED, ever — unlike the handle, this one has no reason to be short, because
    nobody types it and nothing resolves against it. It is read by a machine or not at all."""
    return hashlib.sha256(
        f"{ts}\x00{source}\x00{body}".encode("utf-8")).hexdigest()


def gen_handle(ts, taken=None):
    """@identity:nominal — issues the identity. There is no longer a second, longer one.

    THE CHANGE, 2026-08-05: the handle used to be the shortest unique PREFIX OF THE MINT, so
    it was a name for an identity computed elsewhere. The mint is retired, and the handle is
    now the identity itself — issued at declaration, checked once, never recomputed, and
    derived from nothing about what the block SAYS.

    ITS COORDINATES ARE THE PILE AND THE NAME. That is the whole model. `#dcea` means a block
    in THIS pile; across piles it is written `RIPE-LEDGER#dcea`, and the pile is the namespace
    exactly as a directory is for a filename. The mint bought global uniqueness by folding the
    pile's genesis into every identity — paying 64 unreadable characters per block, forever, to
    avoid ever writing down which pile you meant.

    WHY THE DECLARED MOMENT AND NOT RANDOMNESS. §3.16 sanctions one way to make a short name:
    truncate for filing, and CHECK the abbreviation — Knuth's WEB rule, which lets you shorten
    a section name only after enough text identifies it uniquely, and then performs the check.
    So the handle is the right-hand digits of the timestamp already printed on the same line,
    taken from the right and extended leftward until no other block in this pile holds it.

    That buys three things randomness would not:
      - it is RE-DERIVABLE BY EYE. `#2971` against `2026-08-03T10:59:42.322971` on the same
        line — a fabricated handle does not match its own timestamp, and no stored digest is
        needed to notice;
      - it SORTS, roughly, by when — a free ordering nobody has to maintain;
      - no random source in a records tool, so a capture is reproducible from its inputs.

    And it is the same answer the gForth build reached from the other side (BRIEF §2, candidate
    (c)): a short handle derived from `@formed:`, checked for collision at write time. Two
    implementations, one ruling — which is the point of having only one Charter.

    Collisions EXTEND, never overwrite: a longer handle is the declared, visible consequence
    of two blocks landing in the same microsecond, not a silent renaming."""
    digits = re.sub(r"\D", "", ts or "")
    taken = taken or set()
    for n in range(HANDLE_MIN, len(digits)):
        cand = digits[-n:]
        if cand not in taken:
            return cand
    # Every right-anchored run is taken — possible only with a pinned `--ts` repeated past
    # exhaustion, which the tests do. Declare the overflow rather than return a duplicate.
    n = 0
    while f"{digits}-{n}" in taken:
        n += 1
    return f"{digits}-{n}"



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

def make_block(raw_body, tags, source, ts=None, annotations=None,
               genesis=None, taken=None, ordinal=0, seal=False):
    """Wire capture -> auditor -> canonical block, issuing the identity on the way.

    `taken` is the one fact a block cannot know about itself: which handles the pile it is
    landing in has already issued. It is not optional in practice — the old code asked for
    none of it, which is precisely why it could issue the same id twice.

    `genesis` and `ordinal` are still accepted and are now UNUSED BY IDENTITY (2026-08-05).
    They stay in the signature because callers pass them and because `gen_genesis` still
    marks a pile's birth in its stamp; the identity no longer folds either one in. Named
    here rather than quietly dropped, because a parameter that stopped mattering and looks
    like it still does is the kind of drift §3.13 is about.

    `seal=True` adds `@sealed:` — integrity, opt-in, a separate value doing a separate job."""
    ts = ts or now_ts()
    audited_body, findings = loss_check(raw_body, annotations=annotations)
    handle = gen_handle(ts, taken)
    tags = list(tags)
    # `@sealed:` goes LAST, and the placement is the ruling `@mint:` used to hold: the eye
    # meets the vocabulary it came for — @topic:, @act:, @source: — and the digest trails off
    # the end of the line. The difference is that now the line usually HAS no digest, because
    # the seal is asked for rather than imposed. `scribe keys` excludes it and says so.
    if seal:
        tags.append((SEAL_KEY, gen_seal(audited_body, ts, source)))
    return Block(id=handle, ts=ts, tags=tags, body=audited_body), findings


# ---------------------------------------------------------------------------
# The resolver — the handle branch, and where Knuth's check belongs on LOOKUP.
#
# "Enough text to identify uniquely" is a property of LOOKING SOMETHING UP, not of
# issuing it, so the check lives here as well as at issue time. The two are
# complementary, not duplicated: gen_handle keeps a pile's OWN handles unambiguous as
# they are minted; this keeps a handle a HUMAN TYPED from ever resolving to the wrong
# block. Every existing relational tag in the sovereign's piles is a bare 4-char handle,
# so both halves are load-bearing.
#
# Ambiguity is REFUSED, never guessed. `push_view` used to build `{b.id: b}`, where a
# duplicate silently overwrote — an edit meant for one block landing on another with no
# error. Compare gForth (`:2721`): a redefined word leaves the old one reachable and
# every existing reference still binds to the one it meant. scribe cannot do that yet
# (it has no address under the name), so where Forth disambiguates, scribe must refuse.
# ---------------------------------------------------------------------------

class AmbiguousHandle(Exception):
    """A handle naming more than one block. Carries every match so the refusal can name
    them all — a refusal that will not say WHICH blocks collided is not actionable."""
    def __init__(self, handle, matches):
        self.handle = handle
        self.matches = matches
        super().__init__(
            f"#{handle} names {len(matches)} blocks in this pile "
            f"({', '.join('#' + b.id + ' ' + b.ts for b in matches)})")


def resolve_handle(blocks, handle):
    """Find the one block a handle names. Returns the Block, or None if there is no match.
    Raises AmbiguousHandle if more than one block answers.

    Exact match first; failing that, a unique prefix (so a human may type `#a8e` for
    `#a8eb1c`, git's behaviour and Knuth's rule). A prefix that matches several blocks is
    ambiguous and is refused with the list, asking for more characters."""
    handle = handle.lstrip("#")
    exact = [b for b in blocks if b.id and b.id == handle]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise AmbiguousHandle(handle, exact)
    pref = [b for b in blocks if b.id and b.id.startswith(handle)]
    if len(pref) == 1:
        return pref[0]
    if len(pref) > 1:
        raise AmbiguousHandle(handle, pref)
    return None


def duplicate_handles(blocks):
    """Every handle used by more than one block, as {handle: [Block, ...]}. Derived,
    read-only — the auditor half, which never repairs what it reports (§3.5)."""
    seen = {}
    for b in blocks:
        if b.id:
            seen.setdefault(b.id, []).append(b)
    return {h: bs for h, bs in seen.items() if len(bs) > 1}


# ---------------------------------------------------------------------------
# The seal audit — is a SEALED block still as it was sealed?
#
# REWRITTEN 2026-08-05, and it now answers a narrower question ON PURPOSE. It used
# to re-derive every block's `@mint:` and report the whole pile. That check covered
# everything, which sounds like more and was less: it fired on ordinary corrections,
# it had to invent a deletion-signature search to stay quiet during ordinary edits,
# and across four real piles and 76 blocks it never once reported an edit. A check
# nobody chose, which has never caught anything, is not a guarantee — it is a cost.
#
# So the check is now OPT-IN and the report says what it did NOT check. Blocks with
# no `@sealed:` are not failures and are not silence: they are `not sealed`, stated
# in the count, because an instrument that cannot say what it left out reports its
# blindness as an observation (Charter §3.8 as amended).
#
# FACT-LANGUAGE, AND IT IS THE WHOLE DESIGN CONSTRAINT — not a wording preference.
# v1.3.1 ruled the hand-edit a LEGITIMATE SOVEREIGN ACT: the second doorway, chosen
# per act, history-in-restic instead of history-in-the-pile (§3.1 — the tool binds
# itself, not the human). A verb that reported that act as `MISMATCH`, `UNVERIFIED`,
# `MODIFIED`, or at any severity would recast a sanctioned choice as a defect, and a
# sovereign who feels told off for using his own door stops using it. That is the
# identical trap the path-sovereignty witness already solved once: `substituted` is a
# FACT, never a fault — and the tag-validator's `[HELD]` tier is the same move.
#
# So: every state below is a statement about WHAT HAPPENED. None is a grading of it.
# There is no severity anywhere in this verb, and there must never be one.
#
# WHAT WENT WITH THE MINT, recorded because it was good work and its removal is not
# a judgement on it. `audit_mints` searched for a DELETION SIGNATURE: because the old
# identity encoded a block's ordinal, removing one block from the middle made every
# later block re-derive wrong, so the audit looked for a trailing run that verified
# cleanly at one constant offset and reported "K blocks removed" instead of a wave of
# false alarm. That machinery was correct, and it existed ONLY to defend the choice to
# put position inside identity. An identity that is issued and never recomputed cannot
# drift when its neighbours move, so there is nothing left to compensate for. This is
# the shape of the whole change: most of what is deleted here is not the feature, it is
# the scaffolding the feature needed to stay tolerable.
# ---------------------------------------------------------------------------

AS_SEALED = "as sealed"
CHANGED_SINCE_SEAL = "changed since it was sealed"
NOT_SEALED = "not sealed — this check did not run"

# Kept: `verify` still reads and reports the retired `@mint:` where it finds one, so the
# 31 blocks carrying one do not become unreadable noise. It cannot RE-DERIVE them — that
# needed the pile's genesis and each block's frozen ordinal — so it says exactly that,
# rather than reporting an absence of evidence as evidence.
LEGACY_MINT = "carries a retired @mint: — not re-derivable, not checked"


def rederive_seal(block):
    """The seal this block would receive if it were sealed, now, from what the file says."""
    return gen_seal(block.body, block.ts, _tag_value(block, "source") or "unknown")


def audit_seals(blocks, genesis=None):
    """Report what the file says happened to each SEALED block.

    Returns {states: [...], sealed: n, unsealed: n, legacy: n, blocks: [...]}.

    `genesis` is accepted and unused — callers still read it out of the stamp for other
    reasons, and a signature that quietly changed would break them for no gain. Identity
    no longer folds it in."""
    real = [b for b in blocks if b.id]
    states = []
    for b in real:
        stored = _tag_value(b, SEAL_KEY)
        if stored:
            states.append(AS_SEALED if stored == rederive_seal(b) else CHANGED_SINCE_SEAL)
        elif _tag_value(b, MINT_KEY):
            states.append(LEGACY_MINT)
        else:
            states.append(NOT_SEALED)
    return {"states": states,
            "sealed": sum(1 for s in states if s in (AS_SEALED, CHANGED_SINCE_SEAL)),
            "unsealed": sum(1 for s in states if s == NOT_SEALED),
            "legacy": sum(1 for s in states if s == LEGACY_MINT),
            "blocks": real}

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


def definitions_of(blocks, name):
    """Every block carrying `@name:name`, in ARRIVAL ORDER — oldest first, live one last.

    Arrival order and not most-recent-first, deliberately: a `--ts` can be pinned or
    backdated, so sorting by timestamp would let a backdated capture silently become the
    live definition of a name. The pile is append-only and its order is a fact about what
    happened; a stated moment is a claim. Where the two disagree, this trusts the pile.

    That is the dictionary's rule exactly — gforth resolves a name to the most recently
    ADMITTED definition, not the one whose source file has the latest date."""
    return [b for b in blocks if b.id and (NAME_KEY, name) in b.tags]


def recall(blocks, name):
    """What this name finds: the newest definition, or None. Forth's dictionary lookup."""
    found = definitions_of(blocks, name)
    return found[-1] if found else None


def redefinitions(blocks):
    """{name: [Block, ...]} for every name defined more than once, arrival order.

    DERIVED, READ-ONLY, computed fresh every call and never written back — the contract
    `backlinks` has held since v1.1.2. This is the whole reason a redefinition costs the
    keeper nothing: the record of it is not IN the pile, it is a fact ABOUT the pile, and
    facts about a pile are recomputed rather than maintained."""
    out = {}
    for b in blocks:
        if not b.id:
            continue
        for k, v in b.tags:
            if k == NAME_KEY:
                out.setdefault(v, []).append(b)
    return {n: bs for n, bs in out.items() if len(bs) > 1}


# ---------------------------------------------------------------------------
# Backlinks (v1.1.2) — a DERIVED reverse index over pointer-style tag values.
# ---------------------------------------------------------------------------
# Ratified 2026-07-31: `tagging/TAG-KEYS-reference-v1-DRAFT.md` (A.4, Knuth)
# already stated "back-references are derived, never hand-written" -- this is
# that principle finally built. scribe already had many pointer-style keys
# (@ref/@overrules/@superseded/@yields/@replaces/@continues/@customizes/
# @hoisted-from) but no code path computed the REVERSE direction; a human had
# to already know which specific key to ask `scribe view <key>:<value>` with.
# Confirmed against real prior art before writing this (not reinvented):
# Foam's packages/foam-core/src/model/graph.ts keeps a `links` map (forward)
# and a `backlinks` map (reverse), the reverse computed by one pass over every
# resource and never hand-maintained; Logseq's
# deps/db/src/logseq/db/common/reference.cljs computes get-linked-references
# the same way. Structural detection, not a key allow-list (no registry,
# same as the rest of scribe): a value is a pointer IFF it is shaped `#id`
# (this pile) or `path#id` (a NAMED pile, resolved relative to the pile
# carrying the tag) and that id is real in the target pile. Read-only —
# nothing here is ever written back into a pile.

def compute_backlinks(piles):
    """`piles` is {path: [Block, ...]} (already parsed). Returns
    {(pile_path, target_id): [(from_pile, key, from_id, from_ts), ...]}."""
    ids_by_pile = {p: {b.id for b in blocks if b.id}
                  for p, blocks in piles.items()}

    def _resolve_pile(from_pile, named):
        if named in ids_by_pile:
            return named
        candidate = os.path.normpath(
            os.path.join(os.path.dirname(from_pile), named))
        return candidate if candidate in ids_by_pile else None

    back = {}
    for p, blocks in piles.items():
        for b in blocks:
            if not b.id:
                continue
            for key, val in b.tags:
                if "#" not in val:
                    continue
                head, _, tail = val.partition("#")
                target_pile = p if not head else _resolve_pile(p, head)
                if target_pile and tail in ids_by_pile.get(target_pile, ()):
                    if tail != b.id or target_pile != p:
                        back.setdefault((target_pile, tail), []).append(
                            (p, key, b.id, b.ts))
    return back


def render_backlinks(target_pile, target_id, back, same_pile_label=None):
    """`same_pile_label` names the target pile as the human typed it, so a
    same-pile hit reads `#id` (unchanged) rather than a full path."""
    hits = back.get((target_pile, target_id), [])
    label = f"{same_pile_label or os.path.basename(target_pile)}#{target_id}"
    if not hits:
        return f"(nothing points at {label})\n"
    lines = [f"What points at {label} ({len(hits)}):"]
    for from_pile, key, from_id, ts in hits:
        same = from_pile == target_pile
        origin = f"#{from_id}" if same else f"{os.path.basename(from_pile)}#{from_id}"
        value_shown = f"#{target_id}" if same else f"{os.path.basename(target_pile)}#{target_id}"
        lines.append(f"  {origin} ({ts}) via @{key}:{value_shown}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Activate (v1.2.0) — a DERIVED report over witness-style tag values (the
# other half of a dpkg trigger: `interest` is @awaits:/@dissolves:, already in
# this pile's vocabulary; `activate` was never built).
# ---------------------------------------------------------------------------
# Built 2026-07-31, from fresh research into dpkg's trigger mechanism (not a
# re-reading of this project's own prior ledger): a package declares INTEREST
# in a named trigger; any package ACTIVATES it; dpkg computes, on demand,
# every currently-interested package for that name — "a facility that allows
# events caused by one package but of interest to another package to be
# recorded and aggregated, and processed later by the interested package...
# reduces duplication of processing" (dpkg's triggers.txt spec). This project
# already had the DECLARE half (`@awaits:<condition>`, used throughout
# RIPE-LEDGER.txt) and a coarse, hardcoded NOTIFY half (the SessionStart
# hook's `scribe view aspect:prospective`, one fixed value). Missing: the
# general on-demand query — given any condition string, who is currently
# awaiting it, across any piles named, not just one hardcoded value. Read-only
# by construction, same as backlinks: this NEVER promotes a block. "@awaits is
# a witness, never a promoter... the human rules every promotion, always"
# (tagging/TAG-KEYS-reference-v1-DRAFT.md) still holds — this command only
# removes the eyeball-matching step of finding who is currently waiting.

def compute_activations(piles, condition, key="awaits"):
    """`piles` is {path: [Block, ...]}. Returns [(pile_path, id, ts, key, value)]
    for every block whose tag KEY carries VALUE == condition, across all given
    piles, in arrival order within each pile. Exact match only — structural,
    not fuzzy, same discipline as compute_backlinks's id-matching."""
    hits = []
    for p, blocks in piles.items():
        for b in blocks:
            if not b.id:
                continue
            for k, v in b.tags:
                if k == key and v == condition:
                    hits.append((p, b.id, b.ts, k, v))
    return hits


def render_activate(condition, hits, key="awaits"):
    """Report every current waiter on `condition`. Absence is named, not
    silent (§3.8) — same shape as render_backlinks's own empty case."""
    if not hits:
        return f"(nothing is @{key}:{condition})\n"
    lines = [f"What is @{key}:{condition} ({len(hits)}):"]
    for p, bid, ts, k, v in hits:
        lines.append(f"  {os.path.basename(p)}#{bid} ({ts})")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Converges (v1.2.0) — a DERIVED, DISCLOSED report of candidate convergence
# between DIFFERENT piles (different projects) that were never explicitly
# cross-referenced by a pointer tag. First concrete attempt at Design Charter
# §3.15's still-open founding gap: "a tag nothing ever queries is never found
# wrong... an absent relation cannot be searched for." The 2026-07-30 ruling
# closed only the stateless-model-reconnecting-to-its-own-record shape of
# that gap (GTPS-Agent's fold.py); this is the OTHER shape it explicitly left
# open — separate projects converging on the same philosophy without either
# side ever writing an @ref: to the other.
#
# Deliberately NOT semantic/ML similarity (that would be §3.6's "borrowing a
# word" — importing an embedding model's authority while delivering none of
# its content — and would let a representation "acquire causal authority
# merely because it represents," §3.3's general form). Every finding here is
# a LITERAL match: identical tag VALUES, or identical Charter-clause-shaped
# citation substrings, appearing on blocks in two or more DISTINCT piles.
# Structural, deterministic, disclosed as a contestable candidate only —
# never asserted as a real relation, never merged, never written back.
# ---------------------------------------------------------------------------

CITATION_RE = re.compile(r"§\d+(?:\.\d+)*|Clause \d+")


def compute_convergences(piles, tag_key=None):
    """Groups (key, value) -> [(pile, id, ts), ...] across ALL given piles,
    keeping only groups that touch 2+ DISTINCT piles. Pointer-shaped values
    (containing '#') are excluded — those are explicit relations already
    covered by compute_backlinks; this function is only for the IMPLICIT
    convergence of two blocks that share a value without either pointing at
    the other."""
    groups = {}
    for p, blocks in piles.items():
        for b in blocks:
            if not b.id:
                continue
            for k, v in b.tags:
                if tag_key and k != tag_key:
                    continue
                if "#" in v:
                    continue
                groups.setdefault((k, v), []).append((p, b.id, b.ts))
    return {kv: hits for kv, hits in groups.items()
            if len({p for p, _, _ in hits}) >= 2}


def compute_citation_convergences(piles):
    """Groups literal Charter-clause-shaped citations (§N.N or Clause N) found
    in block BODY text -> [(pile, id, ts), ...], keeping only groups that
    touch 2+ distinct piles. A citation substring match is not proof of a
    real relation (a quoted excerpt could contain one incidentally) — it is a
    candidate for a human to read, same disclosure-only footing as every
    other finding here (§3.3: witness, never govern)."""
    groups = {}
    for p, blocks in piles.items():
        for b in blocks:
            if not b.id:
                continue
            for cite in set(CITATION_RE.findall(b.body)):
                groups.setdefault(cite, []).append((p, b.id, b.ts))
    return {cite: hits for cite, hits in groups.items()
            if len({p for p, _, _ in hits}) >= 2}


def render_convergences(tag_groups, citation_groups):
    """Disclosed candidates only — every line names what was matched and
    where, so a human can go read the two blocks and judge whether the
    convergence is real (§3.3/§3.8). Absence is named, not silent."""
    lines = []
    lines.append(f"# Candidate convergences — LITERAL matches only, never "
                 f"asserted as real relations. Read each pair; nothing here "
                 f"was merged or written back.")
    lines.append("")
    lines.append(f"## Shared tag-values across different piles ({len(tag_groups)})")
    if not tag_groups:
        lines.append("(none found)")
    for (k, v), hits in sorted(tag_groups.items(),
                               key=lambda kv: (-len(kv[1]), kv[0])):
        piles_touched = sorted({os.path.basename(p) for p, _, _ in hits})
        lines.append(f"  @{k}:{v}  — {len(hits)} block(s) across "
                     f"{len(piles_touched)} pile(s): {', '.join(piles_touched)}")
        for p, bid, ts in hits:
            lines.append(f"    {os.path.basename(p)}#{bid} ({ts})")
    lines.append("")
    lines.append(f"## Shared Charter-clause citations across different piles "
                 f"({len(citation_groups)})")
    if not citation_groups:
        lines.append("(none found)")
    for cite, hits in sorted(citation_groups.items(),
                             key=lambda kv: (-len(kv[1]), kv[0])):
        piles_touched = sorted({os.path.basename(p) for p, _, _ in hits})
        lines.append(f"  {cite}  — cited in {len(hits)} block(s) across "
                     f"{len(piles_touched)} pile(s): {', '.join(piles_touched)}")
        for p, bid, ts in hits:
            lines.append(f"    {os.path.basename(p)}#{bid} ({ts})")
    return "\n".join(lines) + "\n"


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


def is_superseded(block):
    """Has a later block replaced this one? Read straight off the status tag `push` wrote —
    no inference, no guessing (§3.3: the tool reports what the file says)."""
    return any(k == SUPERSEDED_KEY for k, _ in block.tags)


def render_view(blocks, key, value, recent=False, tag_form="repeated", current=False):
    """A working view: the matching blocks, each with its `@@ #id` header (the
    back-link), ready to read, edit, and `push` home. It IS a mini-pile.

    SUPERSEDED BLOCKS ARE SHOWN BY DEFAULT and counted separately, never dropped. Since
    `push` began appending rather than overwriting (2026-08-02), a view can contain both an
    old saying and the one that replaced it, and a view that silently hid the old one would
    be an undisclosed exclusion — the failure §3.8 names. `--current` opts into hiding them
    and the hiding is then declared in the view's own header, in-band, where anyone editing
    the file will meet it.

    NAMED LIMIT (§3.8): whether `--current` should become the DEFAULT is deliberately NOT
    decided here. It is a live question at `RIPE-LEDGER.txt#3f02` and belongs to the same
    gate that rules the rest of the supersession behaviour."""
    chosen = order_blocks(select_blocks(blocks, key, value), recent=recent)
    n_superseded = sum(1 for b in chosen if is_superseded(b))
    if current:
        chosen = [b for b in chosen if not is_superseded(b)]
    header = f"# view {key}:{value}" + ("  (most-recent first)" if recent else "")
    note = ("# derived view — disposable. Edit a body and `scribe push` it home by #id.\n"
            "# the pile is the truth; regenerate this any time.")
    if n_superseded and current:
        note += (f"\n# --current: {n_superseded} superseded block(s) HIDDEN from this view. "
                 f"They are still in the pile.")
    elif n_superseded:
        note += (f"\n# {n_superseded} block(s) here carry @superseded: — a later block has "
                 f"replaced them. Shown, not hidden; use --current to drop them.")
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


DEFAULT_JOINER = "\n\n---\n\n"


def content_fingerprint(blocks):
    """A sha256-8 fingerprint of exactly which blocks, with what content, fed a
    derived view — independent of joiner/order choice, so it fingerprints
    IDENTITY-AND-CONTENT, not the rendered text. This is the joiner-method's
    missing half: `render_export`'s manifest always named which `#id`s fed a
    view, but never whether their CONTENT has since moved — so a saved/running
    derived artifact could go stale under the pile with nothing to detect it.
    Same principle Knuth's WEB change-file already uses for its string pool —
    "ships a checksum, not the strings" (tagging/TAG-KEYS-reference-v1-DRAFT.md,
    A.1, `@quoting:`) — applied here to a whole derived view instead of one
    quoted block."""
    h = hashlib.sha256()
    for b in sorted(blocks, key=lambda b: b.id):
        h.update(f"{b.id}\x00{b.body}".encode("utf-8"))
    return h.hexdigest()[:8]


def render_export(blocks, key, value, recent=False, bare=False, joiner=None):
    """A clean export to paste into the next mind: bodies only, no `@@` headers to
    scroll-and-delete. Back-links survive as an unobtrusive trailing manifest unless
    --bare (§3.7: disclosed, not hidden; but out of the way for the paste target).

    `joiner` (None by default) lets the concatenation itself become code-safe: the
    default `---` separator is prose punctuation, and a bare literal `---` line is a
    Python SyntaxError, so bodies meant to tangle into one runnable file need a
    different join (e.g. a blank line) than bodies meant to be read as prose. Scribe
    does not decide what a body IS — it only offers the join a code export needs.

    The manifest also carries a content fingerprint (v1.2.0) so a later
    `scribe verify-export` can tell whether the pile has drifted underneath
    this saved view since it was extracted — see `content_fingerprint`."""
    chosen = order_blocks(select_blocks(blocks, key, value), recent=recent)
    parts = [b.body for b in chosen]
    out = (joiner if joiner is not None else DEFAULT_JOINER).join(parts)
    if not bare and chosen:
        manifest = " ".join(f"#{b.id}" for b in chosen)
        fp = content_fingerprint(chosen)
        out += (f"\n\n<!-- scribe export of {key}:{value} — source blocks: "
               f"{manifest} — content:sha256:{fp} -->")
    return out + "\n", chosen


EXPORT_MANIFEST_RE = re.compile(
    r"<!-- scribe export of \S+ — source blocks: (?P<ids>[^—]*)"
    r"— content:sha256:(?P<fp>[0-9a-f]{8}) -->")


def find_export_manifest(text):
    """Extract the recorded fingerprint + source ids from a previously
    exported file's trailing manifest comment. Returns None if the file
    carries no manifest — e.g. it was exported --bare, or predates this
    fingerprint (§3.8: an absent manifest is named, never mistaken for a
    match)."""
    m = EXPORT_MANIFEST_RE.search(text)
    if not m:
        return None
    return {"fp": m.group("fp"),
           "ids": [i.lstrip("#") for i in m.group("ids").split()]}


def render_verify_export(manifest, blocks, key, value, recent=False):
    """Has the pile drifted since this file was exported? Recomputes the
    CURRENT fingerprint for key:value and compares to what was recorded at
    export time. Never repairs and never re-exports — reports MATCH or DRIFT
    only (§3.10: staleness is reported, never silently repaired)."""
    chosen = order_blocks(select_blocks(blocks, key, value), recent=recent)
    if manifest is None:
        return ("NO MANIFEST — this export carries no content fingerprint "
                "(exported --bare, or predates verify-export). Nothing to "
                "compare against.\n")
    new_fp = content_fingerprint(chosen)
    if new_fp == manifest["fp"]:
        return (f"MATCH — {key}:{value} is unchanged in the pile since export "
                f"(content:sha256:{manifest['fp']}, {len(chosen)} block(s)).\n")
    old_ids, new_ids = set(manifest["ids"]), {b.id for b in chosen}
    added, removed = new_ids - old_ids, old_ids - new_ids
    lines = [f"DRIFT — {key}:{value} has changed in the pile since export: "
            f"was content:sha256:{manifest['fp']}, now content:sha256:{new_fp}."]
    if added:
        lines.append(f"  now also matches: {' '.join('#'+i for i in sorted(added))}")
    if removed:
        lines.append(f"  no longer matches (edited, retagged, or removed): "
                     f"{' '.join('#'+i for i in sorted(removed))}")
    if not added and not removed:
        lines.append(f"  same {len(chosen)} block(s) by id — body content changed")
    lines.append("  the exported file is stale; re-run `scribe export` to refresh it.")
    return "\n".join(lines) + "\n"


def push_view(view_text, pile_blocks, genesis=None):
    """Push edits made in a working view back into the canonical pile by #id (the
    detangle round-trip). **APPENDS A SUPERSEDING BLOCK — it never overwrites one.**

    RULED 2026-08-02. `push` used to assign `pb.body = vb.body`, rewriting the pile in
    place, which made scribe *less append-only than it claimed*: a body could change under
    a `@ref:` that had been written to the old wording. gForth is the model — you may always
    edit the source and recompile, but the dictionary never rewrites a definition underneath
    a reference already bound to it (`ebook_gforth-manual.txt:2721`).

    THE SOVEREIGNTY GROUND, which is why this is not a restriction: *"I can always directly
    edit a block in a pile if I don't want the history that comes with push — so my
    sovereignty is enhanced by the choice."* **Two doorways, chosen per act** —
    history-in-the-pile via `push`, history-in-restic via hand-edit. **The tool binds ITSELF
    to append-only; it does not bind the human** (§3.1: sovereignty is the axiom, not a
    feature). A pile is a plain-text file and stays one.

    WHAT IS INVIOLABLE, and it is exactly two things: **bodies and identities.** No existing
    block's body is ever altered here, and no existing `@mint:` or handle is ever altered or
    reissued. What push may write onto an existing block is **one declared status tag** —
    `@superseded:#new` — and nothing else. That is not an overwrite; it is the same act
    `scribe tag` already performs as a sanctioned verb, and it is what lets **the file itself
    keep telling the truth**: a human reading the raw pile with no tool meets the mark on the
    stale block, which is the whole reason the bench sheet rules `@superseded:` onto the OLD
    block rather than the new (`tagging/TAGS-bench-sheet.md:232` — *"the person who needs
    telling is the one who wandered into the outdated block"*). Deriving that warning instead
    (via `backlinks`) would have been purer and would have cost the tool-off-readable
    invariant; between two stated invariants, legibility was ruled to win.

    The new block carries `@replaces:#old` (`:240`) and inherits the old block's tags, so it
    appears in every view the old one did. Tag edits made in the view are still NOT applied —
    disclosed, as before."""
    view_blocks = [b for b in parse_pile(view_text) if b.id]
    # AMBIGUITY IS CHECKED BEFORE ANYTHING IS TOUCHED, and it aborts the whole push.
    # This was `{b.id: b}` — a dict, so a duplicate handle silently overwrote and the
    # LAST block won, quietly receiving an edit meant for the first. Nothing announced
    # it. §3.6: silent failure is the cardinal engineering sin, and this was silent
    # WRONG-TARGET WRITING, which is worse than a silent no-op.
    dupes = duplicate_handles(pile_blocks)
    ambiguous = sorted({vb.id for vb in view_blocks if vb.id in dupes})
    blank = {"superseded": [], "missing": [], "tag_drift": [], "ambiguous": {},
             "already_superseded": []}
    if ambiguous:
        return pile_blocks, dict(blank, ambiguous={h: dupes[h] for h in ambiguous})

    genesis = genesis or gen_genesis(now_ts(), ".")
    taken = {b.id for b in pile_blocks if b.id}
    ordinal = len([b for b in pile_blocks if b.id])
    superseded, missing, tag_drift, already = [], [], [], []
    appended = []

    for vb in view_blocks:
        pb = resolve_handle(pile_blocks, vb.id)
        if pb is None:
            missing.append(vb.id)
            continue
        if vb.tags and vb.tags != pb.tags:
            tag_drift.append(vb.id)
        if vb.body == pb.body:
            continue
        # A block already superseded must not be superseded again from a stale view —
        # two pushes of the same view would otherwise fork the chain silently.
        prior = [v for k, v in pb.tags if k == SUPERSEDED_KEY]
        if prior:
            already.append((pb.id, prior[0].lstrip("#")))
            continue
        ts = now_ts()
        handle = gen_handle(ts, taken)
        taken.add(handle)
        ordinal += 1
        # The new block inherits the old block's vocabulary so it appears in every view the
        # old one did — a supersession that fell out of its own topic would be a silent loss.
        # Its identity is issued fresh. Neither the retired `@mint:` nor a `@sealed:` is ever
        # carried across: a seal is a claim about a body, and this is a different body. If the
        # superseded block was sealed, the new one is sealed only by being sealed again.
        carried = [(k, v) for k, v in pb.tags
                   if k not in (MINT_KEY, SEAL_KEY, SUPERSEDED_KEY, REPLACES_KEY)]
        new_tags = carried + [(REPLACES_KEY, f"#{pb.id}")]
        if _tag_value(pb, SEAL_KEY):
            new_tags.append(
                (SEAL_KEY, gen_seal(vb.body, ts, _tag_value(pb, "source") or "unknown")))
        appended.append(Block(id=handle, ts=ts, tags=new_tags, body=vb.body))
        # THE ONE PERMITTED WRITE onto an existing block: a status tag. Its body and its
        # identity are not touched, and this is asserted directly in the guard-set.
        # It is placed BEFORE @mint:, deliberately — a status marker parked after 64 hex
        # characters is a status marker nobody reads, and the entire reason this is written
        # into the file rather than derived is that a tool-off reader must MEET it.
        pb.tags = _insert_before_digest(pb.tags, (SUPERSEDED_KEY, f"#{handle}"))
        superseded.append((pb.id, handle))

    return pile_blocks + appended, dict(
        blank, superseded=superseded, missing=missing, tag_drift=tag_drift,
        already_superseded=already)


def add_tags(blocks, block_id, add=None, remove=None):
    """Add/remove tags on a block in place, by id. The human can equally hand-edit the
    header line; this is the named-verb convenience (§3.9). Returns (ok, block)."""
    add = add or []
    remove = set(remove or [])
    # This scanned for the FIRST block whose id matched, while push_view's dict kept the
    # LAST — so on a duplicate handle the two verbs silently disagreed about which block
    # they meant. Both now go through the one resolver, which refuses rather than picks.
    b = resolve_handle(blocks, block_id)
    if b is None:
        return False, None
    # Neither digest tag is editable vocabulary, and the reasons differ. A hand-written
    # `@sealed:` would be a seal over a body nobody sealed — a claim of integrity produced
    # by asserting it. A hand-removed `@mint:` would strip a retired identity while leaving
    # the block looking intact, an absence that does not announce itself (§3.8). Refused on
    # the write side, where validate_tag's refusals already live.
    _frozen = {SEAL_KEY: ("a seal over a body, issued by `capture --seal` at the moment that "
                          "body was declared. Writing one by hand would be asserting the "
                          "check rather than performing it"),
               MINT_KEY: ("a retired identity, issued 2026-08-01..04. It is kept readable "
                          "and is never edited")}
    for key, why in _frozen.items():
        if any(r.split(":", 1)[0] == key for r in remove) or any(k == key for k, _ in add):
            raise TagRefused(
                f"@{key}: is not vocabulary — it is {why}. Tag something else, or edit the "
                f"pile by hand if you truly mean to break it.")
    b.tags = [(k, v) for (k, v) in b.tags if f"{k}:{v}" not in remove]
    for (k, v) in add:
        if (k, v) not in b.tags:
            # BEFORE any digest, for the same reason push's status tag goes there — a digest
            # is placed last at capture so the human's eye meets the vocabulary first and the
            # 64 hex trail off the end of the line (§4.6, argued at `make_block`). A plain
            # `.append` put every later-added tag PAST that wall, which quietly undid the
            # ruling for exactly the tags a human adds by hand and therefore most wants to
            # read. Found live 2026-08-02 tagging a real block: @act: — the most load-
            # bearing key on the bench sheet — landed after the hash.
            b.tags = _insert_before_digest(b.tags, (k, v))
    return True, b


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
    if getattr(args, "name", None):
        notes.extend(validate_tag(NAME_KEY, args.name))
        tags.append((NAME_KEY, args.name))
    source = args.source or "unknown"
    notes.extend(validate_tag("source", source))
    tags.append(("source", source))
    _emit_tag_notes(notes)

    annotations = None
    if args.html:
        body, annotations = capture_html(text)
    else:
        body = capture_plaintext(text)

    # A block cannot know which pile it is being declared into, nor which handles that
    # pile has already issued. Capture DOES know both, and used to pass neither.
    genesis, taken, legacy, ordinal = None, set(), False, 0
    if args.append:
        existing = ""
        if _pile_exists_nonempty(args.append):
            with open(args.append, "r", encoding="utf-8") as fh:
                existing = fh.read()
        if existing:
            genesis, declared = genesis_of(existing, args.append)
            legacy = not declared
            prior = [b for b in parse_pile(existing) if b.id]
            taken = {b.id for b in prior}
            ordinal = len(prior)     # this saying is the (n+1)th declared into this pile
            # `redefined foo`, in the stream you are already reading. gforth announces a
            # redefinition AT THE MOMENT OF THE ACT, unprompted, and that placement is the
            # whole of its value: a redefinition learned about next week is one you have
            # already built on. Nothing is written to the pile and nothing is asked of you.
            if getattr(args, "name", None):
                earlier = definitions_of(prior, args.name)
                if earlier:
                    prior_ids = ", ".join(f"#{b.id}" for b in earlier)
                    sys.stderr.write(
                        f"  redefined {args.name} — {len(earlier)} earlier definition(s) in "
                        f"{args.append}: {prior_ids}\n"
                        f"  They are UNTOUCHED and still resolve by handle; nothing was marked "
                        f"and nothing is owed. From now on `scribe recall {args.name}` finds "
                        f"this one.\n")
        else:
            genesis = gen_genesis(args.ts or now_ts(), args.append)

    block, findings = make_block(body, tags, source, ts=args.ts, annotations=annotations,
                                 genesis=genesis, taken=taken, ordinal=ordinal,
                                 seal=getattr(args, "seal", False))
    out = serialize_block(block, tag_form=args.tag_form)

    if legacy:
        sys.stderr.write(
            f"  NOTE: {args.append} carries no @genesis: line (a pile born before "
            f"2026-08-01), so it carries no birth moment. Nothing now depends on that — "
            f"identity stopped folding the genesis in on 2026-08-05 — so this is a note "
            f"about the pile's history, not a defect. `scribe stamp` adds one; leaving it "
            f"costs nothing.\n")
    if len(block.id) > HANDLE_MIN:
        sys.stderr.write(
            f"  NOTE: handle extended to #{block.id} ({len(block.id)} chars) — a shorter "
            f"one was already taken in this pile. Declared, not renamed away.\n")

    if args.append:
        # A pile is stamped at BIRTH only — never bolted onto an existing one, so that
        # deleting the stamp keeps it deleted (§3.1). Declared, never assumed (§3.6):
        # the stamping is reported, and --no-stamp declines it.
        stamped = False
        if not args.no_stamp and not _pile_exists_nonempty(args.append):
            with open(args.append, "w", encoding="utf-8") as fh:
                fh.write(stamp_for(genesis))
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
        sys.stdout.write(stamp_for("<minted at the pile's birth>"))
        return 0
    with open(args.pile, "r", encoding="utf-8") as fh:
        text = fh.read()
    if is_stamped(text):
        sys.stderr.write(f"{args.pile} is already stamped — unchanged\n")
        return 0
    _refuse_if_malformed(text, args.pile)
    # A retro-fitted pile is given a genesis NOW, and the timestamp says so honestly: it
    # records when this pile was declared to scribe, not when the human started it. Blocks
    # already in the pile keep the handles they have — nothing is re-minted (see
    # `scribe duplicates`), because re-minting would break every relational tag pointing in.
    _atomic_write(args.pile,
                  stamp_for(gen_genesis(now_ts(), args.pile)) + "\n" + text.lstrip("\n"))
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


def _report_findings(findings, block, verb="captured"):
    # Disclosure to stderr so it never contaminates the canonical stdout (§3.7).
    # `verb` because `amend` reuses this and "captured block" would be a small lie about
    # which act just happened — the pile did not grow.
    sys.stderr.write(f"{verb} block #{block.id} ({len(block.body.splitlines())} lines)\n")
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
    n_mint = 0
    for b in blocks:
        for k, v in b.tags:
            # A digest is not vocabulary: one distinct value per block, so listing them would
            # bury the actual vocabulary under a wall of hashes. EXCLUDED and the exclusion is
            # ANNOUNCED — an undisclosed exclusion is the real failure, and this report exists
            # to show what the vocabulary has become.
            if k in (SEAL_KEY, MINT_KEY):
                n_mint += 1
                continue
            per_key.setdefault(k, Counter())[v] += 1
    if not per_key:
        sys.stdout.write("(no tags in this pile)\n")
    if n_mint:
        sys.stdout.write(f"(@{SEAL_KEY}:/@{MINT_KEY}: excluded — {n_mint} digest(s), at most "
                         f"one per block, not vocabulary. `scribe blocks` shows them.)\n")
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
    text, chosen = render_view(blocks, key, value, recent=recent,
                               tag_form=args.tag_form, current=args.current)
    sys.stdout.write(text)
    sys.stderr.write(f"{len(chosen)} block(s) in view {key}:{value} "
                     f"({_order_note(recent)}{', current only' if args.current else ''})\n")
    _note_retired_selector(key)
    bad = _announce_malformed(text_in, args.pile)
    return EXIT_FINDINGS if bad else 0


def cmd_backlinks(args):
    """`scribe backlinks <#id | pile#id> PILE [PILE...]` — every block, in any
    of the given piles, whose tag VALUE names the target. Derived fresh every
    call; nothing is ever written back. Bare `#id` resolves against the FIRST
    named pile (the common case: one pile, asking about its own block)."""
    piles = {}
    bad_total = 0
    for path in args.pile:
        text_in = _read_input(path)
        piles[os.path.abspath(path)] = parse_pile(text_in)
        bad_total += _announce_malformed(text_in, path)

    target_pile_name, _, target_id = args.target.rpartition("#")
    pile_paths = list(piles)
    if not target_pile_name:
        target_pile, same_pile_label = pile_paths[0], None
    else:
        matches = [p for p in pile_paths
                  if os.path.basename(p) == target_pile_name
                  or p == os.path.abspath(target_pile_name)]
        if not matches:
            sys.stderr.write(
                f"REFUSED: {target_pile_name!r} is not among the pile(s) given "
                f"on this command line — list it explicitly so its ids can be "
                f"resolved.\n")
            return 1
        target_pile, same_pile_label = matches[0], target_pile_name

    back = compute_backlinks(piles)
    sys.stdout.write(render_backlinks(target_pile, target_id, back, same_pile_label))
    return EXIT_FINDINGS if bad_total else 0


def cmd_verify(args):
    """`scribe verify PILE [PILE...]` — is each SEALED block still as it was sealed?

    A seal covers the body, the declaration moment and `@source:`, so this speaks to all
    three. It covers nothing else, and it exists only where someone asked for it.

    Read-only, and REPORTS IN FACT-LANGUAGE ONLY. A changed body is not a fault: v1.3.1
    ruled the hand-edit a sanctioned doorway, so this verb says what happened and never
    grades it. There is no severity here and there must never be one.

    EXIT CODES. `0` unless a SEALED block changed; `2` then. Nothing else sets it, and the
    two obvious candidates are refused for the same reason:

      - an UNSEALED block is not an unanswered question, it is a question nobody asked;
      - a LEGACY `@mint:` block is a closed historical set that no future act can shrink, so
        a nonzero exit for it would fire on every run of every existing pile, forever.

    That second one is §3.7-as-amended turned on this verb itself: an alarm that always fires
    defeats disclosure while satisfying it, and teaches the reader to stop reading exit codes.
    The condition is REPORTED IN FULL below; it simply does not colour the exit."""
    undetermined = 0
    for path in args.pile:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
        genesis, declared = genesis_of(text, path)
        rep = audit_seals(parse_pile(text), genesis)
        blocks, states = rep["blocks"], rep["states"]
        n_changed = sum(1 for s in states if s == CHANGED_SINCE_SEAL)
        n_kept = sum(1 for s in states if s == AS_SEALED)
        sys.stdout.write(
            f"{path} — {len(blocks)} block(s): {n_kept} as sealed, "
            f"{n_changed} changed since sealing, {rep['unsealed']} not sealed"
            f"{f', {rep["legacy"]} legacy' if rep["legacy"] else ''}\n")

        # ENUMERATE THE ANOMALY, SUMMARISE THE NORM, AND SAY WHICH WAS DONE. Naming every
        # unsealed block in a pile where sealing is rare is noise that buries the one line
        # worth reading (§4.6) — and under an OPT-IN seal, unsealed is the norm nearly
        # everywhere. So unsealed blocks are never listed; the count is the whole of it.
        # A LEGACY block is not listed either, and that is a change of mind made once the
        # output existed: naming nine of them cost eighteen lines that said nothing the
        # count had not, and there is no per-block act to take from reading them. Where they
        # are is a `grep`, and the line below says which one.
        for b, s in zip(blocks, states):
            if s != CHANGED_SINCE_SEAL:
                continue
            first = (b.body.splitlines() or [""])[0][:56]
            sys.stdout.write(f"    #{b.id}  {b.ts}  {s}\n      {first!r}\n")
        undetermined += n_changed

        if n_changed:
            sys.stdout.write(
                "  'Changed since it was sealed' is a STATEMENT, not a complaint: it is the\n"
                "  second doorway working as ruled — the block was corrected in the file, keeping\n"
                "  that history in your backups rather than in the pile. Precisely, it means the\n"
                "  block is not the one its @sealed: was issued for; a seal covers the BODY, the\n"
                "  TIMESTAMP and @source:, so a change to any of the three says so here. What it\n"
                "  cannot tell you is WHAT changed — no earlier text is kept in the pile, by\n"
                "  design, so only restic or git holds the before.\n")
        if rep["unsealed"]:
            sys.stdout.write(
                f"  {rep['unsealed']} of {len(blocks)} block(s) carry no @sealed:, so THE CHECK DID\n"
                "  NOT RUN for them. That is the ordinary condition and not a gap: sealing is\n"
                "  opt-in (`scribe capture --seal`), for the blocks where you want a body frozen\n"
                "  against later change. Said out loud rather than left to the silence, because a\n"
                "  check that reports only what it looked at reads as a clean bill for the rest.\n")
        if rep["legacy"]:
            sys.stdout.write(
                f"  {rep['legacy']} block(s) carry the RETIRED @mint: (issued 2026-08-01..04) and no\n"
                "  seal. A mint folded the pile's genesis and the block's frozen position into its\n"
                "  value, so it cannot be re-derived from what the file alone says, and this verb\n"
                "  does not try. NOT LISTED — `grep -n \'@mint:\' " + path + "` locates them, and\n"
                "  reading them one by one teaches nothing the count has not already said. To bring\n"
                "  one under the current check, seal it; to leave it, leave it — the @mint: stays\n"
                "  readable and means what it meant. It is simply no longer something this tool\n"
                "  can speak to.\n")
        if not declared:
            sys.stdout.write(
                "  (no @genesis: line — a pile born before 2026-08-01. Nothing now depends on it;\n"
                "  identity stopped folding the genesis in on 2026-08-05.)\n")
    return EXIT_FINDINGS if undetermined else 0



def cmd_duplicates(args):
    """`scribe duplicates PILE [PILE...]` — every handle used by more than one block.

    The auditor half, and Phase 3 of the identity work: duplicates ALREADY EXIST in real
    piles and must not be repaired by the tool. Re-minting them would change ids that
    relational tags already point at, silently breaking the pointer graph to fix a naming
    problem — so this reports and changes nothing (§3.5, actor/auditor). Row 29 exactly:
    allow the collision, DECLARE it, let the human rule.

    Blocks carrying the RETIRED @mint: (issued 2026-08-01..04) are named as such rather
    than presented as though this tool could still speak to them (§3.8). Note the direction:
    legacy is what CARRIES a mint, not what lacks one — until 2026-08-05 it was the other way
    round, and the predicate silently inverted when captures stopped writing mints."""
    total = 0
    legacy_total = 0
    bad_total = 0
    for path in args.pile:
        text_in = _read_input(path)
        blocks = parse_pile(text_in)
        bad_total += _announce_malformed(text_in, path)
        _, declared = genesis_of(text_in, path)
        dupes = duplicate_handles(blocks)
        # INVERTED 2026-08-05, and the inversion was a live defect, not a tidy-up. This
        # read `not ...get(MINT_KEY)` — written when a block WITHOUT a mint was the old one.
        # After v1.4.0 no capture writes a mint at all, so on a pile of blocks captured
        # today it reported every one of them as "minted before the identity split". A
        # predicate that was true of the past and is now true of the present is the most
        # dangerous kind of staleness: the code still runs, and its output is confidently
        # backwards. Found by Schnee asking what `@mint:` was still doing there.
        legacy = [b for b in blocks if b.id and dict(b.tags).get(MINT_KEY)]
        legacy_total += len(legacy)
        real = sum(1 for b in blocks if b.id)
        sys.stdout.write(f"{path} — {real} block(s), {len(dupes)} duplicated handle(s)"
                         # "(legacy pile)" until 2026-08-05 — the SECOND instance of the same
                         # staleness in this one function. A missing @genesis: marked an old
                         # pile only while identity folded the genesis in. It no longer does,
                         # so the absence is now an ordinary fact about a pile's history and
                         # is reported as one. The fact stays; the judgement goes.
                         f"{'' if declared else ', no @genesis: line'}\n")
        if legacy:
            sys.stdout.write(
                f"  {len(legacy)} block(s) carry the RETIRED @mint: (issued 2026-08-01..04). "
                f"Named, not upgraded: nothing here rewrites them.\n")
        for h in sorted(dupes):
            bs = dupes[h]
            sys.stdout.write(f"  #{h} — {len(bs)} blocks\n")
            for b in bs:
                first = (b.body.splitlines() or [""])[0][:60]
                sys.stdout.write(f"      {b.ts}  {first!r}\n")
            # WHAT SEPARATES TWO BLOCKS SHARING A HANDLE, after v1.4.0. It used to be their
            # distinct @mint:s. It is now the DECLARING MOMENT — which is not a substitute
            # for the mint, it is what the mint was mostly made of, now read directly off
            # the header instead of through a digest. Two moments, two declarings, two
            # sayings; the tool can say that much and no more.
            moments = {b.ts for b in bs}
            if len(moments) == len(bs):
                sys.stdout.write(
                    "      ^ distinct declaring moments — these ARE different sayings that "
                    "happen to share a handle. Lengthen one by hand to disambiguate.\n")
            else:
                sys.stdout.write(
                    "      ^ same declaring moment: whether these are one saying or two "
                    "cannot be decided by the tool. Yours to rule.\n")
        total += len(dupes)
    if not total:
        sys.stdout.write("no duplicated handles\n")
    if legacy_total:
        sys.stdout.write(
            f"\n{legacy_total} block(s) across all piles carry the retired @mint:. They are "
            f"not broken and are not upgraded: an id that has worked since capture keeps "
            f"working, and reissuing one would break every relational tag pointing at it.\n")
    return EXIT_FINDINGS if (total or bad_total) else 0


def cmd_activate(args):
    """`scribe activate <condition> PILE [PILE...] [--key awaits]` — every
    block, in any of the given piles, currently declaring interest in this
    condition. Derived fresh every call; nothing is ever written back, and
    nothing is auto-promoted — the human rules every promotion, always."""
    piles = {}
    bad_total = 0
    for path in args.pile:
        text_in = _read_input(path)
        piles[os.path.abspath(path)] = parse_pile(text_in)
        bad_total += _announce_malformed(text_in, path)
    hits = compute_activations(piles, args.condition, key=args.key)
    sys.stdout.write(render_activate(args.condition, hits, key=args.key))
    return EXIT_FINDINGS if bad_total else 0


def cmd_converges(args):
    """`scribe converges PILE PILE [...] [--by KEY] [--no-cites]` — a first
    structural attempt at Charter §3.15's still-open gap: candidate DNA shared
    between different projects that was never explicitly cross-referenced.
    Every finding is a literal match, disclosed as a candidate only."""
    piles = {}
    bad_total = 0
    for path in args.pile:
        text_in = _read_input(path)
        piles[os.path.abspath(path)] = parse_pile(text_in)
        bad_total += _announce_malformed(text_in, path)
    tag_groups = compute_convergences(piles, tag_key=args.by)
    citation_groups = {} if args.no_cites else compute_citation_convergences(piles)
    sys.stdout.write(render_convergences(tag_groups, citation_groups))
    return EXIT_FINDINGS if bad_total else 0


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
    joiner = args.joiner.replace("\\n", "\n") if args.joiner is not None else None
    text, chosen = render_export(blocks, key, value, recent=recent, bare=args.bare, joiner=joiner)
    sys.stdout.write(text)
    sys.stderr.write(f"exported {len(chosen)} block(s) of {key}:{value} "
                     f"({_order_note(recent)})\n")
    _note_retired_selector(key)
    bad = _announce_malformed(text_in, args.pile)
    return EXIT_FINDINGS if bad else 0


def cmd_verify_export(args):
    """`scribe verify-export EXPORTED_FILE selector PILE` — has the pile
    drifted since this file was exported? Never repairs; reports only."""
    with open(args.exported, "r", encoding="utf-8") as fh:
        exported_text = fh.read()
    manifest = find_export_manifest(exported_text)
    text_in = _read_input(args.pile)
    blocks = parse_pile(text_in)
    key, value = _selector(args.selector)
    sys.stdout.write(render_verify_export(manifest, blocks, key, value,
                                          recent=args.recent))
    bad = _announce_malformed(text_in, args.pile)
    return EXIT_FINDINGS if bad else 0


def cmd_push(args):
    view_text = _read_input(args.view)
    with open(args.pile, "r", encoding="utf-8") as fh:
        pile_text = fh.read()
    _refuse_if_malformed(pile_text, args.pile)
    pile_blocks = parse_pile(pile_text)
    genesis, declared = genesis_of(pile_text, args.pile)
    pile_blocks, report = push_view(view_text, pile_blocks, genesis=genesis)
    if not declared and report["superseded"]:
        sys.stderr.write(
            f"  NOTE: {args.pile} carries no @genesis: line (a pile born before 2026-08-01); "
            f"the superseding block's mint falls back to the pile's PATH alone.\n")
    if report.get("ambiguous"):
        sys.stderr.write(
            f"REFUSED: nothing written to {args.pile}. "
            f"{len(report['ambiguous'])} handle(s) in this view name more than one block "
            f"in the pile, so there is no way to know which block your edit belongs to:\n")
        for h, bs in report["ambiguous"].items():
            sys.stderr.write(f"  #{h} names {len(bs)} blocks:\n")
            for b in bs:
                # The @mint: column was dropped 2026-08-05. It printed `(no @mint: — a le…`
                # for any block captured after the retirement — a truncated apology where a
                # discriminator used to be. The declaring moment is what separates them now,
                # and it was always already on the line.
                first = (b.body.splitlines() or [""])[0][:60]
                sys.stderr.write(f"      {b.ts}  {first!r}\n")
        sys.stderr.write(
            "  These are pre-existing duplicates; nothing is re-minted, because that would\n"
            "  break every relational tag pointing at them (row 29: declare the collision,\n"
            "  do not rename it away). Run `scribe duplicates PILE` for the full report,\n"
            "  then disambiguate by hand — the ruling is yours.\n")
        return 1
    # Write the pile back only if something changed; disclose everything (§3.7).
    if report["superseded"]:
        _atomic_write(args.pile, serialize_pile(pile_blocks))
    n = len(report["superseded"])
    sys.stderr.write(
        f"pushed home: {n} block(s) superseded — nothing was overwritten\n"
        if n else "pushed home: nothing changed (no body differed)\n")
    for old, new in report["superseded"]:
        sys.stderr.write(f"  #{old} -> #{new}   (#{old} keeps its body and its @mint:, and "
                         f"gains one tag: @superseded:#{new})\n")
    if n:
        sys.stderr.write(
            "  The old blocks are still there and still say what they said. To correct one\n"
            "  WITHOUT leaving that history in the pile, edit it directly in your editor —\n"
            "  restic keeps that history instead. Both doors are yours; this one is push's.\n")
    if report["already_superseded"]:
        sys.stderr.write(
            f"  SKIPPED {len(report['already_superseded'])} block(s) already superseded — "
            f"your view is stale, and pushing it would fork the chain:\n")
        for old, by in report["already_superseded"]:
            sys.stderr.write(f"      #{old} was superseded by #{by}. Regenerate the view and "
                             f"edit #{by} instead.\n")
    if report["missing"]:
        sys.stderr.write(f"  WARNING: {len(report['missing'])} view block(s) had no "
                         f"matching #id in the pile: {', '.join('#'+i for i in report['missing'])}\n")
    if report["tag_drift"]:
        sys.stderr.write(f"  NOTE: header tags differ for {', '.join('#'+i for i in report['tag_drift'])}"
                         " — NOT applied (use `tag` or edit the pile); the superseding block "
                         "inherits the OLD block's tags\n")
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
    try:
        ok, b = add_tags(blocks, args.id.lstrip("#"), add=add, remove=args.remove)
    except AmbiguousHandle as e:
        sys.stderr.write(f"REFUSED: nothing written to {args.pile}. {e}\n")
        sys.stderr.write("  Type more characters, or run `scribe duplicates PILE`.\n")
        return 1
    if not ok:
        sys.stderr.write(f"no block with id #{args.id.lstrip('#')}\n")
        return 1
    _atomic_write(args.pile, serialize_pile(blocks, tag_form=args.tag_form))
    sys.stderr.write(f"#{b.id} tags now: {' '.join(f'@{k}:{v}' for k, v in b.tags)}\n")
    return 0


def cmd_recall(args):
    """`scribe recall NAME PILE [--all]` — what does this name find?

    FORTH'S DICTIONARY LOOKUP, and the verb is named for the act rather than the structure.
    A name resolves to its most recently ADMITTED definition; the earlier ones are still in
    the pile, still addressable, and were never marked. `--all` shows the lineage, which is
    what `words` would show you about a shadowed definition.

    Read-only. It computes; it never writes. There is no chain in the pile to keep in step
    with, which is the whole point — a redefinition costs the keeper nothing at all."""
    text_in = _read_input(args.pile)
    blocks = parse_pile(text_in)
    found = definitions_of(blocks, args.name)
    if not found:
        sys.stderr.write(f"no block named @{NAME_KEY}:{args.name} in {args.pile}\n")
        defined = sorted({v for b in blocks for k, v in b.tags if k == NAME_KEY})
        if defined:
            sys.stderr.write(f"  names in this pile: {' '.join(defined)}\n")
        else:
            sys.stderr.write(
                f"  this pile carries no @{NAME_KEY}: tags at all. A name is opt-in: capture "
                f"with --name to give a saying one, and say it again under the same name "
                f"whenever it improves.\n")
        _announce_malformed(text_in, args.pile)
        return 1

    shown = found if args.all else found[-1:]
    sys.stdout.write("".join(serialize_block(b, tag_form=args.tag_form) + "\n"
                             for b in shown))
    if args.all:
        sys.stderr.write(
            f"{len(found)} definition(s) of {args.name}, arrival order — the last is what "
            f"the name finds.\n")
    elif len(found) > 1:
        # §3.8: an instrument must be able to say what it did not show. Silently handing
        # back the live definition would make a name look like it had only ever had one.
        earlier = ", ".join(f"#{b.id}" for b in found[:-1])
        sys.stderr.write(
            f"#{found[-1].id} — the live definition of {args.name}.\n"
            f"  NOT SHOWN: {len(found) - 1} earlier definition(s) still in this pile "
            f"({earlier}). They are untouched and unmarked; `--all` shows them.\n")
    else:
        sys.stderr.write(f"#{found[-1].id} — the only definition of {args.name}.\n")
    bad = _announce_malformed(text_in, args.pile)
    return EXIT_FINDINGS if bad else 0


def cmd_names(args):
    """`scribe names PILE [PILE...]` — every name, and which of its definitions is live.

    THE `redefined` REPORT, DERIVED. Nothing here is stored anywhere: it is recomputed from
    the pile on every call, exactly as `backlinks` is, and for the same stated reason —
    "back-references are derived, never hand-written". A pile that recorded its own
    redefinitions would be maintaining a chain, and maintaining a chain is the paperwork
    this whole mechanism exists to abolish."""
    rc = 0
    for path in args.pile:
        text_in = _read_input(path)
        blocks = parse_pile(text_in)
        names = {}
        for b in blocks:
            if not b.id:
                continue
            for k, v in b.tags:
                if k == NAME_KEY:
                    names.setdefault(v, []).append(b)
        if not names:
            sys.stdout.write(f"{path} — no named blocks.\n")
            continue
        redefined = {n: bs for n, bs in names.items() if len(bs) > 1}
        sys.stdout.write(
            f"{path} — {len(names)} name(s), {len(redefined)} redefined\n")
        for n in sorted(names):
            bs = names[n]
            live = bs[-1]
            if len(bs) == 1:
                sys.stdout.write(f"  {n}  -> #{live.id}\n")
            else:
                older = " ".join(f"#{b.id}" for b in bs[:-1])
                sys.stdout.write(
                    f"  {n}  -> #{live.id}   ({len(bs)} definitions; earlier: {older})\n")
        if redefined:
            sys.stdout.write(
                "  A redefined name is not a problem and nothing is owed on it. The earlier\n"
                "  blocks are untouched, unmarked, and still resolve by handle — what moved\n"
                "  is what the NAME finds. This listing is computed fresh and never written\n"
                "  back, so there is no chain here to keep in step.\n")
        rc = EXIT_FINDINGS if _announce_malformed(text_in, path) else rc
    return rc


def cmd_amend(args):
    """`scribe amend #id PILE [--from FILE]` — correct a block's body IN PLACE.

    THE DOORWAY THAT WAS MISSING, and its absence is what made the pile feel like it was
    corralling you. scribe modelled ONE kind of change and called it `push`: append a new
    block, mark the old superseded. That is right for a REVISION — the thinking moved, and
    a new saying deserves its own identity and its own place in the arrival order.

    But there are two kinds of change and the tool modelled one:

      REVISION   the thinking moved. A new saying.  -> `push`: append + supersede.
      CORRECTION the saying is the same and was badly expressed. A word is wrong; you
                 wrote it five minutes ago.         -> `amend`: in place. Nothing appended,
                 nothing superseded, nothing reported. NOTHING HAPPENED.

    Before 2026-08-05 there was no third doorway and the missing one was the common case, so
    a typo either grew the pile by a whole block or drove you out of the tool to a text
    editor. It could not exist while identity contained the body: every correction would have
    been an identity event, so the tool would have had to either change the block's identity
    (breaking every pointer to it) or report it forever as edited. **`amend` is not a feature
    added on top of the identity change. It is the identity change, seen from the user's
    side** — the only thing that had to be true first was that a body is not part of what a
    block IS.

    THE GUARD, AND IT IS A REFUSAL, NOT A WARNING. `amend` refuses if any block in this pile
    — or in any pile named with `--also` — points at the target — `@ref:`, `@replaces:`, `@overrules:`, the whole pointer family.
    The wording under a pointer is exactly what `push` exists to protect: someone wrote
    "@ref:#a4f2" about text that said something, and silently changing that text rewrites
    their citation. **If something points at it, it is no longer only yours to correct, and
    it wants a revision.** The refusal names what points at it, so the choice is informed.

    IT ALSO REFUSES A SEALED BLOCK, and that is what makes `--seal` mean anything. A seal is
    a declaration that this body is to be held as it stands. Amending under a seal would
    either break the seal silently or quietly reissue it — the first is damage, the second
    is a tool forging a claim on your behalf. Break the seal by hand if you mean to.

    AND IT RECORDS NOTHING. No `@amended:`, no counter, no trace. That is a ruling, not an
    oversight, and it is the gForth build's answer adopted here: A TYPO IS NOT AN EVENT. A
    pile that logged every corrected word would be back to accumulating, which is the thing
    that made the old pile feel greedy. What the pile is FOR is sayings; the history of how
    a sentence reached its wording lives in restic and git, which is where §3.1 has always
    put the second doorway's history."""
    with open(args.pile, "r", encoding="utf-8") as fh:
        pile_text = fh.read()
    _refuse_if_malformed(pile_text, args.pile)
    blocks = parse_pile(pile_text)
    handle = args.id.lstrip("#")
    try:
        target = resolve_handle(blocks, handle)
    except AmbiguousHandle as e:
        sys.stderr.write(f"REFUSED: nothing written to {args.pile}. {e}\n")
        return 1
    if target is None:
        sys.stderr.write(f"no block with id #{handle} in {args.pile}\n")
        return 1

    if _tag_value(target, SEAL_KEY):
        sys.stderr.write(
            f"REFUSED: #{target.id} carries @sealed: — it was declared as a body to be held\n"
            f"  as it stands, and amending it would either break that seal or forge a new\n"
            f"  one in your name. Neither is this tool's to do.\n"
            f"  If the saying moved, `scribe push` it. If the seal was a mistake, remove it\n"
            f"  by hand — that is your doorway and it stays open.\n")
        return 1

    # RULED 2026-08-05. The first build checked THIS pile only and said so, which satisfies
    # §3.8 and still leaves a citation in another pile silently rewritable. `--also` widens
    # the check to piles you name. It is opt-in because a tool that hunted for piles on its
    # own would be guessing at which ones are related, and a guess here is a wrong refusal —
    # the most expensive kind, because it sends you to `push` for a typo.
    piles = {os.path.abspath(args.pile): blocks}
    for other in (getattr(args, "also", None) or []):
        other_abs = os.path.abspath(other)
        if other_abs in piles:
            continue
        piles[other_abs] = parse_pile(_read_input(other))
    back = compute_backlinks(piles)
    pointers = [p for (pile_path, tid), ps in back.items()
                if tid == target.id and pile_path == os.path.abspath(args.pile)
                for p in ps]
    if pointers:
        sys.stderr.write(
            f"REFUSED: #{target.id} is pointed at by {len(pointers)} block(s) in this pile:\n")
        for fp, key, from_id, _ts in pointers:
            where = "" if os.path.abspath(fp) == os.path.abspath(args.pile) \
                    else f"   [in {os.path.basename(fp)}]"
            sys.stderr.write(f"    #{from_id}  @{key}:#{target.id}{where}\n")
        sys.stderr.write(
            "  Someone wrote that pointer ABOUT the wording that is there now, so changing it\n"
            "  silently rewrites their citation. This is exactly the case `push` exists for:\n"
            f"  `scribe push` appends the new wording and marks #{target.id} superseded, so the\n"
            "  pointer still resolves to what it was written about and the reader is told.\n"
            f"  (Checked: {len(piles)} pile(s) — {', '.join(sorted(os.path.basename(p) for p in piles))}.\n"
            "  A pointer from a pile not named here is NOT seen. Pass `--also PILE` to widen\n"
            "  the check; scribe will not go looking for related piles on its own.)\n")
        return 1

    new_body = _read_input(args.source_file).rstrip("\n")
    if not new_body.strip():
        sys.stderr.write("REFUSED: the replacement body is empty. An amendment that empties a\n"
                         "  block is a deletion, and deletion is a hand-edit, not a verb here.\n")
        return 1
    if new_body == target.body:
        sys.stderr.write(f"#{target.id} unchanged — the replacement is byte-identical. "
                         f"Nothing written.\n")
        return 0

    audited, findings = loss_check(new_body)
    old_first = (target.body.splitlines() or [""])[0][:64]
    target.body = audited
    _atomic_write(args.pile, serialize_pile(blocks, tag_form=args.tag_form))
    sys.stderr.write(
        f"#{target.id} amended in place. Identity unchanged, nothing appended, nothing "
        f"recorded.\n  was: {old_first!r}\n  now: {(audited.splitlines() or [''])[0][:64]!r}\n")
    _report_findings(findings, target, verb="amended")
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
    c.add_argument("--name", metavar="NAME",
                   help="give this saying a NAME you can say again. Capturing the same "
                        "--name later redefines it: the name follows you to the new block, "
                        "the earlier ones are untouched and unmarked, and nothing is "
                        "appended or owed. `scribe recall NAME` finds the live one")
    c.add_argument("--seal", action="store_true",
                   help="add @sealed: — freeze this body, timestamp and @source: so "
                        "`scribe verify` can say whether they changed. Opt-in, per block, "
                        "for the ones you want held; ordinary blocks stay correctable")
    c.add_argument("--tag-form", choices=["repeated", "comma"], default="repeated")
    c.add_argument("--ts", help="override timestamp (testing)")
    c.set_defaults(func=cmd_capture)

    am = sub.add_parser("amend",
                        help="correct a block's body IN PLACE — no new block, no "
                             "supersession, nothing recorded. For a typo, not a revision; "
                             "refuses if anything points at the block, or if it is sealed")
    # ORDER MATCHES `tag`, its closest sibling: both edit one block, in place, by id. The
    # first draft here took (pile, id) — the order `push` and `verify` use, because those
    # act on a WHOLE pile — and two verbs that do the same kind of thing disagreeing about
    # their own arguments is the sort of drift that gets discovered by a lost edit.
    am.add_argument("id", help="block id, e.g. 2644 or #2644")
    am.add_argument("pile")
    am.add_argument("--also", action="append", metavar="PILE",
                    help="also check this pile for pointers at the block (repeatable). "
                         "Without it the check sees only PILE, and says so")
    am.add_argument("--from", dest="source_file", default="-", metavar="FILE",
                    help="read the replacement body from FILE (default: stdin)")
    am.add_argument("--tag-form", choices=["repeated", "comma"], default="repeated")
    am.set_defaults(func=cmd_amend)

    rc = sub.add_parser("recall",
                        help="what does this name find? — the newest block carrying "
                             "@name:NAME. Forth's dictionary lookup; read-only")
    rc.add_argument("name")
    rc.add_argument("pile")
    rc.add_argument("--all", action="store_true",
                    help="show every definition of the name, arrival order (the last is live)")
    rc.add_argument("--tag-form", choices=["repeated", "comma"], default="repeated")
    rc.set_defaults(func=cmd_recall)

    nm = sub.add_parser("names",
                        help="every @name: in the pile and which definition is live — "
                             "derived fresh, never written back")
    nm.add_argument("pile", nargs="+")
    nm.set_defaults(func=cmd_names)

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
    v.add_argument("--current", action="store_true",
                   help="hide blocks a later block has superseded (declared in the view "
                        "header; they stay in the pile)")
    v.add_argument("--recent", action="store_true", help="most-recent first (salience)")
    v.add_argument("--tag-form", choices=["repeated", "comma"], default="repeated")
    v.set_defaults(func=cmd_view)

    bl = sub.add_parser("backlinks",
                        help="derive every block whose tag VALUE names this one (the "
                             "reverse of @ref:/@overrules:/etc.) — computed fresh, "
                             "never written back")
    bl.add_argument("target", help="#id (this pile) or pile.txt#id (a named pile)")
    bl.add_argument("pile", nargs="+", help="one or more piles to search across")
    bl.set_defaults(func=cmd_backlinks)

    dp = sub.add_parser("duplicates",
                        help="report handles used by more than one block — read-only; "
                             "declares collisions, never repairs them")
    dp.add_argument("pile", nargs="+", help="one or more piles to audit")
    dp.set_defaults(func=cmd_duplicates)

    vf = sub.add_parser("verify",
                        help="is each block still the one its @mint: was issued for? "
                             "re-derives "
                             "every @mint: from the file itself and says what happened — "
                             "'as captured' / 'edited in place since capture'. Read-only, "
                             "no severities: a hand-edit is a sanctioned act, not a fault")
    vf.add_argument("pile", nargs="+", help="one or more piles to audit")
    vf.set_defaults(func=cmd_verify)

    ac = sub.add_parser("activate",
                        help="derive every block currently declaring interest in a "
                             "named condition via @awaits:/etc. (the query half of a "
                             "dpkg-trigger-style interest/activate pair) — read-only, "
                             "never promotes")
    ac.add_argument("condition", help="the exact condition string to match, e.g. "
                                      "schnees-ruling-on-whether-to-check-the-vessel-repos")
    ac.add_argument("pile", nargs="+", help="one or more piles to search across")
    ac.add_argument("--key", default="awaits", metavar="KEY",
                    help="which tag key to match (default: awaits; @dissolves: is "
                         "the other witness-shaped key in this vocabulary)")
    ac.set_defaults(func=cmd_activate)

    cv = sub.add_parser("converges",
                        help="derive candidate DNA shared between DIFFERENT piles that "
                             "was never explicitly cross-referenced: shared tag-values "
                             "and shared Charter-clause citations. Disclosed candidates "
                             "only — never asserted as real relations, never merged")
    cv.add_argument("pile", nargs="+", help="two or more piles (different projects) "
                                            "to compare")
    cv.add_argument("--by", default=None, metavar="KEY",
                    help="restrict the tag-value scan to one key (default: all keys)")
    cv.add_argument("--no-cites", action="store_true",
                    help="skip the body-text Charter-clause citation scan")
    cv.set_defaults(func=cmd_converges)

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
    e.add_argument("--joiner", default=None,
                   help="how to join bodies (default: the prose separator, "
                        r"'\n\n---\n\n'). A bare '---' line is a Python SyntaxError, "
                        r"so a code export that must run wants --joiner '\n\n' "
                        "instead — scribe does not decide what a body is, only offers "
                        r"the join. '\n' is interpreted as a newline.")
    e.set_defaults(func=cmd_export)

    ve = sub.add_parser("verify-export",
                        help="check whether a previously-exported file has gone stale "
                             "relative to the pile it came from (content fingerprint, "
                             "never repairs — Knuth's WEB checksum principle applied "
                             "to a whole derived view)")
    ve.add_argument("exported", help="the previously-exported file to check")
    ve.add_argument("selector", help="the same key:value used at export time")
    ve.add_argument("pile")
    ve.add_argument("--recent", action="store_true",
                    help="pass if the original export used --recent")
    ve.set_defaults(func=cmd_verify_export)

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
