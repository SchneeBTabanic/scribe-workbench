"""
Headless Textual-pilot test for scribe_viewer — proves the shell drives FROZEN scribe
as a subprocess and holds views as editable, non-blocking tabs.

Proves specifically:
  * `view topic:X` opens a tab, side buffer becomes visible, main log stays (non-blocking)
  * the tab is an editable TextArea carrying the derived view, and its block ids are read
  * a pristine buffer refuses to push (no pointless pile rewrite)
  * an EDITED buffer pushes home by #id and the canonical pile actually changes
  * `/help` is DERIVED from scribe's own argparse — every subcommand appears
  * a bad selector is NAMED, not opened as an empty tab (§3.8)
  * the pile is never edited by the shell itself — only `push` writes, only via scribe

Run:  ../../GTPS-Agent/.venv-ui-trial/bin/python3 viewer/test_scribe_viewer_shell.py
"""
import asyncio
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from scribe_viewer import ScribeViewer                       # noqa: E402
from textual.widgets import Input, RichLog, TabbedContent, TabPane, TextArea  # noqa: E402

# Single-sourced with the /help assertion below (§3.13) so the summary print at
# the bottom of this file can never again say a stale count -- found live
# 2026-07-31: it said "(9 verbs)" after a 10th (backlinks) had been added to
# the checked tuple, the exact silent-drift shape this project's tests exist
# to refuse elsewhere. Same day, later: "keys" and "stamp" were ALSO already
# missing from this tuple (a second, quieter instance of the identical drift,
# never caught because the assertion only checks presence, not completeness)
# -- fixed here alongside adding the three v1.2.0 verbs.
_SCRIBE_VERBS = ("capture", "check", "blocks", "view", "toc", "keys", "export",
                "verify-export", "push", "tag", "stamp", "doctor", "backlinks",
                "activate", "converges")

PILE = """@@ #a1b2 2026-07-26T14:00:00 @topic:probe @state:live
First block, on the probe topic.

@@ #c3d4 2026-07-26T14:01:00 @topic:other @state:live
Second block, different topic.

@@ #e5f6 2026-07-26T14:02:00 @topic:probe @state:settled
Third block, probe topic again.
"""


def _log_text(app):
    return "\n".join(str(s) for s in app.query_one("#log", RichLog).lines)


