"""
scribe_viewer_core.py — the framework-agnostic core of the scribe view-buffer shell.
====================================================================================

PROVENANCE — this is a DESCENDANT, not a mirror.
    Forked from `GTPS-Agent/viewer_core.py` @ commit 4c88316,
    blob sha256 f5ac4ebf9a349a27…, on 2026-07-26 (GATE C ruling).
    **Divergence is intended and immediate**: the agent's core models a read-only
    TRANSCRIPT of turns and roles — read-only by construction, because the agent's
    statelessness guarantee requires it. This one models PILE VIEWS: named buffers
    of derived text, their block ids, and whether the human has edited them — because
    scribe's viewer must carry the push-by-#id round trip home, which the agent's core
    must never grow.
    One ancestor, two truths, biography recorded. There is deliberately NO drift-guard
    between them: a test pinning them identical would fight the divergence above and
    fail every time this file legitimately grew (§3.13 forbids two hand-maintained
    copies of ONE truth — these are two).
    If a bug is ever fixed in one and bites the other, THAT is the encounter that would
    earn extracting a genuinely shared contract. Earned then, not speculated now.

WHAT THIS IS. The pure, headless-testable heart of the scribe shell: selector
validation, tab labelling, and an in-memory registry of derived views. No TTY, no
Textual, no subprocess, no disk — so the shell that wraps it can be replaced without
touching anything tested here.

THE LAWS IT KEEPS (all pre-existing; none invented here)
  * §4.3 — the pile is a FILE (persistent, cat-readable with every tool dead); a view
    is a disposable cache. Buffer-ness is derived-ness made visible. Nothing in this
    module writes to disk, and no buffer is ever the canonical anything.
  * §4.6 view-never-doorway — this is optional. `scribe view … | xed -` and plain
    `scribe` must keep working with this uninstalled.
  * §3.8 — an unknown buffer name or a malformed selector is NAMED, never silently
    treated as empty.
"""

import re

GLYPH = "›"

# scribe's own selector grammar: key:value, e.g. topic:nas / state:live.
_SELECTOR = re.compile(r"^(?P<key>[a-z][a-z0-9_-]*):(?P<val>\S+)$")

# scribe's block boundary, as frozen in scribe.py: `@@ #<id> <ts> @tag:v …`
_BLOCK = re.compile(r"^@@\s+#(?P<id>\S+)", re.MULTILINE)


def valid_selector(selector: str) -> bool:
    """True for scribe's `key:value` selector form. Used to refuse a bad selector
    with a named reason rather than opening an empty tab (§3.8)."""
    return bool(_SELECTOR.match(selector or ""))


def prompt_label(pile_name: str) -> str:
    """The input prompt, stamped with the pile in play — the scribe analogue of the
    agent's turn-stamped prompt. The pile is the coordinate here, as the turn is
    there."""
    if not pile_name:
        raise ValueError("pile_name must be non-empty")
    return f"{pile_name} {GLYPH} "


def view_boundary(selector: str, width: int = 60) -> str:
    """A visible rule naming a derived view, e.g. '──── view topic:nas ────'.
    Mirrors the ancestor's `@@ turn N` rule in shape and purpose (a boundary the
    human can see), but carries a SELECTOR, not a turn."""
    label = f" view {selector} "
    if width <= len(label):
        return label.strip()
    pad = width - len(label)
    left = pad // 2
    return "─" * left + label + "─" * (pad - left)


def block_ids(view_text: str):
    """The `#id`s a view carries, in order — what a push would touch. Read straight
    from the frozen `@@ #id` grammar, so this cannot disagree with scribe about what
    a block is."""
    return _BLOCK.findall(view_text or "")


class Buffers:
    """An in-memory registry of derived views. IN MEMORY ONLY — a view is a
    disposable walk, never a file. Nothing here touches disk; the shell pipes a
    buffer to `scribe push -` when the human asks, and that is the only way text
    leaves."""

    def __init__(self):
        self._open = {}       # name -> {"text": str, "original": str, "selector": str}

    def open(self, name: str, selector: str, text: str) -> None:
        if not name:
            raise ValueError("buffer name must be non-empty")
        self._open[name] = {"text": text, "original": text, "selector": selector}

    def names(self):
        """Open buffer names, in the order opened — the navigation coordinates."""
        return list(self._open.keys())

    def get(self, name: str) -> str:
        """The buffer's current text. A missing buffer is NAMED, not faked to ''."""
        if name not in self._open:
            raise KeyError(f"no open buffer named {name!r}")
        return self._open[name]["text"]

    def selector_of(self, name: str) -> str:
        if name not in self._open:
            raise KeyError(f"no open buffer named {name!r}")
        return self._open[name]["selector"]

    def update(self, name: str, text: str) -> None:
        """Record an edit made in the buffer. Does not write anything anywhere."""
        if name not in self._open:
            raise KeyError(f"no open buffer named {name!r}")
        self._open[name]["text"] = text

    def is_edited(self, name: str) -> bool:
        """Has the human changed this buffer since it was derived? `push` is only
        meaningful when True — pushing a pristine view is a no-op that would still
        rewrite the pile's mtime, so the shell refuses it and says why."""
        if name not in self._open:
            raise KeyError(f"no open buffer named {name!r}")
        b = self._open[name]
        return b["text"] != b["original"]

    def close(self, name: str) -> None:
        """Dispose a buffer. Disposal is free and total — that is what buffer-ness
        buys. A missing name is named, not silently ignored."""
        if name not in self._open:
            raise KeyError(f"no open buffer named {name!r}")
        del self._open[name]

    def edited_names(self):
        return [n for n in self._open if self.is_edited(n)]
