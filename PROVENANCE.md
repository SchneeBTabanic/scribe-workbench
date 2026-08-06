# PROVENANCE — Scribe's Workbench

## v1.5.0 — "a check must declare what it covers, and sealing is an act with its own moment" (2026-08-06) — CURRENT

Two things, and the second is why the first was reachable: **the four interface documents were
rewritten as an interface**, and the seal learned to state its own scope.

### The documentation baseline, and the defect class it exposed

Schnee asked for the documents to be audited against the code before he tested the tool through
them, *"because if I run tests, something will always be obfuscated if I am operating on wrong
documentation."* That was the right order, and the audit found the register of defect he
suspected.

**The mechanism, verified in the commit diffs rather than inferred.** The v1.4.0 documentation
pass substituted at every site containing the literal string `@mint:` — in the bench sheet,
thirteen changed lines, every one of them with `@mint:` on the removed side. **Every claim that
expressed the same idea without using the token survived untouched.**

> **A correction that searches for a token cannot find the claims that token was making.**

The consequence that mattered: the README and the bench sheet both still promised, in the
present tense, that a saying could not be silently re-attributed — the README calling it *"the
axis this project cares about most"* — while v1.4.0 had made sealing opt-in, so on an ordinary
block the promise was false. **A capability had left the tool and its description had stayed in
the manual.** Reproduced at the command line, not read off the source.

Also found and fixed: `verify`'s help text named the retired `@mint:` twice; `push` printed
*"keeps its body and its @mint:"* on every run; `view`'s help advertised `state:`, a key the
tool's own `RETIRED_KEYS` announces as retired. **These are the only documentation a user meets
without choosing to open a file**, and they were not part of any doc pass because they are code.

**Rewritten:** `README.md`, `tagging/README.md`, `tagging/TAGS-bench-sheet.md` — present tense
throughout, version archaeology relocated to a marked *"For the record"* section at the foot of
each. `tagging/TAG-KEYS-reference-v1-DRAFT.md` keeps Appendix A as the historical harvest and
gains **A.13**; A.11's supersession notice moved above the table it had been breaking, and A.12
gained one. Every citation to a file outside this repo now says it is outside this repo and
that scribe works fully without it — a recurrence of the defect commit `1333e69` already fixed
once, returning through the two documents that commit moved.

### `@seals:` — the scope, declared in the file

`capture --seal` now writes `@seals:body-ts-source` beside `@sealed:<hex>`. `scribe tag`
refuses it for the reason it refuses the digest. `verify` reads the scope **off the block**,
re-derives under it, and names both the scope and its exclusions on every run.

**The defect it closes.** `@sealed:` recorded a result and said nothing about its coverage,
which lived in `gen_seal`'s source and nowhere else. That is a **prior baked into the procedure
and never asked for** — radio astronomy's CLEAN-versus-MEM distinction, raised in
`RIPE-LEDGER.txt#6546` by Opus reading a transcript rather than by anyone using the tool. §4.3
is the clause; `toc`'s *"NOT shown by this index:"* line was the pattern, never generalised to
the one verb whose whole job is telling you whether to trust a block.

**And it is a §0.1 bifurcation:** one token carried both the digest *and*, invisibly, the claim
about what the digest binds.

**The durable reason, past tidiness:** a seal written today stays interpretable if the recipe
ever widens. Without a declared scope, widening `gen_seal` would make every existing seal
ambiguous — unverifiable and indistinguishable from a broken one. A block declaring a scope
this build cannot re-derive is reported as **undecided**, never as broken. Seals written by
1.4.0–1.4.1 carry no `@seals:`; they keep verifying and the assumed scope is **disclosed**, the
same discipline `genesis_of`'s fallback already had.

### The provenance cut — RULED by the sovereign, 2026-08-06

The audit re-opened the v1.3.4 ruling on `@source:`, because three of its five premises were
mint-dependent: the entropy argument (*"the real guarantee comes from genesis + ordinal"* —
both retired) and the cost argument (*"removing it would invalidate every existing mint"* — no
mints) are void. **The sunk cost that pinned the ruling in place had cleared**, so the decision
was free to be re-made on its merits for the first time since `gen_id` was written.

**What survived is the part that answered Schnee's original objection:** `@source:`'s job is to
record *a claim about origin, frozen at the moment of declaration*, and **a uniform value is
not an empty one.**

**And the question A.12 never asked.** It diagnosed an unexamined inheritance in the
*inclusion* of `@source:` and never asked the same of the *exclusions*: `@origin:` and
`@attests:` are absent from the recipe for exactly the reason `@source:` was present in it —
`gen_id` predates them. Asked properly, **the axis is not subject-matter but whether the claim
is allowed to move:**

| key | kind of claim | sealed |
|---|---|---|
| `@source:` | a **citation** — whose saying this is, fixed when made | **yes** |
| `@origin:` | a **judgement** — reworking an AI draft by hand until it is yours is a real case of it honestly changing | no |
| `@attests:` | an explicitly **current** stance | **no, necessarily** |

Sealing `@attests:` would freeze a relation whose whole nature is that it moves; coming to
stand behind something *is* thinking again, which §0.1 says should cost nothing. **The
vocabulary already held this split and nobody had pointed it at provenance:** `@source:` is the
`@defines:` of provenance, `@attests:` its `@name:`. Birth certificates seal; dictionary
entries must not.

**The deciding fact was that `@source:` takes any value at all** — `self`, `claude`, `Steiner`,
`a-dream-I-had`. Documented as a near-closed list of AI names, it looked like a
machine-checkable provenance field. It is a citation of voice, which is what seals honestly.

**NAMED LIMIT (§3.8):** `@origin:ai` → `@origin:human` is silent **even on a sealed block**.
That is the ruling, and `verify` now says so on every run rather than leaving it to be found.

### A seal is asked for, never assumed — found by a test written for something else

`push_view`'s comment claimed *"neither the retired `@mint:` nor a `@sealed:` is ever carried
across … the new one is sealed only by being sealed again."* **The code re-sealed the new block
automatically**, and had since seals existed. Comment and behaviour had disagreed in silence,
and the disagreement surfaced only because a test written for `@seals:` happened to assert the
comment.

**`amend` had already refused the same act, in so many words:** *"amending it would either
break that seal or **forge a new one in your name**. Neither is this tool's to do."* — and its
refusal message ends by pointing the reader at `push`. Two verbs, opposite answers to one
question, and the half that argued its case was the half that had thought about it.

**The sharpest objection, and why this is a §0.1 bifurcation rather than a preference: nobody
declared any of the inputs.** The body is the human's, the timestamp is the push moment, and
`@source:` is **inherited** from the superseded block. So the tool was freezing a citation
nobody made this time — the same unexamined-inheritance shape as `gen_id` carrying `source`
into the mint, one level down, and squarely against the same day's ruling that `@source:` seals
honestly *because it is a claim someone made at a moment*.

**RULED and built:** push no longer seals unless asked. `push --seal` issues one over the new
body, and discloses that the attribution came across inherited.

**But the silence was the real fault, and dropping a seal quietly would only have moved it.**
Both outcomes are announced, every time:

