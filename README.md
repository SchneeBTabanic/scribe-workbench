# Scribe's Workbench

A sovereign, plain-text tool: **gather** fragments from many minds and your own writing,
**hold** them as one honest pile of tagged plain text, and **present** any ordering you ask
for as a disposable derived view — without the file's line-order ever being forced to carry
meaning it cannot hold, and without any scripting-runtime standing between you and your own
words.

- The **pile is the truth**; every view is a rebuildable cache.
- The pile is a **plain-text file you can read and edit with this tool switched off** —
  `cat`, `less`, any editor. Tags are ordinary labelled lines.
- The tool **witnesses and marks; it never silently alters your text and never decides for
  you.** No scoring, no ML, nothing that steers.
- **The tool binds itself, not you.** No verb rewrites a block's body behind your back or
  reissues its identity. *You* may still edit the file directly, whenever you like.

One stdlib-only Python file (`scribe.py`). The only external it ever calls is `pandoc`, and
only when you capture from saved HTML. Licence **AGPL-3.0-or-later**.

## The stance this is built from

Two forces, and neither is going away.

**A living thought is continuous.** It arrives unfinished, and most of what a person says is
a redraft of what they just said. It does not come in units.

**A computer requires units.** To search a thing, relate it to another, point at it from
elsewhere, or find it again next year, it has to be made discrete, named and addressable.
There is no version of this that is optional.

Neither extreme is available. Refuse the units and you have an unsearchable heap — preserved
and unreachable, which is the same as lost. Embrace them fully and every passing thought
becomes a permanent addressed object that charges you paperwork for having thought again.

**This tool is an attempt to stand between them.** The test it tries to pass, applied to
every mechanism in it: *what does this ask of someone who has simply thought again?* The
answer should usually be **nothing**.

Where you find a place that fails that test, it is a defect, and worth reporting as one.

## Using it beside a plain editor

Scribe is **not** an editor and does not replace one. It sits *beside* the editor you already
use: you compose and edit there; Scribe holds the pile and hands you clean views to work in.

The one habit worth learning first:

```sh
scribe view topic:nas pile.txt | xed -    # opens as an unsaved tab; no file left behind
# …edit bodies in your own editor, save to a file only if you want one…
scribe push nas.view pile.txt             # your edits land home, by #id
```

**Do not add `2>/dev/null`.** This README taught that until 2026-08-11 and it was advice
that had gone stale: the view now carries its own count, its order, and — if the pile did
not fully parse — a warning that **the count you are reading is SHORT**. Those lines travel
*inside* the view, so they survive the pipe into your editor. Everything on standard error is
additional, and silencing it costs you nothing except the extra telling. What it used to cost
you was the only notice that a block had been swallowed.

If you prefer a file to a pipe, `scribe view topic:nas pile.txt > nas.view` still works and
the same disclosures are in it.

For the worked daily walkthrough — where to keep the pile so terminal paths stay short,
capturing from an editor tab, deriving a view into a new tab and pushing it back — see
**[`guide_proposed-workflow.md`](guide_proposed-workflow.md)**. It shows real prompts and
real output rather than describing them, and it is **a working proposal, still being
written** — the front of it is the practical path; further in it still carries open design
questions that are not settled user documentation.

## What a pile is

```
@@ #2644 2026-08-06T14:22:11.522644 @act:protect-against-bit-rot @path:toward-integrity-over-convenience @topic:nas @source:gemini
ZFS on the NAS for checksums and snapshots.
Scrub monthly.
```

A block begins at a line starting `@@ ` in column 0 and runs until the next such line or the
end of the file. That is the whole format.

**Line-order is honest to one axis only — arrival time.** Everything else (topic, salience,
the table of contents) is derived on demand. A block can carry many tags and so appear in
many views **without being moved or duplicated**. Nothing is ever re-sorted in the file.