async def _drive():
    d = tempfile.mkdtemp(prefix="scribe-viewer-test-")
    pile = os.path.join(d, "pile.txt")
    with open(pile, "w", encoding="utf-8") as fh:
        fh.write(PILE)
    before = open(pile, encoding="utf-8").read()

    app = ScribeViewer(pile)
    async with app.run_test() as pilot:
        tabs = app.query_one("#tabs", TabbedContent)
        assert [p.id for p in tabs.query(TabPane)] == ["terminal"], \
            "the terminal is the first and only tab at rest"

        # --- a bad selector is named, never opened as an empty tab (§3.8)
        app.query_one("#entry", Input).value = "view nonsense"
        await pilot.press("enter"); await pilot.pause()
        assert len(tabs.query(TabPane)) == 1, \
            "a malformed selector must not open a tab"
        assert "not a selector" in _log_text(app)

        # --- view opens an EDITABLE tab, non-blocking
        app.query_one("#entry", Input).value = "view topic:probe"
        await pilot.press("enter"); await pilot.pause()
        tabs = app.query_one("#tabs", TabbedContent)
        assert len(tabs.query(TabPane)) == 2, "terminal + one view expected"
        assert tabs.active == "v-topic-probe", "the new view becomes active"
        assert app.query_one("#log", RichLog).display is True, "main log stays — non-blocking"
        area = app.query_one("#ta-v-topic-probe", TextArea)
        assert "First block" in area.text and "Second block" not in area.text, \
            "the tab holds the DERIVED view, not the whole pile"
        assert "#a1b2" in _log_text(app) and "#e5f6" in _log_text(app), \
            "block ids of the view are disclosed"

        # --- pristine push is refused
        app.query_one("#entry", Input).value = "push"
        await pilot.press("enter"); await pilot.pause()
        assert "unchanged" in _log_text(app), "a pristine buffer must refuse to push"
        assert open(pile, encoding="utf-8").read() == before, "pile untouched"

        # --- edit the buffer, then push home by #id
        area.text = area.text.replace("First block, on the probe topic.",
                                      "First block, EDITED IN A BUFFER.")
        app.query_one("#entry", Input).value = "push"
        await pilot.press("enter"); await pilot.pause()
        after = open(pile, encoding="utf-8").read()
        assert "EDITED IN A BUFFER." in after, "push must land the edit in the pile"
        assert "#a1b2" in _log_text(app), "scribe discloses which block it updated"
        assert "Second block, different topic." in after, \
            "blocks outside the view must be untouched"

        # --- /help is DERIVED from scribe's argparse: every verb appears
        app.query_one("#entry", Input).value = "/help"
        await pilot.press("enter"); await pilot.pause()
        helptext = _log_text(app)
        for verb in _SCRIBE_VERBS:
            assert verb in helptext, f"/help missing scribe verb {verb!r}"

        # --- passthrough verb reaches frozen scribe.
        # FOUR, not the three this fixture starts with: the push above appended a
        # superseding block rather than overwriting. This assertion said 3 and had been
        # failing since push changed on 2026-08-02 — found 2026-08-08, still red at the
        # commit before that day's work, so it was nobody's regression. It rotted because
        # this file needs the Textual venv and so never runs with the main suite. If that
        # is ever fixed, this is the class of thing it would have caught.
        app.query_one("#entry", Input).value = "blocks"
        await pilot.press("enter"); await pilot.pause()
        assert "4 block(s)" in _log_text(app)

        # --- backlinks passthrough auto-appends the pile, same as blocks/toc/tag.
        # The original assertion here expected the NAMED ABSENCE ("nothing points at"),
        # on the stated premise that this fixture carries no relational tags. The same
        # 2026-08-02 push change falsified that premise as well: the push above left a
        # superseding block pointing back via @replaces:#a1b2, so #a1b2 now HAS a
        # backlink. Asserting the pointer is the better test anyway — it proves the pile
        # was auto-appended (scribe cannot resolve #a1b2 without it) AND that push left
        # the supersession traceable from the block that was superseded.
        app.query_one("#entry", Input).value = "backlinks #a1b2"
        await pilot.press("enter"); await pilot.pause()
        assert "@replaces:#a1b2" in _log_text(app), \
            "backlinks must reach scribe with the pile auto-appended"

        # --- Esc returns to the terminal WITHOUT disposing of anything. Several views
        # open at once is the requirement; leaving one must never cost you it.
        app.query_one("#entry", Input).value = "view topic:other"
        await pilot.press("enter"); await pilot.pause()
        tabs = app.query_one("#tabs", TabbedContent)
        assert len(tabs.query(TabPane)) == 3, "two views open TOGETHER, plus terminal"

        await pilot.press("escape"); await pilot.pause()
        assert tabs.active == "terminal", "Esc goes back to the terminal tab"
        assert len(tabs.query(TabPane)) == 3, "leaving a view is not disposing of it"

        # --- and switching back does NOT re-derive: the text is the one already there
        tabs.active = "v-topic-probe"; await pilot.pause()
        assert "First block" in app.query_one("#ta-v-topic-probe", TextArea).text

        # --- bare `push` on the terminal tab names the situation, not an internal None
        await pilot.press("escape"); await pilot.pause()
        app.query_one("#entry", Input).value = "push"
        await pilot.press("enter"); await pilot.pause()
        log = _log_text(app)
        assert "terminal tab is active" in log, "the shell must say WHICH nothing it found"
        assert "None" not in log.split("terminal tab is active")[-1][:120]

    print("ok  bad selector named, not opened")
    print("ok  view opens an editable non-blocking tab with its block ids")
    print("ok  pristine push refused; pile untouched")
    print("ok  edited buffer pushes home by #id; neighbours untouched")
    print(f"ok  /help derived from scribe's own argparse ({len(_SCRIBE_VERBS)} verbs)")
    print("ok  passthrough verb reaches frozen scribe")
    print("ok  two views open TOGETHER; Esc returns to the terminal tab, disposing nothing")
    print("ok  switching back does not re-derive")
    print("ok  bare push on the terminal tab names the situation, not an internal None")