```
#2ea7 was SEALED; #b344 is NOT. A seal is a claim about a body, and
this is a different body — so it is yours to make, not push's to assume.
`scribe push --seal` makes it, over the new body, now.
```

**NAMED GAP, not built:** there is no way to seal an *existing* block. `--seal` lives on
`capture` and now `push`; `tag` refuses the key. So a block unsealed at birth can never be
sealed afterwards. A `scribe seal '#id' PILE` verb is the obvious shape of the answer, and is
left for a ruling — sealing a block that has sat revisable for six months freezes it **as it is
now**, not as it was declared, which may or may not be what a keeper means by the word.

Also corrected in the same pass, and missed by the audit that found the other three: `cmd_push`
printed *"the superseding block's mint falls back to the pile's PATH alone"* on any pile without
a `@genesis:` line — a stale sentence about a retired mechanism, on a path most piles never
take, which is why nobody had seen it.

### Sealing is an act, and an act has its own moment — RULED 2026-08-06

**The sovereign's argument:** *"If I am the creator of something and I reach a state with it
from work done that I want then sealed, then I must be able to do that. The moment of capture
is not necessarily the thing that must always be sealed. Declaring something can also be an
act about some worked-on thing that comes later."*

**And its mirror, brought from an inner project rather than this one:** *"We work on an inner,
then freeze it at the time of our choosing. Conversely, if you freeze it and I want to work on
it again, then I must have the chance to unfreeze it — especially if the time of its use and
implementation has not yet arrived."*

Both are right, and the asymmetry they remove was never ruled — it was **inherited**. `--seal`
lived on `capture` because capture was where seals were invented; `tag` refused the key; so a
block unsealed at birth could never be sealed at all, and one sealed at birth could be
unsealed only by hand, unspeakably. **Sealing was opt-in at exactly one instant, which is not
what opt-in means.**

**THE PHILOSOPHICAL GROUND, which is what makes these verbs necessary rather than convenient
— and which the sovereign asked for by name.**

> **A seal is the only act in scribe by which a keeper declares that something has stopped
> moving.** Everything else in the tool exists to let things move: `amend` costs nothing, a
> `@name:` can be said again, `push` appends rather than overwrites.

So sealing at the instant of capture declares a thing finished **at its birth, before any work
has been done on it** — which is §1's **premature crystallization**, arriving through the
storage layer, enacted by a flag. *That was the only sealing scribe offered.* The tool had the
suspicious case as its default and the healthy one as impossible.

**The correction is the sovereign's own saying, captured in this repo's README as its worked
`@name:` example:** *a structure cannot tell its material what to be; a person couples them.*
The seal (structure) must not tell the saying (material) that it is finished. **The person
couples them, at a moment they choose** — and that moment is a fact about the *declaring*, not
about the thing declared, which is why it is recorded and why it belongs inside the digest.

**Built:** `scribe seal '#id' PILE` and `scribe unseal '#id' PILE`. `@sealed-at:` joins the
seal's fields and enters the digest, so a seal moment cannot be backdated by the same hand
that would benefit. Scope widens to `body-ts-source-sealedat`.

**`@seals:` proved itself one day after it shipped.** The recipe widened, and *nothing already
sealed became ambiguous*: a block declaring `body-ts-source` is still re-derived under that
formula, by name, from its own face. That was the entire argument for building it, and it was
tested by events rather than by reasoning.

**Two claims the file now distinguishes, which it could not before:**

| | meaning |
|---|---|
| `@sealed-at:` == the block's own timestamp | held from the start |
| `@sealed-at:` > the block's own timestamp | *I worked on this, and THIS is the state I want held* |

**And the language that had to change with it.** `verify` may now only say **as sealed** /
**changed since it was sealed** — never *as captured*. A seal taken later cannot vouch for
what happened between declaring and sealing, and the tool does not pretend to. The code's own
constants had said this correctly since v1.3.3; the README and the `--help` text written
during this session's documentation pass had regressed to capture-relative wording, and were
corrected. **The documentation was wrong in exactly the way this session existed to fix, one
day after fixing it.**

**Unsealing marks nothing, and that is the ruling, not an omission.** No `@unsealed:`, no
counter, no trace; an unsealed block is byte-identical to one never sealed, which a test pins.
A seal is **a claim the keeper is currently making** — *I hold this as it stands* — putting it
in the same family as `@attests:`, which the same day's provenance ruling deliberately left
outside the seal because a current stance must be free to move. §0.1's test decides it: *what
does this ask of someone who has simply thought again?* **Nothing.**

**Named cost:** unseal then re-seal, and the new `@sealed-at:` is the new moment, with nothing
recording that the block was once held under an older one. A keeper wanting that history has
`push`, which keeps history, or their backups. The tool binds itself, not the human (§3.1).

### What actually did the navigating, recorded because §0.1 does not do it alone

The sovereign named the limit at the end of the session: *"Of course we won't resolve it
perfectly — that is because we are working with the machine, so not a living thing, and we
have to navigate the tension in between. For that there is no clear Charter design clause."*

**That is accurate, and it is not a defect in the Charter.** §0.1 sits in the preamble and says
of itself that it is *not a rule* — it is the stance every rule is an attempt at. Its portable
test (*what does this ask of someone who has simply thought again?*) names the direction but
rarely discriminates: the honest answer is *nothing* almost everywhere, which is why it could
not, on its own, settle any of the four decisions this release made.

**What did settle them, four times out of four, was a question that came from the tag sheet
rather than the Charter:**

> **Is this a birth certificate, or a dictionary entry?**
> A claim about a fixed past may be frozen. A stance currently held must stay free.

`@source:` is a citation — frozen. `@origin:` is a judgement and `@attests:` an avowal — free.
`push` was freezing a citation nobody made this time — stopped. A seal is a current stance, so
withdrawing it marks nothing. The distinction is `@defines:` versus `@name:`, which the
vocabulary had held since July and which nobody had pointed at provenance or at sealing.

**And where the tension genuinely did not resolve, the discipline was not to force it but to
make the tool say where the residue is.** Three are shipped and stated rather than hidden:
correcting a mistyped `@source:` on a sealed block still reports as changed; unsealing loses
the fact that a block was once held; and `@sealed-at:` cannot tell you what happened between
declaring and sealing — `verify` says so in that exact case.

**That part IS covered by a clause — §3.8, and §3.6 behind it.** There is no rule for
navigating the tension perfectly, and there is a rule for what you owe when you cannot: **name
the absence, and never let it look like its own resolution.** The imperfection is structural
because one side of it is a machine. What is not permitted is letting it be silent.

### The documentation gains a guard, and it fired on its first run

**RULED 2026-08-06.** The four interface documents make executable promises on every page and
nothing executed them. This project already knew prose cannot hold a commitment across future
edits — `test_THE_LANGUAGE_GUARD_no_fault_words_anywhere_in_the_output` guards a *wording*
ruling for exactly that reason — and the documents had no equivalent.

`TestTheDOCUMENTSAreExecutable` checks, across all five published documents, that every verb
they name exists, every flag they name exists **on the verb they name it for**, the tool's
fact-language they quote is the tool's actual fact-language, and the bench sheet's reserved-key
count matches the table it heads.