**A pile explains itself.** When `capture --append` creates one, it writes a short comment
header at the top: what the format is, which commands search it well, why a plain `grep`
hands back fragments rather than whole records, what the `#id` is. Any reader meets it in the
file itself — including an assistant asked to search a drive. Nothing has to be configured or
remembered. Every line of it is a comment; block counts and round-trips are identical with or
without it. `--no-stamp` declines it, and deleting it keeps it deleted.

## Identity: the `#id`, and what it deliberately does not know

**`#2644` is the identity.** Issued once when the block is captured, checked unique inside
this pile, and never recomputed.

**It says nothing about what the block contains, on purpose.** Correcting a word does not make
a block a different block. That single decision is what lets you fix a typo without the pile
recording an event, and it is why every relational tag — `@ref:`, `@overrules:`, and the rest
— keeps resolving after you have revised the thing it points at.

Four things worth knowing, and then you can stop thinking about identity:

- **It is a tail of its own timestamp.** `#2644` against `…11.522644` on the same line. You
  can check by eye that a header has not been fabricated, and it costs no stored digest.
- **The pile is the namespace**, as a directory is for a filename. Two piles may hold the
  same id and that is the model, not a collision. Across piles, write `other.txt#2644`.
- **Ids grow, they are never renamed.** If a short one is taken, capture issues a longer one
  and tells you. A pointer you wrote last year still lands.
- **A short id resolves by prefix, like git's** — `#264` finds `#2644` *if it names exactly
  one block*. If it names two, the verb writes nothing and lists the candidates. **Ambiguity
  is refused, never guessed.**

Two blocks reading `agreed` are two *sayings*, not one saying stored twice. So identity is
not computed from what a block says — content alone cannot separate two identical utterances,
and pretending otherwise is what makes a records tool quietly lose one of them.

### Pointing at a block in another pile — two forms, and only one survives a rename

```
@ref:other-pile.txt#2716          the NAME     — readable, and breaks when you rename
@ref:genesis:1c1b8609#2716        the IDENTITY — opaque, and survives it
```

Inside one pile, `#2716` is enough: the pile is the namespace, as a directory is for a
filename. **Across piles, `PILE#id` makes the filename do identity's job** — and a filename
is meant to be changed. Rename the file and every pointer that named it is dead, silently,
because a reference to a file that is not there simply finds nothing.

That is not hypothetical. One `git mv` in this repo on 2026-08-10 broke six references, a
whitelist entry, and a test guard — and the guard broke *quietly*, so the suite went on
passing while the document it checked went unchecked for a day.

So a pile's `@genesis:` — minted once at birth, written into its own stamp, never
recomputed — can be used as the address instead. **Both forms work and neither is
deprecated**: `PILE#id` is what you read and type, `genesis:…#id` is what you write when the
pointer must outlive the filename. Name and identity, kept separate, one level up from
blocks.

**Abbreviate it like a git hash.** Any prefix of 4 hex or more is accepted and **checked**
against the piles you name — if it matches two, scribe says which two and asks for a longer
one; it never picks. The check happens every time rather than once, because the set of piles
a prefix must be unique among is only known when you name them.

```sh
scribe backlinks 'genesis:1c1b8609#2716' pile-a.txt pile-b.txt
#   b.txt#2290 (2026-08-11T…) via @ref:genesis:1c1b8609#2716   (= pile-a.txt)
```

The report shows the pointer **exactly as written**, then names the pile it resolved to —
so you can search the file for what you were shown, and still know where it went.

A pile born before 2026-08-01 has no genesis and cannot grow one backwards: `scribe stamp`
issues it from the moment of stamping, which is a different fact and is said rather than
smoothed over.

## The four acts — and choosing between them is yours

This is the centre of the tool. Four different things can happen to a saying, they cost
different amounts, and **the choice is never made for you**.

| | when you reach for it | what it costs the pile |
|---|---|---|
| **`capture`** | a new saying | one block |
| **`amend`** | a typo. Nothing happened. | **nothing** |
| **`capture --name X`** | *I say this better now* | one block. No marks, no chain. |
| **`push`** | a revision whose supersession is itself worth recording, in the file | one block + one `@superseded:` |

