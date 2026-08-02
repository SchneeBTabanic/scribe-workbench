# Working between Scribe's Workbench and xed

*A guide to the tool **in your hands** — not the feature list, but how Scribe fits the way
you already work in xed. Written for the person who composes in a xed tab because a browser
input box has eaten his thinking before, keeps fragments parked in tabs mid-flight, and has
one long scratchpad with a hand-kept TOC and NAS notes scattered down its length.*

---

## First, what Scribe does and does not touch

Your xed tabs are doing **three different jobs at once**. Naming them separately is the
whole key, because Scribe touches each one differently.

**Job 1 — the crash buffer.** You write long inputs in a xed tab *before* trusting them to
a browser, because you've been burned: the frozen page, the refresh that eats an hour of
thinking. **Scribe does nothing here, and shouldn't.** A plain xed tab saved to disk is
already the right tool — write locally where it's safe, *then* hand it to the browser. Keep
doing exactly this. Scribe never enters Job 1.

**Job 2 — the staging place.** The tabs where you park fragments in flight: hold a passage
between tabs, keep a block open to copy into an AI, assemble pieces. **This is what Scribe
was built for** — but it does the job through *one pile + derived views* instead of many
live tabs. Whether that's better *for you* is something to feel out, not take on faith. Try
it on one real batch and see if the rhythm suits your hand.

**Job 3 — the scratchpad.** The long file with the TOC at the top and the NAS blocks
scattered down its body, kept in sync by memory and discipline. **This is the one Scribe
genuinely dissolves.** You stop hand-keeping the TOC; you stop remembering where each paste
went. One pile holds everything in arrival order; every other ordering is a view you summon.

So: **Job 1 stays a xed tab. Job 3 becomes the pile. Job 2 is the experiment.** The tabs
don't disappear from your life — the crash-buffer tab especially stays exactly as it is.

---

## One-time setup — so paths stop hurting

Scribe is one Python file. It isn't "installed" anywhere on your PATH, so two small habits
remove nearly all the terminal friction you were worried about.

**1. Give it a short name.** Add this to the end of `~/.bashrc`:

```bash
alias scribe='python3 /mnt/data/ProjectNamirha_git/scribe-workbench/scribe.py'
```

Change the path to wherever your copy of `scribe.py` actually lives. Then `source ~/.bashrc`
(or open a new terminal). Now you type `scribe`, not the long path.

**2. Give the pile one fixed home, and work from there.** Pick one folder and keep the pile
in it — for example:

```bash
mkdir -p ~/scribe
cd ~/scribe          # do your Scribe work from here
```

Because you're *in* `~/scribe`, the pile is just `pile.txt` in every command — no long
paths to type, nothing to get wrong. **This is the answer to "paths matter a lot in
terminal": one home, one short filename.** When you're in `~/scribe`, every example below
works verbatim.

> If the pile doesn't exist yet, your first `capture --append pile.txt` creates it.

Check the tool is alive and see its freeze fingerprint any time:

```bash
scribe doctor
```

**And the one command that always tells you everything else: `scribe --help`.** It lists
every verb scribe has, one line each, straight from the tool itself — never a second copy
of the list that this guide could drift out of sync with. Forgotten a verb's exact
arguments? `scribe <verb> --help` (e.g. `scribe backlinks --help`) shows that one verb's
full usage. This guide teaches the *daily rhythm* — when to reach for which verb, and why —
`--help` is the *reference*, and it can never go stale because it's generated from the code
that runs, not written down separately.

```bash
scribe --help              # every verb, one line each
scribe backlinks --help    # one verb, full argument detail
```

---

## The mental model — pile vs view

There are exactly two kinds of file, and keeping them straight is the one thing to
internalise:

| | **The pile** (`pile.txt`) | **A view** (`nas.view`, `live.view`, …) |
|---|---|---|
| what it is | the **truth** — every block, in arrival order | a **disposable** filter of the pile |
| how many | **one**, forever | as many as you like, thrown away freely |
| do you edit it? | rarely, and carefully | **yes — this is where you work** |
| how edits get home | — | `scribe push nas.view pile.txt` — matched by `#id`, landed as a new block |
| lose it? | back it up; it's everything | shrug — `scribe view …` rebuilds it |