**It found a real defect immediately, in the one document this session had explicitly deferred.**
`GUIDE-scribe-with-xed.md` — the file the README sends beginners to — still carried the whole
false promise the audit began with: *"one tag is yours but is sealed: `@source:`. It is folded
into the block's identity at capture, so changing it later is a visible act."* Unconditional,
present tense, four days after sealing became opt-in. The audit had named the GUIDE as out of
scope; the guard did not care what was in scope, which is the entire argument for having one.

**And it needed calibration, which is worth recording honestly.** Two of its three first-run
failures were the test's fault, not the documents': it counted table rows past the end of the
table it meant, and it flagged *"`verify` will tell you the body is as sealed, never **as
captured**"* — a sentence doing the reader a service. The rule now counts only **backticked**
occurrences: a document *quoting* a state scribe no longer emits is making a false promise,
while one *contrasting* it in prose is explaining the change. **That is the mirror of the
output-side ruling** — there even a negation is refused, because output must not put the word
in a reader's head; here the explanation is the point.

**Named limit (§3.8):** this guard checks *mechanical* claims only. It cannot check whether a
paragraph's meaning is still true, and the silent-re-attribution defect that prompted it would
have been caught here **only via its quoted output**, never via its prose. It is a floor, not
a proof, and its docstring says so.

**172 tests** (7 new, `TestSealDeclaresItsOwnScope`). The language guard earned its keep during
the build: it rejected the phrase *"is not tampering"* in new `verify` output — a **negated**
fault word still introduces the frame, which prose could not have held and a test did.


## v1.4.1 — "legacy is what CARRIES a mint, not what lacks one" (2026-08-05)

A defect fix, found by the sovereign asking what `@mint:` was still doing in the code after
v1.4.0 retired it. **The answer was: something wrong, in three places.**

**The defect.** `cmd_duplicates` decided a block was legacy with `not block.tags.get(MINT_KEY)`
— correct while a *missing* mint meant a block predated v1.3.0. After v1.4.0 **no capture
writes a mint at all**, so the predicate silently inverted, and a pile of blocks captured today
was reported, confidently, as *"3 block(s) carry no @mint: — minted before the identity
split."* Two more instances of the same shape came with it: a pile with no `@genesis:` line was
still labelled *"(legacy pile)"* though nothing has depended on the genesis since v1.4.0, and
`push`'s ambiguity report printed `(no @mint: — a le…` where a discriminator used to be — a
truncated apology in a column.

**The class of defect, which is the part worth keeping.**

> **A predicate that was true of the past and is now true of the present.** Nothing errors,
> nothing is skipped, no test fails — and the output is backwards with total confidence. It is
> worse than a crash and worse than a stale comment, because the code still runs and still
> looks like it is checking something.

**Why the suite did not catch it.** `test_audit_reports_and_changes_nothing` asserted
`"legacy" in stdout` for a pile with no `@genesis:` line. **The test encoded the same stale
assumption the code did**, so the two agreed with each other and were both wrong. That is the
real lesson: a test written from the same understanding as the code cannot detect that the
understanding expired.

**Fixed, and pinned in BOTH directions** — a new `TestLegacyIsWhatCARRIESAMintNotWhatLacksOne`
asserts that a pile captured today is *not* called legacy **and** that a pile of minted blocks
*is*. An inversion is only catchable by a test that checks both ways round; asserting one
direction would have passed before and after.

**Also changed:** what separates two blocks sharing an id. It was their distinct `@mint:`s; it
is now the **declaring moment** — which is not a substitute for the mint, it is what the mint
was mostly made of, read straight off the header instead of through a digest.

**153 tests.**

---

## v1.4.0 — "identity stops being an integrity check, and a name can be said again" (2026-08-05)

**The largest change since v1.0.0, and the only one that removes a guarantee.** Read this
entry before the ones below it: several of them argue carefully for a design this version
retires. Those arguments are kept exactly as written — they were true when made, and a
changelog that edits its own history is the thing §5.8 exists to prevent.

### 1. `@mint:` is retired. Identity is `#id` alone.

Until now a block's identity was `sha256(genesis + ordinal + ts + source + body)` and the
handle was its checked prefix. **Every ingredient except `body` was already stated, readably,
on the same header line** — genesis is the file you are reading, ordinal is the block's
position in it, `ts` is the timestamp column, `source` is `@source:`. So the header stated the
same facts twice: once where a human could read them, and once folded into 64 characters no
human can read — and the unreadable copy was the one called *identity*. That is §3.13 (one
contract, one place) and §4.3 (readable with the tool off), in one line of one file.

**And `body` being in there fused identity with integrity.** An identity answers *which thing
is this*; an integrity check answers *is this thing as it was*. An identity must be stable
across every correction that leaves the saying intact; an integrity check must be disturbed by
exactly those corrections. §3.16's own reasoning therefore forbids the fusion, as it does for
a name and an identity. The practical consequence was that **every corrected word was an
identity event**, so fixing a typo meant growing the pile by a block or leaving the tool.

**THE EVIDENCE, GATHERED BEFORE THE CHANGE AND NOT AFTER**, because the revisit brief said it
must be. `scribe verify` across every real pile on disk — `STANDING-PROCEDURES.txt`,
`RIPE-LEDGER.txt`, `tagging-lab/WATCHES.txt`, `pn-scribe/pn_canonical.txt`:

| | blocks | as captured | **edited in place** | no mint |
|---|---|---|---|---|
| **total** | **76** | **31** | **0** | **45** |

**Zero, of seventy-six, ever** — and 45 had no mint at all, so the check had only ever applied
to 31 blocks. It cost something on every capture and every read and had never once caught
anything. That is what makes this a removal rather than a trade.

**What identity is now.** `#2644` — the right-hand digits of the timestamp printed beside it,
extended leftward until no other block in this pile holds it. Issued at capture, checked once,
never recomputed, and **derived from nothing about the content**. Its coordinates are *the pile
and the name*: `PILE#id` across piles, the pile being the namespace as a directory is for a
filename. Chosen over a random value because §3.16 sanctions exactly one way to make a short
name — truncate for filing, and *check* the abbreviation (Knuth's WEB rule; the 2026-08-01
defect was a truncation shipped **without** the check) — and because a handle that is a tail of
its own timestamp can be checked by eye with no stored digest. It is also the answer the gForth
build reached independently from the other side.

**Declared cost.** The old scheme kept two identical backdated sayings apart *by construction*
(`ordinal` cannot collapse in an append-only pile). That construction is gone and only the
**check** remains, so the `taken` set is load-bearing in a way it was not before. Pinned
through the real CLI with the timestamp pinned to the microsecond.

**Removed with it: the deletion-signature search.** Because identity contained a block's
ordinal, cutting one block from the middle made every later block re-derive wrong, so
`audit_mints` searched for a trailing run verifying at one constant offset and reported
*"K blocks removed"* instead of a wave of false alarm. That machinery was correct **and existed
only to defend the choice to put position inside identity.** Most of what this version deletes
is not the feature — it is the scaffolding the feature needed in order to stay tolerable.

### 2. `@sealed:` — integrity, alone and opt-in

`scribe capture --seal` writes a digest over the body, the declaring moment and `@source:`.
Nothing else is covered: the rest of the vocabulary is how a pile is re-interrogated as
thinking moves, and sealing it would make ordinary re-filing look like tampering.

