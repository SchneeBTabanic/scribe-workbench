# Scribe's Workbench

A sovereign, plain-text tool: **gather** fragments from many minds and your own writing,
**hold** them as one honest canonical pile of tagged plain text, and **present** any
ordering you ask for as a disposable derived view — without the file's line-order ever
being forced to carry meaning it cannot hold, and without any scripting-runtime standing
between you and your own words.

- The **pile is the truth**; every view is a rebuildable cache.
- The pile is a **plain-text file you can read and edit with this tool switched off** —
  `cat`, `less`, any editor. Tags are ordinary labelled lines.
- The tool **witnesses and marks; it never silently alters your text and never decides
  for you.** No scoring, no ML, nothing that steers.

One stdlib-only Python file (`scribe.py`). The only external it ever calls is `pandoc`,
and only when you capture from saved HTML.

## Using it alongside a plain editor (xed, gedit, any text editor)

Scribe is **not** an editor and does not replace one. It sits *beside* the editor you
already use: you compose and edit in your editor; Scribe holds the canonical pile and hands
you clean views to work in. For a practical, worked walkthrough — how to wire it into a
daily xed workflow, where to keep the pile so terminal paths stay short, capturing a
fragment from an editor tab, deriving a view into a new tab, editing it and pushing the
edits home — see **[`GUIDE-scribe-with-xed.md`](GUIDE-scribe-with-xed.md)**. The one habit
worth learning up front: `scribe view topic:X pile.txt > X.view 2>/dev/null` writes a clean
view file you can open in any editor, and `scribe push X.view pile.txt` lands your edits
back in the pile by block id.

## The pile format

```
@@ #<id> <ISO-timestamp> @topic:nas @topic:zfs @state:live @source:gemini
<the canonical block body, verbatim, any number of lines,
 until the next @@ line or end of file>
```

Line-order is honest to **one** axis only — arrival time. Everything else (topic,
salience, the table of contents) is derived on demand. A block can carry many tags and so
appear in many views **without being moved or duplicated**.

## Verbs

```
scribe capture [--source S] [--topic T]... [--state live] [--html] [--append PILE]
    Clean handed input into a block. Plain text is kept verbatim; --html recovers
    structure + LaTeX (from MathML) + strips fluff via pandoc. Loss is marked in-band.

scribe view topic:nas PILE            # gather every block on a topic (un-moved)
scribe view state:live PILE           # the current desktop, across topics, recent-first
scribe toc PILE                       # regenerate the table of contents from tags
scribe export topic:nas PILE [--bare] # clean export to paste into the next mind
scribe push VIEW PILE                 # push edits made in a view home, by #id
scribe tag 50c1 PILE --topic ai       # add/remove tags on a block
scribe blocks PILE                    # list blocks
scribe check TEXT                     # run the loss-auditor standalone
scribe doctor                         # disclose the artifact SHA + runtime deps
```

Nothing runs on its own; you summon every view by an explicit command. The pile is never
mutated to produce a view. Edits pushed home are matched deterministically by `#id`.

## Capturing from a chat (edge/)

`edge/chatgpt_adapter.py` turns a **saved** ChatGPT page (File ▸ Save Page As) into
canonical blocks — recovering the clean LaTeX and code fences that a plain copy-paste
garbles. It is a **quarantined, non-frozen** component (provider DOMs drift); the frozen
core never depends on it. See `edge/README.md`.

## Freeze

v1.0-frozen. Stdlib-only, offline-rebuildable; see `PROVENANCE.md`. Verify with
`scribe doctor`. License **AGPL-3.0-or-later**.

## Design principle

The tool does **no generation** and steers nothing: no scoring, no embeddings, no
measurement ever governs an output. It captures, holds, and presents; the human decides.
Capture *witnesses and marks* (a separate deterministic auditor flags lossy reductions
in-band); it never silently alters your text. This is deliberate — a measurement that
feeds back into what gets produced is the one pattern this project refuses.

## Documents in this repo

- `GUIDE-scribe-with-xed.md` — practical guide to using Scribe beside a plain editor (xed).
- `PROVENANCE.md` — freeze record (SHAs, toolchain).
- `edge/README.md` — the quarantined capture edge.

*(The full gated build record and design correspondence are kept in the sovereign's
development repository, not in this public release.)*