The block header looks like this and is plain text you can read with Scribe switched off:

```
@@ #c98b 2026-07-07T19:48:03.112904 @act:protect-against-bit-rot @topic:nas @source:gemini @mint:c98b4f1a…64 hex…
ZFS vs ext4: use ZFS on the NAS for checksums and snapshots.
```

`@@` starts a block; `#c98b` is its **handle**; the `@key:value` tags are what views filter
on. Everything after the header line, until the next `@@`, is your verbatim text.

**Two names on that line, doing two different jobs (new in v1.3.0).** This is worth one
minute, because it changes what you can safely type:

| | | |
|---|---|---|
| `#c98b` at the front | the **handle** — the short name | yours to type, and what every `@ref:`-style tag points at |
| `@mint:c98b4f1a…` at the end | the **identity** — a whole 64-character fingerprint | nobody types it; nothing points at it; **never edit it** |

Why two? Because a name and an identity want opposite things. A name must be short enough to
type — and therefore short enough that two blocks could want the same one. An identity must
be long enough that they never can. One four-character token was doing both jobs, and it
broke: two blocks saying the same thing on the same minute got the *same* id, and a push then
landed an edit on the wrong one. The fix is not a longer id; it is **two fields**.

The practical upshot, in four lines:

- **The handle can grow.** If `#c98b` were already taken, capture would issue `#c98b1` and
  tell you so. It is never renamed afterwards.
- **You can abbreviate a handle**, git-style: `scribe tag c98 pile.txt …` works if `c98`
  names exactly one block. If it names two, scribe **refuses and lists them** instead of
  guessing — type another character.
- **A block's identity says two identical sayings are two sayings**, not one stored twice.
  That is the whole reason the mint is not computed from what the block says.
- **Piles made before 2026-08-01 have no mints.** They are not broken and are not upgraded
  behind you; `scribe duplicates pile.txt` names them as legacy. See the end of this guide.

The mint is 64 characters of hex on the end of every header, and yes, it is ugly. It sits
**last** on purpose: your eye meets the vocabulary you came for — `@topic:`, `@act:`,
`@source:` — and the hash trails off the end of the line where you can ignore it.

**Which tags to write is a separate sheet, deliberately.** Scribe accepts *any* `@key:value` —
there is no list of approved keys in the code — so the vocabulary is a discipline you keep, not
something the tool enforces. Keep
`tagging/TAGS-bench-sheet.md` (in this repo) open beside this guide; it is the working list.
(`TAG-KEYS-reference-v1-DRAFT.md` beside it explains *why* each key exists — read it later, not
while you work.)

**You can write any tag from the command line** — `--tag key:value`, as many as you like:

```bash
xsel -b | scribe capture --tag act:keeps-the-thread-alive --tag path:toward-one-pile \
                         --tag aspect:manifesting --topic nas --source gemini --append pile.txt
```

`--topic` and `--source` still work as before; `--tag` is simply the door to every other key.
You no longer have to type headers by hand in xed to use the vocabulary. (You still *can* —
hand-editing the tag run is safe; the `#id` and the timestamp are the two things not to touch.)

**Two things about tags that used to bite you in the terminal — one is now caught for you.**
A tag value must contain **no spaces** — hyphenate. A space stops scribe recognising the
header, and the block then folds into the one above it. As of **v1.1.0** scribe will not
write such a value at all: it refuses, names the line, and shows you the hyphenated form —

```
REFUSED: tag value 'two words' for @topic: contains whitespace. … Use hyphens: @topic:two-words
```

and if it meets one already in a pile (typed by hand, or written by an older scribe) it says so
loudly on every read, names the line number, and warns that the block count is short. It will
**not refuse to open the pile** — your material always stays reachable — but `scribe tag` and
`scribe push` refuse to *rewrite* a pile in that state, because a rewrite would make the loss
permanent. Fix the line it names, then re-run.

And `@state:` is **retired**: it is now `@aspect:` with exactly three values (`manifesting`,
`manifested`, `prospective`). Old piles carrying `@state:` still parse fine, and `--state`
still writes it if you ask — but scribe now announces the retirement every time, on writing
and on reading, so a dead key can never look like a live one. One thing that changed with it:
a view selected on `state:` used to quietly sort newest-first. It no longer does; **ordering
now comes from `--recent` only**, and every view says out loud which order it used.

