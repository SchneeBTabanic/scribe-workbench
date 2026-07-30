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
# to refuse elsewhere.
_SCRIBE_VERBS = ("capture", "check", "blocks", "view", "toc", "export",
                "push", "tag", "doctor", "backlinks")

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
        assert app.query_one("#sidebuffer").display is False, "buffer starts hidden"

        # --- a bad selector is named, never opened as an empty tab (§3.8)
        app.query_one("#entry", Input).value = "view nonsense"
        await pilot.press("enter"); await pilot.pause()
        assert not app.query_one("#tabs", TabbedContent).query(TabPane), \
            "a malformed selector must not open a tab"
        assert "not a selector" in _log_text(app)

        # --- view opens an EDITABLE tab, non-blocking
        app.query_one("#entry", Input).value = "view topic:probe"
        await pilot.press("enter"); await pilot.pause()
        tabs = app.query_one("#tabs", TabbedContent)
        assert len(tabs.query(TabPane)) == 1, "one tab expected"
        assert app.query_one("#sidebuffer").display is True
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

        # --- passthrough verb reaches frozen scribe
        app.query_one("#entry", Input).value = "blocks"
        await pilot.press("enter"); await pilot.pause()
        assert "3 block(s)" in _log_text(app)

        # --- backlinks passthrough auto-appends the pile, same as blocks/toc/tag.
        # This fixture has no relational tags, so the honest answer is the named
        # absence -- confirms the command reached scribe (not a shell-side error)
        # AND that the pile was auto-appended (scribe needs it to resolve #a1b2).
        app.query_one("#entry", Input).value = "backlinks #a1b2"
        await pilot.press("enter"); await pilot.pause()
        assert "nothing points at" in _log_text(app), \
            "backlinks must reach scribe with the pile auto-appended"

        # --- Esc hides without disposing
        await pilot.press("escape"); await pilot.pause()
        assert app.query_one("#sidebuffer").display is False
        assert len(app.query_one("#tabs", TabbedContent).query(TabPane)) == 1, \
            "hiding is not disposing"

    print("ok  bad selector named, not opened")
    print("ok  view opens an editable non-blocking tab with its block ids")
    print("ok  pristine push refused; pile untouched")
    print("ok  edited buffer pushes home by #id; neighbours untouched")
    print(f"ok  /help derived from scribe's own argparse ({len(_SCRIBE_VERBS)} verbs)")
    print("ok  passthrough verb reaches frozen scribe")
    print("ok  Esc hides without disposing")


if __name__ == "__main__":
    asyncio.run(_drive())
    print("\n7/7 scribe_viewer shell pilot passed")
