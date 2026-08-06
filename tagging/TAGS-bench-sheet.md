# Tags — the bench sheet

**This is the one to keep open while you work.** Plain language, no citations, no history.
Everything here is *doing*.

Its companion, `TAG-KEYS-reference-v1-DRAFT.md`, holds **why** each key exists, where it came
from, and what was rejected. That is reading for a rainy day, not for now.

---

## Five mechanical rules. Read these once; they will save you an evening.

**1. A tag value must never contain a space.** Hyphenate instead: `@act:extend-insight`, never
`@act:extend insight`. **This is caught for you** — scribe refuses to write such a value, tells
you which tag, and shows you the hyphenated form:

```
REFUSED: tag value 'Rudolf Steiner' for @source: contains whitespace.
  Use hyphens: @source:Rudolf-Steiner
```

*Why the rule exists:* a space makes scribe stop recognising the whole header, and the block
folds into the one above it. Five blocks in, four blocks out. That can no longer happen
silently — but it is still the shape of the fault, and knowing it is how you read the warning.

**2. A key is one lowercase word; hyphens are allowed.** `@renames:` and `@renamed-from:` are
both fine. Prefer the single word where one will do; reach for the hyphen when the relation
genuinely needs two.

**3. `@topic:` is optional.** `scribe toc pile.txt --by act` — or `--by path`, or any key —
indexes the same pile along whichever axis you name, and every index says at the top which key
it used and which keys it is **not** showing you. So keeping `@topic:` is a free choice: it is
**the label on the drawer**. It helps you find the block; it does not say what the block
*means*. That is `@act:` and `@path:`'s job.

*The one thing no command can do for you:* whichever index you open habitually is the one you
will quietly start writing *for*. That is why the axis is plural rather than merely better — so
no single one pulls. Watch whether your own `@path:` values start being chosen for how tidily
they group rather than for whether they are true. Nothing can check that but you.

**4. Repeated values make views; unique values don't.** `scribe view aspect:prospective`
gathers every block sharing that exact value. So keys with a **short fixed list of values**
become useful views, and keys where every block says something different are simply read where
they sit. Both are fine — just know which you're writing.

**Values compare exactly.** `Claude` and `claude` are two different values and will split a
view in two. Worse, the listing sorts capitals first, so the two halves of an accidental split
are not adjacent on screen — they look like two unrelated entries. `scribe keys` shows you the
whole list, which is the argument for running it weekly.

**5. Five keys are the tool's, not yours.** Everything else on this sheet is vocabulary you
write. These five scribe writes itself:

| key | who writes it | what to do about it |
|---|---|---|
| `@sealed:` | scribe, on `scribe seal` / `capture --seal` | **Never touch it.** The integrity digest. `scribe tag --tag sealed:…` is refused — writing one by hand would assert the check instead of performing it. |
| `@sealed-at:` | the same three verbs | **Never touch it.** *When* the seal was taken, which is not always when the block was written. Inside the digest, so it cannot be backdated. Where it equals the block's own timestamp, the block was held from birth; where it is later, you worked on it first. |
| `@seals:` | the same three verbs | **Never touch it.** Declares *what the digest covers*, in the file, so the scope of the check is readable with the tool off. Also refused by `scribe tag`. |
| `@superseded:#new` | `scribe push`, onto the **old** block | Read it: a later block replaced this one. You may still write it by hand for a supersession `push` had no part in. |
| `@replaces:#old` | `scribe push`, onto the **new** block | Same — read it, and write it by hand when you are recording the relation yourself. |

The point of the rule is the **first three rows**: a digest, its declared scope and its moment
are assertions about a check that ran, so only the thing that ran the check may write them.
`scribe seal '#id' PILE` performs it; `scribe unseal` withdraws it and marks nothing. The last
two are still yours to write; they simply are no longer *only* yours.