### `amend` — correct a body in place

```sh
echo "the quick brown fox" | scribe amend '#2644' pile.txt
```

Nothing appended, nothing superseded, **nothing recorded**. A typo is not an event.

It **refuses** in two cases, and both refusals are the point. If another block points at this
one (`@ref:`, `@replaces:`, `@overrules:` …), someone wrote that pointer *about the wording
that is there now* — so the wording is no longer only yours to change quietly, and `push` is
the verb for that. And it refuses a sealed block, which is what makes sealing mean anything.

The pointer check reads the piles you name. `--also PILE` widens it. **A pointer from a pile
you did not name is not seen** — scribe will not go looking for related piles on its own, and
it says so when it refuses.

### `@name:` — say it again, without paperwork

A living thought gets said again, better, over and over. If the only way to record that is a
new block plus a mark plus a chain to keep in step, then say a thing five times and your pile
has become a record of your revisions rather than of what you think.

**Forth has answered this since 1970.** Define `foo` twice and gforth does not refuse, does
not make you supersede anything, and keeps no chain. It prints `redefined foo` in the stream
you are already reading and moves on. The old definition stays in the dictionary, unmarked,
still reachable by anything holding it. **What moved is not the old thing — it is what the
name finds.**

```sh
echo "Structure never informs its material." |
  scribe capture --name coupling-law --append pile.txt --tag act:… --tag path:…

echo "A structure cannot tell its material what to be; a person couples them." |
  scribe capture --name coupling-law --append pile.txt --tag act:… --tag path:…
#   redefined coupling-law — 1 earlier definition(s) in pile.txt: #3177
#   They are UNTOUCHED and still resolve by handle; nothing was marked and nothing is owed.

scribe recall coupling-law pile.txt          # what the name finds now
scribe recall coupling-law pile.txt --all    # the whole lineage, arrival order
scribe names pile.txt                        # every name, and which definition is live
```

**Nothing is written onto the earlier blocks, and there is no chain in the pile.** `scribe
names` works redefinition out fresh on every call and never writes back — the same contract
`backlinks` holds, and for the same reason: *back-references are derived, never
hand-written.* It is what makes saying a thing again cost you nothing at all.

The live definition is the last one **admitted**, not the one with the latest timestamp.
`--ts` is a supported flag, and ordering by a stated moment would let a backdated capture
silently take over a name.

### `push` — when the supersession is itself worth recording

Sometimes the fact that you changed your mind *is* the saying, and you want the reader who
wanders into the outdated block to be told **in the file, with the tool switched off**.

```
before                                  after `scribe push`
@@ #2ea7 … @topic:nas                   @@ #2ea7 … @topic:nas @superseded:#b344
ZFS on the NAS for checksums.           ZFS on the NAS for checksums.        ← body unchanged

                                        @@ #b344 … @topic:nas @replaces:#2ea7
                                        ZFS on the NAS for checksums.
                                        Also: scrub monthly.                 ← your edit, appended
```

**Push appends. It never overwrites.** No existing body changes, no id is reissued, and the
only tag an existing block may gain is `@superseded:`, at most one.

- The new block **inherits the old block's tags**, so the correction appears in every view the
  original did. A revision that fell out of its own topic would be a silent loss.
- The mark is **written into the file** rather than derived, deliberately. Derived would have
  been purer and would have meant a reader with the tool off met no warning at all on the
  stale block — and that reader is the whole reason the mark exists.
- Pushing the same view twice is **skipped, not forked**. You are told which block to edit.
- `view` shows superseded blocks and says so in its header. `view --current` hides them and
  declares the hiding. Never hidden by default, never removed from the pile.

**A seal is asked for, never assumed.** If the block you supersede was sealed, the new one is
**not** — a seal is a claim about a body, and this is a different body. Push says so rather
than leaving you to find out:

```
#2ea7 was SEALED; #b344 is NOT. A seal is a claim about a body, and
this is a different body — so it is yours to make, not push's to assume.
`scribe push --seal` makes it, over the new body, now.
```

`push --seal` issues one over the new body. Worth knowing before you use it: **the attribution
is inherited** from the superseded block, so if `@source:` is no longer right for the new
wording, sealing freezes a citation you did not make this time. Push says that too.

**Two doors, chosen per act.** Want the history in the pile? `push`. Don't want it? Edit the
block in your editor and let your backups hold that history instead.

*Named limit:* `toc` and `export` do **not** filter superseded blocks and have no `--current`,
so an export of a pushed-to view carries both wordings. Only `view` knows about supersession.

## Integrity is opt-in, and sealing is an act with its own moment

Most blocks are meant to be correctable. Some reach a state you want held.

**A seal is the only act in this tool by which you declare that something has stopped
moving.** Everything else here exists to let things move — `amend` costs nothing, a `@name:`
can be said again, `push` appends rather than overwrites. So the seal is the one place where
*when you do it* carries meaning, and the tool treats the moment as a fact worth recording.

```sh
scribe seal '#2644' pile.txt      # I have worked on this. THIS is the state I want held.
scribe unseal '#2644' pile.txt    # its time has not come after all; let it move again
scribe verify pile.txt

echo "…" | scribe capture --seal --append pile.txt   # held from birth, where you mean that
```

**Sealing at capture and sealing on reflection are different claims, and the block says
which.** `@sealed-at:` records when the seal was taken; where it equals the block's own
timestamp, the thing was held from the start. Where it is later, you worked on it first —
and `verify` will then tell you the body is *as sealed*, never *as captured*, because the
tool cannot know what happened in between and will not pretend to.

**Unsealing marks nothing.** No tag records that a block was ever sealed. A seal is a claim
you are *currently* making — not an event — and changing your mind about holding something
owes the pile nothing. That is the same reason `@attests:` sits outside the seal: a current
stance has to be free to move.

A sealed block gets `@sealed-at:<moment>`, `@seals:body-ts-source-sealedat` and
`@sealed:<digest>`. `scribe verify` re-derives the digest and reports whether the block is
still the one the seal was issued for.

**The seal declares its own scope, in the file, and this matters more than it looks.** A check
whose coverage is knowable only by reading the tool's source is a prior baked into the
procedure and never stated. `@seals:body-ts-source` says on the block itself what the digest
covers — so you can read it with the tool off, and so a seal written today stays interpretable
if the formula ever widens.

| the seal covers | the seal does **not** cover |
|---|---|
| the **body** | `@topic:`, `@act:`, `@path:` — the whole revisable vocabulary |
| the **declaring moment**, and the **seal moment** | `@origin:` (human or ai) |
| *(and only when asked — `seal`, `capture --seal`, `push --seal`)* | |
| **`@source:`** — whose saying it is | `@attests:` (who vouches for it) |

**Those exclusions are chosen, not overlooked.** Re-filing a block as your thinking moves is
not tampering, and a check that fired on it would be useless. `@attests:` in particular is a
*current* stance — coming to stand behind something, or withdrawing from it, is thinking
again, and thinking again should cost nothing. `@source:` is different in kind: it is a
citation, a claim about a fixed past, and freezing it is what stops a saying being quietly
re-attributed.

**Consequence, declared rather than left to be discovered:** on an unsealed block, changing
`@source:` is reported nowhere. On a sealed block, changing `@origin:` or `@attests:` is
reported nowhere. `verify` states what it did not check, every time it runs.

`verify` reports in **fact-language only** — `as sealed` / `changed since it was sealed` /
`not sealed, so this check did not run`. A hand-edit is a sanctioned act. There are no
severities here and there never will be.

## Tagging, in one page

```
@@ #2644 … @act:protect-against-bit-rot @path:toward-integrity-over-convenience @topic:nas @source:gemini
```

