# Tagging — the vocabulary scribe's `@key:value` tags are written in

scribe itself has **no registry and no opinion**: `TAG_RE` accepts any `@key:value`, and
`--tag key:value` writes any key you name. That is deliberate (the vocabulary belongs to the
person keeping the pile, not to the tool). It also means the discipline has to live somewhere,
and it lives here.

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