**And one key is yours but behaves unlike the rest — `@name:`.** A name you can **say again**.
Capture the same `@name:` later and the name follows you to the new block; the earlier ones are
untouched, unmarked, and still resolve by `#id`. Nothing is superseded and nothing is owed.
`scribe recall NAME PILE` finds the live one; `scribe names PILE` lists them all. **No shape
discipline** — unlike `@act:`/`@path:`, a name compares with nothing, so write what you like.

---

## Every key does one of two jobs — and this decides whether it can ever make a VIEW

Worth understanding before the lists below, because it is the whole answer to *"which tags let
me call which views."* `scribe view key:value` and `scribe toc --by key` both work by finding
blocks where a key matches **exactly**. That single mechanical fact splits every tag key into
two families, and nothing else determines which:

| kind | value shape | what it can do |
|---|---|---|
| **grouping key** | a **small, closed** list of values — `@aspect:`, `@because:`, `@kept:` | makes a real view: `scribe view aspect:prospective pile.txt` pulls together every block sharing that value, whole |
| **witness key** | free text, different on every block — `@awaits:`, `@rejected:`, `@dissolves:` | read **in place**, on the block where it sits; it can never gather blocks into a grouping, and that was never its job |

So when you invent a new tag, the first question is not "what should I call it" — it's **which
kind is this**. A closed, short value-list earns you a view forever. A free-text value earns you
a note you'll be glad to find later, but never a grouping. Neither is better; picking the wrong
one for what you actually wanted is the only mistake here.

**One narrower door:** a witness key still can't make a *grouping* view, but
`@awaits:`/`@dissolves:` can be *queried by exact value* — `scribe activate
<the-exact-condition-string> pile.txt` finds every block carrying that precise value, across
any piles you name. It is an exact-match lookup, not a grouping view: you have to know or copy
the condition string verbatim.

**None of this is hard-wired into scribe** — it accepts any `@key:value`, no registry, no key
list in the code. **This sheet is the only registry that exists.** One partial exception:
`scribe toc` defaults to grouping by `@topic:` unless you pass `--by`, so `@topic:` gets a
small head start the others don't. No other key earns a second hard-wired default — `--by
<key>` already makes any key a grouping axis at the cost of one flag, and a second privileged
default would buy ergonomics by quietly re-introducing the registry this sheet exists to avoid.

---

## The two that carry the meaning

### `@act:` — what this block *does*
A verb phrase, hyphenated. Not a subject, not a category — **a doing**.

Think of a doorbell. A doorbell isn't "the entrance category", it *rings*. `@act:` is the
ringing. The test that catches the fake ones: strip the verb off and see what's left. If
`@act:manage-storage` leaves you holding a tidy noun called "storage", the verb was decoration
bolted onto a box, and the box is what you actually meant. Rephrase until the verb is doing
real work.

Good: `extend-insight` · `protect-against-bit-rot` · `guard-against-drift`
Avoid verbs that *finish*: `decide`, `choose`, `define`, `review`. Those name a task you
complete and tick off. You want verbs that keep going.

### `@path:` — what it reaches *toward*
The direction the block is heading. **A signpost, not an address.**

Formula: a direction word, then at least two real words.
`toward-creative-recombination` · `away-from-silent-data-loss` · `from-settled-toward-alive`

Direction words that count: toward · towards · away · from · into · onto · out · over · back ·
up · down · beyond · across · through · past.

Why this key exists, in one line: a block with only a subject-label goes cold and becomes
filing. A block that reaches somewhere stays alive.

**Two special values — the honest empties.** Use them rather than inventing a fake direction:

| value | means | the difference |
|---|---|---|
| `not-yet-discerned` | I feel this matters, but I don't yet know where it reaches | *I haven't looked in the cupboard yet* |
| `ruled-none` | I looked, and there is genuinely nothing | *I checked the cupboard; it's empty* |

Both are legitimate — they are a real answer, and the question stays open. Write the search
itself into the body when you use `ruled-none`, so a later reader knows you actually looked.

---

## Keys with a fixed list of values — grouping keys, these make VIEWS

Each has a **closed** list. Don't invent new values; the whole use is that a handful of blocks
share exactly one.

### `@aspect:` — how ripe it is · **3 values**
| value | means |
|---|---|
| `manifesting` | live, in progress, becoming |
| `manifested` | settled, done |
| `prospective` | promised, not yet — **this is the pod** |

Fruit on a tree: swelling · ripe · a bud that has not opened. `prospective` marks a thing you
believe but haven't earned yet, and marking it is what keeps it from quietly acting like law.

### `@origin:` — which kind of mind made it · **2 values**
`human` | `ai`. **This is the axis that lets the pile be split into "the human's programme" and
"the AI's programme" later.** Cheap to write now, impossible to reconstruct afterwards. If you
ever want to derive one artifact from the human-written blocks and another from the AI-written
ones, this is the key that does it — not `@source:`.

It is **not** covered by a seal: reworking an AI draft by hand until it is yours is a real
case, and that judgement is allowed to change.

### `@because:` — why a suppression or exception was made · **4 values**
Used together with `@overrules:`.

| value | means |
|---|---|
| `misread` | the check looked at it wrong |
| `parser-wrong` | the tool itself is broken here |
| `ruling` | nothing is broken — I've simply decided, and I stand behind it |
| `fix-elsewhere` | the fault is real, but the repair belongs somewhere else |

`fix-elsewhere` is the interesting one: it's an exception that is *waiting* for something, so
pair it with `@awaits:` or `@dissolves:`.

### `@kept:` — why something no longer in use is still here · **4 values**
`pedagogy` (kept to teach) | `foundation` (kept because later things stand on it) |
`evidence` (kept to prove something happened) | `specimen` (kept as an example of a kind).

**A museum label.** Without it, anything retired looks like litter, and the next person tidies
away something that was deliberate.

### `@reviewed:` — the claim only a human can make
A version or a date: `@reviewed:v1.4.1`. **This is not a fact a machine can assert for you** —
it means *"I read this since that point and acted on it."* An old value here is not a bug; it
just means nobody has reviewed it since.

### `@relaxes:` / `@tightens:` / `@reverts:#id` — which way the rule moved
Three small values naming the **direction** a change went, not just that a change happened.
*Loosened a requirement* · *made it stricter* · *undid an earlier change, which still stands
above this note so nobody loses the history.*

