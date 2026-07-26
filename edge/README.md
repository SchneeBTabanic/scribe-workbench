# edge/ — the quarantined, world-facing capture edge

**This directory is NOT part of the frozen core.** The pile + tangler (`../scribe.py`)
is frozen, stdlib-only, and never imports anything here. This component exists to solve
capture at its source: read the canonical form from a browser the sovereign controls,
**before** the render flattens it — instead of fishing garbled text back out of a paste.

Read `../FORBIDDEN-PATTERN-CASESTUDY.md` alongside this file. The edge captures content
faithfully **as inert text**; it never executes or adopts what it captures.

## Extraction-only (GATE 3 ruling B)

`chatgpt_adapter.py` (`extract_turns`, `turns_to_blocks`, and the CLI) does pure stdlib
DOM slicing: it splits a **saved** ChatGPT page into message turns and hands each turn's
inner HTML to the **frozen core**'s `capture_html` (pandoc + MathML-annotation LaTeX
recovery + `aria-hidden` visual-duplicate strip + the separate loss-auditor). **No browser
is needed or used.** The sovereign provides the HTML (File ▸ Save Page As, or his own
tooling).

There is **no live browser drive in Scribe** (ruling B). The world-facing controlled-
browser → inert-text discovery was preserved, generalized to a non-authenticated URL
reader, in `../FUTURE-FORK_url-text-reader_playwright-discovery.md` — a seed for a
separate future fork (the boundary-architecture text web reader), not part of Scribe.
Re-adding a live transport here needs a new ruling.

## The honest costs (named — do not smooth over)

Because ruling B is extraction-from-saved-HTML, the two *world-facing* costs
(authentication/login friction, terms-of-use on the sovereign's accounts) **do not apply
to Scribe** — there is no live automation here. Two costs remain:

1. **Provider-DOM churn (§4.7), but bounded to a saved file.** ChatGPT's page structure
   changes over time, so a page saved today parses today; a very old saved page may not.
   The adapter is still the one place that would need updating — never the frozen core.
2. **Per-provider fragility.** The one provider-specific fact this adapter encodes is the
   message-container attribute (`data-message-author-role`). When ChatGPT changes its DOM,
   **only this adapter breaks** — the core and any future Claude/Gemini/Grok adapter are
   untouched. Keep each adapter tiny and isolated (Poverty, §4.6).

(The world-facing live-drive costs — login friction, ToU — were the reason ruling B kept
Scribe extraction-only. They now belong to the separate future URL-reader fork, documented
in `../FUTURE-FORK_url-text-reader_playwright-discovery.md`.)

## Usage

```
# from a saved ChatGPT page (File ▸ Save Page As, or the sovereign's own tooling):
python3 edge/chatgpt_adapter.py saved_chat.html --append ../my.pile
# capture both sides of the conversation:
python3 edge/chatgpt_adapter.py saved_chat.html --roles user,assistant
```

No browser, no dependency beyond the core's `pandoc`. The sovereign supplies the saved
HTML; the adapter yields canonical pile blocks.
