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
- **The tool only ever appends.** No verb rewrites a block's body or reissues its identity;
  a correction lands as a new block that declares what it replaces. *You* may still edit the
  file directly — the tool binds itself, not you.

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
@@ #<handle> <ISO-timestamp> @topic:nas @topic:zfs @source:gemini @mint:<64-hex>
<the canonical block body, verbatim, any number of lines,
 until the next @@ line or end of file>
```

Line-order is honest to **one** axis only — arrival time. Everything else (topic,
salience, the table of contents) is derived on demand. A block can carry many tags and so
appear in many views **without being moved or duplicated**.

### Handle and mint — two jobs, two fields (v1.3.0)

**`@identity:nominal`** — scribe's declared identity kind, and this line is the declaration.
A block is a **nominal** object: two blocks reading `agreed` are two *sayings*, not one
saying stored twice. So identity is not computed from what a block says. (A future
content-dedup tool over the same piles would declare `structural` and would be right to.)

| | what it is | scope | who uses it |
|---|---|---|---|
| **handle** `#a8eb` | short, typeable name — a prefix of the mint | unique **within its pile** | you, and every `@ref:`/`@overrules:`-style tag |
| **mint** `@mint:…` | the identity: whole SHA-256, never truncated, frozen at capture | globally distinct | nothing points at it; it settles *whether two blocks are the same saying* |

The mint is taken from three facts about the **declaring**, none of them content — which
pile (`@genesis:`, written into the stamp at the pile's birth), where in that pile's
arrival order, and when to the microsecond. Content alone cannot separate two identical
utterances; that is what content-addressing *means*.

Consequences worth knowing:

- **Handles grow, they are never renamed.** If a short handle is taken, capture issues a
  longer one and says so.
- **A handle resolves by prefix, like git's.** Type `#a8e` for `#a8eb1c` and it resolves —
  *if* it names exactly one block. If it names two, the verb refuses and asks for more
  characters rather than picking one.
- **Ambiguity is refused, never guessed.** If a handle names two blocks, `push` and `tag`
  write *nothing* and name the candidates. `scribe duplicates PILE` reports them.
- **Nothing is ever re-minted.** Blocks captured before v1.3.0 carry no `@mint:` and are
  reported as legacy, not upgraded — re-minting would change ids that relational tags
  already point at.
- **Re-capturing the same text no longer reproduces the same id.** That reproducibility
  *was* the duplicate bug. `--ts` still pins the timestamp for tests.
- No registry, no manifest, no directory scan. Uniqueness across piles falls out of each
  pile's own genesis, not from anything central.

### Push appends and supersedes — it never overwrites (v1.3.1)

Until v1.3.1, `push` wrote a view's edited body over the pile's block. That made the tool
**less append-only than it claimed**: a body could change underneath a `@ref:` that had
been written to the old wording. It now **appends**.

```
before                                  after `scribe push`
@@ #2ea7 … @topic:nas @mint:2ea7…       @@ #2ea7 … @topic:nas @superseded:#b344 @mint:2ea7…
ZFS on the NAS for checksums.           ZFS on the NAS for checksums.        ← body unchanged

                                        @@ #b344 … @topic:nas @replaces:#2ea7 @mint:b344…
                                        ZFS on the NAS for checksums.
                                        Also: scrub monthly.                 ← your edit, as a new block
```

**Bodies and identities are inviolable.** Across a push, no existing block's body changes,
no `@mint:` or handle is reissued, and the only tag an existing block may gain is
`@superseded:`, at most one. That is not an overwrite; it is the same act `scribe tag`
already performs as a named verb.

- The new block **inherits the old block's tags**, so the supersession appears in every view
  the original did — a correction that fell out of its own topic would be a silent loss.
- The status tag is written into the file rather than derived, so **a reader with the tool
  switched off still meets the warning** on the stale block. That legibility was chosen
  over the purer derived form, deliberately.
- Pushing the same view twice is **skipped, not forked**: a block already carrying
  `@superseded:` is named, and you are told which block to edit instead.
- `view` shows superseded blocks and **says so in its own header**; `view --current` hides
  them and declares the hiding. Never hidden by default, never removed from the pile.
- **Two doors, chosen per act.** Want the history in the pile? `push`. Don't want it? Edit
  the block directly in your editor — restic keeps that history instead. The tool binds
  *itself* to append-only; it does not bind you.

*Named limit:* `toc` and `export` do **not** filter superseded blocks and have no
`--current` flag, so an export of a pushed-to view carries both the old body and the new.
Only `view` knows about supersession today.

## Verbs

```
scribe capture [--tag k:v]... [--topic T]... [--source S] [--html] [--append PILE]
    Clean handed input into a block. Plain text is kept verbatim; --html recovers
    structure + LaTeX (from MathML) + strips fluff via pandoc. Loss is marked in-band.
    --tag writes ANY key: the vocabulary is the human's, not the tool's.

scribe view topic:nas PILE            # gather every block on a topic (un-moved);
    --current hides blocks a later block superseded (declared in the view header —
    they are never hidden by default, and never removed from the pile)
scribe view act:guards-the-edge PILE  # …or on any other key; --recent for newest-first
scribe toc PILE [--by KEY]            # contents by any key; names its axis and its loss
scribe keys PILE                      # every key and value in the pile, with counts
scribe export topic:nas PILE [--bare] [--joiner S] # clean export to paste into the
    next mind; --joiner (v1.1.1) makes the concatenation itself code-safe when a body
    is meant to tangle into one runnable file (default joiner is prose punctuation and
    breaks code) — see tagging/TAGS-bench-sheet.md's "For the tangle-loop" section
scribe push VIEW PILE                 # push edits made in a view home, by #id —
    APPENDS a superseding block, never overwrites. The old block keeps its body and
    its @mint: and gains exactly one tag, @superseded:#new; the new one carries
    @replaces:#old and inherits the old block's tags. To correct a block WITHOUT
    leaving that history in the pile, edit it directly — restic keeps that history
    instead. Both doors are yours; this one is push's.
scribe tag 50c1 PILE --tag aspect:manifesting   # add/remove tags on a block
scribe blocks PILE                    # list blocks with their whole tag run
scribe backlinks TARGET PILE [PILE...] # derive every block whose tag VALUE names
    TARGET (the reverse of @ref:/@overrules:/etc.) — TARGET is #id (this pile) or
    pile.txt#id (a named pile, for relations BETWEEN piles); computed fresh, never
    written back — see tagging/TAG-KEYS-reference-v1-DRAFT.md A.9
scribe verify PILE [PILE...]          # is each block still the one its @mint: was
    issued for? Re-derives every mint from the file itself and reports in FACT-language
    only: `as captured` / `edited in place since capture` / `no mint — this check did
    not run`. A hand-edit is a sanctioned act, so there are no severities here and never
    will be. A cut block is reported as a POSITION SHIFT, not as a wave of edits
scribe duplicates PILE [PILE...]      # every handle used by more than one block, with
    each one's @mint: so you can see whether they are one saying or two. Read-only:
    it declares collisions and never repairs them (re-minting would break every
    relational tag pointing in). Also names blocks with no @mint: as legacy.
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
mutated to produce a view. Edits pushed home are matched deterministically by `#id`, and
land as an appended superseding block — never as an overwrite.

**Tagging.** scribe stores any `@key:value` and holds no registry — the vocabulary is the pile
keeper's. The discipline that vocabulary is written in lives in [`tagging/`](tagging/): open
`tagging/TAGS-bench-sheet.md` while you work, `tagging/TAG-KEYS-reference-v1-DRAFT.md` when you
want to know why a key exists. One-line version: a tag should carry **a verb and a toward**.

Three keys are the **tool's**, not yours: `@mint:` (a block's identity — refused by `tag`,
excluded from `keys` with a notice, and it says so), and `@superseded:`/`@replaces:`, which
`push` writes as the two halves of one supersession. You may still write the supersession pair
by hand to record a relation `push` had no part in; `@mint:` is never yours to edit.