`scribe verify` now answers *is each SEALED block still as it was sealed?* — the same
fact-language and the same no-severities ruling as before, guarded by the same test. It exits
`0` unless a sealed block changed. **Neither an unsealed block nor a legacy `@mint:` sets the
exit code**: both are permanent conditions of ordinary piles, and an alarm that always fires
defeats disclosure while satisfying it (§3.7), teaching the reader to stop reading exit codes.
Both are reported in full in the text.

**Legacy blocks are never upgraded.** A `@mint:` cannot be re-derived from what the file alone
says — it needed the pile's genesis and the block's frozen ordinal — so `verify` says exactly
that rather than reporting an absence of evidence as evidence. They stay readable and mean what
they meant.

### 3. `@name:` — a name you can say again (Forth's dictionary)

**The tension this answers**, in the sovereign's words: *"it would be corralling my living
impulses into frozen addended crystallized blocks over and over???"* Until now the only way to
record a thought said better was `push` — a new block, `@replaces:` on it, `@superseded:`
written back onto the old one, and a chain to keep in step. Say a thing five times and the pile
holds four bookkeeping writes and has become a record of your revisions rather than of what you
think.

**gforth has answered this since 1970.** Define `foo` twice: it does not refuse, does not make
you supersede anything, keeps no chain. It prints `redefined foo` in the stream you are already
reading and moves on; the old definition stays in the dictionary, unmarked and still reachable.
**What moved is not the old thing — it is what the NAME finds.**

```sh
scribe capture --name coupling-law --append pile.txt   # …and again, later, as often as you like
#   redefined coupling-law — 1 earlier definition(s) in pile.txt: #6308
#   They are UNTOUCHED and still resolve by handle; nothing was marked and nothing is owed.
scribe recall coupling-law pile.txt [--all]            # what the name finds; --all for the lineage
scribe names pile.txt [PILE...]                        # every name, and which definition is live
```

**Nothing is written onto the earlier blocks and there is no chain in the pile.** `names`
computes redefinition fresh on every call and never writes back — the contract `backlinks` has
held since v1.1.2, for the reason `tagging/TAG-KEYS-reference-v1-DRAFT.md` (A.4, after Knuth)
already gave: *back-references are derived, never hand-written.* That is what makes a
redefinition cost the keeper nothing.

**The live definition is the last one ADMITTED, not the latest-dated.** `--ts` is a supported
flag; sorting by a stated moment would let a backdated capture silently take over a name. The
pile is append-only and its order is a fact about what happened; a stated moment is a claim.

**`@name:` carries no shape discipline, and that is a ruling (2026-08-05).** `@act:`/`@path:`
have one because they are a shared *vocabulary* — they only work if they compare. A name is
yours and singular and compares with nothing, so the writer refuses only what the format cannot
survive, never what a vocabulary dislikes.

**`recall` is single-pile and stays so.** Resolving a name across piles would need a rule for
which pile wins — a global search order, which is what the pile-as-namespace model just
removed. `names` accepts several piles, which is enough to find where a name lives.

### 4. `scribe amend` — correct a body in place

```sh
echo "the quick brown fox" | scribe amend '#2644' pile.txt [--also OTHER.txt ...]
```

Nothing appended, nothing superseded, **nothing recorded** — a typo is not an event. It
**refuses** if any block points at the target, naming what points at it and where: someone
wrote that pointer *about the wording that is there now*, and that is exactly what `push`
exists for. It refuses a `@sealed:` block, which is what makes sealing mean anything. `--also`
widens the pointer check to piles you name; without it the check sees only the named pile, says
so, and names the piles it did check. Opt-in because a tool that hunted for related piles on
its own would be guessing, and a wrong guess here is a wrong *refusal* — which sends you to
`push` for a typo.

**This is not a feature added on top of the identity change. It is that change, seen from the
user's side.** It could not exist while identity contained the body.

### 5. `push` is unchanged and must not be tidied away

Sometimes the supersession *is* the saying, and you want the reader who wanders into the
outdated block to be told **in the file, with the tool off** (§4.3) — a property the gForth
build cannot have at all. **Four acts now, and choosing between them is the keeper's:**
`capture` (a new saying) · `amend` (a typo — nothing happened) · `--name` (I say this better
now) · `push` (a revision whose supersession is itself worth recording).

### 6. Charter §0.1, and where this change actually came from

The narrow, evidence-backed removal in §1 above would have shipped a tool that still charged
its keeper for having thought again. It was redirected twice by the sovereign — first to what
`@mint:` was a *symptom* of, then to the standing tension underneath — and the result is a new
preamble section, **§0.1 "The third position"**: a living impulse is continuous and said again;
a computer requires nominalization to search and relate at all; **neither extreme is available
and the job is to navigate between them.** Its third consequence is the portable test:

> **What does this ask of someone who has simply thought again? The answer should usually be
> nothing.**

And the connection that earned it: the sovereign's word for the complaint was *"crystallized"*
— which is §1's own word. **Premature crystallization** has named this project's founding
diagnosis for five years, stated against *conversation*. It enters through the *record* too,
and nobody had written that down: **the conversation dies while appearing fluent; the pile
ossifies while appearing complete.**

Full pathway, including the prior art that had been cited in `scribe.py` for four days in a
narrower role than it deserved: `FINDINGS_the-identity-rebuild-and-the-tension-it-was-hiding.md`
(development repository).

**149 tests.** Test classes repinned rather than deleted: `TestIdStability`,
`TestCaptureIssuesNominally`, `TestSealAudit`, plus new `TestAmendTheThirdDoorway` and
`TestTheMovingName`.

---

## v1.3.4 — "@source: is an attribution seal, not entropy — and it is the only sealed tag" (2026-08-02)

A named new version, not a silent edit (§5.8). **No behaviour change**: no format change, no
new verb, no flag, and every existing mint still verifies. What changed is a **justification
that was false**, a **property that was true but undeclared**, and a **guard** for both. It is
versioned rather than folded into v1.3.3 because that version is already published under its
own pinned SHA, and amending a published record in place is what §5.8 exists to prevent.

**The docstring told a falsehood.** `gen_mint` said `source` was there as *"extra entropy"*.
Measurably wrong: `@source:` is the *lowest*-entropy field in a block, near-constant across a
pile. The mint's real guarantee comes from `genesis + ordinal`, which cannot collide. `source`
was never ruled on at any gate — it was inherited from `gen_id(ts, body, source)` and carried
forward under a new name, **the same pattern as `#<id>` shipping unruled**, which is §3.16's own
worked example. The identity work fixed one unexamined default and passed this one through.

*(This file names an identity-shaped placeholder above, so it owes a kind declaration and here
it is: scribe issues **`@identity:nominal`** — a block is an utterance, and two identical
declarations are two things. Caught while writing this entry by the §3.16 guard-set's own
guard 4, on this very document. The guard was built to catch a spec introducing an unruled
placeholder; it caught the provenance record that cites one, which is the guard working, and
the honest response is to declare rather than to add an exemption.)*

