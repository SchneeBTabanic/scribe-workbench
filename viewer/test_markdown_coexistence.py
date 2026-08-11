"""
Can markdown live inside a pile without fighting scribe's grammar?
=================================================================

AUDITED AND ANSWERED 2026-07-26. Run against the frozen `scribe.py` grammar, not
against a description of it.

THE QUESTION. The pile is plain text; people write markdown. If a block body
carries `# headings`, `- lists`, `> quotes` or fenced code, can any of it
impersonate a block boundary and split the canonical?

THE ANSWER: NO, and by construction rather than by luck. `HEADER_RE` requires
THREE elements on one line — `@@`, then `#<id>`, then a timestamp field:

    ^@@ +#(?P<id>\\S+) +(?P<ts>\\S+)(?: +@key:val)*\\s*$

Markdown has no line-leader beginning `@@`. Not one of its constructs can satisfy
even the first element, so the grammars are DISJOINT, and this test pins that.

THE ONE REAL COLLISION, named rather than hidden: the only thing that can
impersonate a boundary is **a real scribe header** — pasting a pile excerpt into a
block body splits that block in two. Not a markdown problem; a self-quotation
problem, and the same one the walker's sample was built to expose.

WHY THIS TEST LIVES IN viewer/ AND NOT BESIDE scribe.py: `scribe.py` and
`test_scribe.py` are v1.0-frozen. This is a property the VIEWER depends on — it is
the thing that would ever render markdown — so the question is asked from the side
that needs the answer, and the frozen artifact stays untouched.

Run:  python3 viewer/test_markdown_coexistence.py
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIBE = os.path.join(os.path.dirname(HERE), "scribe.py")

# Read the boundary grammar OUT OF the frozen source rather than restating it, so
# this audit cannot quietly disagree with the thing it audits (§3.13).
with open(SCRIBE, encoding="utf-8") as _fh:
    _m = re.search(r"^HEADER_RE = re\.compile\(r\"(?P<pat>.+)\"\)$", _fh.read(), re.M)
assert _m, "HEADER_RE not found in scribe.py — the audit cannot proceed blind"
HEADER_RE = re.compile(_m.group("pat"))

MARKDOWN_LEADERS = [
    "# Heading", "## Sub", "###### Six deep", "- bullet", "* bullet", "+ bullet",
    "1. ordered", "10) ordered", "> block quote", ">> nested quote",
    "```python", "~~~", "    four-space code", "\tindented with a tab",
    "| table | row |", "---", "***", "___", "[ref]: http://example.com",
    "<div>", "![img](x.png)", "Term", ": definition", "- [ ] task", "- [x] done",
]


def test_no_markdown_leader_can_impersonate_a_block_boundary():
    """The load-bearing fact. If this ever fails, markdown in a pile became unsafe."""
    for line in MARKDOWN_LEADERS:
        assert not HEADER_RE.match(line), \
            f"markdown leader impersonates a block boundary: {line!r}"


def test_the_boundary_needs_all_three_elements():
    """Shows WHY the disjointness holds, so a future reader can see the mechanism
    rather than trusting the list above to have been exhaustive."""
    assert not HEADER_RE.match("@@ turn 42")                       # no #id
    assert not HEADER_RE.match("@@ #id")                           # no timestamp
    assert not HEADER_RE.match("@@#id 2026-07-26T10:00:00")        # no space
    assert HEADER_RE.match("@@ #id 2026-07-26T10:00:00")           # all three
    assert HEADER_RE.match("@@ #id 2026-07-26T10:00:00 @topic:x")  # + tags


def test_the_one_real_collision_is_self_quotation():
    """NAMED, not hidden (§3.8): a pasted pile excerpt DOES split a block. This is
    the honest limit, and it is a self-quotation problem, not a markdown one."""
    assert HEADER_RE.match("@@ #other 2026-01-01T00:00:00 @topic:quoted")


def _run(args, stdin=None):
    p = subprocess.run([sys.executable, SCRIBE] + args, input=stdin,
                       capture_output=True, text=True)
    return p.stdout, p.stderr


def test_markdown_survives_a_real_round_trip_byte_for_byte():
    """End to end against frozen scribe: a body full of markdown, derived into a
    view and pushed home, comes back unchanged."""
    body = ("# A heading\n\nProse with **bold** and a [link](http://example.com).\n\n"
            "- one\n- two\n\n> quoted\n\n```python\ndef f(): return 1\n```\n\n## Sub\n")
    pile = "@@ #m001 2026-07-26T10:00:00 @topic:md @state:live\n" + body
    d = tempfile.mkdtemp(prefix="md-coexist-")
    path = os.path.join(d, "pile.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(pile)

    view, _ = _run(["view", "topic:md", path])
    assert "**bold**" in view and "```python" in view, "markdown must reach the view"
    _run(["push", "-", path], stdin=view)
    with open(path, encoding="utf-8") as fh:
        assert fh.read() == pile, "the round trip must not alter one byte"


def test_an_edit_lands_and_view_comments_never_leak_into_the_pile():
    """The view carries its own `#`-prefixed disposability notice. Those lines are
    markdown-shaped too — and they must never be pushed home as content."""
    pile = ("@@ #m002 2026-07-26T10:00:00 @topic:md @state:live\n"
            "## original heading\n")
    d = tempfile.mkdtemp(prefix="md-coexist-")
    path = os.path.join(d, "pile.txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(pile)

    view, _ = _run(["view", "topic:md", path])
    # Since 2026-08-11 every header line carries VIEW_MARK, so scribe can tell its own
    # words from the human's above the first block. The old test asserted a bare
    # `# view topic:md`, which a human could type by hand and which push therefore could
    # not distinguish from a note-to-self — the ambiguity the mark removes.
    assert view.startswith("# scribe: view topic:md"), "the view's own comment header moved"
    assert all(ln.startswith("# scribe:") for ln in view.split("\n\n")[0].split("\n")), \
        "EVERY header line must declare that scribe wrote it, not just the first"
    edited = view.replace("## original heading", "## edited heading")
    _run(["push", "-", path], stdin=edited)

    with open(path, encoding="utf-8") as fh:
        after = fh.read()
    assert "## edited heading" in after, "the edit must land"
    assert "# scribe:" not in after, "view comments must never enter the pile"
    assert "view topic:md" not in after
    assert "# derived view" not in after


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name); n += 1
    print(f"\n{n}/{n} markdown-coexistence tests passed")