async def _drive_lifecycle():
    """THE TAB LIFECYCLE, added 2026-08-08 after the shell was shown declaring an edit
    saved that never left the tab.

    Two failures, both demonstrated before they were fixed:
      * a REFUSED push exits 0, and the shell read the exit code as success — it
        re-baselined the buffer as pristine, which switched off the unpushed-edits guard
        in `/close`, so the tab could be closed and the words lost with no warning;
      * a LANDED push left the tab holding the OLD `@@ #id` while the pile had moved to a
        new block, so the tab was stale the instant it succeeded and the next push from it
        was refused as a fork. The staleness was manufactured by the re-baseline itself.
    """
    d = tempfile.mkdtemp(prefix="scribe-viewer-lifecycle-")
    pile = os.path.join(d, "pile.txt")
    with open(pile, "w", encoding="utf-8") as fh:
        fh.write("@@ #a001 2026-03-01T09:00:00 @topic:nas @source:schnee\noriginal body.\n")

    app = ScribeViewer(pile)
    async with app.run_test() as pilot:
        app.query_one("#entry", Input).value = "view topic:nas"
        await pilot.press("enter"); await pilot.pause()
        area = app.query_one("#ta-v-topic-nas", TextArea)
        assert "#a001" in area.text

        # --- FIRST push lands, and the tab RE-DERIVES rather than keeping what was typed
        area.text = area.text.replace("original body.", "FIRST EDIT.")
        app.query_one("#entry", Input).value = "push"
        await pilot.press("enter"); await pilot.pause()
        area = app.query_one("#ta-v-topic-nas", TextArea)
        assert "FIRST EDIT." in area.text, "the pushed text must still be shown"
        assert "@replaces:#a001" in area.text, \
            "the tab must re-derive: it should now carry the NEW block, not the old id"
        assert not app._buffers.is_edited("topic:nas"), "a landed push leaves it pristine"

        # --- and BECAUSE it re-derived, a second edit pushes too. This is the sequence
        # that used to be refused as a fork on its second turn.
        area.text = area.text.replace("FIRST EDIT.", "SECOND EDIT.")
        app.query_one("#entry", Input).value = "push"
        await pilot.press("enter"); await pilot.pause()
        with open(pile, encoding="utf-8") as fh:
            after = fh.read()
        assert "SECOND EDIT." in after, "edit -> push -> edit -> push must simply work"
        assert "FIRST EDIT." in after, "and the superseded body is still there"

        # --- A PARTLY-LANDED push must still count as landed. This is the case the `rc`
        # gate was dropped for: since the 2026-08-08 exit-code ruling a partial push exits
        # EXIT_FINDINGS (2), and the old `rc == 0 and bytes changed` test would have called
        # a push that DID change the pile "not landed" — the mirror of the bug the check
        # was written to fix. The bytes were always the real test.
        #
        # Run here, while the tab is genuinely re-derived, and BEFORE the refused case
        # below: a refused push leaves the tab holding whatever was typed, so building a
        # mixed view out of it afterwards would have nothing fresh in it to land.
        area = app.query_one("#ta-v-topic-nas", TextArea)
        area.text = area.text.replace("SECOND EDIT.", "THIRD EDIT.") + (
            "\n@@ #a001 2026-03-01T09:00:00 @topic:nas @source:schnee\n"
            "AN EDIT ON A LONG-SUPERSEDED BLOCK.\n")
        app.query_one("#entry", Input).value = "push"
        await pilot.press("enter"); await pilot.pause()
        with open(pile, encoding="utf-8") as fh:
            after = fh.read()
        assert "THIRD EDIT." in after, "the half that could land must have landed"
        assert "AN EDIT ON A LONG-SUPERSEDED BLOCK." not in after, "the stale half must not"
        assert not app._buffers.is_edited("topic:nas"), \
            "a partly-landed push is a landed push: the tab re-derives and is pristine"
        assert "re-derived" in _log_text(app), "and the shell says so"

        # --- a REFUSED push must NOT be reported as saved. Force the stale case by
        # pushing a view that names a block the pile has already superseded.
        stale = ("# scribe: view topic:nas\n\n"
                 "@@ #a001 2026-03-01T09:00:00 @topic:nas @source:schnee\n"
                 "EDIT FROM A STALE TAB.\n")
        area = app.query_one("#ta-v-topic-nas", TextArea)
        area.text = stale
        before_bytes = open(pile, "rb").read()
        app.query_one("#entry", Input).value = "push"
        await pilot.press("enter"); await pilot.pause()
        assert open(pile, "rb").read() == before_bytes, "a refused push writes nothing"
        assert app._buffers.is_edited("topic:nas"), \
            "the buffer must STAY edited so /close still guards it"
        log = _log_text(app)
        assert "NOT pushed" in log, "the shell must say it did not land"
        assert "NOTHING LANDED" in log, "and scribe's own headline must not say 'nothing changed'"

        # --- `view` on an already-open tab that HAS unpushed edits must refuse to
        # refresh. A view lives in memory only, so an overwrite here deletes typing that
        # exists nowhere else — the loss is named before it happens, and the choice stays
        # the human's. The tab is still holding the refused stale edit from just above.
        assert app._buffers.is_edited("topic:nas")
        held = app.query_one("#ta-v-topic-nas", TextArea).text
        app.query_one("#entry", Input).value = "view topic:nas"
        await pilot.press("enter"); await pilot.pause()
        assert app.query_one("#ta-v-topic-nas", TextArea).text == held, \
            "a refresh must NEVER silently discard unpushed edits"
        log = _log_text(app)
        assert "NOT refreshed" in log and "nowhere else" in log, \
            "and it must say why, not just decline"

        # --- but a PRISTINE tab refreshes, and shows what the pile now says. Reach that
        # state by discarding: /close twice (the first names the loss), then re-open.
        app.query_one("#entry", Input).value = "/close topic:nas"
        await pilot.press("enter"); await pilot.pause()
        app.query_one("#entry", Input).value = "/close topic:nas"
        await pilot.press("enter"); await pilot.pause()
        app.query_one("#entry", Input).value = "view topic:nas"
        await pilot.press("enter"); await pilot.pause()
        area = app.query_one("#ta-v-topic-nas", TextArea)
        assert "THIRD EDIT." in area.text, "a re-opened tab shows the pile as it stands"
        assert not app._buffers.is_edited("topic:nas")

        # --- and refreshing a pristine, already-current tab says so rather than
        # pretending to have done something.
        app.query_one("#entry", Input).value = "view topic:nas"
        await pilot.press("enter"); await pilot.pause()
        assert "already shows the pile as it stands" in _log_text(app)