**Re-justified rather than removed, because it turned out to be doing a different job well.**
Including `source` **seals the attribution**: a block's claim about which mind said it is frozen
into its identity at declaration, so a saying **cannot be silently re-attributed** — handed-in
material cannot be quietly relabelled as one's own, nor one's own as an AI's, without `verify`
reporting the block as edited in place. It was put there as entropy, fails at that, and succeeds
as a seal. Removing it now would invalidate every existing mint for a field doing real work.

**The objection that sharpens it:** as a keeper's practice matures, `@source:` may converge on
one value and lose all discriminating power — but discriminating between blocks was never its
job. **A uniform value is not an empty one:** *"in this period everything was self-sourced"* is a
true historical claim, and the more the human/machine boundary dissolves in practice, the more
worth freezing the claim made at the time.

**THE DECLARED SURFACE, which is the substantive change (§3.8).** `@source:` is **the only tag
inside the mint.** Every other tag — `@topic:`, `@act:`, `@path:`, `@aspect:`, the whole
vocabulary — is freely revisable and does not affect verification. **The tag layer is therefore
only partly revisable, and nothing in the docs said so anywhere.** Stated now in README, the xed
guide, the bench sheet and tag reference A.12, and pinned by
`test_ONLY_source_is_sealed_into_the_mint` — which also guards the seal's SCOPE: widen the mint
to cover more tags and that test fails, so the widening must be declared rather than shipped.

**Companion doc fix, raised by the sovereign reading the published README.** The canonical
pile-format example showed `@topic:` and `@source:` alone — no `@act:`, no `@path:`. Not
*retired* vocabulary (`@topic:` is rehabilitated as a legitimate index entry), but the
**dead-tag shape the project's own one-line rule forbids**: *a noun in a drawer*. The canonical
example was teaching against the discipline it exists to introduce. Fixed in all three docs.

| File | Role | SHA-256 |
|---|---|---|
| `scribe.py` | frozen core | `e9aa4313fd27a1c0f75e7718bd788f76af1a11da820b5397e765bb2833ba7137` |
| `test_scribe.py` | core tests (136) | `e5dbb51f9a5fa9fa2a40e0a2c1f041b18a2575bd9a66cd1ed76b8160a06acbbb` |

**Test attestation at v1.3.4:** 136 tests pass (135 + 1).

---

## v1.3.3 — "the pile audits itself, and says what happened rather than grading it" (2026-08-02)

A named new version, not a silent edit (§5.8). One new read-only verb, `scribe verify`.
Nothing else changed; no format change, no flag, no behaviour change to any existing verb.

**What it does.** The mint is `sha256(genesis + ordinal + ts + source + body)`, and every one
of those five inputs is recoverable **from the file itself**. So the mint can be re-derived
and compared to the stored one, which makes a pile **self-auditing at rest**. This is the
intra-pile twin of `verify-export`: that verb answers *has the pile moved under a derived
view*, using `content_fingerprint`; this one answers *is each block still the one its
`@mint:` was issued for*. Same principle, one level in.

**FACT-LANGUAGE, AND IT IS THE DESIGN, NOT THE WORDING.** v1.3.1 ruled the hand-edit a
**legitimate sovereign act** — the second doorway, chosen per act, history-in-restic instead
of history-in-the-pile (§3.1: the tool binds itself, not the human). A verb reporting that act
as `MISMATCH`, `INVALID`, `MODIFIED` or at any severity would **recast a sanctioned choice as
a defect**, and a sovereign who feels told off for using his own door stops using it. That is
the identical trap the path-sovereignty witness already solved once — *`substituted` is a
fact, never a fault* — and the tag-validator's `[HELD]` tier is the same move (Debian's
`classification`: a witness formally separate from a fault). So the three states are
`as captured`, `edited in place since capture`, `no mint — this check did not run`. **There is
no severity anywhere in this verb and there must never be one**, which is held by
`test_THE_LANGUAGE_GUARD_no_fault_words_anywhere_in_the_output` — a test guarding a *ruling*,
because prose cannot hold that line across future edits.

**THE DELETION SIGNATURE, DEMONSTRATED RATHER THAN GUESSED.** `ordinal` is a block's position
at capture, frozen. Cut a block from the middle and every later block's ordinal stops matching
its position, so a naive check reports the whole tail as changed — **a wave of alarm produced
by one ordinary act; cutting a scene from a novel would light up everything after it.** So the
audit *searches* for the shift: if a trailing run all re-derive cleanly at one constant ordinal
offset, that is not N edits, it is K blocks removed (offset > 0) or inserted (offset < 0)
earlier, and **the bodies are as captured — only their position moved.** The offset is proved,
not assumed: the tail either verifies at it or it does not.

**Exit codes carry §3.8's distinction.** `0` = every block's state was **determined**; an
edited body is an *answer*, not a fault. `2` = the check **could not run** somewhere (a block
with no `@mint:`), because a check that did not run must never be reported like one that passed.

**Two things found by running it, fixed rather than filed:**
* **The mint covers `ts` and `@source:`, not only the body** — found by a failing test. Removing
  a `@source:` tag makes a block stop matching its mint, correctly, since `@source:` is part of
  what was declared. The consequence is a wording duty: this verb must never claim to detect
  *body* changes specifically, and it no longer does.
* **Summarise the norm, enumerate the anomaly — and say which was done.** Found by running it on
  the sovereign's real `RIPE-LEDGER.txt`: 43 legacy blocks beside 5 minted ones printed 86 lines
  while calling them "the exception". An all-or-nothing rule was wrong; a *transitional* pile is
  the common case today. Now majority-legacy is summarised with its count, a minority is named
  individually, and the output states which happened.

**Named limit (§3.8):** it reports *that* a block changed, never *what* changed — no earlier
text is kept in the pile, by design, so only restic or git holds the before. A block cut from
one position and pasted at another reads as `edited in place`, which is true in the only sense
this verb can mean it.

| File | Role | SHA-256 |
|---|---|---|
| `scribe.py` | frozen core | `46615bcdd6be73891f78bbbd131e0acfc8c4cef67695182157339cd0c4a6c16a` |
| `test_scribe.py` | core tests (135) | `659385b1ac4d72fded2ba74117fbdc21f7c5dfa0b5326774fd0a1f36b0868173` |

**Test attestation at v1.3.3:** 135 tests pass (132 carried forward + 3; `TestMintAudit` is 12
tests covering the clean pile, an in-place edit, a timestamp edit, the deletion and insertion
signatures, scattered edits *not* read as a shift, the `@source:` limit, the moved-block limit,
bulk-legacy summarising, transitional piles, the individually-named anomaly, the exit-code
split, and the language guard).

---

## v1.3.2 — "a tag a human adds must land where a human reads" (2026-08-02)

A named new version, not a silent edit (§5.8). Two defects, **both found by using the tool
rather than by reading it**, and both of the same shape: a rule the project had already
stated, enacted in one place and quietly not in another.

**1. `add_tags` appended past the mint.** `@mint:` is placed last at capture, deliberately
and against a real objection (§4.6: 64 hex per header in a file whose whole virtue is being
readable in an editor) — the trade being that the human's eye meets the vocabulary first and
the hash trails off the end of the line. v1.3.1 honoured that for `push`'s status tag, via
`_insert_before_mint`. `add_tags` still used a plain `.append`, so **every tag a human added
by hand landed BEYOND the wall of hex** — precisely the tags most meant to be read. Found
live while tagging a real block in `STANDING-PROCEDURES.txt`: `@act:`, the most load-bearing
key on the bench sheet, ended up after the hash. Both writers now go through the one
placement rule. A legacy block carrying no `@mint:` still simply appends.