### `@preserves:` — what this change deliberately left alone
The anti-over-reading guard: *"this does NOT relax the requirement that…"* Use it when a change
is narrow and you can already picture a reader assuming it was broader than it was.

### `@breaches:` — a rule this block knowingly broke
Not a bug report — a **confession, kept**. Recording it in the record it breaches means the
next reader isn't left to discover the inconsistency and wonder if it was a mistake.

### `@gates:` — the irreversible act this block is withholding
A guard sitting in front of a point of no return. The safety on a trigger: naming what it
withholds is what lets a tool, or a person, refuse to fire while the gate is up.

### `@forecloses:` — the retreat this block ends
*"Past here, there is no backing out."* Worth locating precisely, because knowing exactly where
the point of no return is is what lets you deliberate **before** it rather than during it.

### `@enables:` — what someone else must be able to DO because of this block
Phrased as a verb they can perform, not a fact they now know. *"A stranger, with only this
note, can now restart the service"* — not *"the restart procedure is documented."*

### `@defers:` — whose judgment this is, even though you technically could act
A fence around someone else's competence. *"Not locked — just not yours to decide."*

### `@watches:` — an outside thing this block is keeping an eye on
A path or a URL, plus a plain note on HOW it's being watched, so nobody mistakes light watching
for a guarantee nothing drifted.

---

## Provenance — three keys, three different jobs

These are easy to confuse, and the difference matters because only one of them is ever frozen.

**`@source:` — whose saying is this.** `self` · `claude` · `gemini` · `Steiner` ·
`a-dream-I-had`. **Any value you like** — there is no list, and scribe will write whatever you
hand it. Keep your spellings consistent or the views split in two (rule 4). It is a
**citation**: a claim about a fixed past, which is why it is the one provenance key a seal
freezes.

