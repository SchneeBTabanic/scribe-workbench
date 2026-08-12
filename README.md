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
@@ #<id> <ISO-timestamp> @act:protect-against-bit-rot @path:toward-integrity-over-convenience @topic:nas @source:gemini
<the canonical block body, verbatim, any number of lines,
 until the next @@ line or end of file>
```

Line-order is honest to **one** axis only — arrival time. Everything else (topic,
salience, the table of contents) is derived on demand. A block can carry many tags and so
appear in many views **without being moved or duplicated**.

**The tags in that example are not decoration, and the order they are read in is the point.**
scribe enforces no vocabulary — it stores any `@key:value` — but the discipline the vocabulary
is written in has one rule above the rest: **a tag should carry a verb and a toward.**

| | | |
|---|---|---|
| `@act:` | what the block **does** — an open verb phrase | carries the meaning |
| `@path:` | what it **reaches toward or away from** | carries the meaning |
| `@topic:` | the label on the drawer — helps you *find* it, does not say what it *means* | optional since v1.1.0 |
| `@source:` | which mind said it | **sealed into the identity — see below** |

An earlier version of this example showed `@topic:` and `@source:` alone. That is the exact
shape the bench sheet calls a **dead tag** — *a noun in a drawer* — so the canonical example
was quietly teaching against the project's own rule. `@topic:` is **not** retired and is
legitimate as an index entry (Knuth's WEB index carries concepts, not just identifiers); it
simply must not stand in for a block's meaning. The full vocabulary is in
[`tagging/TAGS-bench-sheet.md`](tagging/TAGS-bench-sheet.md).

### `@source:` is sealed into the mint — and it is the only tag that is

The mint is taken over `genesis + ordinal + ts + source + body`, so **`@source:` alone among
tags is frozen into a block's identity.** Every other tag — `@topic:`, `@act:`, `@path:`, the
whole vocabulary — is freely revisable and does not affect verification. **The tag layer is
therefore only partly revisable**, which is a real property of the format and is stated here
rather than left to be discovered.

**Why it is there, honestly.** Not as entropy. It was inherited from the old `gen_id`, which
no ruling ever examined, and it is measurably the *lowest*-entropy field in a block —
near-constant across a pile. The mint's actual guarantee comes from `genesis + ordinal`, which
cannot collide. But it turns out to be doing a different job, and doing it well: it **seals the
attribution.** A saying cannot be silently re-attributed — you cannot quietly relabel handed-in
material as your own, or your own as an AI's, without `scribe verify` reporting the block as
edited in place. That is the axis this project cares about most.

**Consequence, declared:** correcting a `@source:` value is a visible act. It will report
`edited in place since capture`, and that is right — re-attributing a saying should not be
silent. If the value was simply wrong, correct it and let the record show that you did.

*And the obvious objection, which sharpens rather than weakens it:* as a keeper's practice
matures, `@source:` may converge on a single value and lose all discriminating power. But
discriminating between blocks was never its job here. **A uniform value is not an empty one** —
*"in this period, everything was self-sourced"* is a true historical claim, and the more the
boundary between one's own thinking and a machine's dissolves in practice, the more worth
freezing the claim that was made at the time.

### Handle and mint — two jobs, two fields (v1.3.0)

**`@identity:nominal`** — scribe's declared identity kind, and this line is the declaration.
A block is a **nominal** object: two blocks reading `agreed` are two *sayings*, not one
saying stored twice. So identity is not computed from what a block says. (A future
content-dedup tool over the same piles would declare `structural` and would be right to.)

| | what it is | scope | who uses it |
|---|---|---|---|
| **id** `#2644` | the identity: issued at capture, checked unique, never recomputed | unique **within its pile**; write `PILE#id` across piles | you, and every `@ref:`/`@overrules:`-style tag |
| **name** `@name:…` | *optional.* A name you can say again — it follows you to the newest block carrying it | as you choose | `scribe recall`, `scribe names` |
| **seal** `@sealed:…` | *optional.* Integrity, not identity: freezes this body, moment and `@source:` | this block | `scribe verify` |