---

## Job 3, dissolved — moving the scratchpad into the pile

You don't convert the old scratchpad in one shot (that would need your eye on every block
boundary — Scribe won't guess where your blocks split). You do it **the same way you'll use
it going forward: one block at a time, as you touch each topic.**

Say you're looking at the NAS section of your old scratchpad in a xed tab. Select that one
block, and get it into the pile. Two ways, depending on whether you'd rather hand Scribe a
**file** or a **clipboard**:

**A — via a file (most robust, zero extra tools).** In xed, save the fragment as its own
little file (or just save the whole tab), then:

```bash
scribe capture zfs-note.txt --topic nas --topic zfs --tag aspect:manifesting --source gemini --append pile.txt
```

Scribe cleans it into a block, stamps the arrival time, and appends it to the pile. It
prints something like `captured block #c98b (1 lines)` and tells you honestly whether its
loss-auditor flagged anything — it never silently alters your words.

**B — via the clipboard (fewer keystrokes once set up).** Scribe reads standard input when
you don't give it a file, so you can pipe your clipboard straight in. This needs a tiny
clipboard tool (one-time install on Mint/LMDE):

```bash
sudo apt install xsel        # one time only
```

Then, after selecting-and-copying the block in xed:

```bash
xsel -b | scribe capture --topic nas --topic zfs --tag aspect:manifesting --source gemini --append pile.txt
```

(`xclip -selection clipboard -o | scribe capture …` works identically if you have `xclip`
instead.) Path B is the closest thing to "grab from xed, drop in the pile" in one motion.