**2. Two guards passed without running.** `test_handle_floor_matches_the_ruled_spec` and
`test_guard4_the_guard_is_not_blind` both read `PHASE-0-RECON-AND-PROPOSAL.md` behind an
`if spec.exists():`. That file is part of the withheld development history, so **in every
published clone the suite reported a clean `OK` while two of its checks had silently not
run** — a skipped check and a passing check looking identical, which is the one thing §3.8
forbids, in the artifact that ships. They now raise `unittest.SkipTest` with the reason
named: the runner prints `OK (skipped=2)` and says which comparison did not happen and
where to run it. Debian's `classification` tier again — a witness formally separate from a
fault, and countable. Verified by running the suite against a tree containing only the
published files.

Nothing else changed: no format change, no new verb, no flag. Existing piles are untouched,
and a pile written by any earlier version parses identically.

| File | Role | SHA-256 |
|---|---|---|
| `scribe.py` | frozen core | `fd20aaa10328d999e10a13b2402c8a960d884df1248fe9322ed6a9f953139e6a` |
| `test_scribe.py` | core tests (121) | `9ba856690dc1ec5737a4cd8e42b680a5c1e77dc6e45e94fb79c7d8d71835c517` |

**Test attestation at v1.3.2:** 121 tests pass (119 carried forward + 2 new: added tags land
before the mint and keep their order; a legacy block with no mint still appends normally).
The skip fix is mutation-verified — with the spec file absent the suite reports
`OK (skipped=2)` where it previously reported a bare `OK`.

---

## v1.3.1 — "push appends and supersedes; it never overwrites" (2026-08-02)

A named new version, not a silent edit (§5.8). **Behaviour change to `push`, ruled by the
sovereign 2026-08-02** and recorded at `RIPE-LEDGER.txt#3f02`.

`push` used to assign `pb.body = vb.body`, rewriting the pile in place — which made scribe
*less append-only than it claimed*: a body could change underneath a `@ref:` written to the
old wording. It now **appends a superseding block**. The old block keeps its body and its
`@mint:` and gains exactly **one** tag, `@superseded:#new`; the new block carries
`@replaces:#old`, inherits the old block's vocabulary, and mints its own identity.

**Bodies and identities are inviolable — that is the whole rule**, asserted directly by
`test_INVIOLABLE_bodies_and_identities`. The one permitted write onto an existing block is a
status tag, which is the same act `scribe tag` already performs as a sanctioned verb, and it
is placed BEFORE `@mint:` so a tool-off reader actually meets it. Deriving the warning via
`backlinks` instead would have been purer and would have cost the tool-off-readable
invariant; between two stated invariants, **legibility was ruled to win** — the file itself
keeps telling the truth.

**The sovereignty ground, which is why this is not a restriction:** *"I can always directly
edit a block in a pile if I don't want the history that comes with push — so my sovereignty
is enhanced by the choice."* Two doorways, chosen per act: history-in-the-pile via `push`,
history-in-restic via hand-edit. **The tool binds itself; it does not bind the human**
(§3.1). gForth is the model — you may always edit the source and recompile, but the
dictionary never rewrites a definition underneath a reference already bound to it
(`ebook_gforth-manual.txt:2721`).

Also: `view --current` opts into hiding superseded blocks, and **the hiding is declared in
the view's own header**. They are never hidden by default and never removed from the pile —
a view that silently dropped them would be the undisclosed exclusion §3.8 names. Whether
`--current` should become the default is deliberately NOT decided; it belongs to the same
gate.

| File | Role | SHA-256 |
|---|---|---|
| `scribe.py` | frozen core | `d3604fa5282a8fbe52631c1548e69bb14bdd09307b1bf57c06ce8d53f22a52d6` |
| `test_scribe.py` | core tests (119) | `8419c95e2c2072296f647e5a848d9b6ce48581ca36193709138101feb91facf1` |

**Test attestation at v1.3.1:** 119 tests pass. `TestPushHome` was rewritten against the
ruled behaviour (its old tests asserted the overwrite and are gone, not disabled), plus the
inviolability assertion, the stale-view fork refusal, the status-tag-precedes-mint check, and
two view-disclosure tests.

---

## v1.3.0 — "separate the mint from the handle" (2026-08-01)

A named new version, not a silent edit (§5.8). The ONE breaking change in scribe's history,
and it is named as such: `gen_id` is gone, replaced by `gen_mint` + `gen_handle`, and every
newly captured block carries a `@mint:` tag. Existing piles are untouched and keep working —
nothing is ever re-minted, because re-minting would change ids that relational tags already
point at.

**What it fixes.** Block ids collided — within a single pile as well as across piles — and
`push` silently wrote an edit to the wrong block when they did. Root cause was a category
error, not a hash weakness: a block is a NOMINAL object (an utterance, declared at a moment)
and scribe identified it STRUCTURALLY (a hash of its content), so two identical sayings were
asserted to be one saying. No hash width could have fixed that.

| File | Role | SHA-256 |
|---|---|---|
| `scribe.py` | frozen core | `37bbeb9219a706cc1a334b9615152037311f42b74dbe8a70c292d504dc001071` |
| `test_scribe.py` | core tests (112) | `2f650ff083f7773cf87b85bd14442d0d6f0ce2ba7fc9dd01196210a9a232f867` |

**Test attestation at v1.3.0:** 112 tests pass (82 carried forward unchanged + 30 new:
9 for the mint/handle split, 7 for ambiguity refusal, 5 for nominal capture, 2 for the
duplicates audit, and 7 for the proposed §3.16 guard-set — kind-declaration lint,
signature-test-per-kind, whole-identity check, unitemised-placeholder guard. All four
guards were mutation-verified: each was made to fail by reintroducing the defect it
exists to catch.). Verified on the sovereign's real piles: `RIPE-LEDGER.txt` (43 blocks) and
`STANDING-PROCEDURES.txt` (1 block) audit clean — 0 duplicate handles, 44 blocks correctly
named legacy.

**Prior art, cited because the ruling is not scribe's invention:** gForth
(`ebook_gforth-manual.txt:2399`, `:2710`, `:2721`), Unison (`docs/data-types.markdown:7-12`,
`codebase-editor-design.markdown:23`, `:82`), restic (`data-safety/DESIGN.md:99`, `:110`,
`:129`), Sovereign Pool (`tagio.h:44`), Knuth (`Literate-Programming-Knuth.txt:827`), Debian
ledger row 29 (`LEDGER-debian-pillars.md:47`).

---

## v1.2.0 — "the other half of a trigger, a checksum for a view, a first reach at §3.15" (2026-07-31)

A named new version, not a silent edit (§5.8). Additive only; v1.1.2 below is unchanged.

| File | Role | SHA-256 |
|---|---|---|
| `scribe.py` | frozen core | `0a640fdef615508a107180f36861f4c6ec5d0e4208975f09b6050ffe2035fa25` |
| `test_scribe.py` | core tests (82) | `85c6599da6e229b0b8a9afe558ca45c41e05c109eff98c83b126d3516c84efdb` |