The id is the right-hand digits of the timestamp printed beside it, extended leftward if a
shorter form is already taken in this pile. **It says nothing about what the block
contains, deliberately** — correcting a word does not make a block a different block — and
you can check by eye that a header has not been fabricated, because the id is a tail of its
own timestamp. Content alone cannot separate two identical utterances anyway; that is what
content-addressing *means*.

**Changed in v1.4.0, and it is a change of foundation.** Until 2026-08-05 identity was
`@mint:` — a SHA-256 over the pile, the position, the moment, the speaker **and the body** —
with the handle as its checked prefix. That fused three different questions into one token:
*which thing is this* (identity), *where did it come from* (provenance), and *is it as it
was* (integrity). The consequence was that **every corrected word was an identity event**,
so fixing a typo meant either growing the pile by a whole block or leaving the tool. The
three questions now have three answers: the id, the tags, and an opt-in seal.

The evidence was gathered before the change, not after: `verify` across every real pile —
**76 blocks — had reported `edited in place` zero times**, and 45 of those 76 carried no
mint at all. The check cost something every day and had never once caught anything.

Consequences worth knowing:

- **Ids grow, they are never renamed.** If a short id is taken, capture issues a longer one
  and says so.
- **An id resolves by prefix, like git's.** Type `#264` for `#2644` and it resolves — *if*
  it names exactly one block. If it names two, the verb refuses and asks for more characters
  rather than picking one.
- **Ambiguity is refused, never guessed.** If an id names two blocks, `push` and `tag` write
  *nothing* and name the candidates. `scribe duplicates PILE` reports them.
- **Two piles may reuse an id, and that is the model, not a collision.** The pile is the
  namespace, as a directory is for a filename. The bug fixed in v1.3.0 was two identical ids
  *inside one pile*, which is still refused.
- **Nothing is ever reissued.** Blocks carrying the retired `@mint:` keep it: it stays
  readable, it is reported as legacy by `verify`, and it is not upgraded behind you.
- **Re-capturing the same text does not reproduce the same id.** `--ts` still pins the
  timestamp for tests.
- No registry, no manifest, no directory scan.

### Say it again without paperwork — `@name:` (v1.4.0)

**The pill this swallows:** a living thought is said again, better, over and over. Until
v1.4.0 the only way to record that was `push` — a new block, `@replaces:` on it,
`@superseded:` written back onto the old one, and a chain to keep in step. Say a thing five
times and the pile holds four bookkeeping writes and has become a record of your revisions
rather than of what you think.

**Forth has answered this since 1970.** Define `foo` twice and gforth does not refuse, does
not make you supersede anything, and keeps no chain. It prints `redefined foo` in the stream
you are already reading and moves on; the old definition stays in the dictionary, unmarked
and still reachable by anything holding it. **What moved is not the old thing — it is what
the name finds.**

```sh
echo "Structure never informs its material." |
  scribe capture --name coupling-law --append pile.txt --tag act:… --tag path:…

echo "A structure cannot tell its material what to be; a person couples them." |
  scribe capture --name coupling-law --append pile.txt --tag act:… --tag path:…
#   redefined coupling-law — 1 earlier definition(s) in pile.txt: #6308
#   They are UNTOUCHED and still resolve by handle; nothing was marked and nothing is owed.

scribe recall coupling-law pile.txt          # what the name finds now
scribe recall coupling-law pile.txt --all    # the whole lineage, arrival order
scribe names pile.txt                        # every name, and which definition is live
```

**Nothing is written onto the earlier blocks. There is no chain in the pile.** `scribe names`
computes redefinition fresh on every call and never writes back — the same contract
`backlinks` has held since v1.1.2, and for the same reason: *back-references are derived,
never hand-written.*

The live definition is the last one **admitted**, not the one with the latest timestamp —
`--ts` is a supported flag, and sorting by a stated moment would let a backdated capture
silently take over a name.

### Correct a typo without an event — `scribe amend` (v1.4.0)

```sh
echo "the quick brown fox" | scribe amend '#2644' pile.txt
```

In place. Nothing appended, nothing superseded, **nothing recorded** — a typo is not an
event. It **refuses** if any block in the pile points at the target (`@ref:`, `@replaces:`,
`@overrules:` …), because someone wrote that pointer *about the wording that is there now*,
and that is precisely the case `push` exists for. It also refuses a `@sealed:` block, which
is what makes sealing mean anything.

