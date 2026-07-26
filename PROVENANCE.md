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
