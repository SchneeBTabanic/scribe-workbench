# Tag-Keys Reference — v1 WORKING DRAFT (2026-07-25)

> **Working by hand? Open `TAGS-bench-sheet.md` instead.** That is the doing sheet — plain language,
> the key list, the value formulas, and how to get a tag onto a block today. **This** file is the
> *why*: where each key came from, what it was tested against, and which Charter point it sits under.
> Useful later; overload now.

**Status: CANDIDATE, not settled.** These keys are drawn from this session's pod + verb-formative work.
Refine them as *you* test tagging by hand — the method is yours to lead. scribe accepts ANY `@key:value`
(no registry in the code), so this sheet — not scribe — is the discipline that keeps keys coherent.

**Check any tag as you go:** `python3 GTPS-Agent/tag_validator.py "@act:… @path:… @aspect:…"` → PASS or the
exact reasons to REPHRASE. It gates the *shape*; you own the *reaching*.

---

## THE LIVE CORE — a good tag has at least these two
| key | value shape | notes |
|---|---|---|
| `@act:` | an **open verb-phrase** — `extend-insight`, `guard-against-drift`, `protect-against-bit-rot` | the *doing*. Open/continuous verb that transforms from within; NOT a verb bolted on a noun, NOT a closed/terminating verb (`decide`,`choose`,`define`,`review`). **Validator requires it.** |
| `@path:` | `toward-X` / `away-from-Y` / `from-X-toward-Y` | the *reaching* (the anti-freeze). Must be **directional** (toward/away/from/into/over…) and **concrete** (≥2 content words). **Validator requires it.** |

**Pod's honest empty toward:** `@path:not-yet-discerned` — when you feel the block matters but don't yet know
what it reaches toward (§3.8 absence-named). A legitimate value, not a failure.

**THE NAMED EMPTIES — a closed set of two, and this block is their single source.** They differ by
**whether a search happened**, and only you can assert that; the machine can never tell them apart.
The validator routes these *before* the toward-test and reports them as **`HELD`** — a third verdict,
neither `PASS` nor `REPHRASE` (Debian's `classification` tier, LEDGER row 9: a witness formally
separate from a fault). `tag_validator.py` mirrors this list and
`tests/test_closed_class_single_source.py` fails if the two ever disagree — which is the exact drift
that went unnoticed until 2026-07-27.

```named-empties
not-yet-discerned
ruled-none
```

- `not-yet-discerned` — I feel this matters; I do not yet know what it reaches toward. **The pod.**
- `ruled-none` — I looked, and there is none. **The body must carry the search** (row 59: absence
  must be *enacted*; R5: a void with provenance is data, not a defect).

**Keep it at two.** Every member weakens the toward-test for every tag in the pile, so the set is
size-capped by a test. And pair a named empty with `@awaits:` or `@dissolves:` so it states its own
retirement condition — otherwise it is the vestigial guard (row 13) with no cure.

## ASPECT — replaces `@state` (the pod research changed this!)
| old (dead) | → new | meaning |
|---|---|---|
| `@state:live` | `@aspect:manifesting` | live / in-progress / becoming |
| `@state:settled` | `@aspect:manifested` | settled / complete / done |
| *(new)* | `@aspect:prospective` | promised / not-yet / future-facing = **THE POD** |
Closed set — exactly these three (the grammar pins them; the validator checks).