**Four acts, and choosing between them is yours:**

| | when | what it costs the pile |
|---|---|---|
| `capture` | a new saying | one block |
| `amend` | a typo. Nothing happened. | nothing |
| `--name` | *I say this better now* | one block, no marks, no chain |
| `push` | a revision whose supersession is itself worth recording, in the file | one block + one `@superseded:` |

### Push appends and supersedes — it never overwrites (v1.3.1)

Until v1.3.1, `push` wrote a view's edited body over the pile's block. That made the tool
**less append-only than it claimed**: a body could change underneath a `@ref:` that had
been written to the old wording. It now **appends**.

```
before                                  after `scribe push`
@@ #2ea7 … @topic:nas                   @@ #2ea7 … @topic:nas @superseded:#b344
ZFS on the NAS for checksums.           ZFS on the NAS for checksums.        ← body unchanged

                                        @@ #b344 … @topic:nas @replaces:#2ea7
                                        ZFS on the NAS for checksums.
                                        Also: scrub monthly.                 ← your edit, as a new block
```

**Bodies and identities are inviolable.** Across a push, no existing block's body changes,
no id is reissued, and the only tag an existing block may gain is
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
    its id and gains exactly one tag, @superseded:#new; the new one carries
    @replaces:#old and inherits the old block's tags. To correct a block WITHOUT
    leaving that history in the pile, edit it directly — restic keeps that history
    instead. Both doors are yours; this one is push's.
scribe tag 50c1 PILE --tag aspect:manifesting   # add/remove tags on a block
scribe blocks PILE                    # list blocks with their whole tag run
scribe backlinks TARGET PILE [PILE...] # derive every block whose tag VALUE names
    TARGET (the reverse of @ref:/@overrules:/etc.) — TARGET is #id (this pile) or
    pile.txt#id (a named pile, for relations BETWEEN piles); computed fresh, never
    written back — see tagging/TAG-KEYS-reference-v1-DRAFT.md A.9
scribe recall NAME PILE [--all]       # what does this name find? (Forth's lookup)
scribe names PILE [PILE...]           # every @name: and which definition is live
scribe amend '#id' PILE               # correct a body in place — no block, no mark
scribe verify PILE [PILE...]          # is each SEALED block still the one its @sealed: was
    issued for? Re-derives every mint from the file itself and reports in FACT-language
    only: `as captured` / `edited in place since capture` / `no mint — this check did
    not run`. A hand-edit is a sanctioned act, so there are no severities here and never
    will be. A cut block is reported as a POSITION SHIFT, not as a wave of edits
scribe duplicates PILE [PILE...]      # every handle used by more than one block, with
    each one's tags so you can see whether they are one saying or two. Read-only:
    it declares collisions and never repairs them (re-minting would break every
    relational tag pointing in).
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

Three keys are the **tool's**, not yours: `@sealed:`/`@mint:` (digests — refused by `tag`,
excluded from `keys` with a notice, and it says so), and `@superseded:`/`@replaces:`, which
`push` writes as the two halves of one supersession. You may still write the supersession pair
by hand to record a relation `push` had no part in; a digest is never yours to edit.

**A pile explains itself.** When `capture --append` creates a pile it writes a short comment
header at the top — what the format is, which commands search it well, why a plain `grep`
returns fragments rather than whole records, what the `#id` is, and how `@name:` lets a
saying be said again. Any reader meets it in the file itself, including an assistant asked to search a drive;
nothing has to be configured or remembered. The header also carries the pile's own
`@genesis:` line — its birth moment, kept as a record of when the pile began. Until v1.4.0
it was also load-bearing: it was folded into every `@mint:` and was what kept one pile's
identities distinct from another's. Nothing depends on it now — the pile itself is the
namespace — and it is retained because when a pile began is worth knowing on its own
account. It is written **only at birth** (or by `scribe stamp` on an existing pile), so
deleting it keeps it deleted, and `--no-stamp` declines it. Every line is a comment in the preamble: block counts, indexes and
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

v1.3.4 current (additive over v1.0-frozen; frozen-ness was ruled to never be a reason
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
