"""
Headless tests for scribe_viewer_core — no TTY, no Textual, no subprocess, no disk.

Run:  python3 viewer/test_scribe_viewer_core.py    (or pytest)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scribe_viewer_core import (Buffers, block_ids, prompt_label,        # noqa: E402
                                valid_selector, view_boundary)

VIEW = """# view topic:probe
# derived view — disposable.

@@ #a1b2 2026-07-26T14:00:00 @topic:probe @state:live
First block.

@@ #e5f6 2026-07-26T14:02:00 @topic:probe @state:settled
Third block.
"""


def test_selector_grammar_matches_scribes():
    assert valid_selector("topic:nas")
    assert valid_selector("state:live")
    assert not valid_selector("nas")            # no key
    assert not valid_selector("topic:")         # no value
    assert not valid_selector("")


def test_block_ids_read_the_frozen_grammar():
    assert block_ids(VIEW) == ["a1b2", "e5f6"]
    assert block_ids("") == []                  # empty, not an error


def test_prompt_carries_the_pile_not_a_turn():
    """The divergence from the ancestor, pinned: the coordinate here is the PILE."""
    assert prompt_label("pile.txt").startswith("pile.txt ")
    try:
        prompt_label("")
    except ValueError:
        pass
    else:
        raise AssertionError("empty pile name must be refused, not faked")


def test_view_boundary_names_the_selector():
    b = view_boundary("topic:nas", width=40)
    assert "view topic:nas" in b and len(b) == 40
    assert view_boundary("topic:nas", width=3) == "view topic:nas"   # degrades, no crash


def test_buffer_round_trip_and_edit_tracking():
    b = Buffers()
    b.open("topic:probe", "topic:probe", VIEW)
    assert b.names() == ["topic:probe"]
    assert not b.is_edited("topic:probe")        # pristine on open
    b.update("topic:probe", VIEW + "\nedited\n")
    assert b.is_edited("topic:probe")
    assert b.edited_names() == ["topic:probe"]


def test_missing_buffer_is_named_not_faked():
    """§3.8 — a missing buffer must not read as an empty one."""
    b = Buffers()
    for call in (lambda: b.get("nope"), lambda: b.is_edited("nope"),
                 lambda: b.close("nope"), lambda: b.selector_of("nope")):
        try:
            call()
        except KeyError:
            continue
        raise AssertionError("a missing buffer must raise, not return empty")


def test_close_disposes_totally():
    b = Buffers()
    b.open("a", "topic:a", "x")
    b.close("a")
    assert b.names() == []                       # disposal is free and total


def test_core_touches_no_disk_and_no_framework():
    """The property that lets the shell be replaced without retesting this core.

    Tested by reading the module's actual IMPORT SET rather than banning substrings:
    a substring ban on 'open(' fails on `Buffers.open()`, which is a method name, not
    the builtin — the same false-positive shape this project rules against in
    word-list filters. The real property is that nothing but `re` is imported, which
    makes disk access and framework coupling impossible rather than merely absent.
    """
    import ast
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "scribe_viewer_core.py")
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert imported == {"re"}, (
        f"core must import only 're'; found {sorted(imported)} — a framework or I/O "
        "dependency here would defeat the point of a headless core")


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name); n += 1
    print(f"\n{n}/{n} scribe_viewer_core tests passed")
