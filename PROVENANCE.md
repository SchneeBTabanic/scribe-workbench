# PROVENANCE — Scribe's Workbench

## v1.1.2 — "derive the reverse" (2026-07-31) — CURRENT

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
