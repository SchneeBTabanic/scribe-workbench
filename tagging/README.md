# Tagging — the vocabulary scribe's `@key:value` tags are written in

scribe itself has **no registry and no opinion**: `TAG_RE` accepts any `@key:value`, and
`--tag key:value` writes any key you name. That is deliberate (the vocabulary belongs to the
person keeping the pile, not to the tool). It also means the discipline has to live somewhere,
and it lives here.

**Three exceptions, added 2026-08-01/02 and small enough to state here in full.** scribe now
writes three tags of its own, and one of them it will not let you write:

- **`@mint:`** — a block's identity, minted once at capture and never recomputed. `scribe tag`
  **refuses** it, `scribe keys` excludes it with a notice, and it sits last on the header so
  your vocabulary stays on the readable side of the hash. It is not a description of a block;
  it is *which block this is*. The short `#id` at the front is a separate thing — the **handle**,
  a name — and that is what every `@ref:`-style tag points at. This is not a registry: nothing
  central knows about any block; each pile carries its own `@genesis:` in its stamp and the
  distinctness falls out of that.
- **`@superseded:`** and **`@replaces:`** — still ordinary vocabulary you may write by hand, but
  `scribe push` now writes them too, as the two halves of one supersession, because `push`
  appends a corrected block rather than overwriting the original. The *direction* it writes them
  in is this sheet's own ruling, quoted in the source: the mark goes on the block a reader will
  wander into by mistake.

Both are covered properly in `TAGS-bench-sheet.md` — mechanical rule 5, the `#id` section before
the pointer keys, and the two key entries themselves.

**Two documents, and they are different jobs:**

- **`TAGS-bench-sheet.md` — the DOING sheet.** Keep this open while you work. Plain language,
  no citations, four mechanical rules, then the keys with metaphors and value tables. It ends
  with START WITH FIVE, because reaching for the whole vocabulary at once is how a method dies
  in week one. **If you read one file, read this one.**
- **`TAG-KEYS-reference-v1-DRAFT.md` — the WHY.** Where each key came from, what it was tested
  against, what was rejected and why. Reading for a rainy day, not for while you work.

**The one-line version:** a tag should carry **a verb and a toward**. `@act:` names what the
block *does*; `@path:` names what it *reaches toward* or *away from*. A tag with a verb but no
direction re-freezes into a bucket; a bucket is a dead tag.

    @topic:knowledge-integration                    dead — a noun in a drawer
    @act:extend-insight @path:toward-recombination  alive — a doing, and a direction

**Why any of this.** A tag that only names a subject can only ever answer *"what is this
about?"* — and an index that reads one key teaches you to write for that key. Hence
`scribe toc PILE --by <key>`: the same pile indexed along whatever axis you name, with the
index stating which keys it is *not* showing you.

**Where this came from, honestly.** The vocabulary was developed in a sibling research project
by reading systems that have kept large tagged corpora honest for decades — Debian's lintian
tag registry (the `Show-Always` tier, the classification-that-is-not-a-fault, `Name-Spaced`),
Knuth's WEB (a repeated `@key:value` is a named section, so **a view is a tangle**), and work
on verb-framing in language. The reference document carries those citations per key.

**A companion checker exists but is not in this repo:** `tag_validator.py` (in the sibling
GTPS-Agent project) checks a proposed tag against the mechanical floor — has an act, has a
path, the path names a direction, the aspect is one of three — and asks the human the one
question a machine must not decide: *does the verb transform the whole from within, or is it
bolted onto an intact noun?* scribe works fully without it.

**Status:** the reference is a v1 working draft. The bench sheet is in daily use.