**`@origin:` — which *kind* of mind made it.** `human` | `ai`. The derivation axis (above).

**`@attests:` — who *vouches* for this**, which is not always who wrote it. Author and guarantor
are different jobs: `@origin:ai @attests:self` says *the AI wrote it, I stand behind it.*
Deliberately **not** sealed — coming to stand behind something, or withdrawing from it, is
thinking again, and thinking again costs nothing here.

**`@captured:<where-and-when>`** — where this text actually came from, e.g. a chat thread.
Historical, unlike `@source:`.

**`@touched:<who>`** — a mind that passed through lightly, as distinct from the one who owns it.

**`@quoting:`** — pin a citation so it can't rot quietly. Either a short hash of the exact
sentence (`sha256:e44def50`) or a file and line (`policy.txt:4215-4736`). *A photograph of the
thing you're pointing at* — if the original shifts, the photo no longer matches and you find
out, instead of your reference silently coming to mean something else. (This is the same move
`@sealed:` makes, pointed outward instead of at the block itself.)

**`@formed:` / `@amended:`** — dates. When it came to be, and when a later layer was added.

**`@renames:<old-key>`** — you retired a key and this is the record. Keeps old spellings
readable instead of turning them into rubble.

---

## What a `#id` in a tag value points at

Every key in the next section carries another block's id.

| on the header | what it is | do you type it? |
|---|---|---|
| `#c98b` at the front | the **identity** — issued at capture, unique *within its pile* | **yes** — this is what `@ref:` and every key below point at |
| `@sealed:c98b4f…` at the end, *where one appears* | **integrity, not identity** — opt-in | **no** — nothing points at it, and `scribe tag` refuses to write it |

**In practice:**

- **Write the id, with or without the `#`.** `@ref:#c98b` is the convention; `@ref:c98b` parses
  identically. Cross-pile, use `@ref:other.txt#c98b` — `scribe backlinks` reads it.
- **An id may be longer than four characters.** If a short one was taken, capture issued a
  longer one and said so. Copy what is actually on the block; don't assume four.
- **Ids are never renamed** — they only ever grow at issue time. A pointer you wrote last year
  still lands.
- **A truncated pointer is resolved, not guessed.** `@ref:c9` resolves if `c9` names exactly one
  block; if it names two, the verb refuses and lists them. Prefer the full id.

## Keys that point at another block — witness keys, read in place

All take a block id: `@overrules:#c98b`.

**Every key below only ever names the FORWARD direction.** To ask the reverse question — *what
points at ME?* — use `scribe backlinks '#c98b' pile.txt`, which finds every block naming `c98b`
under ANY of these keys at once, across piles too (`scribe backlinks 'other.txt#c98b' this.txt
other.txt`). It is computed fresh and never written back.

**`@ref:#id`** — this block reaches to that one. The underlying rule is worth knowing: *being in
the pile is belonging; a reference is salience.* A block nothing points at is not an orphan — it
just hasn't been called on yet.

**`@overrules:#id`** — this block sets that one aside. Always pair with `@because:`. A note
pinned over a rule saying "not here, and here's why."

**`@superseded:#id`** — put this on the **old** block, pointing forward to what replaced it. Not
on the new one. The person who needs telling is the one who wandered into the outdated block;
the person reading the current version already knows. Never delete the old block — a stale note
that says it's stale beats no note at all.

> **This rule is enacted in the tool, and it is why `push` works the way it does.** `scribe
> push` appends your edited version as a new block and writes `@superseded:#new` onto the old
> one — **the only tag it may ever add to an existing block, at most one, touching neither the
> body nor the identity.** It is *written into the file* rather than derived, deliberately:
> derived would have been purer, and would have meant a reader with the tool switched off met
> no mark at all on the stale block. Scribe also places it **before** any digest in the tag
> run, because a warning parked behind sixty-four characters of hex is a warning nobody reads.
>
> **If the old block was sealed, the new one is not** — a seal is a claim about a body, and
> this is a different body, so it is yours to make rather than push's to assume. `push --seal`
> makes it. Either way push tells you which happened.

