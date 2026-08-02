# The scribe shell — an optional full-screen front-end (Textual)

> **STATUS: NOT READY. This is unfinished work, and it needs more before anyone should rely
> on it for daily use.** Everything scribe does, it does from the command line beside your own
> editor — that is the supported path, and the guide (`GUIDE-scribe-with-xed.md`) teaches it.
> This shell is an experiment sitting on top of that, and it lags the tool: it has fallen
> behind scribe's verb list at least three times (see `duplicates` below), and its own tests
> check that the verbs it forwards *work*, not that it forwards *all* of them. Treat it as a
> sketch to be finished, not a component to depend on. Nothing in it can hurt a pile — it
> shells out to scribe and only `push` writes — but it may quietly not offer you something
> scribe has.

Commands in, derived views as throwaway tabs, edits home by `#id`.

It is a **view, never a doorway** (Charter §4.3, §4.6): the pile is a file you edit in your
own editor, and this shell renders from it; kill the shell and you lose only prettiness —
your pile stays exactly where it was, readable with `cat`, editable in `xed`, and every
`scribe` verb keeps working.

## What the pipe already gives you (read this before deciding you need this)

`xed` accepts standard input as an **unsaved, untitled tab** (verified on xed 3.8.9), and
`scribe view` writes the view to stdout with its block count on stderr. So:

```sh
scribe view topic:X pile.txt 2>/dev/null | xed -
```

already gives you buffer semantics — no file is created anywhere, nothing for a filesystem
tagger to notice, nothing to clean up. **If that is all you want, you do not need this
program.** What it adds is only this: several views open side by side, re-derivable in place,
and `push` from inside a tab instead of saving out first.

## Run

```sh
python3 viewer/scribe_viewer.py pile.txt      # needs `textual`; scribe itself does not
```

| you type | what happens |
|---|---|
| `view topic:nas` | derives the view, opens it as an **editable** tab, discloses its `#id`s |
| `push` / `push topic:nas` | sends that tab home by `#id` — the only thing that writes |
| `blocks`, `toc`, `export …`, `check`, `tag …`, `backlinks …`, `doctor` | passed to scribe, output in the log |
| `/help` | scribe's own command list, **derived from scribe** (see below) |
| `/close NAME`, `/hide`, `Esc` | dispose a tab / hide the panel |

## Three properties worth knowing

**`/help` cannot be wrong.** It is not a hand-written list — the shell runs `scribe --help`
and shows what scribe says. A hand-maintained command list would be a second copy of scribe's
surface with nothing to catch its drift (§3.13); this one is derived, so it is complete by
construction and stays complete when scribe grows a verb.

**Nothing is written until you push, and no temp file is ever made.** `scribe view` reads to
stdout and `scribe push -` reads the edited view from **stdin**, so the whole round trip —
derive, edit, push — never materialises a file. The canonical pile is the only thing on disk,
and only `push` touches it.

**Frozen scribe is never imported, only invoked.** `scribe.py` is at v1.3.3 (additive over
v1.0-frozen; see `PROVENANCE.md`). This shell calls it as a subprocess, so it *cannot* change
scribe's behaviour — the freeze holds by construction rather than by promise. `viewer/` is an
unfrozen sibling of a frozen core; the freeze covers `scribe.py` and its tests, not this
directory.

**`push` from a tab appends; it does not overwrite** (scribe v1.3.1). The shell is a thin
caller, so it inherits this whole: an edited tab pushed home lands as a **new** block carrying
`@replaces:#old`, and the original gains `@superseded:#new` and keeps its body. A tab you
derived before a push is therefore stale after one — re-derive it rather than pushing twice;
scribe will skip the second push and say so, rather than forking the chain.

## Provenance — this is a descendant, not a mirror

Forked from `GTPS-Agent/viewer_core.py` and `viewer_textual.py` @ commit `4c88316`,
2026-07-26, under the GATE C ruling. **Divergence is intended:** the agent's core models a
read-only transcript of turns and personas — read-only because its statelessness guarantee
requires it — while this one models pile views as *editable* buffers with a push-home path
the agent's must never grow.

There is deliberately **no drift-guard** between them. §3.13 forbids two hand-maintained
copies of *one* truth; these are two truths with one ancestor, and a test pinning them
identical would fight the divergence and fail every time this side legitimately grew. If a
bug is ever fixed in one and bites the other, that is the encounter that would earn
extracting a genuinely shared contract — earned then, not speculated now.

## Tests

```sh
python3 viewer/test_scribe_viewer_core.py     # 8, headless: no TTY, no textual, no disk
<venv>/python3 viewer/test_scribe_viewer_shell.py   # 7, Textual pilot: drives real scribe
```

The pilot proves the parts that matter: a malformed selector is **named**, never opened as an
empty tab; a pristine buffer **refuses** to push rather than rewriting the pile for nothing;
an edited buffer lands by `#id` while blocks outside the view stay untouched; and `/help`
carries the verbs listed in `_SCRIBE_VERBS`.

**Known gap, stated rather than left to be discovered.** That assertion checks the verbs in its
tuple are **present**, not that the tuple is **complete** — so a verb added to scribe and not to
the tuple passes silently. It has happened three times (`backlinks`; then `keys` and `stamp`;
and now **`duplicates`** (v1.3.0) and **`verify`** (v1.3.3), both missing from
`_FORWARDED_VERBS` and the test tuple). `/help` still shows it, because `/help` is derived from `scribe --help` and
cannot be wrong — but typing `duplicates` in the shell will not forward it. Run it from the
terminal. The real repair is a completeness assertion against `scribe --help`, which is part of
what "not ready" above means.

**Not covered by tests, and yours to judge:** layout, blocking and key capture on a real
terminal. The agent's viewer proved why — a modal that blocked the whole screen and an input
that ate `Ctrl+W` were both TTY-only catches.