**Tagging is yours, and only yours.** Scribe will never guess a topic for you (that's the
sovereignty line it won't cross). The `--topic`/`--tag` flags are you telling it what the
block *is*. A block with no topic just lives in arrival order and shows up in no topic view
— which is fine; tag it later with `scribe tag c98b pile.txt --topic nas` when you decide.
(One tag is not yours: `scribe tag … --tag mint:…` is **refused**. The identity is minted
once, at capture, and is not vocabulary.)

Repeat, block by block, whenever you're already touching that material. There's no
"migration day" — the pile fills as you work.

---

## Job 2, the experiment — a view instead of a staging tab

Here's the daily loop that replaces "keep five tabs open to hold things." Suppose you want
to work on everything NAS-related.

**1. Derive a clean view file and open it in xed:**

```bash
scribe view topic:nas pile.txt > nas.view 2>/dev/null
xed nas.view &
```

The `> nas.view 2>/dev/null` part matters: it sends the **view** into the file and Scribe's
chatter (`1 block(s) in view…`) to the terminal, so the file opens **clean** in xed. The
`&` hands the terminal back to you.

Now `nas.view` holds every NAS block, **gathered together**, even though in the pile they're
scattered among router notes and git notes and philosophy. **None of them moved in the
pile.** This is your staging tab — except you didn't have to keep it open all week; you
summoned it in one line and you'll throw it away at the end.

**2. Work in it in xed** — develop a thought, add a `NOTE-TO-SELF:` line under a block, fix a
typo. Edit the **bodies**; leave the `@@ #id …` header lines alone (they're how edits find
their way home). Save the file in xed as usual.

**3. Push your edits home:**

```bash
scribe push nas.view pile.txt
```

Scribe matches each block by its `#id` and — **as of v1.3.1** — *appends* your edited version
as a new block rather than writing over the old one. (The output below is from a real run, so
its handles are real too; yours will differ.)

```
pushed home: 1 block(s) superseded — nothing was overwritten
  #2ea7 -> #b344   (#2ea7 keeps its body and its @mint:, and gains one tag: @superseded:#b344)
  The old blocks are still there and still say what they said. To correct one
  WITHOUT leaving that history in the pile, edit it directly in your editor —
  restic keeps that history instead. Both doors are yours; this one is push's.
```

The router block you didn't touch stays untouched. The thought you developed in the view is
now in the canonical pile and you can delete `nas.view` without a second thought.

**This is the one change most worth internalising, so here is what the pile actually looks
like afterwards.** Your edit did not replace anything. There are now two blocks:

```
@@ #2ea7 …  @topic:nas @source:gemini @superseded:#b344 @mint:2ea7…
ZFS vs ext4: use ZFS on the NAS for checksums and snapshots.       ← untouched, and marked stale

@@ #b344 …  @topic:nas @source:gemini @replaces:#2ea7 @mint:b344…
ZFS vs ext4: use ZFS on the NAS for checksums and snapshots.
Also: scrub monthly.                                               ← your edit, as its own block
```

Four things follow, and they are all things you will meet in a normal week:

- **The old block keeps its words.** Push never rewrites a body and never reissues an
  identity. The only mark it may add to an existing block is `@superseded:`, once.
- **The new block inherits the old one's tags**, so it turns up in every view the original
  did. A correction that fell out of its own topic would be a quiet loss.
- **`@superseded:` is written into the file, not worked out on demand** — so if you open the
  pile in xed a year from now with no tool running, the stale block *tells you itself* that
  something replaced it, and names what.
- **Pushing the same view twice is skipped, not doubled.** Scribe notices the block is
  already superseded, tells you your view is stale, and names the block to edit instead:

  ```
  SKIPPED 1 block(s) already superseded — your view is stale, and pushing it would fork the chain:
      #2ea7 was superseded by #b344. Regenerate the view and edit #b344 instead.
  ```

**Don't want that history in the pile?** Then don't use `push`. Open `pile.txt` in xed and
fix the block in place — it is a plain text file and always was, and restic keeps *that*
history instead. **Two doors, and you pick per edit:** history-in-the-pile through `push`,
history-in-your-backups through your editor. Scribe binds *itself* to append-only; it does
not bind you.

**Reading a pile that has supersessions in it.** A view shows both blocks and says so in its
own header, because hiding them by default would be exactly the silent exclusion this tool
refuses:

```bash
scribe view topic:nas pile.txt
#   # 1 block(s) here carry @superseded: — a later block has replaced them.
#   # Shown, not hidden; use --current to drop them.

scribe view topic:nas pile.txt --current       # just the live ones
#   # --current: 1 superseded block(s) HIDDEN from this view. They are still in the pile.
```

Use `--current` when you want to *work*; leave it off when you want to see how a thought
moved. Either way the pile keeps everything.

*One rough edge, said plainly:* `toc` and `export` do **not** know about supersession and
have no `--current`. So `scribe export topic:nas pile.txt --bare` hands the next mind **both**
the old wording and the new. When you export a topic you have pushed to, check what came out
before you paste it.

**To hand a batch to an AI** (the "copy the staging tab into ChatGPT" move), export instead
of view — `--bare` strips every header and back-link so there's nothing to scroll-and-delete
on the other end:

```bash
scribe export topic:nas pile.txt --bare > for-ai.txt
xed for-ai.txt &          # copy from here into the browser input box
```

Notice this respects **Job 1**: you're pasting *out of a local file into the browser*, the
safe direction you already trust.

---

## The daily rhythm, in one glance

```
   ┌─ Job 1: still a xed tab. Compose long input here, safe from the browser. Unchanged. ─┐

   capture   :  (saved fragment | xsel -b)  →  scribe capture … --append pile.txt
   explain   :  scribe stamp pile.txt               # once, for a pile made before v1.1.0 —
                                                    #   also gives an old pile its @genesis:
   look      :  scribe toc pile.txt                 # contents by subject (the default)
   look again:  scribe toc pile.txt --by path       # …the SAME pile, ordered by reaching
   what keys :  scribe keys pile.txt                # what your vocabulary has become
   gather    :  scribe view topic:X pile.txt > X.view 2>/dev/null ; xed X.view &
   live only :  scribe view topic:X pile.txt --current   # v1.3.1 — hide superseded blocks
   work      :  edit bodies in xed, save
   land      :  scribe push X.view pile.txt         # v1.3.1 — APPENDS a superseding block,
                                                    #   never overwrites ; delete the view
   hand off  :  scribe export topic:X pile.txt --bare > for-ai.txt ; xed for-ai.txt &
   who points at it: scribe backlinks '#c98b' pile.txt   # v1.1.2 — see below
   two blocks, one name: scribe duplicates pile.txt      # v1.3.0 — see below
   what did I change: scribe verify pile.txt             # v1.3.3 — as captured, or
                                                         #   edited by hand? see below
```

`scribe toc pile.txt` any time prints the whole table of contents from your tags — the list
you used to hand-maintain at the top of the scratchpad, now free and always current.

**The contents page opens by any key you name.** `--by topic` is only the default, kept so
nothing you already do changes. `--by act`, `--by path`, `--by aspect` index the same pile
along a different axis — the pile never moves; only the way in does. And every index now says
at the top which key it grouped by and **which keys it is not showing you**, so a contents
page can never quietly suggest that subjects are all there is:

```
# grouped by @topic: — 13 blocks, 8 distinct @topic: values
# NOT shown by this index: @source:(13) @act:(9) @path:(9) @aspect:(6)
# 2 of 13 blocks carry no @topic: — listed under (no @topic:) below
```

`scribe keys pile.txt` lists every key in the pile with its values and counts — use it to see
what you actually reach for, and to find the axes worth indexing by. (It replaces the
`grep | tr | sed | sort -u` recipe this guide used to carry: a practice living in a paragraph
of prose belongs in the tool.)

**`scribe backlinks` (v1.1.2) — "what points at this block?"** The moment you start using
relational tags — `@ref:`, `@overrules:`, `@corrects:`, `@superseded:`, or any key you invent
that names another block's id — you'll want the REVERSE question answered: not "what does
block c98b point at" (that's just reading its own header) but "what points *at* c98b?" That's
what this derives, fresh, every time you ask — never written back into the pile:

```bash
scribe backlinks '#c98b' pile.txt
#   What points at pile.txt#c98b (1):
#     #d4e1 (2026-08-01T09:00) via @corrects:#c98b
#
# nothing pointing at it yet?
scribe backlinks '#a1a1' pile.txt
#   (nothing points at pile.txt#a1a1)
```

It also works **across piles**, if you ever split your work into more than one — say a work
pile and a personal one, or one pile per project. Name the other pile in the target, `pile#id`:

```bash
scribe backlinks 'work.txt#c98b' work.txt personal.txt
```

Any tag value shaped `#id` or `otherpile.txt#id` counts, on any key — there's no fixed list of
"relational" keys to remember; if a value names a real block id, `backlinks` finds it.

**`scribe activate` (v1.2.0) — "who is currently waiting on this?"** If you use `@awaits:` to
mark a block as blocked on some condition (the way `RIPE-LEDGER.txt` does), this answers "which
blocks, right now, are waiting on exactly this" without you having to eyeball a `toc --by awaits`
grouping by hand:

```bash
scribe activate the-sovereigns-ruling pile.txt
#   What is @awaits:the-sovereigns-ruling (1):
#     pile.txt#a2 (2026-01-01T00:01)
```

It never edits anything — you still resolve the block yourself with `scribe tag`, once you've
acted on what was waiting. `--key dissolves` asks the same question of `@dissolves:` (a block's
own named retirement condition) instead.

**`scribe verify-export` (v1.2.0) — "has the pile moved since I saved this?"** Every non-bare
`export` now stamps its trailing manifest with a content fingerprint. If you keep an exported
view around — pasted into another tool, or tangled into a running file — this tells you whether
the pile it came from has since changed underneath it:

```bash
scribe export topic:nas pile.txt > nas.export.txt
# ... later, after editing pile.txt ...
scribe verify-export nas.export.txt topic:nas pile.txt
#   DRIFT — topic:nas has changed in the pile since export: was content:sha256:86829acf,
#   now content:sha256:0fae1347.
#     same 1 block(s) by id — body content changed
#     the exported file is stale; re-run `scribe export` to refresh it.
```

It never re-exports or repairs anything for you — MATCH, DRIFT, or NO MANIFEST (if the file was
exported `--bare`) is all it reports.

**`scribe converges` (v1.2.0) — "does this pile share DNA with a different one?"** If you keep
more than one pile — one per project — this looks for blocks in DIFFERENT piles that share a
literal tag value or a literal Charter-clause-shaped citation, without either side ever having
written a pointer to the other:

```bash
scribe converges projectA.txt projectB.txt
#   ## Shared tag-values across different piles (1)
#     @act:guard-against-drift  — 2 block(s) across 2 pile(s): projectA.txt, projectB.txt
#       projectA.txt#a1 (...)
#       projectB.txt#b1 (...)
```

Every line is a candidate to go READ, never an asserted relation — nothing here is merged or
written back, and a shared value can be a real convergence or just a coincidence; that judgment
stays yours. `--by act` (or any key) narrows the scan to one key; `--no-cites` skips the
citation half if you only want the tag-value scan.

**`scribe duplicates` (v1.3.0) — "do two blocks answer to the same name?"** In a pile made by
v1.3.0 or later this should always come back empty, because handles are checked as they are
issued. It matters for the piles you already had: those were made by a scribe that could mint
the same id twice, and this is how you find out whether yours did.

```bash
scribe duplicates pile.txt
#   pile.txt — 42 block(s), 0 duplicated handle(s)
#   no duplicated handles
```

On an older pile that *did* collide, it shows you both blocks with their identities, so you
can see whether they are one saying recorded twice or two different sayings:

```bash
scribe duplicates old-pile.txt
#   old-pile.txt — 2 block(s), 1 duplicated handle(s), NO @genesis: line (legacy pile)
#     2 block(s) carry no @mint: — minted before the identity split. Named, not upgraded.
#     #aaaa — 2 blocks
#         2026-01-01T00:00  no @mint: (legacy)  'first saying'
#         2026-01-02T00:00  no @mint: (legacy)  'second saying'
#         ^ all legacy: whether these are one saying or two cannot be decided by the tool.
#           Yours to rule.
```

**It never repairs anything, and that is deliberate** — re-minting a block would break every
`@ref:` already pointing at it. It reports; the ruling is yours. While a handle is ambiguous,
`push` and `tag` **refuse to write to it at all** and list the candidates, rather than picking
one and getting it wrong silently. That refusal is the actual protection; `duplicates` is just
how you go looking before you get refused.

**Old piles, and what to do about them.** A pile started before 2026-08-01 has no `@genesis:`
line and its blocks have no `@mint:`. Nothing is wrong with it — every handle that has worked
since capture keeps working — and scribe will **not** upgrade it behind your back, because
re-minting would break the relational tags pointing in. Verbs that meet one say so:

```
NOTE: pile.txt carries no @genesis: line (a pile born before 2026-08-01). Its mints fall
back to the pile's PATH alone — still distinct from other piles, but carrying no birth
moment. Run `scribe stamp` on a pile you have unstamped, or leave it.
```

`scribe stamp pile.txt` gives it a genesis from that moment on, so blocks captured *from now*
are minted properly. Blocks already in it keep exactly the handles they have. Leaving it alone
is also a fine answer.

**`scribe verify` (v1.3.3) — "is this block still the one I captured?"** You have two doorways
for changing a block: `push`, which appends and leaves a trail, and your own editor, which
leaves none in the pile. This tells you afterwards which door each block went through.

```bash
scribe verify pile.txt
#   pile.txt — 3 block(s): 2 as captured, 1 edited in place, 0 with no mint
#       #b5af  2026-08-02T13:36:51.552200  edited in place since capture
#         'Original sentence one. Rewritten final sentence.'
```

It works because the mint was computed from the block's own body, timestamp and `@source:` —
so re-computing it from what is in the file now and comparing to the stored `@mint:` says
whether anything moved. No database, no history, no copy of your old text anywhere.

**Read the wording carefully, because it is deliberate.** `edited in place since capture` is a
**statement of fact, not a complaint.** Editing a block by hand is a door the tool deliberately
leaves open for you; scribe has no business grading you for walking through it. That is why
this verb has no severities, no "invalid", no warnings — and a test enforces that, so it
cannot drift into scolding you later.

Three things it will tell you:

- **`as captured`** — untouched since it was written.
- **`edited in place since capture`** — the body, timestamp or `@source:` changed in the file.
  It cannot tell you *what* changed: the pile keeps no earlier copy, by design, so only restic
  or git holds the before.
- **`no mint — this check did not run`** — a block typed straight in, or captured before
  v1.3.0. Not a fault, and deliberately *not* reported as a clean pass either.

**If you cut a block out of the pile, it will not panic.** Deleting a block shifts every later
block's position, and a naive check would report the whole rest of the file as changed — which
would be intolerable if you were, say, cutting a scene from a long piece of writing. Instead it
recognises the pattern and says so:

```
POSITION SHIFT, not edits — and this is the ordinary shape of cutting material.
  From #05f4 onward, every block re-derives exactly at a constant offset of 1, which is what
  1 block(s) removed from the pile earlier does to the position each later block was minted at.
  Their BODIES ARE AS CAPTURED — only their position moved.
```

On an old pile (made before v1.3.0) it will say most blocks have no mint and that the check
therefore did not run on them. That is honest rather than reassuring, which is the point.

**Your pile explains itself to whoever opens it.** A pile created from v1.1.0 onward starts with
a short comment header saying what the format is, which commands search it properly, and why a
plain `grep` over it hands back fragments — a body line with no id or tags, or a header with no
claim, never a whole record. From v1.3.0 it also explains the long hex at the end of each header
(the mint) and carries the pile's own `@genesis:` line: this pile's birth identity, and the
reason its blocks stay distinct from every other pile's without any central register anywhere.
That matters beyond your own use: if you ever point an AI assistant
at the drive where your piles live, it meets the instruction **in the file** rather than needing
you to remember to explain it. For a pile you made before this, run `scribe stamp pile.txt` once.
It is only ever written when a pile is *created* (or when you run `stamp` yourself), so if you
delete the header it stays deleted — and `--no-stamp` declines it up front. It is all comment
lines above the first `@@`, so it changes no count, no index and nothing you can push home.

**One thing no command can do for you.** Whichever index you open habitually is the one you
will quietly start writing *for*. That is why the axis is now plural rather than merely
better — so that no single one pulls. Watching whether your own `@path:` values start being
chosen for how tidily they group, rather than for whether they are true, is yours alone; no
tool can check it.

---

## Gotchas that bite in the terminal (all real, all avoidable)

- **Always redirect a view to a file with `2>/dev/null`.** Without it, Scribe's status line
  lands in the file too and clutters what you open in xed. With it, the file is clean.
- **Edit views, not the pile — with one deliberate exception.** The pile is safe to read and
  safe to `push` into; but if you hand-edit a block's `@@ #id …` header you can orphan it.
  Change tags with `scribe tag <id> pile.txt --tag act:… ` / `--remove topic:…`, not by
  retyping the header. **Three things on that line are never yours to retype:** the `#id`, the
  timestamp, and `@mint:`. The exception is the one named above: editing a **body** by hand,
  when you deliberately want the correction without a supersession trail in the pile.
- **A push adds a block; it does not change one.** If your pile got longer after a push,
  nothing went wrong — that is the design. `scribe view … --current` gives you the tidy read;
  the pile itself keeps the whole movement.
- **An export can contain a stale body.** `export` and `toc` don't filter superseded blocks,
  so a topic you have pushed to exports both wordings. Eyeball `for-ai.txt` before pasting.
- **A non-zero exit is not always a failure.** Exit `1` means scribe refused to do what you
  asked. Exit `2` means it *did* the job and has something to disclose — a malformed header
  line, most often. Only `1` means nothing happened.
- **A view is a snapshot.** If you derive `nas.view`, then capture new NAS blocks, the old
  `nas.view` won't know about them — re-derive it. Views are cheap; regenerate freely.
- **`--append` vs no `--append`.** With `--append pile.txt`, the block goes into the pile.
  *Without* it, `capture` just prints the block to the terminal so you can eyeball it first.
  Use the print form when you're unsure and want to check before committing it to the pile.
- **Back up the pile; ignore the views.** The pile is the only irreplaceable file. This is
  exactly where the restic-plain backup tool (the sibling project) earns its keep — point it
  at `~/scribe/` and your whole thinking-pile is preserved, plainly, checksummed.

---

## What to actually test first

Don't adopt this wholesale. Take **one** real topic out of your current scratchpad — NAS is
the obvious one, since it's the scattered case that hurts. Capture its blocks into a fresh
`pile.txt`, derive `topic:nas` into xed, develop one note, push it home. Then ask the only
question that matters: *did that feel better in the hand than the five tabs did?* If yes,
Job 2 is yours to keep. If it felt like a step sideways, keep Scribe for Job 3 (the
scratchpad it plainly dissolves) and leave Job 2 to your tabs. Either answer is a good one.