**What changed, and why — three builds from one session's fresh research, each answering a
gap named against real prior art rather than invented.**

1. **`scribe activate <condition> PILE [PILE...] [--key awaits]`.** Fresh research into
   dpkg's trigger mechanism (`man deb-triggers`, dpkg's `triggers.txt` spec — not a re-reading
   of this project's own prior ledger) found the one true computed-fan-out pub-sub mechanism
   in the whole Debian ecosystem: a package declares `interest` in a named trigger, any
   package `activate`s it, and dpkg computes on demand every currently-interested package —
   *"a facility that allows events caused by one package but of interest to another package
   to be recorded and aggregated, and processed later by the interested package."* This
   project already had the DECLARE half (`@awaits:`, live throughout `RIPE-LEDGER.txt`) and a
   coarse, hardcoded NOTIFY half (the SessionStart hook's `scribe view aspect:prospective`,
   one fixed value) — but no general on-demand query. `compute_activations`/`render_activate`
   close it: read-only, same discipline as `backlinks`, and it does not promote anything —
   "`@awaits` is a witness, never a promoter... the human rules every promotion, always"
   (`tagging/TAG-KEYS-reference-v1-DRAFT.md`) still holds.
2. **`scribe verify-export EXPORTED_FILE selector PILE`**, backed by `content_fingerprint`
   (a sha256-8 over sorted `(id, body)` pairs, order/joiner-independent) stamped into every
   non-bare `export`'s manifest. Closes a real hole in the "joiner method" architecture: a
   derived view (a running code file, a saved export) had no way to disclose whether the pile
   it came from had since moved underneath it. The building block was already named in this
   project's own vocabulary — Knuth's WEB change-file *"ships a checksum, not the strings"*
   (`tagging/TAG-KEYS-reference-v1-DRAFT.md`, A.1, `@quoting:`) — just never wired into
   `export`. Reports `MATCH`/`DRIFT`/`NO MANIFEST` only; never repairs, never re-exports
   (§3.10 — staleness is reported, not silently fixed).
3. **`scribe converges PILE PILE [...] [--by KEY] [--no-cites]`.** A first concrete attempt
   at Design Charter §3.15's still-open founding gap: *"a tag nothing ever queries is never
   found wrong... an absent relation cannot be searched for."* The 2026-07-30 ruling closed
   only the stateless-model-reconnecting-to-its-own-record shape of that gap (GTPS-Agent's
   `fold.py`); the shape named in the Charter's own founding example — convergence between
   separate projects that share a philosophy but were never explicitly cross-referenced by a
   pointer tag — was left open. `compute_convergences` (shared literal tag-values across 2+
   distinct piles, excluding pointer-shaped values already covered by `backlinks`) and
   `compute_citation_convergences` (shared Charter-clause-shaped citations, `§N.N` / `Clause
   N`, in body text across 2+ piles) surface these as disclosed candidates only — never
   asserted as real relations, never merged, never written back (§3.3: geometry may witness,
   never govern; §3.6: no borrowed-word semantic/ML similarity scoring — every match here is
   a literal string, not an embedding). This replaces, for the shapes it covers, the fragile
   hand-maintained "Cross-repo edges" section of `namirha-memory-matrix.md`, which worked only
   as long as a session happened to notice and write it down.

**Test attestation at v1.2.0:** 82 core tests pass (61 + 21 new: 5 for `activate`, 8 for
`converges`, 8 for `verify-export`/the fingerprint). Toolchain unchanged.

**Not yet done, named rather than silently skipped:** whether Design Charter §3.15's own text
should be amended to record this as the first answer to its founding gap is a ruling for the
sovereign, not a decision this build made unilaterally — the mechanism is built and tested;
the Charter's own wording is untouched pending that ruling.

---

## v1.1.2 — "derive the reverse" (2026-07-31)

A named new version, not a silent edit (§5.8). Additive only; v1.1.1 below is unchanged.

| File | Role | SHA-256 |
|---|---|---|
| `scribe.py` | frozen core | `e718af8f2e85901b9b2edaedae62de0cc58e360d9d72e353ee94c29da23a8f57` |
| `test_scribe.py` | core tests (61) | `00db399488aaccea9b9c0fcd4547599d23282cacdd6a4e4a29fdf71699865f10` |