scribe **enforces no vocabulary** — it stores any `@key:value` and holds no registry. The
vocabulary belongs to the person keeping the pile. The discipline it is written in has one
rule above the rest: **a tag should carry a verb and a toward.**

| | | |
|---|---|---|
| `@act:` | what the block **does** — an open verb phrase | carries the meaning |
| `@path:` | what it **reaches toward or away from** | carries the meaning |
| `@topic:` | the label on the drawer — helps you *find* it, does not say what it *means* | optional |
| `@source:` | whose saying it is — **any value you like**, `self`, `claude`, `Steiner` | sealed, where a seal is taken |

    @topic:knowledge-integration                    dead — a noun in a drawer
    @act:extend-insight @path:toward-recombination  alive — a doing, and a direction

A tag that only names a subject can answer one question — *what is this about?* — and an
index that reads one key teaches you to write for that key. Hence `scribe toc PILE --by
<key>`: the same pile indexed along whatever axis you name, with the index stating which keys
it is **not** showing you.

**Four keys are the tool's**, not vocabulary:

- **`@sealed:`** and **`@seals:`** — the digest and its declared scope. `scribe tag` refuses
  both; writing one by hand would assert a check rather than perform it.
- **`@superseded:`** and **`@replaces:`** — the two halves of one supersession, written by
  `push`. You may also write these by hand, to record a relation `push` had no part in.

Full vocabulary and the working discipline: **[`tagging/`](tagging/)** — open
`TAGS-bench-sheet.md` while you work, `TAG-KEYS-reference-v1-DRAFT.md` when you want to know
why a key exists.

## Mint and place — declaring a block anywhere in the file

Everything above appends: a new saying arrived now, and now is after everything that arrived
before, so the end of the file is where it honestly goes.

**But declaring is not the same act as appending, and scribe has always let you separate
them.** You need this the moment you have an ordinary document — notes written months ago, a
transcript, a page of prose — and you want to turn a paragraph in the *middle* of it into a
real block, leaving the rest where it is.

**Leave off `--append` and `capture` writes nothing. It prints the finished block instead:**

```sh
scribe capture --source self --tag topic:nas --tag act:record-the-boot-order
# ↳ @@ #4953 2026-08-11T11:15:44.954953 @topic:nas @act:record-the-boot-order @source:self
```

That is a complete, honest header: a real declaring moment, an issued handle, your tags.
Nothing about it is provisional. Paste it into your editor immediately above the paragraph
you mean to declare, save, and the block is real — it parses, it carries its identity, and it
appears in every derived view it belongs to. The text never moved.

```sh
# 1. mint            (prints; writes nothing)
scribe capture --source self --tag topic:nas
# 2. place           (xed, or any editor — put the line above the paragraph you mean)
# 3. check           (see below — this step is not optional)
scribe duplicates pile.txt
```

**Why step 3.** A handle is checked unique *within a pile*. When you mint without `--append`,
scribe has not been told which pile the block is going into, so it cannot make that check for
you. Collisions are unlikely — the handle comes from the declaring moment, and two moments
differ — but *unlikely* is not *checked*, and pasting a block that was minted for one pile
into another is exactly how you would get one. `scribe duplicates` names any collision
plainly; it never repairs one, because which of two blocks should move is yours to decide.

**Why this is not a workaround.** The pile is a plain text file and hand-editing it is a
sanctioned doorway, not a fallback (§3.1). What `--append` offers is convenience and the
uniqueness check — not permission. The format has never had a rule about *where* a block may
be declared, because position carries nothing (Charter §0.2: *belonging by presence, salience
by reference*). For a while the guides only documented the appending half, which made the
other half look like a limitation of the tool. It was a gap in the writing.

**What you still cannot do:** ask scribe to carve an existing region out of surrounding text
for you. You place the boundary yourself, in your editor, where you want it. That is the same
answer the tool gives everywhere else — it will mint identity and tell you the truth about
what it reads, and it will not decide where your thoughts begin.

## Verbs