**`@yields:#id`** — if this block and that one ever contradict each other, that one wins.
Decided in advance, while you're calm, rather than during the argument.

**`@replaces:#id`** — a rewrite of that block, kept as a separate change rather than an edit
over the top. **`push` writes this half too**, onto the block it appends, so the pair is
complete from both ends. The new block **inherits the old one's tags**, so the correction shows
up in every view the original did. Both blocks answer `scribe view topic:X`, and the view says
so in its header; `--current` hides the superseded ones and declares that it did.

---

## Keys that carry a condition — witness keys, read in place

**`@awaits:`** — the encounter that would prove this. *A "call me when…" note.* Free text,
hyphenated: `@awaits:the-first-citation-that-drifts-and-is-caught`.

**`@dissolves:`** — the condition that would make this obsolete. *A "throw me away when…" note.*
`@dissolves:when-the-validator-accepts-hyphens`.

A matched pair — a birth condition and a death condition. Nearly every workaround you write
should carry a `@dissolves:`, because otherwise nobody, including you, will ever dare remove it.
Neither one *does* anything on its own: they tell you whether the moment arrived. You still
decide.

**`@verified:`** — the note you attach **after the fact**, when an `@aspect:prospective` block
closes, saying what confirmed it: `@verified:merged-to-main-ff-only`. **It overlaps
`@dissolves:` on purpose, and that overlap is still an open question:** `@dissolves:` is written
at BIRTH (*this is what would retire me*); `@verified:` at the CLOSE (*this is what actually
did*). You may find you only need one once you've used both a while — worth watching, not
deciding yet.

---

## Keys you can repeat on one block — witness keys, read in place

**`@defines:<word>`** — this is where that word was **born**, as opposed to merely used. A birth
certificate, not a sighting. No machine can work this out; only you know which block is the real
definition. Enormously useful later when you can't remember where a term came from.

**`@rejected:<the-path-not-taken>`** — the road you considered and didn't take. **The most
valuable tag on this sheet and the one nobody ever writes.** Records survive saying *what* was
decided; almost none say what was rejected, so six months later somebody — usually you —
proposes the dead idea again with enthusiasm. Signposts on the roads you closed.

---

## Keys about SHAPE and ORDER — witness keys, read in place

Not about what a block *means* — about how several blocks relate as a structure.

**`@continues:<the-whole-this-extends>`** — this block is another chapter of an earlier one, not
a new thing. Worth knowing: **you already have this without a new key** — `scribe view act:X`
gathers every block sharing that value into one whole. A view *is* a tangle. So the real
question isn't "is this a new key" but "what wholes do I want gathered," which is really about
which `@act:`/`@path:` values you choose to repeat.

**`@reads:after-#id`** — the order a human should read these in, which is neither arrival order
nor most-recent-first (the only two scribe offers). If you ever have a pile where the *telling*
order and the *arrival* order genuinely differ, this is the missing third axis.

**`@customizes:#id`** — a small, local adaptation of another block, declared as exactly that
rather than folded silently into it.

**`@refuses:<the-thing-not-done>`** — a capability you deliberately left out, with the reason
attached, so a future reader doesn't assume it was never considered.

**`@carries:<what-would-fall-without-this>`** — load-bearing, as opposed to decoration. Naming
which parts are structural is what lets everyone else avoid the change that looks harmless and
quietly erodes something.

**`@hoisted:from-#id`** — this block used to be squeezed inside that one and got its own space
because it needed to grow. The subtle reason this exists: people quietly shrink the important
but awkward part of something — error-handling, an edge case — just to keep the parent tidy,
without noticing they're doing it.

---

## For the tangle-loop: piles that derive more than one artifact

**`@part:<which-derived-artifact>`** — a grouping key. When one pile holds tagged blocks meant
for **different audiences or outputs** — a plain guide for a person, working code for a tool —
`@part:guide` and `@part:reader-logic` let `scribe export part:X pile.txt --bare` pull out
exactly one artifact at a time, leaving the other alone.