**What changed, and why.** `tagging/TAG-KEYS-reference-v1-DRAFT.md` (A.4, citing Knuth's WEAVE)
already said back-references must be derived, never hand-written — but no code path in scribe
computed the reverse direction for any of its own pointer-style keys (`@ref:`, `@overrules:`,
`@superseded:`, `@yields:`, `@replaces:`, `@continues:`, `@customizes:`, `@hoisted:from-`). A
human had to already know which specific key to ask `scribe view <key>:<value>` with. Confirmed
against real prior art before building this: Foam's `packages/foam-core/src/model/graph.ts`
keeps a computed `backlinks` map (never hand-maintained), Logseq's
`deps/db/src/logseq/db/common/reference.cljs` computes `get-linked-references` the same way.
New verb: `scribe backlinks <#id | pile#id> PILE [PILE...]` — a derived, read-only reverse index
over the given pile(s), computed fresh every call, never written back. Detection is structural,
not a key allow-list (no registry, same as the rest of scribe): any tag value shaped `#id` or
`path#id` naming a real block id counts. The `path#id` form (a single whitespace-free string,
the 30-year-old URL-fragment convention) extends the mechanism to relations BETWEEN piles, not
only within one — no database, no new dependency, per the sovereignty requirement this was
built under. `compute_backlinks`/`render_backlinks` are pure functions; `cmd_backlinks` is the
CLI wrapper. 7 new tests, including a false-positive guard (a `#`-prefixed value that is not a
real block id is never mistaken for a pointer) and a genuine cross-pile round trip against two
real temp files.

**Test attestation at v1.1.2:** 61 core tests pass (54 + 7 new). Toolchain unchanged.

---

## v1.1.1 — "a code-safe join" (2026-07-29)

A named new version, not a silent edit (§5.8). Additive only; v1.1.0 below is unchanged.

| File | Role | SHA-256 |
|---|---|---|
| `scribe.py` | frozen core | `7aaf6d692306fe6506dca2ffade4fe182e75c29a5cac51a2177dc1869bb66a67` |
| `test_scribe.py` | core tests (54) | `eb11fbbf4dafc622839f019b56a7611007d6a37bcec6b55eb7de32c121781716` |

**What changed, and why.** `export`'s body-joiner (`\n\n---\n\n`) was hard-coded — fine for prose, but
a bare `---` line is a Python `SyntaxError`, so bodies meant to tangle into one runnable file (a
canonical pile carrying both prose and code blocks, each derived separately — see
`ontology-midwife/sandbox/tangle-loop-demo.txt`) had no clean path to a directly-runnable export.
Added `--joiner` (default unchanged; `\n` in the given string is interpreted as a newline, so
`--joiner '\n\n'` gives a blank-line join). Scribe still does not decide what a body IS — it only
offers the join a code export needs. `render_export` gained a `joiner=None` parameter (falls back to
the prior literal default, `DEFAULT_JOINER`); no other call site changed. Verified: default export is
byte-for-byte unchanged (regression test), a custom joiner is confirmed code-safe (compiles + runs), and
the frozen-core edit itself was never the hard part — `PROVENANCE.md`'s own v1.1.0 entry already settled
that frozen-ness is never a reason not to correct the tool.

**Test attestation at v1.1.1:** 54 core tests pass (51 + 3 new: default-joiner-unchanged, custom-joiner-
is-code-safe, empty-joiner). Toolchain unchanged from v1.1.0.

---

## v1.1.0 — "unfreeze the keys" (2026-07-28)

A named new version, not a silent edit (§5.8: preserve history; never modify a prior
version in place). The **v1.0-frozen record below is left exactly as it was** and remains
the attestation for that artifact; this section is additive.

| File | Role | SHA-256 |
|---|---|---|
| `scribe.py` | frozen core | `33de9062407a2a3d0a93dba540bd68a9c2b73974cb5d5f24c3bc872ba27c27c6` |
| `test_scribe.py` | core tests (51) | `1d18ee6a0647c875f6127de3634c46ee9dc874da34013a781428d52ac910de2a` |

The edge (`edge/*`) is **unchanged** from v1.0-frozen; its rows below still hold.

**What changed, and why the freeze was opened.** The sovereign ruled that frozen-ness was
never a reason not to correct the tool. Five welds bound the code to one tag key, and one
of them was losing material:

1. **A silent-loss path closed (§3.6).** `capture` would write a tag value containing a
   space, report success at exit 0, and the block would be absorbed into its predecessor
   on the next read — a dropped block and a short pile being indistinguishable. Reproduced
   against v1.0.0 on 2026-07-28; the reproduction is recorded in `validate_tag`'s docstring
   (§3.14). Now refused on write, announced on every read.
2. **The read/write ruling.** A read announces and continues with a non-zero exit — a pile
   with one bad line must never become unopenable (§3.1). A write-back (`tag`, `push`)
   refuses, because a rewrite would make the loss permanent.
3. **`toc --by KEY` (§3.13),** and the index now names its axis and the keys it does not
   show (§3.8). The tool no longer decides which axis is load-bearing; nor does it pick
   the "best" one (§3.3).
4. **`--tag key:value` (§3.1)** — the CLI no longer holds an opinion about which vocabulary
   is expressible.
5. **`@state:` declared retired** and announced wherever met; the undisclosed recency
   ordering welded to it is removed, and every view now states its order (§3.8).
6. **`scribe keys`** — report what the vocabulary has become.
7. **A pile carries its own reading instructions in-band** (sovereign's ruling, 2026-07-28,
   for a reason wider than this tool: piles sit on a drive an AI assistant may be asked to
   search, and an instruction living in a config can be skipped *silently* — §5.4/§3.8).
   Written only when `capture --append` CREATES a pile, or by `scribe stamp` on an existing
   one; never bolted onto a pile behind the human's back, and never re-added once deleted
   (§3.1). `--no-stamp` declines it. All comment lines in the preamble: counts, indexes and
   round trips are provably identical with and without it, and a rewrite preserves it.

**Test attestation at v1.1.0:** 51 core + 6 edge tests pass. Toolchain unchanged
(Python 3.13.5, pandoc 3.1.11.1 for the HTML path only, LMDE 7 / Debian 13, non-root).

---

# PROVENANCE — Scribe's Workbench v1.0-frozen

*Freeze record for the frozen core (§4.4: pinned, reproducible, offline-rebuildable from
the bundle alone, indefinitely). The world-facing browser edge is the explicit
non-frozen exception (§4.7) and is documented as such.*

## What is frozen

The **frozen core** is a single stdlib-only Python file plus its tests. It has **no pip
dependencies**, so "rebuild" is trivial and genuine: the file *is* the artifact; running
`python3 scribe.py` needs only a CPython interpreter. There is no build step, no network,
no package resolution — offline-rebuildable indefinitely by definition.

| File | Role | SHA-256 |
|---|---|---|
| `scribe.py` | frozen core (pile + capture + tangler) | `7923320b6306ae9ded25bf89bc6fe7cf0947591a587708c10a88e3712e4adcf3` |
| `test_scribe.py` | core tests (31) | `4f2e2373afa7bdb9d8ba76c773fb31e2a9eaa49d459afdfa08750a943b1a71e9` |
| `edge/chatgpt_adapter.py` | edge (extraction-only) | `810fa8c10c2cd139eaf26757cae5b649abe623e8b138541af7b5d17b72dcc862` |
| `edge/test_chatgpt_adapter.py` | edge tests (6) | `64723ebaefcf88fc654c7cf260d05bd5afb033085f5185032678a1ec5ef320e2` |
| `edge/fixtures/chatgpt_sample.html` | edge test fixture | `18d86423900c9b58b5016c78d33c1d9ac972ffab6d06046b6ab9b4df959d218b` |

Verify the running core at any time with `python3 scribe.py doctor` and compare its
`scribe.py sha256:` line to the table above.

## Toolchain recorded (the freeze wall — §4.7)

- **Python** 3.13.5 (CPython). The core uses only the standard library.
- **pandoc** 3.1.11.1 — the single external process, shelled to **only** on the HTML
  capture path (`capture --html`). It is *not* embedded and *not* required for any
  pile/view/tangle/tag verb or for plain-text capture. If absent, the HTML path
  **hard-fails loudly** (§3.6) — it never degrades silently. Recorded as
  `PANDOC_PINNED = "3.1.11.1"` in `scribe.py`; `doctor` flags a running pandoc that
  differs.
- **git** 2.47.3.
- Built and tested on LMDE 7 / Debian 13, kernel 6.12.94, non-root.

## Freeze / world-facing split (§4.7 — two walls kept separate)

- **Frozen (behind the moat):** `scribe.py` and everything it does — the pile format,
  capture from handed input, the loss-auditor, and the view-stripper/tangler. Nothing
  here faces the world; it processes only files the sovereign hands it. Frozen freely.
- **NOT frozen (world-facing exception):** the `edge/` adapter reads *saved* HTML the
  sovereign supplies (no live automation under ruling B), but a saved page still reflects
  a provider DOM that drifts, so the adapter is the one component that may need updating
  over time. It is quarantined; its churn never reaches the frozen core. The
  controlled-browser *transport* is not in this repo — it was preserved separately,
  outside this public release.

## Test attestation

At freeze: **31 core tests + 6 edge tests pass** (`python3 -m unittest test_scribe`;
`cd edge && python3 -m unittest test_chatgpt_adapter`). pandoc-dependent tests skip
cleanly if pandoc is absent (declared, not silent — §3.6).

## License

`AGPL-3.0-or-later` across `scribe.py`, `test_scribe.py`, and the edge (Vessel/Agent
family). Protocol/prose docs in this repo are the sovereign's under the project's
`CC-BY-NC-SA-4.0` convention.

## Genesis commit

This public release is a clean single-commit publication of the frozen artifact. The full
gated development history (Phases 0–4) lives in the sovereign's private development
repository. Accepted `v1.0-frozen`, in the manner of the `restic-plain` freeze.