```
scribe capture [--tag k:v]... [--topic T]... [--source S] [--name N] [--seal]
               [--html] [--append PILE] [--no-stamp]
    Clean handed input into a block. Plain text is kept verbatim; --html recovers
    structure + LaTeX (from MathML) and strips fluff via pandoc, marking loss in-band.
    --tag writes ANY key: the vocabulary is the human's, not the tool's.
    WITHOUT --append it does not write anywhere — it PRINTS the finished block, which
    is the mint-and-place path below. With --append it writes to the end of PILE.

scribe view key:value PILE [--recent] [--current]
    Gather every block carrying that tag, whole and un-moved. --current hides blocks a
    later block superseded, and declares the hiding in the view header.
scribe toc PILE [--by KEY]        contents by any key; names its axis and its loss
scribe keys PILE                  every key and value in the pile, with counts
scribe blocks PILE                every block with its whole tag run
scribe export key:value PILE [--bare] [--joiner S]
    Clean export to paste into the next mind. --joiner makes the concatenation itself
    code-safe when bodies are meant to tangle into one runnable file.
    If the pile has a header that does not parse, the export would be SHORT — so the
    warning rides along in the trailing manifest, and with --bare (which omits that
    manifest) the export is REFUSED outright rather than handed to you silently.
    Every other short artifact stays in reach: re-run the toc, regenerate the view,
    repair the pile. An export LEAVES. Once it is pasted somewhere else, nothing
    downstream can discover it was incomplete.

scribe push VIEW PILE [--seal]    land a view's edits home by #id — appends a superseding
                                  block; never overwrites. The new block is not sealed
                                  unless you ask; either way push says which.
                                  VIEW may be `-` to read the edited view from stdin.
                                  EXITS: 0 it happened (all landed, or nothing differed)
                                         1 nothing landed and nothing was written — a
                                           stale view whose block was already superseded,
                                           or a #id that is not in the pile
                                         2 part landed, part was declined
                                  A refusal means the tool declined, not that it broke —
                                  the same sense in which `git push` rejects a stale ref.
                                  Read the reasons it prints; they name what to regenerate.
scribe amend '#id' PILE [--also PILE]   correct a body in place — no block, no mark
scribe tag '#id' PILE --tag k:v [--remove k:v]   add or remove tags on a block
scribe capture --name N …         say it again; the name follows you
scribe recall NAME PILE [--all]   what does this name find? (Forth's lookup)
scribe names PILE [PILE...]       every @name:, and which definition is live

scribe seal '#id' PILE            hold the body now in the pile, recording WHEN you held
                                  it. Refuses an already-sealed or superseded block.
scribe unseal '#id' PILE          withdraw a seal; the block is ordinary again. Nothing
                                  is marked — changing your mind owes the pile nothing.
scribe verify PILE [PILE...]      is each SEALED block still the one its seal was issued
                                  for? Reports in fact-language, and states what it did
                                  NOT check
scribe backlinks TARGET PILE [PILE...]
    Every block whose tag VALUE names TARGET — the reverse of @ref:/@overrules:/etc.
    TARGET is '#id', 'pile.txt#id', or 'genesis:<hex>#id'. Computed fresh, never
    written back, and the report shows each pointer exactly as it is written.
scribe duplicates PILE [PILE...]  every id used by more than one block, with its tags.
                                  Read-only: declares, never repairs.
scribe activate CONDITION PILE [PILE...] [--key awaits]
    Every block declaring @awaits:CONDITION — the query half of an interest/activate
    pair. Read-only, never promotes.
scribe verify-export EXPORTED key:value PILE
    Has the pile drifted since EXPORTED was written? MATCH / DRIFT / NO MANIFEST.
scribe converges PILE PILE [...] [--by KEY]
    Candidate shared DNA between different piles never explicitly cross-referenced.
    Disclosed candidates only, never merged.

scribe stamp PILE [--show]        put the pile's own reading instructions on top
scribe check TEXT                 run the loss-auditor standalone
scribe doctor                     disclose the artifact SHA + runtime deps
```

