# Tags — the bench sheet

**This is the one to keep open while you work.** Plain language, no citations, no history.
Everything here is *doing*.

Two companions, and neither is needed to start:
- `TAG-KEYS-reference-v1-DRAFT.md` — **why** each key exists, where it came from, what it was
  tested against, which Charter point it sits under. That is reading for a rainy day, not for now.
- My memory files — **you never need these.** They are my recall, not your reference.

---

## Four mechanical rules. Read these once; they will save you an evening.

**1. A tag value must never contain a space.** Hyphenate instead: `@act:extend-insight`, never
`@act:extend insight`. **As of scribe v1.1.0 this one is caught for you** — scribe refuses to write
such a value, tells you which tag, and shows you the hyphenated form. If it meets one already in a
pile (hand-typed, or written by an older scribe) it says so loudly on every read and names the line
number. *Why the rule still exists:* a space makes scribe stop recognising the whole header, and the
block folds into the one above it. Five blocks in, four blocks out. That can no longer happen
silently — but it is still the shape of the fault, and knowing it is how you read the warning.

**2. A key is one lowercase word — hyphens are now allowed.** `@renames:` and `@renamed-from:` are
both fine and both **visible to the validator** (fixed 2026-07-28: hyphenated keys used to be
invisible to it and it never said so). Prefer the single word where one will do; reach for the
hyphen when the relation genuinely needs two.

**3. `@topic:` is now optional, and that is new.** Until v1.1.0 the contents page could read
`@topic:` and nothing else, so dropping it emptied your whole index — the sheet said *demoted* and
the tool said *load-bearing*, and the tool always wins. Now `scribe toc pile.txt --by act` (or
`--by path`, or any key) indexes the same pile along whichever axis you name, and every index says
at the top which key it used and which keys it is **not** showing you. So keeping `@topic:` is a
free choice again: it is **the label on the drawer** — it helps you find the block, it does not say
what the block *means*. That is `@act:` and `@path:`'s job.

*The one thing no command can do for you:* whichever index you open habitually is the one you will
quietly start writing *for*. That is why the axis is now plural rather than merely better — so no
single one pulls. Watch whether your own `@path:` values start being chosen for how tidily they
group rather than for whether they are true. Nothing can check that but you.

**4. Repeated values make views; unique values don't.** `scribe view aspect:prospective` gathers
every block sharing that exact value. So keys with a **short fixed list of values** become useful
views, and keys where every block says something different are simply read where they sit. Both are
fine — just know which you're writing.

---

## Every key does one of two jobs — and this is what decides whether it can ever make a VIEW

This is worth understanding before the lists below, because it is the whole answer to *"which tags
let me call which views."* `scribe view key:value` and `scribe toc --by key` both work by finding
blocks where a key matches **exactly**. That single mechanical fact splits every tag key in this
sheet into two families, and nothing else determines which family a key is in:

| kind | value shape | what it can do |
|---|---|---|
| **grouping key** | a **small, closed** list of values — `@aspect:`, `@because:`, `@kept:` | makes a real view: `scribe view aspect:prospective pile.txt` pulls together every block that shares that value, whole |
| **witness key** | free text, different on every block — `@awaits:`, `@rejected:`, `@dissolves:` | read **in place**, on the block where it sits; it can never gather blocks into a `toc`/`view` grouping, and that is fine — that was never its job |

So when you invent a new tag, the first question is not "what should I call it" — it's **which
kind is this**. A closed, short value-list earns you a view forever. A free-text value earns you a
note you'll be glad to find later, but never a `toc`/`view` grouping. Neither is better; picking
the wrong one for what you actually wanted is the only mistake here.

**One narrower exception, added v1.2.0:** a witness key still can't make a *grouping* view (it has
no small closed set of values to group by), but `@awaits:`/`@dissolves:` specifically can now be
*queried by exact value*: `scribe activate <the-exact-condition-string> pile.txt` finds every block
currently carrying that precise `@awaits:`/`@dissolves:` value, across any piles you name. It is an
exact-match lookup, not a grouping view — you still have to know (or copy) the condition string
verbatim, unlike a grouping key's small closed vocabulary you can browse.