To derive a directly-runnable file:

```sh
scribe export part:reader-logic pile.txt --bare --joiner '\n\n'
```

The default separator is prose punctuation and breaks code; `--joiner` gives you a blank-line
join instead.

---

## Start with five. Add the rest when a block asks for it.

`@act:` · `@path:` · `@aspect:` · `@topic:` · `@source:`

That's a live, view-able, honest pile on day one. Everything else on this sheet answers a
*situation* — you overruled something, you retired something, you rejected a path — so reach
for it when the situation actually turns up. Reaching for all of them at once is how a method
dies in week one.

A worked block, using nothing exotic (**one line, however long** — a header wrapped onto a
second line is not a header, and its remainder becomes body text):

```
@@ #2904 2026-07-07T19:48:03.112904 @act:protect-against-bit-rot @path:toward-integrity-over-convenience @aspect:manifested @topic:nas @source:gemini @origin:ai @attests:self
ZFS vs ext4: use ZFS on the NAS for checksums and snapshots.
```

Every tag there is yours. The `#2904` at the front is scribe's, issued once at capture.

---

## How to get these onto a block

`--tag key:value`, repeatable, on both `capture` and `tag`:

```bash
scribe capture note.txt --tag act:protect-against-bit-rot \
                        --tag path:toward-integrity-over-convenience \
                        --tag aspect:manifested \
                        --topic nas --source gemini --append pile.txt
```

```bash
scribe tag c98b pile.txt --tag aspect:manifested --remove aspect:manifesting
```

`--topic` and `--source` are shortcuts; `--tag` is the door to everything else. The door does
not open for `--tag sealed:…` or `--tag seals:…` — those are refused on both verbs, because
they assert a check rather than describe a block.

*(Hand-editing the tag run in your own editor is perfectly safe if you prefer it — the `#id`,
the timestamp and any digest are the three things never to touch.)*

**Then check, in this order:**

1. **`scribe blocks pile.txt`** — shows each block's whole tag run, so you can see at a glance
   that what you meant to write actually landed.
2. **`scribe keys pile.txt`** — what your vocabulary has actually become: every key, every
   value, with counts. Worth running weekly; it is how you notice a key you invented once and
   never used again, a value that has quietly become a bucket, or a capitalisation split.
3. **`scribe toc pile.txt --by path`** — read your own pile along the axis of reaching rather
   than subject. The honest test of whether your paths are alive: if two blocks reach the same
   way, they gather; if every path is unique, they don't, and that tells you something too.
4. **`scribe verify pile.txt`** — for the blocks you sealed, whether they are still as sealed.
   It states what it did **not** check, every run: unsealed blocks, and the tags outside the
   seal's scope. A hand-edit is a sanctioned act; this verb carries no severities and never
   will.

**A companion checker exists and is not in this repo.** `tag_validator.py`, in the sibling
GTPS-Agent project, checks a tag's *shape* — has an act, has a path, the path names a
direction — and answers `PASS`, `REPHRASE` or `HELD` (a declared empty). **scribe works fully
without it**; nothing here calls it. Whether the reaching is *true* is yours either way.

---

## For the record — how some of this arrived

*Skip this. It is here so the reasoning is recoverable, not because you need it to tag.*

`@aspect:` replaced an earlier `@state:` key, which scribe still writes if you ask for it and
announces as retired when you do. `@verified:` and `@part:` were both found already in live use
before they were ever documented, and were added the moment a coverage check caught the gap.
`@topic:` was briefly load-bearing — the contents page could read nothing else — which is why
this sheet is careful to say it is now one axis among many.

The keys about shape and order come from Knuth's WEB read as a tagging system. The
grouping/witness split, the classification-that-is-not-a-fault, and the discipline of declaring
what an index does *not* show all come from Debian's lintian tag registry. Those source files
live in the sovereign's research repositories and are **not in this repo**; the reference
document carries the citations per key.
