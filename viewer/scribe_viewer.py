"""
scribe_viewer.py — an OPTIONAL Textual shell for scribe: commands in, views as tabs.
====================================================================================

PROVENANCE — a DESCENDANT of `GTPS-Agent/viewer_textual.py` @ commit 4c88316,
forked 2026-07-26 (GATE C). Divergence intended: the agent's shell renders three
persona panels of a live turn; this one runs scribe verbs and holds derived views as
EDITABLE buffers with a push-home path the agent's must never have.

WHAT IT IS. One tab bar across the full width. The FIRST tab is the terminal — the
command log — and every `view` opens beside it as its own tab, editable, with `push`
sending the active tab home by `#id`. The command prompt is pinned below every tab, so
you type from wherever you are reading. Nothing is written to disk except the canonical
pile itself, and only when you push.

  ┌ [terminal] [topic:nas] [aspect:ripe] ──────────────────────┐
  │  the active one, full width                                │
  └────────────────────────────────────────────────────────────┘
    scribe>                                       always present

LAYOUT HISTORY, so it is not re-broken. Until 2026-08-08 the log and the tabs sat in a
permanent `Horizontal` split with the tabs pinned to `width: 50%`, hidden until a view
opened. Every view therefore arrived by halving the screen, and Schnee's report was that
opening one "takes over a portion of the screen and makes everything else smaller". The
tab machinery was never the problem — panes persisted, switching never re-derived — it
was one width declaration. A full-screen modal was considered and REJECTED by him for
the right reason: it allows one view at a time and makes you close it to get back, which
is not a workspace. Several views open at once IS the requirement, and it is what
selects a TUI here: scrollback cannot hold something you click back into.

THE TWO LAWS THAT SHAPE IT
  * **view-never-doorway (§4.6).** This program is OPTIONAL. `scribe` works without
    it; `scribe view topic:X pile.txt | xed -` gives you buffer semantics with this
    uninstalled. (The `2>/dev/null` this line used to carry is now counterproductive:
    since v1.6.0 a view names its own count and any damage IN BAND, and stderr never
    entered the pipe anyway — you want those lines visible in your terminal.) If the
    shell ever becomes the way IN to your own words, the doorway proof is undone — so
    the PILE is never edited here. It is displayed; raw pile editing stays xed's job,
    at the doorway.
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
from textual.containers import Vertical
from textual.widgets import (RichLog, Input, Label, Footer, TextArea,
                             TabbedContent, TabPane)

# The terminal is a TAB, not a pane beside the tabs. Its id is deliberately NOT of the
# `v-<selector>` form every view pane uses, so no selector can ever collide with it and
# no lookup can mistake it for a buffer.
LOG_PANE = "terminal"

# scribe's own EXIT_FINDINGS, mirrored rather than imported — the freeze forbids importing
# scribe (see run_scribe), so this is the one place a value must be duplicated instead of
# shared. Kept to a single named constant with the reason attached, because the honest cost
# of the freeze is a copy, and an unexplained bare `2` is how that copy becomes a mystery.
# It means "the verb ran and has something to disclose", not "it failed".
SCRIBE_EXIT_FINDINGS = 2

# scribe's VIEW_MARK, mirrored for the same reason as the exit code above: the freeze forbids
# importing it. Every line scribe writes into a derived artifact's header carries this, which
# is what lets this shell tell scribe's own words from the artifact's — and from the human's.
VIEW_MARK = "# scribe:"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scribe_viewer_core import (Buffers, prompt_label, valid_selector,   # noqa: E402
                                view_boundary, block_ids)

SCRIBE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "scribe.py")


def run_scribe(args, stdin_text=None):
    """Invoke FROZEN scribe as a subprocess. Never an import — the freeze holds by
    construction. Returns (stdout, stderr, returncode); stderr is scribe's own
    disclosure channel and is shown, never swallowed (§3.7).

    THE CHILD MUST NEVER INHERIT THIS PROGRAM'S STDIN. `input=None` does not mean "no
    stdin" — it means "do not redirect", so the child inherits the terminal, which under
    Textual is in raw mode and never reaches EOF. Any scribe verb that reads stdin by
    default then blocks forever, and because this call is synchronous on the UI thread the
    WHOLE INTERFACE freezes: no Esc, no Ctrl-Q, no backspace. Recovering it needs another
    terminal to kill the process, and even then the first terminal is left in the alternate
    screen and needs `reset`.

    Found 2026-08-10 by Schnee typing `capture --append … --source self` at the viewer
    prompt, reported through Grok, and reproduced here non-interactively by giving the
    parent an stdin that does not EOF. FOUR verbs read stdin by default (`capture`,
    `amend`, `check`, `blocks`); of those `capture` and `check` reach this path.

    Passing `""` gives the child an immediately-closed stdin instead. That is the
    structural half — it makes the freeze impossible for any verb, including ones added
    later. The other half is refusing the two verbs by name in `_passthrough`, because an
    empty body is NOT what someone typing `capture` meant, and silently writing an
    empty-bodied block would trade a visible freeze for an invisible wrong outcome."""
    p = subprocess.run([sys.executable, SCRIBE] + list(args),
                       input=stdin_text if stdin_text is not None else "",
                       capture_output=True, text=True)
    return p.stdout, p.stderr, p.returncode


class ScribeViewer(App):
    BINDINGS = [
        ("ctrl+c", "quit", "quit"),
        ("ctrl+q", "quit", "quit"),
        ("escape", "show_log", "terminal tab"),
    ]

    # SELECTION AND COPY ARE ON. Reported by Schnee through Grok as a hard limitation —
    # "cannot select and copy the way one can in a normal terminal", filed as a Textual
    # constraint and a real regression against the plain terminal + xed path. Checked
    # 2026-08-11 against the installed Textual (8.2.8) rather than against the report:
    # `App.ALLOW_SELECT`, `Widget.ALLOW_SELECT` and `App.copy_to_clipboard` all exist. It
    # was a VERSION artifact, not a framework limit — and it had been recorded as inherent,
    # which would have kept anyone from trying again. Re-measure a "known limitation" whose
    # cause is someone else's software; theirs moves.
    ALLOW_SELECT = True

    CSS = """
    #tabs { height: 1fr; }
    #log { border: round $primary; height: 1fr; }
    TextArea { height: 1fr; }
    #promptbar { height: auto; }
    #entry { border: none; }
    """

    def __init__(self, pile: str):
        super().__init__()
        self.pile = pile
        self._buffers = Buffers()

    def compose(self) -> ComposeResult:
        with TabbedContent(id="tabs"):
            with TabPane("terminal", id=LOG_PANE):
                yield RichLog(id="log", highlight=False, markup=False, wrap=True)
        with Vertical(id="promptbar"):
            yield Label(prompt_label(os.path.basename(self.pile)), id="prompt")
            yield Input(id="entry",
                        placeholder="scribe command  ·  view topic:X = tab  ·  "
                                    "push = send tab home  ·  /help  ·  /close")
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        log.write(f"scribe shell — pile: {self.pile}")
        log.write(self._pile_standing())
        log.write("the pile is a FILE (edit it in xed at the doorway); "
                  "views are BUFFERS (throwaway tabs here).")
        log.write("/help for scribe's own command list.  Esc returns to this tab; "
                  "views stay open behind it.  ctrl+q quits.")
        self.query_one("#entry", Input).focus()

    def _pile_standing(self) -> str:
        """WHAT THE PILE ACTUALLY IS, said at launch. Added 2026-08-11.

        Two of Schnee's first-run reports were the same complaint wearing two faces: a
        path that does not exist is accepted in silence, and an empty pile opens with no
        tab and no explanation. Both are the shell declining to say what it found — and
        both were defended as 'by design, because the viewer never creates the pile'.
        That defence confuses two different things. Not CREATING the file is the design
        (§4.6, view-never-doorway) and stays. Not SAYING what is there was never a design
        decision; it was an omission wearing one, which is the §3.8 shape: an absence must
        be named, never left to look like a presence.

        The count is asked of scribe rather than computed here — the shell must not grow a
        second opinion about what a pile contains (§3.13)."""
        if not os.path.exists(self.pile):
            return (f"  this file does NOT exist yet. Nothing has been created — the "
                    f"viewer never writes a pile. It will appear the first time a scribe "
                    f"verb writes to it (`capture --append`, from a terminal).")
        out, _, rc = run_scribe(["blocks", self.pile])
        n = len(block_ids(out))
        if rc not in (0, SCRIBE_EXIT_FINDINGS):
            return "  could not read it — scribe refused; see /help or run `blocks` here."
        if not n:
            return ("  it exists and holds NO blocks yet, so no view can derive from it. "
                    "Capture something into it from a terminal first.")
        return (f"  {n} block(s). Try `view topic:X` — a view opens as its own tab beside "
                f"this one, and nothing is written until you `push`.")

    # ------------------------------------------------------------ pane <-> name
    # One mapping, used by push and close alike. They each had their own copy of the
    # `"v-" + name.replace(...)` expression, which is the shape of drift #d18f already
    # caught once in this file (two lists that disagreed about `backlinks`).
    @staticmethod
    def _pane_for(name: str) -> str:
        return "v-" + name.replace(":", "-").replace(".", "-")

    # Q3, the last of the four lifecycle questions, answered 2026-08-11. Long selectors
    # (`topic:github-push`, `aspect:prospective`) make wide tabs, and six of them push the
    # terminal tab off the bar — which is the tab you get back to with Esc, so losing it is
    # worse than losing a view.
    #
    # TRUNCATE THE LABEL, NEVER THE SELECTOR. The label is a NAME (short, revisable, allowed
    # to be ambiguous); the selector is what the buffer is keyed by and what `push topic:X`
    # takes. §3.16's split, applied to a tab strip. Nothing is lost by shortening a label
    # because the full selector is disclosed in three other places that survive: the log line
    # when the view opens, the view's own `# scribe:` header inside the tab, and `push` naming
    # it back. A label is the one place it can be abbreviated without costing the reader
    # anything — and `…` says plainly that it has been.
    TAB_LABEL_MAX = 16

    @classmethod
    def _tab_label(cls, selector: str) -> str:
        if len(selector) <= cls.TAB_LABEL_MAX:
            return selector
        # Cut the VALUE, keep the key whole: `topic:` is what tells you which axis you are
        # looking along, and two tabs reading `top…` would be worse than two reading
        # `topic:github-…`. The key is the part that disambiguates.
        key, sep, value = selector.partition(":")
        if sep and len(key) + 2 < cls.TAB_LABEL_MAX:
            return f"{key}:{value[:cls.TAB_LABEL_MAX - len(key) - 2]}…"
        return selector[:cls.TAB_LABEL_MAX - 1] + "…"

    def _name_for_pane(self, pane_id):
        """The buffer a pane shows, or None — which the TERMINAL tab always is. Callers
        must handle None rather than let it fall through to a 'no buffer named None'."""
        if not pane_id or pane_id == LOG_PANE:
            return None
        return next((b for b in self._buffers.names()
                     if self._pane_for(b) == pane_id), None)

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
        elif text in ("/hide", "/terminal"):
            # `/hide` is KEPT as a working word rather than removed. It no longer hides
            # (nothing is hidden now) — it returns you to the terminal tab, which is what
            # anyone typing it wanted. A retired word that still works and says so beats
            # one that errors: §3.8's rule for retired keys, applied to a command.
            self.action_show_log()
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
                  "the active tab home by #id   /close [name] = close a view   "
                  "Esc = back to the terminal tab (views stay open)")

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

        tabs = self.query_one("#tabs", TabbedContent)
        pane_id = self._pane_for(selector)
        # `view` ON AN ALREADY-OPEN TAB IS A REFRESH — but never a silent overwrite.
        #
        # Until 2026-08-08 it was neither. The pane was only filled at creation, so
        # re-running `view topic:X` left the old text on screen; meanwhile `_buffers.open`
        # ran unconditionally and re-baselined the registry to the FRESH derivation. The
        # tab and the record of what the tab was derived from therefore disagreed, and the
        # command that looks like "show me the pile as it stands now" did nothing visible.
        # It self-corrected at push time, so nothing was ever lost — but a command whose
        # visible effect is nothing is a command that teaches the wrong model.
        #
        # WHAT IT MUST NOT DO is refresh over unpushed edits. That is Q1 of the tab
        # lifecycle and the answer is the one this whole codebase keeps giving: the loss is
        # named BEFORE it happens and the choice stays the human's (§3.1). Auto-refresh
        # would silently delete typing that exists nowhere else — a view is in memory only,
        # so there is no file to recover it from.
        if pane_id in {p.id for p in tabs.query(TabPane)}:
            area = self.query_one(f"#ta-{pane_id}", TextArea)
            self._buffers.update(selector, area.text)      # what is actually on screen
            if self._buffers.is_edited(selector):
                tabs.active = pane_id
                self.query_one("#entry", Input).focus()
                log.write(f"  {selector} is already open AND has unpushed edits — NOT "
                          f"refreshed, because that would delete them and they exist "
                          f"nowhere else.")
                log.write("  `push` them home first, or `/close` the tab and open it "
                          "again to start from the pile.")
                return
            if area.text == out:
                tabs.active = pane_id
                self.query_one("#entry", Input).focus()
                log.write(f"  {selector} already shows the pile as it stands — unchanged.")
                return
            area.text = out
            self._buffers.open(selector, selector, out)
            tabs.active = pane_id
            self.query_one("#entry", Input).focus()
            log.write(view_boundary(selector))
            log.write(f"  refreshed from the pile — {len(ids)} block(s): "
                      f"{', '.join('#'+i for i in ids)}")
            return

        self._buffers.open(selector, selector, out)
        area = TextArea(out, id=f"ta-{pane_id}")          # EDITABLE — the divergence
        await tabs.add_pane(TabPane(self._tab_label(selector), area, id=pane_id))
        tabs.active = pane_id
        self.query_one("#entry", Input).focus()           # no focus trap
        log.write(view_boundary(selector))
        log.write(f"  {len(ids)} block(s) in a buffer: {', '.join('#'+i for i in ids)}")
        log.write("  edit in the tab, then `push` — nothing is written until you do.")

    # ---------------------------------------------------------------- push
    def _pile_bytes(self):
        """The pile as it is on disk, or None if it cannot be read. Used to answer 'did
        anything land?' from the artifact rather than from a return code."""
        try:
            with open(self.pile, "rb") as fh:
                return fh.read()
        except OSError:
            return None

    def _push(self, cmd: str) -> None:
        log = self.query_one("#log", RichLog)
        parts = cmd.split(None, 1)
        tabs = self.query_one("#tabs", TabbedContent)
        name = parts[1].strip() if len(parts) > 1 else None
        if name is None:
            name = self._name_for_pane(tabs.active)
            if name is None:
                # Naming WHICH nothing there is to push (§3.8). Bare `push` on the
                # terminal tab used to fall through and report `no open buffer named
                # None`, which describes an internal value rather than the situation.
                log.write("  the terminal tab is active, and it is not a view — switch "
                          "to a view tab, or name one: `push topic:nas`")
                return
        if name not in self._buffers.names():
            log.write(f"  no open buffer named {name!r}")     # §3.8, named
            return

        pane_id = self._pane_for(name)
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
        # DID ANYTHING ACTUALLY LAND? Asked of the PILE ALONE — not the exit code, not
        # scribe's prose. The bytes of the file are the only thing that cannot be wrong
        # about whether the file changed.
        #
        # This was `rc == 0 and bytes changed`. The `rc` half went on 2026-08-08 when
        # Schnee ruled push's exit codes: a partly-landed push now exits EXIT_FINDINGS (2),
        # so gating on `rc == 0` would report a push that DID land as not landed — the
        # mirror of the bug this check was written to fix. The rc half was always
        # redundant belt-and-braces; the bytes were always the real test.
        #
        # It is also deliberately NOT a parse of scribe's stderr: a second copy of scribe's
        # wording here would be the drift this file already fights (`/help` is derived from
        # argparse for exactly that reason), and it would break on any rewording.
        #
        # What the old `rc == 0` cost, demonstrated before it was removed: a push whose
        # every edit was refused exited 0, the viewer re-baselined the buffer as pristine,
        # and that switched OFF the unpushed-edits guard in `_close` — `SECOND EDIT.` in
        # the tab, `FIRST EDIT.` in the pile, closeable without warning.
        before = self._pile_bytes()
        out, err, rc = run_scribe(["push", "-", self.pile], stdin_text=area.text)
        log.write((out or "").strip())
        log.write((err or "").strip())          # scribe discloses what it updated
        landed = self._pile_bytes() != before
        if not landed:
            # The buffer stays EDITED, so `/close` still guards it and the tab keeps
            # showing your words. Nothing is quietly declared saved.
            log.write("  NOT pushed — the pile is unchanged and your edits are still only "
                      "in this tab. Read the reason above; the tab is still marked edited.")
            return
        # RE-DERIVE, rather than re-baseline to what you typed. The old code kept your text
        # and called the tab pristine — but a landed push means the pile now holds a NEW
        # block with a NEW id, while your text still carries the OLD `@@ #id` header. The
        # tab was therefore stale the instant the push succeeded, and the NEXT push from it
        # would be refused as a fork. The staleness was manufactured by the re-baseline
        # itself. Deriving afresh makes edit -> push -> edit -> push simply work.
        fresh, ferr, frc = run_scribe(["view", name, self.pile])
        if frc != 0 or not block_ids(fresh):
            # Named, never faked (§3.8): the push DID land, so say that first, and say
            # plainly that the tab can no longer be trusted to show the pile.
            log.write("  pushed — but this view no longer derives (the selector matches "
                      "nothing now). The tab is left as you typed it and is NOT the pile.")
            return
        area.text = fresh
        self._buffers.open(name, name, fresh)   # baseline is the DERIVED text, not yours
        log.write("  pushed, and this tab re-derived from the pile — it now shows the new "
                  "block ids, so you can edit and push it again.")

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

    # Verbs whose body comes from STDIN, which this shell cannot supply. Derived from
    # scribe's own argparse defaults (`nargs="?", default="-"`), not guessed: `capture`,
    # `amend`, `check`, `blocks`. `blocks` is safe here because the pile is auto-appended
    # as its positional, and `amend` is not forwarded at all — so these two are the live
    # ones. Named rather than silently given an empty body: someone typing `capture`
    # means to write something, and an empty-bodied block is not that.
    _NEEDS_STDIN = ("capture", "check")

    def _passthrough(self, text: str) -> None:
        """Any other scribe verb, run against this pile. Unknown verbs are answered
        by scribe itself, not by a hand-maintained list here."""
        args = text.split()
        if args and args[0] == "scribe":
            args = args[1:]
        if args and args[0] in self._NEEDS_STDIN and "-" not in args:
            log = self.query_one("#log", RichLog)
            log.write(f"  `{args[0]}` reads its body from standard input, which this shell "
                      f"cannot type into — so it is refused here rather than run with an "
                      f"empty body.")
            log.write(f"  Run it in a normal terminal:  scribe {' '.join(args)}")
            log.write("  (Until 2026-08-11 this froze the whole viewer instead of saying so.)")
            return
        if args and args[0] in self._FORWARDED_VERBS:
            if args[0] in self._PILE_TRAILING_VERBS and self.pile not in args:
                args = args + [self.pile]
        out, err, _ = run_scribe(args)
        log = self.query_one("#log", RichLog)
        if out:
            log.write(self._drop_inband(out).rstrip())
        if err:
            log.write(err.rstrip())

    @staticmethod
    def _drop_inband(text: str) -> str:
        """Strip scribe's IN-BAND disclosure lines from passthrough output shown in the log.

        WHY, and it is the in-band change of 2026-08-11 meeting its one consumer that reads
        both streams. `toc`, `keys`, `backlinks` and `export` now carry their malformed-header
        warning in-band, marked `# scribe:`, so it survives a pipe into an editor where stderr
        cannot follow. **The log is not such a place.** It shows stdout AND stderr, in the same
        panel, so the in-band copy and the stderr announcement arrive together saying the same
        thing — and a disclosure printed twice is on its way to being read none, which is the
        §3.7 failure the in-band work exists to serve.

        So the rule is conditional on the reader, not on the verb: **keep the in-band lines
        where stderr cannot follow, drop them where it can.** Views are the first case and are
        untouched — `_open_view` puts `out` into the TextArea verbatim, and a view tab is
        exactly a place stderr does not reach. Passthrough output is the second case.

        THIS IS ONLY POSSIBLE BECAUSE THE LINES ARE MARKED. `toc`'s own header also begins
        with `# `; without VIEW_MARK there would be no way to tell scribe's cross-verb
        disclosure from the artifact's own description, and the choice would have been keep
        both or lose both. The mark is doing here precisely what it was added for."""
        return "\n".join(ln for ln in text.split("\n") if not ln.startswith(VIEW_MARK))

    def action_show_log(self) -> None:
        """Esc goes BACK to the terminal tab. It no longer hides anything: every open
        view stays open behind it, which is the whole point of the tab bar — you leave a
        view by looking somewhere else, not by disposing of it."""
        self.query_one("#tabs", TabbedContent).active = LOG_PANE
        self.query_one("#entry", Input).focus()

    async def _close(self, cmd: str) -> None:
        parts = cmd.split(None, 1)
        tabs = self.query_one("#tabs", TabbedContent)
        log = self.query_one("#log", RichLog)
        if len(parts) < 2:
            # Bare `/close` used to HIDE the pane, back when there was a pane to hide.
            # With the terminal as a tab there is nothing left to hide, so the word now
            # means what it says: close the view you are looking at.
            name = self._name_for_pane(tabs.active)
            if name is None:
                log.write("  the terminal tab does not close — it is the shell itself. "
                          "Name a view to close, e.g. `/close topic:nas`")
                return
        else:
            name = parts[1].strip()
        if name not in self._buffers.names():
            log.write(f"  no open buffer named {name!r}")
            return
        if self._buffers.is_edited(name):
            log.write(f"  {name} has unpushed edits — push it or /close it again "
                      "to discard")                      # loss named before it happens
            self._buffers.open(name, name, self._buffers.get(name))
            return
        pane_id = self._pane_for(name)
        if pane_id in {p.id for p in tabs.query(TabPane)}:
            await tabs.remove_pane(pane_id)
        self._buffers.close(name)
        tabs.active = LOG_PANE                           # never leave the bar empty
        self.query_one("#entry", Input).focus()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: scribe_viewer.py PILE   "
                 "(optional — `scribe view … | xed -` needs none of this)")
    ScribeViewer(sys.argv[1]).run()