Nothing runs on its own; you summon every view by an explicit command. The pile is never
mutated to produce a view.

**Exit codes.** `0` clean · `1` refused, and nothing was done · `2` done, with findings to
disclose.

## Two components that are not the core

**`viewer/` — not ready.** An experimental full-screen Textual front-end: commands in, views
as throwaway tabs. **Unfinished; do not depend on it.** It cannot damage a pile — it shells
out to scribe — but it may silently not offer you something scribe has. `textual` is its
dependency alone; scribe itself stays stdlib-only. See `viewer/README.md`.

**`edge/` — capturing from a chat.** `edge/chatgpt_adapter.py` turns a **saved** ChatGPT page
into canonical blocks, recovering the LaTeX and code fences a copy-paste garbles. Deliberately
**quarantined** (provider DOMs drift); the core never depends on it. See `edge/README.md`.

## Design principle

The tool does **no generation** and steers nothing: no scoring, no embeddings, no measurement
ever governs an output. It captures, holds, and presents; the human decides. Capture
*witnesses and marks* — a separate deterministic auditor flags lossy reductions in-band — and
never silently alters your text.

This is deliberate. A measurement that feeds back into what gets produced is the one pattern
this project refuses.

## Documents in this repo

- `guide_proposed-workflow.md` — the practical walkthrough: Scribe beside a plain editor,
  shown as real prompts and real output. **A working proposal, not finished documentation** —
  the opening is the usable path; later sections still hold unresolved design questions.
- `tagging/README.md` — which of the two tag documents to open, and when.
- `tagging/TAGS-bench-sheet.md` — the DOING sheet; keep it open while you tag.
- `tagging/TAG-KEYS-reference-v1-DRAFT.md` — the WHY behind each key, for a rainy day.
- `edge/README.md` · `viewer/README.md` — the two non-core components.
- `PROVENANCE.md` — the build record: what changed, when, and on what evidence.

---

## For the record — how this arrived

*Everything above describes the tool as it is. This section is for a reader who wants to know
why it is that shape, and it is safe to skip. Nothing here is needed to use scribe.*

**Verify with `scribe doctor`.** Stdlib-only, offline-rebuildable.

**Identity was rebuilt on 2026-08-05, and it is the change everything else hangs off.** Until
then a block's identity was `@mint:` — a SHA-256 over the pile, the block's position in it,
the moment, the speaker **and the body**. That fused three different questions into one token:
*which thing is this* (identity), *where did it come from* (provenance), and *is it as it was*
(integrity). The consequence was that **every corrected word was an identity event**, so
fixing a typo meant either growing the pile by a whole block or leaving the tool.

The evidence was gathered before the change, not after: `verify` across every real pile — 76
blocks — had reported `edited in place` **zero times**, and 45 of those 76 carried no mint at
all. The check cost something every day and had never once caught anything. That is what makes
it a removal rather than a trade.

The three questions now have three answers: the `#id`, the tags, and an opt-in seal. `amend`
is that change seen from the user's side — the only thing that had to be true first was that a
body is not part of what a block *is*.

**Blocks carrying the retired `@mint:` keep it.** It stays readable, `verify` reports it as
legacy, and it is never upgraded behind you — reissuing would change values that relational
tags already resolve against.

**`@genesis:` in the pile stamp** records when the pile began. Until 2026-08-05 it was
load-bearing: it was folded into every `@mint:` and was what kept one pile's identities
distinct from another's. Nothing depends on it now — the pile itself is the namespace — and it
is kept because when a pile began is worth knowing on its own account.

**Breaking behaviour changes, named as such.** v1.3.0 removed the content-derived id, so
re-capturing the same text no longer reproduces the same id — that reproducibility *was* a
duplicate-block bug. v1.3.1 made `push` append instead of overwrite. v1.4.0 retired `@mint:`.
Existing piles are untouched by all three and keep working.

**Full history, with the reasoning and the evidence for each ruling:** `PROVENANCE.md`.