**None of this is hard-wired into scribe itself** — `scribe.py` accepts any `@key:value`, no
registry, no key list in the code (confirmed: `TAG_RE = @([^\s:]+):(\S+)`, matches anything).
**This sheet is the only registry that exists.** The one partial exception: `scribe toc` defaults to
grouping by `@topic:` unless you pass `--by`, so `@topic:` gets a small head start that the others
don't — worth knowing. **Ruled DECLINED, 2026-07-30** (RIPE-LEDGER.txt `#b558`, the
sovereign's hub ledger): no other key earns a second hard-wired default. §4.6 Poverty, plus
`--by <key>` already making any key a grouping axis at the cost of one flag — a second
privileged default would buy ergonomics by quietly re-introducing the very registry this
sheet exists to avoid. A future session can overturn this on evidence; it is a rejection
recorded with its reasoning, not a further deferral.

---

## The two that carry the meaning

### `@act:` — what this block *does*
A verb phrase, hyphenated. Not a subject, not a category — **a doing**.

Think of a doorbell. A doorbell isn't "the entrance category", it *rings*. `@act:` is the ringing.
The test that catches the fake ones: strip the verb off and see what's left. If `@act:manage-storage`
leaves you holding a tidy noun called "storage", the verb was decoration bolted onto a box, and the
box is what you actually meant. Rephrase until the verb is doing real work.

Good: `extend-insight` · `protect-against-bit-rot` · `guard-against-drift`
Avoid verbs that *finish*: `decide`, `choose`, `define`, `review`. Those name a task you complete
and tick off. You want verbs that keep going.

### `@path:` — what it reaches *toward*
The direction the block is heading. **A signpost, not an address.**

Formula: a direction word, then at least two real words.
`toward-creative-recombination` · `away-from-silent-data-loss` · `from-settled-toward-alive`

Direction words that count: toward · towards · away · from · into · onto · out · over · back · up ·
down · beyond · across · through · past.

Why this key exists at all, in one line: a block with only a subject-label goes cold and becomes
filing. A block that reaches somewhere stays alive.

**Two special values — the honest empties.** Use them rather than inventing a fake direction:

| value | means | the difference |
|---|---|---|
| `not-yet-discerned` | I feel this matters, but I don't yet know where it reaches | *I haven't looked in the cupboard yet* |
| `ruled-none` | I looked, and there is genuinely nothing | *I checked the cupboard; it's empty* |

Both are legitimate. The validator answers `HELD` rather than pass or fail — it is telling you
"noted, that's a real answer, and it's still open." Write the search itself into the body when you
use `ruled-none`, so a later reader knows you actually looked.

---

## Keys with a fixed list of values (the ones with a formula) — grouping keys, make VIEWS

These are the view-makers. Each has a **closed** list — don't invent new values, the whole use is
that a handful of blocks share exactly one.

### `@aspect:` — how ripe it is · **3 values**
| value | means |
|---|---|
| `manifesting` | live, in progress, becoming |
| `manifested` | settled, done |
| `prospective` | promised, not yet — **this is the pod** |

Fruit on a tree: swelling · ripe · a bud that has not opened. `prospective` marks a thing you
believe but haven't earned yet, and marking it is what keeps it from quietly acting like law.

### `@origin:` — which kind of mind made it · **2 values**
`human` | `ai`. This is the axis that lets the pile be split into "the human's programme" and "the
AI's programme" later. Cheap to write now, impossible to reconstruct afterwards.

### `@because:` — why a suppression or exception was made · **4 values**
Used together with `@overrules:` (below). Four reasons, worked out from real cases:

| value | means |
|---|---|
| `misread` | the check looked at it wrong |
| `parser-wrong` | the tool itself is broken here |
| `ruling` | nothing is broken — I've simply decided, and I stand behind it |
| `fix-elsewhere` | the fault is real, but the repair belongs somewhere else |

`fix-elsewhere` is the interesting one: it's an exception that is *waiting* for something, so pair
it with `@awaits:` or `@dissolves:`.

### `@kept:` — why something no longer in use is still here · **4 values**
`pedagogy` (kept to teach) | `foundation` (kept because later things stand on it) |
`evidence` (kept to prove something happened) | `specimen` (kept as an example of a kind).

