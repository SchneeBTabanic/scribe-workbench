# PROVENANCE — Scribe's Workbench

## v1.3.4 — "@source: is an attribution seal, not entropy — and it is the only sealed tag" (2026-08-02) — CURRENT

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

## v1.3.3 — "the pile audits itself, and says what happened rather than grading it" (2026-08-02) — CURRENT

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

## v1.3.2 — "a tag a human adds must land where a human reads" (2026-08-02) — CURRENT

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
