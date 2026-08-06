# Tagging — the vocabulary scribe's `@key:value` tags are written in

scribe itself has **no registry and no opinion**: it accepts any `@key:value`, and
`--tag key:value` writes any key you name. That is deliberate — the vocabulary belongs to the
person keeping the pile, not to the tool. It also means the discipline has to live somewhere,
and it lives here.

**The one-line version:** a tag should carry **a verb and a toward**. `@act:` names what the
block *does*; `@path:` names what it *reaches toward* or *away from*. A tag with a verb but no
direction re-freezes into a bucket, and a bucket is a dead tag.

    @topic:knowledge-integration                    dead — a noun in a drawer
    @act:extend-insight @path:toward-recombination  alive — a doing, and a direction

**Why any of this.** A tag that only names a subject can only ever answer *"what is this
about?"* — and an index that reads one key teaches you to write for that key. Hence
`scribe toc PILE --by <key>`: the same pile indexed along whatever axis you name, with the
index stating which keys it is *not* showing you.

## Two documents, and they are different jobs

- **`TAGS-bench-sheet.md` — the DOING sheet.** Keep this open while you work. Plain language,
  no citations, four mechanical rules, then the keys with metaphors and value tables. It ends
  with START WITH FIVE, because reaching for the whole vocabulary at once is how a method dies
  in week one. **If you read one file, read this one.**
- **`TAG-KEYS-reference-v1-DRAFT.md` — the WHY.** Where each key came from, what it was tested
  against, what was rejected and why. Reading for a rainy day, not for while you work.

## Four keys are the tool's, not yours

Everything else on the bench sheet is vocabulary you write. These four scribe writes itself,
and two of them it will not let you write:

- **`@sealed:`** and **`@seals:`** — *opt-in* integrity, written only by `capture --seal`.
  `@sealed:` is the digest; `@seals:` declares what that digest covers, in the file, so the
  scope of the check is readable with the tool switched off. `scribe tag` **refuses** both —
  writing one by hand would assert the check rather than perform it — and they sit last on the
  header so your vocabulary stays on the readable side of the hash.

  **A seal is not an identity.** *Which block this is* is the `#id` at the front, and that is
  what every `@ref:`-style tag points at.

- **`@superseded:`** and **`@replaces:`** — the two halves of one supersession, written by
  `scribe push` because push appends a corrected block rather than overwriting the original.
  These stay ordinary vocabulary you may also write by hand, to record a supersession push had
  no part in. The *direction* push writes them in is this sheet's own ruling, quoted in the
  source: **the mark goes on the block a reader will wander into by mistake.**

One key is **yours**, optionally, and is worth knowing about early:

- **`@name:`** — a name you can **say again**. Capture the same `@name:` later and the name
  simply follows you to the new block; the earlier ones are untouched, unmarked, and still
  resolve by their `#id`. Nothing is superseded and nothing is owed. `scribe recall NAME`
  finds the live one, `scribe names` lists them all. It carries **no shape discipline** —
  unlike `@act:`/`@path:`, a name compares with nothing, so write what you like.

All are covered properly in `TAGS-bench-sheet.md`: mechanical rule 5, the `#id` section before
the pointer keys, and the key entries themselves.

## Where this came from, honestly

Two layers, and the order matters — because the earlier version of this section named only the
second, which quietly made the whole thing look reasoned down from other people's systems.

**The impulse is the keeper's own, and it came from a lived problem.** Working at length with a
language model, he noticed how easily the work was pulled up into abstract thought — fluent,
agreeable, and going nowhere anybody could act on. The response was to insist that a record be
grounded in **doing**. What was born there was called **Affordances** — real levers a human can
actually take, rather than a smooth surface to receive — and it is where the `@act:` idea began,
long before it had a syntax.

**Then it was lost, and had to be found again — three times.** This is not incidental; it is
the shape of the thing. It came back through **Talmy's** verb-framed / satellite-framed
distinction, which gave the *reaching* half its name. It was reinforced from an unexpected
direction: **filing systems from before computers**, where organisations filed paper by
**function** — what a document *does* — and where the arrival of computing flattened that into
nominal categories and the functional axis was simply lost for a while. From there it went
through **FrameNet** and into a sibling agent project, and finally here.

**One strand is still running, and it is the reason this discipline is not only for humans.**
A pile is a mixture: some of it an AI wrote. So the question arose whether a language model
could resist its *own* pull toward nominalisation well enough to write `@act:` and `@path:`
values for its own memory piles that were genuine doings — rather than, in the keeper's phrase,
**a verb garment worn over a noun**. A gauntlet was built to find out: a stack that puts a
proposed tag through a language with strong verb-and-path formative force — **Japanese** —
before it is accepted. That is a separate research project, still open, and not in this repo.
It is worth knowing it exists, because it is the honest measure of how hard the rule below is:
the machine that generates tags fastest is the one that needs the most help obeying it.

**The enemy is the same one every time, wearing three costumes:** a conversation that drifts
into abstraction, a filing system that turns *what this does* into *what drawer it lives in*,
and a tag that is a noun in a drawer. All three are the same move — **nominalisation** — and
resisting it is not a stylistic preference. It is the whole reason `@act:` and `@path:` are
shaped the way they are.

That tension does not go away, and this vocabulary does not resolve it. A machine cannot search,
relate, or find anything again without discrete named units; a living thought does not arrive in
units. **The discipline here is an attempt to stand between the two** — to nominalise as little
as will still let you find the thing.

**The second layer is where it was tested and sharpened.** The mechanics — and most of the keys
beyond the first two — were worked out by reading systems that have kept large tagged corpora
honest for decades: **Debian's lintian tag registry** (the `Show-Always` tier, the
classification-that-is-not-a-fault, `Name-Spaced`), **Knuth's WEB** (a repeated `@key:value` is
a named section, so **a view is a tangle**), and work on verb-framing in language. The reference
document carries those citations per key. They did not supply the impulse; they kept it honest.

Those cited source files live in the keeper's research repositories and are **not in this
repo**, so a citation there is a record of what was read rather than a link you can follow.

## A companion checker exists, and is not in this repo

`tag_validator.py` (in the sibling GTPS-Agent project) checks a proposed tag against the
mechanical floor — has an act, has a path, the path names a direction, the aspect is one of
three — and asks the human the one question a machine must not decide: *does the verb
transform the whole from within, or is it bolted onto an intact noun?*

**scribe works fully without it.** Nothing in this repo calls it, and no verb needs it.

**Status:** the reference is a v1 working draft. The bench sheet is in daily use.