**A pile explains itself.** When `capture --append` creates a pile it writes a short comment
header at the top — what the format is, which commands search it well, why a plain `grep`
returns fragments rather than whole records, and what the long hex at the end of each header
is. Any reader meets it in the file itself, including an assistant asked to search a drive;
nothing has to be configured or remembered. The header also carries the pile's own
`@genesis:` line — its birth identity, and the half of every `@mint:` that keeps this pile's
blocks distinct from every other pile's with no registry anywhere. It is written **only at
birth** (or by `scribe stamp` on an existing pile), so deleting it keeps it deleted, and
`--no-stamp` declines it. Every line is a comment in the preamble: block counts, indexes and
round trips are identical with or without it.

A pile born before 2026-08-01 has no `@genesis:` line. It is **not broken** and nothing is
upgraded behind you: its mints fall back to the pile's path alone — still distinct from other
piles, but carrying no birth moment — and every verb that meets one says so. `scribe stamp`
gives such a pile a genesis from that moment forward; blocks already in it keep the handles
they have.

**Exit codes.** `0` clean · `1` refused (nothing was done) · `2` done, with findings to
disclose. A tag value that would make a header unreadable is refused on write and announced
on every read; a read never refuses to open a pile, a write-back always refuses to rewrite a
broken one.

## The optional shell (viewer/) — **not ready**

`viewer/` holds an experimental full-screen front-end built on Textual: commands in, derived
views as throwaway tabs, `push` from inside a tab. **It is unfinished and needs more work — do
not depend on it.** The supported way to use scribe is the command line beside your own editor,
which is what `GUIDE-scribe-with-xed.md` teaches; the shell adds only convenience on top of
that, and it has repeatedly fallen behind scribe's own verb list (`duplicates`, added in
v1.3.0, is not forwarded). It cannot damage a pile — it shells out to scribe and only `push`
writes — but it may silently not offer you something scribe has. `textual` is its dependency
alone; scribe itself stays stdlib-only. See `viewer/README.md`.

## Capturing from a chat (edge/)

`edge/chatgpt_adapter.py` turns a **saved** ChatGPT page (File ▸ Save Page As) into
canonical blocks — recovering the clean LaTeX and code fences that a plain copy-paste
garbles. It is a **quarantined, non-frozen** component (provider DOMs drift); the frozen
core never depends on it. See `edge/README.md`.

## Freeze

v1.3.3 current (additive over v1.0-frozen; frozen-ness was ruled to never be a reason
not to correct the tool — see `PROVENANCE.md`'s v1.1.0 entry). Stdlib-only,
offline-rebuildable. Verify with `scribe doctor`. License **AGPL-3.0-or-later**.

**Two behaviour changes are breaking, and are named as such.** v1.3.0 removed `gen_id`, so
re-capturing the same text no longer reproduces the same id — that reproducibility *was* the
duplicate bug. v1.3.1 changed what `push` does to the pile: it appends instead of
overwriting. Existing piles are untouched by both and keep working.

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
- `viewer/README.md` — the optional Textual shell. **Unfinished; not ready for daily use.**
- `tagging/README.md` — which of the two tag docs below to open, and when.
- `tagging/TAGS-bench-sheet.md` — the DOING sheet; keep this open while you tag.
- `tagging/TAG-KEYS-reference-v1-DRAFT.md` — the WHY behind each key, for a rainy day.

*(The full gated build record and design correspondence are kept in the sovereign's
development repository, not in this public release.)*
