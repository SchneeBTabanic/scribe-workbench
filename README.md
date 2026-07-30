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
scribe capture [--tag k:v]... [--topic T]... [--source S] [--html] [--append PILE]
    Clean handed input into a block. Plain text is kept verbatim; --html recovers
    structure + LaTeX (from MathML) + strips fluff via pandoc. Loss is marked in-band.
    --tag writes ANY key: the vocabulary is the human's, not the tool's.

scribe view topic:nas PILE            # gather every block on a topic (un-moved)
scribe view act:guards-the-edge PILE  # …or on any other key; --recent for newest-first
scribe toc PILE [--by KEY]            # contents by any key; names its axis and its loss
scribe keys PILE                      # every key and value in the pile, with counts
scribe export topic:nas PILE [--bare] [--joiner S] # clean export to paste into the
    next mind; --joiner (v1.1.1) makes the concatenation itself code-safe when a body
    is meant to tangle into one runnable file (default joiner is prose punctuation and
    breaks code) — see tagging/TAGS-bench-sheet.md's "For the tangle-loop" section
scribe push VIEW PILE                 # push edits made in a view home, by #id
scribe tag 50c1 PILE --tag aspect:manifesting   # add/remove tags on a block
scribe blocks PILE                    # list blocks with their whole tag run
scribe backlinks TARGET PILE [PILE...] # derive every block whose tag VALUE names
    TARGET (the reverse of @ref:/@overrules:/etc.) — TARGET is #id (this pile) or
    pile.txt#id (a named pile, for relations BETWEEN piles); computed fresh, never
    written back — see tagging/TAG-KEYS-reference-v1-DRAFT.md A.9
scribe activate CONDITION PILE [PILE...] [--key awaits] # every block currently
    declaring @awaits:CONDITION (or --key), across any piles named — the query
    half of a dpkg-trigger-style interest/activate pair; read-only, never promotes
scribe verify-export EXPORTED selector PILE [--recent] # has the pile drifted
    since EXPORTED was written? Reports MATCH/DRIFT/NO MANIFEST only, never
    repairs — see the content:sha256: fingerprint every non-bare export now carries
scribe converges PILE PILE [...] [--by KEY] [--no-cites] # candidate DNA shared
    between DIFFERENT piles never explicitly cross-referenced: shared tag-values
    and shared Charter-clause citations. Disclosed candidates only, never merged
scribe stamp PILE [--show]            # put the pile's own reading instructions on top
scribe check TEXT                     # run the loss-auditor standalone
scribe doctor                         # disclose the artifact SHA + runtime deps
```

Nothing runs on its own; you summon every view by an explicit command. The pile is never
mutated to produce a view. Edits pushed home are matched deterministically by `#id`.

**Tagging.** scribe stores any `@key:value` and holds no registry — the vocabulary is the pile
keeper's. The discipline that vocabulary is written in lives in [`tagging/`](tagging/): open
`tagging/TAGS-bench-sheet.md` while you work, `tagging/TAG-KEYS-reference-v1-DRAFT.md` when you
want to know why a key exists. One-line version: a tag should carry **a verb and a toward**.

**A pile explains itself.** When `capture --append` creates a pile it writes a short comment
header at the top — what the format is, which commands search it well, and why a plain `grep`
returns fragments rather than whole records. Any reader meets it in the file itself, including
an assistant asked to search a drive; nothing has to be configured or remembered. It is written
**only at birth** (or by `scribe stamp` on an existing pile), so deleting it keeps it deleted,
and `--no-stamp` declines it. Every line is a comment in the preamble: block counts, indexes and
round trips are identical with or without it.

**Exit codes.** `0` clean · `1` refused (nothing was done) · `2` done, with findings to
disclose. A tag value that would make a header unreadable is refused on write and announced
on every read; a read never refuses to open a pile, a write-back always refuses to rewrite a
broken one.

## Capturing from a chat (edge/)

`edge/chatgpt_adapter.py` turns a **saved** ChatGPT page (File ▸ Save Page As) into
canonical blocks — recovering the clean LaTeX and code fences that a plain copy-paste
garbles. It is a **quarantined, non-frozen** component (provider DOMs drift); the frozen
core never depends on it. See `edge/README.md`.

## Freeze

v1.2.0 current (additive over v1.0-frozen; frozen-ness was ruled to never be a reason
not to correct the tool — see `PROVENANCE.md`'s v1.1.0 entry). Stdlib-only,
offline-rebuildable. Verify with `scribe doctor`. License **AGPL-3.0-or-later**.

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
- `tagging/README.md` — which of the two tag docs below to open, and when.
- `tagging/TAGS-bench-sheet.md` — the DOING sheet; keep this open while you tag.
- `tagging/TAG-KEYS-reference-v1-DRAFT.md` — the WHY behind each key, for a rainy day.

*(The full gated build record and design correspondence are kept in the sovereign's
development repository, not in this public release.)*