## PROVENANCE — who / which side
| key | value | notes |
|---|---|---|
| `@source:` | `self` \| `claude` \| `fable` \| `gemini` \| `grok` … | which mind said it (scribe's existing convention) |
| `@origin:` | `human` \| `ai` | the **derivation axis** — the human/ai selector for "derive the human program vs the ai program" (the single-file idea's genuinely-new key) |

## TEMPORAL — the authored-formation strata ("the second timestamp")
| key | value | notes |
|---|---|---|
| `@formed:` | a date | WHEN it came to be |
| `@amended:` | a date | a later stratum — narrated formation; what makes the block reverse-walkable |

## RELATIONAL / SALIENCE — belonging vs naming (the Unison lesson)
| key | value | notes |
|---|---|---|
| `@ref:` | `#<id>` | this block reaches to another. **Presence in the pile = belonging (unconditional); `@ref` = salience (earned).** An unreferenced block is a *pod*, never an orphan. |

## DEMOTED — pure description only, never the sole meaning
| key | value | notes |
|---|---|---|
| `@topic:` | a noun | the dangerous one. OK as *demoted description* beside `@act`/`@path`; a block with **only** `@topic` is dead (the validator flags it). |

---

## The two mechanical tests the validator runs (and one you own)
- **Strip test** — remove the verb from `@act`; if a tidy noun-bucket remains (`storage-filesystem`), it was verbish clothing → rephrase.
- **Toward test** — can you name what `@path` reaches *toward* / *away-from*? If not, it names a task, not a reaching → rephrase.
- **Yours (the validator won't decide it):** does the `@act` verb transform the whole *from within*, or is it bolted onto an intact noun? Only you can judge the reaching.

## One worked dead → alive
`@topic:knowledge-integration`  →  `@act:extend-insight @path:toward-creative-recombination @aspect:prospective`


.......................

Confirmed from the code (TAG_RE = @(?P<key>[^\s:]+):(?P<val>[^\s]+)): scribe 
  accepts any @key:value — there is no allow-list, no registry, no key 
  validation. So the honest answer to your registration question: no, new keys 
  never need registering in scribe — it'll store whatever you type. Which means
  you are the registry, and the discipline

at scribe-workbench/tagging/TAG-KEYS-reference-v1-DRAFT.md,
  keep it open beside scribe. Quick tour, and don't be intimidated — the whole
  thing reduces to two keys plus optional refinement:

  The live core is just two: @act: (the doing) + @path: (the reaching,
  toward-…). If a tag has those two, it's alive. Everything else is seasoning.

  The one thing that changed from your list (pod research did move it): your
  @state:(live/settled) → @aspect:, a closed set of three — manifesting (live),
  manifested (settled), and the new one, prospective = the pod (present,
  not-yet-connected). So @state retires into @aspect.

  What I extracted beyond your list (all grounded in this session):
  - @origin:human|ai — the derivation axis (your single-file "derive the human
  program vs the ai program" key).
  - @formed: / @amended: — the temporal strata (the "second timestamp" that
  makes a block reverse-walkable).
  - @ref:#id — the salience layer (belonging is presence-in-the-pile; @ref is
  earned reference — the Unison lesson).
  - @path:not-yet-discerned — the pod's honest empty toward, when you feel it
  matters but don't yet know where it reaches.
  - @topic: stays, but demoted — pure description only; a block with only @topic
  is dead (that's your "dangerous key," and the validator flags it).

  Your by-hand safety net: as you invent tags, run python3 
  GTPS-Agent/tag_validator.py "@act:… @path:…" — it'll PASS or tell you exactly
  why to rephrase. It checks the shape; you own the reaching. So you're not
  tagging into the dark.

  On registration: confirmed no — scribe stores any @key:value, no allow-list in
  the code. You're the registry; that sheet is it.

a candidate law is @aspect:prospective @awaits:<earning-encounter>. And
  notice @awaits: passes our own verb-path test — "awaits" is a verb, the
  earning-condition is its toward. The promotion vocabulary is already
  verb-formative; the block literally reaches toward its own ratification.
  2. @awaits and the three-citation test are the two ends of one promotion, not 
  two ideas. @awaits is the forward declaration ("here is the encounter that
  would ratify me"); the three-citation test is the backward verification at
  integration ("here are the code-need + human-principle + Charter-clause I
  earned"). Which means a candidate is a Causal-chain node with a pending edge
  (the Unison read, Trial 3): deposit opens the edge, ratification closes it
  with its three parents. So this procedure and Trial 3's lineage-graph are the
  same structure — promotion is how the Causal chain grows a node.

@awaits is a witness, never
  a promoter. It discloses whether the encounter has happened; it never
  triggers integration. The human rules every promotion, always.
And the integration event, recorded, is
  the authored-formation-stratum — so the walker can reverse-walk any law to its
  earning encounter. The Charter's laws each carry their biography.

=======================================================================

# APPENDIX A — THE MINED HARVEST (candidates, 2026-07-27)

**What this is.** Schnee asked whether the Debian study and the Knuth material hold tag ideas we
never went looking for. They do. This appendix is a **re-reading of existing deliverables with a
tagging lens** — it opened no new corpus. Sources, all local and re-checkable:
`ontology-midwife/LEDGER-debian-pillars.md` (rows), `RESIDUE-what-must-stay-human.md` (R-entries),
`references/Literate-Programming-Knuth.txt` (line numbers), `references/swa-sen.txt`
(= Perry & Wolf 1992, **not** a paper by "swa-sen"), `references/bird2011dtm.txt`.

**Nothing below is settled.** Every row is a candidate; the sheet above is still the live core.
Everything here is *seasoning on* `@act` + `@path`, never a replacement for them.

### The filter actually applied (so this list is auditable, not merely nice)

**The selection principle, stated plainly: I kept the practices that were NOT LIVING IN STRUCTURE.**
That turned out to be the through-line of the whole harvest, and it is worth naming because it is
also the definition of what a tag key *is for* — a key moves a practice out of a head, a habit, or a
paragraph of prose, and into the record's structure where the next reader meets it whether or not
anyone remembers to say so. The study is full of these, already located:

- **R3 / RESIDUE-1** — every lintian override carries its reason as a `#` comment, and **lintian
  never requires or reads it.** The grammar of the ruling is machine-enforced; the justification is
  held by the culture alone. Policy runs the *other* regime — the reason is `must` and its file is
  named. Two regimes, one practice, and only one of them is in structure. → `@because:`
- **F3** — 47% of rules carry no citation. The justification existed once, in an encounter, and
  never entered the record at all.
- **F8** — the `law → check` annotation was declared, deposited **once**, and abandoned (0.3%),
  while `check → law` lived for thirty years. A practice only becomes structure where the receiving
  organ has a live need for it.
- **F13** — `README.source` is mandated in the constitution, named in passing in the method
  document, and **absent from the tutorial entirely**. The law reached the constitution and never
  reached the doorway.
- **F18** — `dch` hard-`fatal`s on five absences, and its manpage contains no *invalid*, *reject*,
  *malformed*, *parse error* or *syntax check* — zero hits. **A guarantee that cannot be discovered
  from a tool's own documentation is a guarantee nobody will rely on.**
- **R12** — the departure procedure has five steps and **none is a knowledge-transfer step**. The
  obligation to write down what you know lives nowhere.
- And our own: `references/README.md` records that *"the obligation to populate lived in a human's
  head, not in the file"* — the pod worked **because a person remembered**, which is the one thing
  the Debian study says never to rely on.

So each key below is one such practice given a structural home. The inverse case is in here too and
must not be flattened: Knuth's *"underlining is **not** automatic; the user is supposed to mark
identifiers at their point of definition"* is a practice **correctly** left outside structure,
because no machine can know where a term was born — which is why `@defines:` is a place for the
human to declare it, not a thing to compute.

### What this list has NOT passed

Honest, because it changes how much weight these rows can bear:

- **Lens 1 (the ledger's governing question)** — applied, but *inherited* rather than re-run. The
  harvest draws only on **PILLARS** and **RESIDUE**; nothing was taken from the **ORNAMENTS** rows
  (22–24), which the study had already ruled cathedral-only.
- **Lens 6 (doorway form)** — largely pre-computed. Most LEDGER rows already carry a *"Doorway
  form"* column; several keys below are that column, keyed.
- **The Brief Lens** — applied: what is lifted is **vocabulary and shape**, never Debian's or
  Knuth's tooling. Compass, not ground.
- **The three-citation test — NOT RUN, on any row.** Each key below carries a **prior-human-principle**
  citation and nothing else. The **real-code-need** citation and the **Charter-clause** citation are
  both absent. By our own rule that makes every one of these *a preference wearing a convention's
  clothes* until it earns the other two. **They are candidates for your hand, not conventions** —
  and the way each earns its place is the ordinary one: an encounter, ruled by you.

---

## A.0 — Read this before the tables (three verified facts about our own tools)

1. **The study already answered the registry question, and we filed it under a different name.**
   Lintian's `usr/share/lintian/tags/` is **a 1,546-record tag vocabulary maintained for ~30 years** —
   the closest thing to prior art for this sheet that exists. LEDGER **row 29** is the finding:
   four tag *names* are each defined twice with **different severities**, every one carrying
   `Name-Spaced: yes`, the namespace living in `Check:`. The verdict: *no global allow-list —
   allow the collision, **declare** it, let the namespace discriminate, and let the same name carry
   different force in different contexts.* And per **F7** it was only found because a 4-record count
   discrepancy was refused rather than rounded away. That row is the single most directly applicable
   thing in the whole study and it predates this appendix.

2. **`scribe toc` groups by `@topic:` and by nothing else.** `scribe.py:494–503` calls
   `Block.topics()` (`scribe.py:68`), which filters for `k == "topic"`. So if you follow this
   sheet and demote `@topic:` out of use, **your derived TOC becomes one flat `(untagged)` list**.
   Either keep one `@topic:` per block purely as its index entry (which is exactly what Knuth's
   index is — see A.4), or widen `render_toc` to group by a key you choose. Worth deciding before
   the pile trial, not after.

   **UPDATE (v1.1.0, 2026-07-28): this row is now stale as written — `toc --by KEY` shipped,**
   widening `render_toc` to any key, `@topic:` kept only as the unwidened default. The remaining
   half of this row's question (should a SECOND key also get a hard-wired default?) was raised
   again independently in `TAGS-bench-sheet.md` and ruled **DECLINED, 2026-07-30**
   (RIPE-LEDGER.txt `#b558`): `--by <key>` already gives any key the axis at the cost of one
   flag, so a second privileged default buys ergonomics by re-introducing the registry this
   sheet exists to avoid. Left in place above rather than deleted, per this file's own §A.7
   discipline — the working-draft reasoning is part of the record, not just its conclusion.

3. **The validator cannot see hyphenated keys.** `tag_validator.py:48` is
   `@(?P<key>[a-z]+):(?P<val>\S+)` — keys are lowercase letters only. scribe's own
   `TAG_RE` (`scribe.py:54`) is `@([^\s:]+):(\S+)` and accepts anything. So `@renamed-from:x`
   parses in scribe and is **silently invisible** to the validator — no error, just absence.
   Every key proposed below is therefore **one lowercase word**, matching the existing vocabulary
   (`act path aspect source origin formed amended ref topic awaits`). Keep it that way, or widen
   that one regex deliberately.

**And one design rule that falls out of the code.** `select_blocks` (`scribe.py:455`) matches
`(key, value)` **exactly**. So keys divide in two, and it is worth knowing which you are writing:

| kind | value space | what it can do |
|---|---|---|
| **grouping key** | small **closed** set (`@aspect:`, `@because:`, `@kept:`) | makes a real view — `scribe view because:parser-wrong` |
| **witness key** | free / unique per block (`@awaits:`, `@rejected:`, `@dissolves:`) | read **in place**; can never make a view, and that is fine |

This is why row 18's four-way override taxonomy (below) matters so much: it is **closed**, so it
groups. When you invent a key, decide which kind it is *first* — that decision, not the wording,
is what determines whether it ever pays you back.

### A.0b — three more, found by BUILDING the worked examples rather than describing them

The six keys of §A.1 were written into a real five-block pile of real Namirha material and run
through `scribe blocks / view / toc` and `tag_validator.py`. Three things surfaced that no amount of
reading would have produced. **All three are ours, not Debian's or Knuth's.**

4. **A tag value containing a space silently swallows the whole block.** `@quoting:` was first
   written carrying Knuth's sentence verbatim — the obvious reading of *"quote your target"*.
   `HEADER_RE` (`scribe.py:53`) requires the tag run to be `(?: +@[^\s:]+:[^\s]+)*`, so the header
   line **failed to match as a header** and was absorbed into the **previous** block's body. Five
   blocks in, four blocks out, **no error** — the pile just quietly got shorter. So `@quoting:`
   must carry `sha256:<8>`, never the prose. **Which is what Knuth's own answer was**: the string
   pool ships a **check sum**, not the strings (`Knuth:1010–1016`). The verbatim `@x` block works
   for him because it lives in a *file*, not in a header field. Worked, verified:
   `@quoting:sha256:e44def50`.

5. **`@path:not-yet-discerned` — the sheet's OWN blessed value — is REPHRASEd by the validator.**
   Not just the new `@path:ruled-none`; both fail identically, and for the same reason:
   `_DIRECTIONAL` (`tag_validator.py:44–46`) requires a preposition from a closed class, and
   *"not-yet-discerned"* contains none. The sheet says *"A legitimate value, not a failure"*; the
   tool says `✗ names no direction — the toward-test fails.` **They disagree about a value that was
   already settled**, and the disagreement was invisible until someone ran it. This wants your
   ruling, not mine — the two honest options are to exempt a tiny closed set of named-empties in
   `_DIRECTIONAL`, or to give both empties a direction (`@path:toward-a-toward-not-yet-found`,
   `@path:away-from-a-toward-that-was-searched-for`), which is uglier but keeps the floor uniform.
6. **Repeatable keys are lossy in the validator and fine in scribe.** `validate()` builds
   `tags = {m.group("key"): m.group("val") …}` (`tag_validator.py:66`) — a **dict**, so
   `@defines:pod @defines:corpse` collapses to `corpse` and *pod silently disappears from the
   verdict line*. scribe keeps a **list of tuples** (`scribe.py:65`), so both survive the pile and
   `scribe view defines:pod` correctly returns the block. **Consequence:** every repeatable key
   proposed here — `@defines:`, `@rejected:`, `@touched:` — is checked only on its last occurrence.
   Harmless today (the validator only reads `act`/`path`/`aspect`), but it is a trap the moment the
   validator is taught to check any repeatable key.

**The method point, which is the reusable part.** Three defects in our own tooling, none of them
findable by reading, all three found by writing five real blocks and running the tools over them.
That is **F18 again** — *"reading the source rather than the manpage is what found it"* — one turn
further: reading the source found the regex; **running it** found what the regex does to a pile.

---

## A.1 — TAKE THESE SIX FIRST

| key | value shape | what it does | provenance |
|---|---|---|---|
| `@rejected:` | a path not taken (repeatable) | **The road not taken, deposited.** RESIDUE-3: `Closes:` couples a change to a *report*; **nothing in Debian couples a change to its reasoning** — the rejected paths, the judgment-material. Confirmed, not assumed. Perry & Wolf name the same absence from the other side: architecture = `{Elements, Form, **Rationale**}`, and rationale "captures the motivation for the choice" (`swa-sen.txt:382, 441–448`). **This is the axis the brief predicted we are ahead on, and the prediction held against a 30-year corpus.** | RESIDUE-3; R9; `swa-sen.txt:441–448` |
| `@overrules:` + `@because:` | `#id` · one of `misread` \| `parser-wrong` \| `ruling` \| `fix-elsewhere` | **The reasoned suppression, with a closed reason-set.** Row 18 harvested a four-way taxonomy of legitimate override reasons from six real overrides — and the fourth, *"the fault is real and the fix is elsewhere"* with a citation to where, **is the pod** (`@aspect:prospective @awaits:…`). R3 sharpens it: lintian never reads the reason (cultural), but **Policy makes it `must` and names the file it goes in** — *"The reasons … must be recorded in the file README.Debian"*. **Adopt the stricter regime.** | rows 12, 17, 18; R3 |
| `@dissolves:` | the condition that retires this block | **The mirror of `@awaits:`.** *"document your kludge so that people know to remove it once the external problems have been fixed"* (row 60), and row 13's `unused-override` — a suppression that suppresses nothing is **reported**, `Show-Always: yes`. Together: a guard that cannot announce its own obsolescence is a guard nobody can ever safely delete. `@awaits:` = what would ratify me; `@dissolves:` = what would retire me. **The lifecycle currently has a birth condition and no death condition.** | rows 13, 60 |
| `@defines:` | a term (repeatable) | **The definition site, human-declared.** Knuth: the index marks where each identifier is *defined* — and *"underlining of section numbers is **not automatic**; the user is supposed to mark identifiers at their point of definition in the WEB source file"* (`Knuth:607–610`, `@!` at `828`). A machine can count mentions; only the author knows which block is where a term was **born**. Sits exactly on the residue boundary: *the machine audits form, the human owns truth.* | `Knuth:601–617, 828`; RESIDUE "THE BOUNDARY, STATED" |
| `@quoting:` | `<sha256-8>` or a verbatim first line | **The pointer that cannot silently decay.** **F9 already ruled this** and it has been waiting for a key: Debian's upgrading-checklist keys entries to *section numbers*, which Policy itself admits *"probably no longer correspond to sections"* before 2.5.0 — a known-decaying pointer, re-pointed by hand. Knuth's change file **quotes its target verbatim** in the `@x` block, so shifting the master **breaks the build loudly** (`Knuth:1139–1149`: *"An error message is given if the m lines replaced did not match perfectly"*). Same key serves the derived-view watermark (row 61) and Knuth's string-pool check-sum (`Knuth:1010–1016`). | **F9**; rows 5, 61; `Knuth:1139–1149, 1010–1016` |
| `@path:ruled-none` | *(a value, not a new key)* | **The second honest empty.** The sheet has `@path:not-yet-discerned` = *I don't yet know the toward*. Debian has the other one: absence must be **enacted**. The template ships pre-named with its own instruction — *"<possible notes … if none, delete this file>"* — so a surviving placeholder is a **detectable defect** and *"I never got round to it"* cannot masquerade as *"there was nothing to say"* (row 59). R5 gives it teeth: a void the user made is **data with provenance**, preserved as a `must`. **Two different silences; one value each.** | rows 56, 59; R5 |

---

## A.2 — DEBIAN: the record's own strata

| key | value shape | what it does | provenance |
|---|---|---|---|
| `@reviewed:` | a Charter version or hash | **The claim only a human can make.** `Standards-Version` is a hand-asserted claim that *"I read the diff and acted on it"* — and Policy is explicit that an old value **is not a bug**, it *"just means that no-one has yet reviewed"* it. The machine may still guard what it can: date-consistency (`timewarp-`) and staleness at the **weakest** fault tier (`out-of-date-`, severity *info*). Maps to `/revises` — **asserted, never computed** — and R2 says we currently assert but do not guard. | **R2**; rows 5, 40 |
| `@relaxes:` `@tightens:` `@reverts:` | `#id` | **Force direction as a first-class entry.** The change ledger records *"relaxed from a 'must' to a 'should'"*, *"(up from a should to a must)"*, and *"**Revert** the cgi-lib change"* — with the reverted entry **still standing above it**. Strata record the *direction* of a change, not only its content. | row 38 |
| `@preserves:` | what this change leaves standing | **The anti-over-reading guard.** *"This **does not relax** the requirement that…"* — recording what a change did **not** change, to pre-empt a reader inferring more than was meant. Rare and, as far as the study found, unique to Policy. | row 38 (`upgrading-checklist.txt:102–105`) |
| `@superseded:` | `#id` of the successor | **Stale-but-labelled, at every door.** *"Avoid removing a translation completely because it is outdated. Old documentation is often better than no documentation at all"* (row 62) — and maint-guide announces its own supersession **eleven times**, once in the front matter and once at the head of **every chapter**, so a reader entering at any point is told *there* (row 76). **Direction matters:** put it on the **superseded** block. F8 measured both directions of a norm↔checker link over 30 years — `check → law` lived (20%, maintained), `law → check` died (0.3%, disclaimed) — because *only the direction with a live need in the receiving organ survives*. The reader entering the old block is the live need. **Do not build the reverse index.** | rows 62, 76; **F8** |
| `@kept:` | `pedagogy` \| `foundation` \| `evidence` \| `specimen` | **Retired but deliberately retained.** `debian/rules-old` — 43 lines, self-annotated, shipped in the real tarball, **and the auditor is silent on it at all five severity levels**, because whether it is pedagogy or rot **cannot be machine-decided** (row 25 / RESIDUE-2). **F2/F15**: this is the one narrow hole in Debian's divergence net, *"the only place in this study where reinvention is not rediscovery."* Closed set → groups in views. Covers the memory's *cast-off* (refuted, kept as foundation, never deleted). | row 25; RESIDUE-2; **F2, F15** |
| `@yields:` | `#id` | **The precedence rule declared before the conflict arrives.** The appendices are kept "for convenience, and for historical reasons", explicitly *"very likely not relevant to policy"* — with three admissions in one paragraph: consistency **not yet checked**, a **precedence rule for the contradictions it expects**, and source material **not read in detail**. Keep-and-demote rather than delete, and say in advance who wins. | row 42 |
| `@breaches:` | the convention this block violates | **A breach deposited in the record it breached.** *"This release broke the normal rule against introducing normative changes without changing the major patch level"* — **twice, 25 years apart**, visible in the numbering itself, cross-referenced from the front matter. Not corrected out of the record. | row 39 |
| `@gates:` | the act this block withholds | **A sentinel in the record gates the irreversible step.** `UNRELEASED` is a deliberately invalid distribution value honoured by three tools: *"Signing will be skipped if the distribution is UNRELEASED."* **You cannot accidentally sign what you marked incomplete.** | row 58 |
| `@forecloses:` | what retreat this ends | **The irreversibility boundary, located and named inside the procedure.** *"**This is the point of no return.** If dpkg gets this far, it won't back off past this point"* — at step 5 of 13, with a second boundary named later and its bad state named (*"half-removed limbo"*). R7 gives the n=1 form: *"creates an obligation … **in perpetuity**"* — some deposits cannot be withdrawn, and that fact is what warrants deliberation before depositing. | rows 31, 34; R7 |
| `@enables:` | a verb-phrase the reader must be able to perform | **The handover file as a list of acts, not a description of state.** `README.source` must make **four verbs performable** by someone without the author's tacit knowledge, and *"should not assume familiarity with any specific … tools"* (row 46). Row 49 states the principle: a field's value is *"defined by the act it is meant to enable in someone else, not by what is factually true"* — **the purest verb-path field in the whole document.** And **R12**: Debian's retirement procedure has **no knowledge-transfer step at all** — this is the gap we are building into. | rows 46, 49; **R12, F13** |
| `@defers:` | whose judgment this belongs to | **A zone you must not enter even though you can.** *"never edit the translations in any way (**even to reformat the layout**) … what you consider an error can be right (or even needed) in the given language."* Not locked — someone else's competence. | **R10**; R5 |
| `@attests:` | who vouches (≠ who authored) | **Authorship and attestation are two fields of one object.** The `Maintainer` field names the sponsee (who authored); the OpenPGP signature names the sponsor (who vouched) — *"even if you're not the maintainer, as a sponsor you are still **responsible** for what you upload"* (row 63). Years later the signature is *"the fallback index into lost knowledge"* (row 67). **Direct consequence for `@origin:human\|ai`:** it currently fuses two facts. `@origin:ai @attests:self` says something `@origin:` alone cannot — *the AI authored it, the human is answerable for it.* | rows 63, 67 |
| `@captured:` | where this text was actually got, and when | **Three provenance claims, not one `@source:`.** Location (`debian/watch`, mutable, network-derived) · authority (`upstream/signing-key.asc`, local, never fetched, verified out-of-band) · **and "where I got my copy", which is historical, not live** (`debian/copyright`, row 78). `@source:` today carries only *which mind said it*. | rows 8, 55, 78 |
| `@watches:` | a path or URI | **Declare where the external original lives, then a tool — not vigilance — watches it.** **With F17's limit stated on the sheet:** uscan compares **version strings, not bytes** — searched `sha256\|sha1\|md5\|mtime`, **no content digest anywhere** — so silent in-place republication is invisible to it. A solo keeper who needs *"these bytes drifted"* must pair this with `@quoting:<sha>`. | row 7; **F17** |
| `@renames:` | the retired key or id | **The vocabulary keeps its own append-only name history.** 194 lintian definitions carry `Renamed-From`; overrides using retired names are **auto-translated *and* reported** (`renamed-tag`, pedantic) rather than silently accepted, and an override naming a rule that does not exist is a hard **error** (`alien-tag` — a suppression cannot point into the void). Policy does the same at constitutional level: retired field names are *kept, marked and dated* rather than deleted (row 48). **First use is this sheet's own `@state:` → `@aspect:` retirement, which happened with no record of the rename.** | rows 15, 16, 48 |

---

## A.3 — PERRY & WOLF: what erosion actually is

| key | value shape | what it does | provenance |
|---|---|---|---|
| `@carries:` | what would fall without this block | **Load-bearing vs decoration, declared.** *"**Separate aesthetics from engineering** — that is, indicate what is 'load-bearing' from what is 'decoration'. **This separation enables us to avoid the kinds of changes that result in architectural erosion**"* (`swa-sen.txt:341–344`). This is the LEDGER's own pillar/ornament question given a home **in the record itself** rather than in a one-off study. Their two named diseases are worth having in the vocabulary: **erosion** = *violations* of the architecture; **drift** = *insensitivity* to it — and drift is the one that *"makes it much easier to violate the architecture that has now become more obscured"* (`298–305`). | `swa-sen.txt:298–305, 341–344, 382, 441–448` |

**And a value-shape rule, from two corpora agreeing.** Perry & Wolf ask for a *"principle of least
constraint … express only those constraints that are necessary"* (`329–332`); lintian's
`mismatched-override` carries the identical maxim — *"overrides work best when you require **as
little context as needed**"* (row 14). **Make every value as narrow as necessary and no narrower.**
Over-specified values go stale and start silently mis-matching; that failure is reported in Debian,
and would be silent in ours.

---

## A.4 — KNUTH: WEB, read as a tagging system

**First, the honest one.** Knuth states our thesis, in 1984, and then diverges from it:

> *"I usually **start the name of a section with an imperative verb**, but I give a declarative
> commentary at the beginning of a section. Thus, PRIMES.WEB says '8. Now that appropriate …
> ⟨Print table p 8⟩ ≡ …'; **I wouldn't do the opposite** and say '8. Print the table.
> ⟨Code for printing 8⟩ ≡ …'."* — `Knuth:1313–1317`

That is verb-first naming as a deliberate discipline, forty years early, and it is a real
prior-human-principle citation for `@act:`. **But his verbs are closed and terminating** — *Print
table p*, *Increase j until…* — precisely the class this sheet rules out (`decide`, `choose`,
`define`, `review`). So Knuth corroborates *verb-first* and **not** *open-verb*. Cite him for the
former; the latter is still ours to earn. Two further rules of his transfer intact: a section name
*"should be long enough to encapsulate the essential characteristics … but not too verbose"*, and
it *"should explicitly mention any nonstandard control structures, even though its data structures
can often be left implied"* (`1318–1331`) — **name what would surprise the reader; leave the
expected implied.** That is a usable test for how much to put in a value.

| key | value shape | what it does | provenance |
|---|---|---|---|
| `@continues:` | the name of the whole this block extends | **`+≡` — WEB's append operator.** A section reusing an earlier name *appends* to it: `⟨Variables of the program 4⟩ +≡`, and the whole is the concatenation across §§4, 7, 12, 15, 17, 23, 24. *"The expanded meaning … consists of **all** the program texts for this name, not just the text found in §4"* (`Knuth:278–281, 352–355`). **scribe already has this and we have not been calling it that:** `select_blocks(key, value)` (`scribe.py:455`) makes every repeated `@key:value` a WEB named-section, and `render_view` tangles it. Which means **a view is a tangle**, and the question "what should a key be?" is really "what wholes do I want tangled?" | `Knuth:278–281, 352–355`; `scribe.py:455, 480` |
| `@reads:` | `after-#id` | **The expository order, distinct from every other order.** *"A program is best thought of as a **web** instead of a tree … the programmer's task is to state those parts and those relationships, **in whatever order is best for human comprehension** — not in some rigidly determined order like top-down or bottom-up"*; WEB lets you write in *"stream of consciousness"* order and TANGLE scrambles it into what the compiler demands (`Knuth:1203–1247`). scribe offers arrival order and recency order (`order_blocks`, `scribe.py:472`) — **neither is expository.** For a pile of 131 memories that is a real missing axis, and the value carries its own direction. | `Knuth:1193–1247` |
| `@replaces:` | `#id` (pair with `@quoting:`) | **The change file: adapt without touching the master.** *"you **never actually change the master file** TANGLE.WEB"* — changes live in a separate `.CH` file, and the scheme works *"when the WEB file is constant and the CH file is modified, **and** when the CH file is constant but the WEB file is modified"* (`Knuth:1131–1178`). Directly on ontology-midwife's **mutate-nothing-at-source** guardrail and the read-only-derived split. | `Knuth:1131–1178` |
| `@customizes:` | `#id` + the context | The same shape at n=1: a local adaptation declared as an adaptation. *"The system-dependent changes do not affect any of the subtle parts"* — and note the honesty about what it costs: TANGLE has ~190 sections and a typical installation changes ~15. | `Knuth:1157–1178` |
| `@refuses:` | the capability deliberately not taken | **Occam's razor as a recorded act.** Knuth's §H exists solely to list *"several things that were **intentionally left out** of WEB"* — no conditional macros, no Boolean evaluation in TANGLE, at most one macro parameter — each with its reason and its workaround (`Knuth:1027–1079`). Debian does the identical thing in a *declaration format*: uscan's mangle rules name the closed operator set and then name the escape they refuse — *"**Code execution is not allowed** (i.e. no `(?{})` or `(??{})` constructs)"* — with `e` simply absent from the flag list (row 52). Row 53 adds the ordering: *"This is very powerful … **If other mangling rules can be used to address your objective, do not use this rule.**"* **Two independent corpora, same shape: name the door you closed, or a reader will assume you never saw it.** | `Knuth:1027–1079`; rows 52, 53 |
| `@hoisted:` | `from-#id` | **The size-distortion insight, and it is subtle.** A programmer writing inline error-recovery *"subconsciously tries to get by with the fewest possible lines"*, because a long recovery would make the routine **look** like it is about errors — *"the programmer knows that the error is really an exceptional case … therefore a lengthy error recovery doesn't look right, and most programmers will minimize it (**without realizing that they are doing so**)."* Naming it separately means *"the whole point of that section is to do the best error recovery, and it becomes quite natural to write a better program as a result"* (`Knuth:1260–1293`). **A concern given its own block can grow to its own size without distorting its parent** — the argument for splitting a block that has nothing to do with tidiness. | `Knuth:1260–1293` |

**Two Knuth notes that are not keys.**

- **`@topic:` is rehabilitated as an index entry — and only as that.** WEB's index carries far more
  than identifiers: *"Bertrand, Joseph, postulate: 21"*, *"output format: 5, 9"*, *"prime number,
  definition of: 13"* — *"Special instructions … can be used to insert essentially **anything**
  into the index"* (`Knuth:611–617`). So a topic word is a legitimate **index entry**; what this
  sheet rules dead is a topic word standing in for the block's **meaning**. Both hold at once, and
  §A.0(2) means you probably need one per block anyway for `scribe toc`.
- **Back-references are derived, never hand-written.** WEAVE computes *"This code is used in
  section N"* and *"See also sections 7, 12, …"* in both directions from one declaration
  (`Knuth:242, 285`). Ours is **F6**, learned the hard way: *"A one-directional reference search
  manufactures false orphans"* — the `rules-old` grep asked only who points *at* the file and
  condemned one that pointed at its own successor. **Write `@ref:` once, in the direction with the
  live need (F8), and derive the reverse — never maintain both by hand.**

---

## A.5 — BIRD 2011: the one honest thing it offers a tag sheet

`bird2011dtm.txt` is an ownership/defect study, and most of it is org-scale. One finding transfers:
a **minor contributor** is defined as someone with **under 5% of the commits** to a component
(`:251–266`), and *"the number of minor contributors has a strong positive relationship with both
pre- and post-release failures"* (`:660`) — a stronger signal than the top owner's share.

Candidate, offered weakly: **`@touched:`** (repeatable) beside `@source:`, so a block records the
minds that passed through lightly, not only the one that owns it. The reason to want it here is
narrow and specific: in a mixed human/AI pile, `@origin:human|ai` is a **binary on a block that
several minds may have shaped**, and Bird's result says the *lightly-touched* ones are where trouble
concentrates. Treat it as a hypothesis to test on a real pile, not a finding — the study is about
Windows binaries and n=1 is not its setting.

---

## A.6 — What did NOT survive the reading (recorded so the absence is deliberate, §3.8)

- **`@show-always:`** — row 11 is superb (7 of 1,546 rules are unsuppressible, and **6 of the 7 audit
  the overrides themselves**), but it is a property of a *checker's* rule registry, not of a block.
  It belongs in the pile-checker spec, where SPEC-SEED note 1 already puts it: *build the audit of
  your own suppressions **before** the second check exists.*
- **`@rests:<until-date>`** (row 66, the DELAYED queue — *"review intensity as a duration, not a
  roster"*) — real and elegant, but it prices a **third party's** opportunity to object. At n=1 the
  third party is your later self, and R11's two-clock structure is probably the better form if this
  is ever wanted. Held.
- **A `@cites:`-style required-justification key** — refused on evidence. **F3**: 720 of 1,546
  lintian rules (**47%**, including 239 uncited *errors*) carry no citation, and **Debian left the
  field empty rather than back-fill a fake justification.** An empty citation is honest; a
  manufactured one is worse than nothing. If we add such a key it must be optional by design.
- **A law→check index** — **F8**, explicitly: *"do not build the law→check index. It will rot."*

---

## A.7 — The method caution this appendix owes you

The Debian study logged **three** ways its own reading went wrong, and all three are live hazards
for a tag sheet built by hand:

- **F13** — two reader-agents independently concluded Debian never instructs anyone to *write* a
  `README.source`. Both were wrong, in the same direction; Policy §4.14 mandates it. *"Two
  independent agents converging on a claim is **correlated error, not corroboration**"* — they read
  two documents and neither read the third.
- **F19** — a `grep -c` for an eleven-times-repeated phrase returned **0**, because the phrase is
  hard-wrapped and never exists on one line. *"In a hard-wrapped plain-text corpus, phrase-absence
  is not established by a line-oriented grep."*
- **F6** — the one-directional reference search that manufactured a false orphan.

Applied here: **every citation above is a pointer into a document, not a quotation I re-verified
against the original corpus this session.** The LEDGER and RESIDUE rows were verified verbatim when
written; the Knuth and Perry & Wolf line numbers are from this session's reading of the local files.
If a row is about to earn a place in the settled sheet, re-read its source first — that is the
three-citation test's own discipline, and this appendix is at most one citation of the three.

---

## A.8 — Found already in use, not mined: fed back per `vocabulary_coverage.py`'s own finding (2026-07-29)

**Not from Debian, Knuth, Perry & Wolf, or Bird.** `ontology-midwife/tagging-lab/vocabulary_coverage.py`
cross-references this sheet against actual pile usage — the reverse direction from A.1–A.5, checking
what a session already DOES rather than what a study SAYS. First run found two keys live in real piles
and absent here: exactly the F8 shape (§A.0), caught early instead of after thirty years.

| key | value shape | what it does | provenance |
|---|---|---|---|
| `@verified:` | a short slug describing what confirmed the claim | **The evidentiary note attached when an `@aspect:prospective` closes.** Live in `RIPE-LEDGER.txt` on 7 of 9 blocks before this entry existed (e.g. `@verified:merged-to-main-ff-only-7a48325-unpushed`, `@verified:prediction-held-branch-closed`) — coined in practice, never fed back. **Overlaps `@dissolves:` in spirit** (both are about a prospective item's ending) but differs in shape: `@dissolves:` is a *pre-declared condition* set when the block opens ("this is what would retire me"); `@verified:` is *evidence attached after the fact* ("this is what actually did"). Worth deciding whether they should be one key or stay two — a real open question, not resolved here. | found in use, `RIPE-LEDGER.txt`, 2026-07-29 |
| `@part:` | a short slug naming which derived artifact this block belongs to | **The tangle-loop's own grouping key.** Live in `ontology-midwife/sandbox/tangle-loop-demo.txt` (`@part:guide`, `@part:reader-logic`) — one canonical pile, two audiences, each derived separately via `scribe export part:X --bare`. A **grouping key** in A.0's own taxonomy (closed-ish set, makes a real view), same family as `@aspect:`. | found in use, `tangle-loop-demo.txt`, 2026-07-29 |

**Neither is ratified.** Both are recorded because they are already real, not because they are decided —
same footing as Appendix A: candidates for your hand. The three-citation test has not been run on
either row.

## A.9 — Found missing, then built: `scribe backlinks`, the reverse-lookup capability (2026-07-31)

**The inverse of A.8.** Schnee's question, after reading `scribe-workbench/support-ref`'s Gemini/
Obsidian write-up: are the pointer-style keys already on this sheet (`@ref:`, `@overrules:`,
`@superseded:`, `@yields:`, `@replaces:`, `@continues:`, `@customizes:`, `@hoisted:from-`) short on
*relational power*? Checked the actual cloned repos, not the summary: Foam
(`packages/foam-core/src/model/graph.ts`) and Logseq (`deps/db/src/logseq/db/common/reference.cljs`)
both confirm the exact principle A.4 already states from Knuth — *"back-references are derived,
never hand-written"* — but this sheet had never had that principle actually built into `scribe.py`.
None of these keys had a reverse query: `scribe view overrules:c98b` finds the OVERRULING block, but
nothing found every block that named `c98b` under ANY of these keys at once — a human had to
already know which specific key to ask.

**RATIFIED AND SHIPPED, v1.1.2.** `scribe backlinks <#id | pile#id> PILE [PILE...]` computes this:
one pass over `parse_pile()`'s own blocks, matching any tag value shaped `#id` (or, for relations
BETWEEN piles, `path#id` — the URL-fragment convention, still one whitespace-free string, no new
dependency, per Schnee's explicit data-sovereignty instruction: no database, ever) against real
block ids, building the reverse map fresh every call — same shape as Foam's `backlinks` map and
Logseq's `get-linked-references`, never written back into the pile. Tested live against
`RIPE-LEDGER.txt` (real `@corrects:`/`@resolves:`/`@reconfirms:` tags) and a genuine cross-pile
case (`STANDING-PROCEDURES.txt#g1tp` → `RIPE-LEDGER.txt#4d2e`) before shipping, and pinned by 7
tests in `test_scribe.py::TestBacklinks` — including a false-positive guard (a `#`-prefixed value
that is not a real block id is never mistaken for a pointer) and a real cross-pile round trip.
Kanboard's typed-bidirectional-relation-PAIRS (a `links` table with a label/opposite-label pair)
were checked and are NOT adopted: they need a registry, which this sheet's whole discipline
(§A.0's "none of this is hard-wired") refuses; this project's existing per-key typing (the key
itself names the relation) already gets the same benefit without one. Full writeup:
`RIPE-LEDGER.txt` `#a4c1`; provenance: `PROVENANCE.md` v1.1.2.