def test_tab_labels_truncate_the_NAME_and_never_the_selector():
    """Q3, the last lifecycle question. Long selectors push the terminal tab off the bar —
    and that is the tab Esc returns to, so losing it is worse than losing a view.

    The label is a NAME (short, revisable, allowed to be ambiguous); the selector is what
    the buffer is keyed by and what `push topic:X` takes. §3.16's split on a tab strip.
    Truncation cuts the VALUE and keeps the KEY, because the key names the axis you are
    looking along — two tabs reading `top…` would be worse than two reading
    `topic:github-…`."""
    assert ScribeViewer._tab_label("topic:nas") == "topic:nas", "short ones are untouched"
    long = ScribeViewer._tab_label("topic:github-push")
    assert long.startswith("topic:") and long.endswith("…"), "key kept, value cut, cut shown"
    assert len(long) <= ScribeViewer.TAB_LABEL_MAX
    assert ScribeViewer._tab_label("keywithnocolonatallxxxxx").endswith("…")
    # the selector itself must survive intact — the label is not the key
    assert ScribeViewer._pane_for("topic:github-push") == "v-topic-github-push"


def test_the_log_does_not_print_a_disclosure_twice():
    """Since 2026-08-11 `toc`/`keys`/`backlinks` carry their malformed-header warning IN
    BAND so it survives a pipe into an editor. The log is the one consumer that shows BOTH
    streams, so there the in-band copy and the stderr announcement say the same thing — and
    a disclosure printed twice is on its way to being read none (§3.7).

    Keep it where stderr cannot follow, drop it where it can. Only possible because the
    lines are MARKED: `toc`'s own header also starts with `# `."""
    text = ("# scribe: WARNING: 1 header line(s) did not parse\n"
            "# scribe:   Line(s) 4 in the pile.\n"
            "# Table of contents (derived — do not hand-edit)\n"
            "## nas (2)")
    kept = ScribeViewer._drop_inband(text)
    assert "WARNING" not in kept, "scribe's own disclosure is dropped from the log"
    assert "# Table of contents" in kept, "the artifact's OWN header must survive"
    assert "## nas (2)" in kept


def test_selection_is_enabled():
    """Reported as a hard Textual limitation and filed as inherent. Checked against the
    installed Textual (8.2.8) rather than against the report: it was a VERSION artifact."""
    assert ScribeViewer.ALLOW_SELECT is True


if __name__ == "__main__":
    test_tab_labels_truncate_the_NAME_and_never_the_selector()
    test_the_log_does_not_print_a_disclosure_twice()
    test_selection_is_enabled()
    print("ok  tab labels truncate the NAME, never the selector (Q3)")
    print("ok  the log never prints a disclosure twice")
    print("ok  selection is enabled — the 'Textual limitation' was a version artifact")
    asyncio.run(_drive())
    asyncio.run(_drive_lifecycle())
    print("ok  a landed push re-derives the tab, so edit->push->edit->push works")
    print("ok  a PARTLY-landed push still counts as landed (exit 2 must not read as failure)")
    print("ok  a refused push is not reported as saved; the buffer stays edited")
    print("ok  `view` on a tab with unpushed edits REFUSES to refresh, and says why")
    print("ok  `view` on a pristine tab refreshes; on a current one it says nothing changed")
    print("\n15/15 scribe_viewer shell pilot passed")
