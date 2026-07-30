"""
scribe_viewer.py — an OPTIONAL Textual shell for scribe: commands in, views as tabs.
====================================================================================

PROVENANCE — a DESCENDANT of `GTPS-Agent/viewer_textual.py` @ commit 4c88316,
forked 2026-07-26 (GATE C). Divergence intended: the agent's shell renders three
persona panels of a live turn; this one runs scribe verbs and holds derived views as
EDITABLE buffers with a push-home path the agent's must never have.

WHAT IT IS. You type scribe commands; output lands in the log on the left; `view`
opens the derived view as a throwaway tab on the right, editable, and `push` sends
that tab home by `#id`. Nothing is written to disk except the canonical pile itself,
and only when you push.

THE TWO LAWS THAT SHAPE IT
  * **view-never-doorway (§4.6).** This program is OPTIONAL. `scribe` works without
    it; `scribe view topic:X pile.txt 2>/dev/null | xed -` gives you buffer semantics
    with this uninstalled. If the shell ever becomes the way IN to your own words,
    the doorway proof is undone — so the PILE is never edited here. It is displayed;
    raw pile editing stays xed's job, at the doorway.
  * **frozen scribe (v1.0).** `scribe.py` is never imported, only invoked as a
    subprocess. This shell cannot change scribe's behaviour, only call it — so the
    freeze holds by construction, not by promise.

WHY THE ROUND TRIP TOUCHES NO FILES. Verified 2026-07-26: `scribe view` writes to
stdout (its count goes to stderr), and `scribe push -` reads the edited view from
STDIN. So view → buffer → edit → push never materialises a file, and no scratch zone
is needed.

Run:  python3 scribe_viewer.py PILE
"""

import os
import subprocess
import sys

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (RichLog, Input, Label, Footer, TextArea,
                             TabbedContent, TabPane)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scribe_viewer_core import (Buffers, prompt_label, valid_selector,   # noqa: E402
                                view_boundary, block_ids)

SCRIBE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "scribe.py")


def run_scribe(args, stdin_text=None):
    """Invoke FROZEN scribe as a subprocess. Never an import — the freeze holds by
    construction. Returns (stdout, stderr, returncode); stderr is scribe's own
    disclosure channel and is shown, never swallowed (§3.7)."""
    p = subprocess.run([sys.executable, SCRIBE] + list(args),
                       input=stdin_text, capture_output=True, text=True)
    return p.stdout, p.stderr, p.returncode