**A museum label.** Without it, anything retired looks like litter, and the next person tidies away
something that was deliberate.

### `@source:` — which mind said it
`self` | `claude` | `fable` | `gemini` | `grok` … Conventional rather than strictly closed; keep the
spellings consistent or the views split in two.

### `@reviewed:` — the claim only a human can make
A version or a date: `@reviewed:v1.1.0`. **This is not a fact a machine can assert for you** — it
means *"I read this since that point and acted on it."* An old value here is not a bug; it just
means nobody has reviewed it since. A tool can still watch the gap and flag staleness gently — it
just can never write this tag itself.

### `@relaxes:` / `@tightens:` / `@reverts:#id` — which way the rule moved
Three small, closed values naming the **direction** a change went, not just that a change happened.
*Loosened a requirement* · *made it stricter* · *undid an earlier change, which still stands above
this note so nobody loses the history.* A changelog that only says "the rule changed" makes you
re-derive the direction by comparing old and new; this just says it.

### `@preserves:` — what this change deliberately left alone
The anti-over-reading guard: *"this does NOT relax the requirement that…"* Use it when a change is
narrow and you can already picture a reader assuming it was broader than it was.

### `@breaches:` — a rule this block knowingly broke
Not a bug report — a **confession, kept**. Some breaks are real and get made anyway, on purpose, for
a stated reason. Recording it in the record it breaches means the next reader isn't left to discover
the inconsistency and wonder if it was a mistake.

### `@gates:` — the irreversible act this block is withholding
A guard sitting in front of a point of no return. Think of the safety on a trigger: naming what it
withholds is what lets a tool (or a person) refuse to fire while the gate is up.

### `@forecloses:` — the retreat this block ends
The moment named as *"past here, there is no backing out."* Worth locating precisely, because
knowing exactly where the point of no return is is what lets you deliberate **before** it rather than
during it.

### `@enables:` — the thing someone else must be able to DO because of this block
Phrased as a verb they can perform, not a fact they now know. *"A stranger, with only this note, can
now restart the service"* — not *"the service's restart procedure is documented."* A handover note
that only states facts can still leave the next person stuck; one that names an act they can perform
doesn't.

### `@defers:` — whose judgment this is, even though you technically could act
A fence around someone else's competence. *"Not locked — just not yours to decide."* Marks a zone
you can enter but shouldn't, rather than one you structurally can't.

### `@watches:` — an outside thing this block is keeping an eye on
A path or a URL, plus a plain note on HOW it's being watched (by a tool comparing version strings? by
a person checking now and then?) so nobody mistakes light watching for a guarantee nothing drifted.

---

## Keys that point at another block — witness keys, read in place

All take a block id: `@overrules:#c98b`.

**Every key below only ever names the FORWARD direction — which block reaches out.** Until
v1.1.2 there was no way to ask the reverse question ("what points at ME?") without knowing
in advance which of these keys to search and running `scribe view <key>:<value>` once per
key. Now: `scribe backlinks '#c98b' pile.txt` finds every block naming `c98b` under ANY of
these keys at once (see GUIDE-scribe-with-xed.md for the worked example, and
`tagging/TAG-KEYS-reference-v1-DRAFT.md` A.9 for the full why). Same command answers it
across piles too: `scribe backlinks 'other.txt#c98b' this.txt other.txt`.

**`@ref:#id`** — this block reaches to that one. Worth knowing the underlying rule: *being in the
pile is belonging; a reference is salience.* A block nothing points at is not an orphan — it just
hasn't been called on yet.

**`@overrules:#id`** — this block sets that one aside. Always pair with `@because:`. A note pinned
over a rule saying "not here, and here's why."

**`@superseded:#id`** — put this on the **old** block, pointing forward to what replaced it. Not on
the new one. The person who needs telling is the one who wandered into the outdated block; the
person reading the current version already knows. Never delete the old block — a stale note that
says it's stale beats no note at all.

**`@yields:#id`** — if this block and that one ever contradict each other, that one wins. Decided
in advance, while you're calm, rather than during the argument.

