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

The vocabulary was developed in a sibling research project by reading systems that have kept
large tagged corpora honest for decades — Debian's lintian tag registry (the `Show-Always`
tier, the classification-that-is-not-a-fault, `Name-Spaced`), Knuth's WEB (a repeated
`@key:value` is a named section, so **a view is a tangle**), and work on verb-framing in
language. The reference document carries those citations per key.

Those cited source files live in the sovereign's research repositories and are **not in this
repo**, so a citation there is a record of what was read rather than a link you can follow.

## A companion checker exists, and is not in this repo

`tag_validator.py` (in the sibling GTPS-Agent project) checks a proposed tag against the
mechanical floor — has an act, has a path, the path names a direction, the aspect is one of
three — and asks the human the one question a machine must not decide: *does the verb
transform the whole from within, or is it bolted onto an intact noun?*

**scribe works fully without it.** Nothing in this repo calls it, and no verb needs it.

**Status:** the reference is a v1 working draft. The bench sheet is in daily use.