class ScribeViewer(App):
    BINDINGS = [
        ("ctrl+c", "quit", "quit"),
        ("ctrl+q", "quit", "quit"),
        ("escape", "hide_buffer", "hide views"),
    ]

    CSS = """
    #body { height: 1fr; }
    #log { width: 1fr; border: round $primary; }
    #sidebuffer { width: 50%; border: round $accent; display: none; }
    #promptbar { height: auto; }
    #entry { border: none; }
    """

    def __init__(self, pile: str):
        super().__init__()
        self.pile = pile
        self._buffers = Buffers()

    def compose(self) -> ComposeResult:
        with Horizontal(id="body"):
            yield RichLog(id="log", highlight=False, markup=False, wrap=True)
            with VerticalScroll(id="sidebuffer"):
                yield TabbedContent(id="tabs")
        with Vertical(id="promptbar"):
            yield Label(prompt_label(os.path.basename(self.pile)), id="prompt")
            yield Input(id="entry",
                        placeholder="scribe command  ·  view topic:X = tab  ·  "
                                    "push = send tab home  ·  /help  ·  /close")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"scribe shell — pile: {self.pile}")
        log.write("the pile is a FILE (edit it in xed at the doorway); "
                  "views are BUFFERS (throwaway tabs here).")
        log.write("/help for scribe's own command list.  Esc hides the tabs.")
        self.query_one("#entry", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        self.query_one("#entry", Input).value = ""
        if not text:
            return
        log = self.query_one("#log", RichLog)
        log.write(f"\n{prompt_label(os.path.basename(self.pile))}{text}")

        if text in ("/help", "help"):
            self._help()
        elif text.startswith("/close"):
            await self._close(text)
        elif text in ("/hide",):
            self.action_hide_buffer()
        elif text.startswith("view "):
            await self._open_view(text.split(None, 1)[1].strip())
        elif text.startswith("push"):
            self._push(text)
        else:
            self._passthrough(text)

    # ---------------------------------------------------------------- help
    def _help(self) -> None:
        """DERIVED from scribe's own argparse, never hand-copied. A hand-written
        command list is a second copy of scribe's surface with nothing to catch its
        drift (§3.13) — so this asks scribe what it can do, and cannot be wrong."""
        out, err, _ = run_scribe(["--help"])
        log = self.query_one("#log", RichLog)
        log.write(out or err)
        log.write("shell-only:  view <selector> = open as tab   push [name] = send "
                  "tab home by #id   /close [name]   /hide   Esc")

    # ---------------------------------------------------------------- views
    async def _open_view(self, selector: str) -> None:
        log = self.query_one("#log", RichLog)
        if not valid_selector(selector):
            log.write(f"  not a selector: {selector!r} — expected key:value, "
                      "e.g. topic:nas or state:live")     # named, not an empty tab
            return
        out, err, rc = run_scribe(["view", selector, self.pile])
        if rc != 0:
            log.write(err.strip() or f"  scribe view failed (rc={rc})")
            return
        log.write(err.strip())                            # scribe's own "N block(s)"
        ids = block_ids(out)
        if not ids:
            log.write(f"  no blocks matched {selector} — nothing to open")
            return

        self._buffers.open(selector, selector, out)
        tabs = self.query_one("#tabs", TabbedContent)
        pane_id = "v-" + selector.replace(":", "-").replace(".", "-")
        if pane_id not in {p.id for p in tabs.query(TabPane)}:
            area = TextArea(out, id=f"ta-{pane_id}")      # EDITABLE — the divergence
            await tabs.add_pane(TabPane(selector, area, id=pane_id))
        tabs.active = pane_id
        self.query_one("#sidebuffer").display = True      # non-blocking
        self.query_one("#entry", Input).focus()           # no focus trap
        log.write(view_boundary(selector))
        log.write(f"  {len(ids)} block(s) in a buffer: {', '.join('#'+i for i in ids)}")
        log.write("  edit in the tab, then `push` — nothing is written until you do.")

    # ---------------------------------------------------------------- push
    def _push(self, cmd: str) -> None:
        log = self.query_one("#log", RichLog)
        parts = cmd.split(None, 1)
        tabs = self.query_one("#tabs", TabbedContent)
        name = parts[1].strip() if len(parts) > 1 else None
        if name is None:
            active = tabs.active
            if not active:
                log.write("  no active view to push")
                return
            name = next((b for b in self._buffers.names()
                         if "v-" + b.replace(":", "-").replace(".", "-") == active), None)
        if name not in self._buffers.names():
            log.write(f"  no open buffer named {name!r}")     # §3.8, named
            return

        pane_id = "v-" + name.replace(":", "-").replace(".", "-")
        try:
            area = self.query_one(f"#ta-{pane_id}", TextArea)
        except Exception:
            log.write(f"  buffer {name!r} has no editable pane")
            return
        self._buffers.update(name, area.text)
        if not self._buffers.is_edited(name):
            log.write("  buffer unchanged — nothing to push "
                      "(refused rather than rewriting the pile for no reason)")
            return
        out, err, rc = run_scribe(["push", "-", self.pile], stdin_text=area.text)
        log.write((out or "").strip())
        log.write((err or "").strip())          # scribe discloses what it updated
        if rc == 0:
            self._buffers.open(name, name, area.text)   # re-baseline: now pristine
            log.write("  pushed. the pile is the truth; this tab is a view of it again.")

    # ---------------------------------------------------------------- misc
    # The verbs this shell forwards to frozen scribe, and which of those take the
    # pile as a TRAILING positional (so it can be auto-appended when the human
    # omits it, since they are already looking at one pile). Kept as one list
    # rather than the two disagreeing ones found live 2026-07-31 (#d18f: backlinks
    # was in one tuple but not the other) — a verb added here belongs in exactly
    # one place now.
    _FORWARDED_VERBS = ("blocks", "toc", "export", "check", "tag", "doctor",
                        "capture", "backlinks", "activate", "converges",
                        "keys", "stamp", "verify-export")
    _PILE_TRAILING_VERBS = ("blocks", "toc", "tag", "backlinks", "activate",
                            "converges", "keys", "stamp", "verify-export", "export")

    def _passthrough(self, text: str) -> None:
        """Any other scribe verb, run against this pile. Unknown verbs are answered
        by scribe itself, not by a hand-maintained list here."""
        args = text.split()
        if args and args[0] == "scribe":
            args = args[1:]
        if args and args[0] in self._FORWARDED_VERBS:
            if args[0] in self._PILE_TRAILING_VERBS and self.pile not in args:
                args = args + [self.pile]
        out, err, _ = run_scribe(args)
        log = self.query_one("#log", RichLog)
        if out:
            log.write(out.rstrip())
        if err:
            log.write(err.rstrip())

    def action_hide_buffer(self) -> None:
        self.query_one("#sidebuffer").display = False
        self.query_one("#entry", Input).focus()

    async def _close(self, cmd: str) -> None:
        parts = cmd.split(None, 1)
        tabs = self.query_one("#tabs", TabbedContent)
        if len(parts) < 2:
            self.action_hide_buffer()
            return
        name = parts[1].strip()
        log = self.query_one("#log", RichLog)
        if name not in self._buffers.names():
            log.write(f"  no open buffer named {name!r}")
            return
        if self._buffers.is_edited(name):
            log.write(f"  {name} has unpushed edits — push it or /close it again "
                      "to discard")                      # loss named before it happens
            self._buffers.open(name, name, self._buffers.get(name))
            return
        pane_id = "v-" + name.replace(":", "-").replace(".", "-")
        if pane_id in {p.id for p in tabs.query(TabPane)}:
            await tabs.remove_pane(pane_id)
        self._buffers.close(name)
        if not tabs.query(TabPane):
            self.query_one("#sidebuffer").display = False
        self.query_one("#entry", Input).focus()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: scribe_viewer.py PILE   "
                 "(optional — `scribe view … | xed -` needs none of this)")
    ScribeViewer(sys.argv[1]).run()