**`@replaces:#id`** — a rewrite of that block, kept as a separate change rather than an edit over
the top.

---

## Keys that carry a condition — witness keys, read in place

**`@awaits:`** — the encounter that would prove this. *A "call me when…" note.* Free text,
hyphenated: `@awaits:the-first-citation-that-drifts-and-is-caught`.

**`@dissolves:`** — the condition that would make this obsolete. *A "throw me away when…" note.*
`@dissolves:when-the-validator-accepts-hyphens`.

These two are a matched pair — a birth condition and a death condition. Nearly every workaround you
will ever write should carry a `@dissolves:`, because otherwise nobody, including you, will ever
dare remove it. Neither one *does* anything on its own: they tell you whether the moment arrived.
You still decide.

**`@verified:`** — found already in live use (2026-07-29), not on this sheet until now, added the
moment a checker caught the gap. What it actually is: the note you attach **after the fact**, when a
`@aspect:prospective` block closes, saying what confirmed it — `@verified:merged-to-main-ff-only`,
`@verified:prediction-held-branch-closed`. **It overlaps `@dissolves:` on purpose, and that overlap
is still an open question, not a settled one:** `@dissolves:` is written at BIRTH ("this is what
would retire me"); `@verified:` is written at the CLOSE ("this is what actually did"). You may find
you only ever need one of the two once you've used both a while — worth watching, not deciding yet.

---

## Keys you can repeat on one block — witness keys, read in place

**`@defines:<word>`** — this is where that word was **born**, as opposed to merely used. A birth
certificate, not a sighting. No machine can work this out; only you know which block is the real
definition. Enormously useful later when you can't remember where a term came from.

**`@rejected:<the-path-not-taken>`** — the road you considered and didn't take. **The most valuable
tag on this sheet and the one nobody ever writes.** Records survive saying *what* was decided;
almost none say what was rejected, so six months later somebody — usually you — proposes the dead
idea again with enthusiasm. Signposts on the roads you closed.

**`@touched:<who>`** — a mind that passed through lightly, as distinct from `@source:`, the one who
owns it.

---

## Provenance, when you want it — mostly witness; `@source:` groups if you keep spellings consistent

**`@attests:<who>`** — who *vouches* for this, which is not always who wrote it. Author and
guarantor are different jobs: `@origin:ai @attests:self` says *the AI wrote it, I stand behind it.*

**`@captured:<where-and-when>`** — where this text actually came from, e.g. a chat thread.
Historical, unlike `@source:`.

**`@quoting:`** — pin a citation so it can't rot quietly. Either a short hash of the exact sentence
(`sha256:e44def50`) or a file and line (`policy.txt:4215-4736`). *A photograph of the thing you're
pointing at* — if the original shifts, the photo no longer matches and you find out, instead of your
reference silently coming to mean something else.

**`@formed:` / `@amended:`** — dates. When it came to be, and when a later layer was added.
`@amended:` is what lets you walk a block backwards through its own changes.

**`@renames:<old-key>`** — you retired a key and this is the record. Keeps old spellings readable
instead of turning them into rubble.

---

## Keys about SHAPE and ORDER — witness keys, read in place

These come from Knuth's WEB, read as a tagging system. They're not about what a block *means* — they're
about how several blocks relate to each other as a structure.

**`@continues:<the-whole-this-extends>`** — this block is another chapter of an earlier one, not a
new thing. Worth knowing: **you already have this without a new key** — `scribe view act:X pile.txt`
gathers every block sharing that value into one whole. A view *is* a tangle. So the real question
this key answers isn't "is this a new key" — it's "what wholes do I want gathered," and that question
is really about which `@act:`/`@path:` values you choose to repeat.

**`@reads:after-#id`** — the order a human should read these in, which is neither arrival order nor
most-recent-first (the only two scribe offers today). If you ever have a pile where the *telling*
order and the *arrival* order genuinely differ, this is the missing third axis.

**`@customizes:#id`** — a small, local adaptation of another block, declared as exactly that rather
than folded silently into it.

**`@refuses:<the-thing-not-done>`** — a capability you deliberately left out, with the reason
attached. *"I saw this option and chose not to build it, and here's why"* — so a future reader (or
future you) doesn't assume it was simply never considered.

**`@carries:<what-would-fall-without-this>`** — load-bearing, as opposed to decoration. Naming which
parts of a pile or a design are structural is what lets everyone else avoid the kind of change that
looks harmless and quietly erodes it.

**`@hoisted:from-#id`** — this block used to be squeezed inside that one, and got its own space
because it needed to grow. The subtle reason to know this exists: people quietly shrink the important
but awkward part of something (error-handling, an edge case) just to keep the parent tidy, without
noticing they're doing it. Splitting it out and naming where it came from lets it grow to whatever
size it actually needs.

---

## For the tangle-loop: piles that derive more than one artifact

**`@part:<which-derived-artifact>`** — a grouping key, found in live use (2026-07-29) before it was
ever documented. When one canonical pile holds tagged blocks meant for **different audiences or
outputs** — a plain guide for a person, working code for a tool — `@part:guide` and
`@part:reader-logic` let `scribe export part:X pile.txt --bare` pull out exactly one artifact at a
time, leaving the other alone. See `ontology-midwife/sandbox/tangle-loop-demo.txt` for a small,
real, working example — including how to derive a directly-runnable file:
`scribe export part:reader-logic pile.txt --bare --joiner '\n\n'` (v1.1.1 — the default separator is
prose punctuation and breaks code; `--joiner` gives you a blank-line join instead).

---

## Start with five. Add the rest when a block asks for it.

`@act:` · `@path:` · `@aspect:` · `@topic:` · `@source:`

That's a live, view-able, honest pile on day one. Everything else on this sheet answers a *situation*
— you overruled something, you retired something, you rejected a path — so reach for it when the
situation actually turns up. Reaching for all of them at once is how a method dies in week one.

A worked block, using nothing exotic:

```
@@ #c98b 2026-07-07T19:48 @act:protect-against-bit-rot @path:toward-integrity-over-convenience
   @aspect:manifested @topic:nas @source:gemini @origin:ai @attests:self
ZFS vs ext4: use ZFS on the NAS for checksums and snapshots.
```

---

## How to actually get these onto a block (scribe v1.1.0 — changed 2026-07-28)

**You can now write every key on this sheet straight from the command line.** `--tag key:value`,
repeatable, on both `capture` and `tag`:

```bash
scribe capture note.txt --tag act:protect-against-bit-rot \
                        --tag path:toward-integrity-over-convenience \
                        --tag aspect:manifested \
                        --topic nas --source gemini --append pile.txt
```

```bash
scribe tag c98b pile.txt --tag aspect:manifested --remove aspect:manifesting
```

`--topic` and `--source` still work; `--tag` is simply the door to everything else. `--state` also
still works but announces that it writes a **retired** key — write `--tag aspect:…` instead.

*(This replaces the old hand-typing workaround. Hand-editing the tag run in xed is still perfectly
safe if you prefer it — the `#id` and the timestamp are the two things never to touch — but it is no
longer the only route, and it was the route that tripped the space bug.)*

**Then check, in this order:**

1. `python3 GTPS-Agent/tag_validator.py "@act:… @path:… @aspect:…"` — checks the *shape* of the
   reaching, before you commit to the wording.
2. `scribe blocks pile.txt` — now shows each block's **whole tag run**, so you can see at a glance
   that what you meant to write actually landed.
3. `scribe keys pile.txt` — what your vocabulary has actually become: every key, every value, with
   counts. Worth running weekly; it is how you notice a key you invented once and never used again,
   or a value that has quietly become a bucket.
4. `scribe toc pile.txt --by path` — read your own pile along the axis of reaching rather than
   subject. This is the honest test of whether your paths are alive: if two blocks reach the same
   way, they gather; if every path is unique, they don't, and that tells you something too.

---

**Check any tag before you commit to it:**
`python3 GTPS-Agent/tag_validator.py "@act:… @path:… @aspect:…"`
It answers `PASS`, `REPHRASE` (with the reason), or `HELD` (a declared empty). It checks the
**shape** only. Whether the reaching is true is yours, and it will say so.
