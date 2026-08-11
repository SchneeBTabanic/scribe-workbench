# The scribe shell — an optional full-screen front-end (Textual)

> **STATUS: usable, optional, and behind the command line — updated 2026-08-11.**
>
> It replaces a **NOT READY** banner that had become false. That banner said the shell was
> "a sketch to be finished, not a component to depend on"; since it was written the shell has
> been rebuilt around a single full-width tab bar, a stdin-reading verb can no longer freeze
> it, a landed push re-derives its tab, a refused push is never reported as saved, `view` on
> an open tab refreshes without overwriting unpushed edits, and text selection works. It was
> tested in earnest for the first time on 2026-08-10 and the faults that pass found are
> fixed. Leaving the old banner up would have been the same failure it warns about — a
> statement that stopped being true and kept being read.
>
> **What is still honestly true, and it is the part worth keeping:**
> * **This shell is optional and always will be.** Everything scribe does, it does from the
>   command line beside your own editor — that is the supported path, and
>   [`guide_proposed-workflow.md`](../guide_proposed-workflow.md) teaches it.
> * **It lags the tool.** Seven verbs are not forwarded (`amend`, `duplicates`, `names`,
>   `recall`, `seal`, `unseal`, `verify`), and its tests check that the verbs it forwards
>   *work*, not that it forwards *all* of them. Run those from a terminal. The real repair is
>   a completeness assertion against `scribe --help`; see the known gap below.
> * **`capture` and `check` are refused here on purpose.** They read their body from standard
>   input, which this shell cannot type into. It says so and points you at a terminal, rather
>   than writing an empty-bodied block.
> * **Nothing in it can hurt a pile.** It shells out to frozen scribe and never imports it;
>   only `push` writes, and scribe applies every one of its own refusals whoever calls it.

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
program.** What it adds is only this: several views open **at once as tabs you click
between**, re-derivable in place, and `push` from inside a tab instead of saving out first.

One tab bar spans the full width. The **first tab is the terminal** — the command log — and
each view opens beside it; the command prompt stays pinned under every tab, so you type from
whatever you are reading. Until 2026-08-08 the log and the views sat in a fixed half-and-half
split, so opening a view could only shrink everything else; that was one CSS width, not
anything about tabs.

## Run

```sh
python3 viewer/scribe_viewer.py pile.txt      # needs `textual`; scribe itself does not
```

| you type | what happens |
|---|---|
| `view topic:nas` | derives the view, opens it as an **editable** tab, discloses its `#id`s. Run again on an open tab and it **refreshes** from the pile — unless the tab has unpushed edits, which it refuses to overwrite and says so |
| `push` / `push topic:nas` | sends the active tab home by `#id` — the only thing that writes. On success the tab **re-derives**, so it carries the new block ids and can be edited and pushed again |
| `blocks`, `toc`, `export …`, `check`, `tag …`, `backlinks …`, `doctor` | passed to scribe, output in the log |
| `/help` | scribe's own command list, **derived from scribe** (see below) |
| `/close [NAME]` | closes a view tab; refuses once if it has unpushed edits, naming the loss before it can happen. The terminal tab does not close |
| `Esc` / `/hide` | back to the terminal tab. **Nothing is disposed** — every view stays open behind it |

## Three properties worth knowing

**`/help` cannot be wrong.** It is not a hand-written list — the shell runs `scribe --help`
and shows what scribe says. A hand-maintained command list would be a second copy of scribe's
surface with nothing to catch its drift (§3.13); this one is derived, so it is complete by
construction and stays complete when scribe grows a verb.

**Nothing is written until you push, and no temp file is ever made.** `scribe view` reads to
stdout and `scribe push -` reads the edited view from **stdin**, so the whole round trip —
derive, edit, push — never materialises a file. The canonical pile is the only thing on disk,
and only `push` touches it.

**Frozen scribe is never imported, only invoked.** `scribe.py` is at v1.3.4 (additive over
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
<venv>/python3 viewer/test_scribe_viewer_shell.py   # 12, Textual pilot: drives real scribe
```

The pilot proves the parts that matter: a malformed selector is **named**, never opened as an
empty tab; a pristine buffer **refuses** to push rather than rewriting the pile for nothing;
an edited buffer lands by `#id` while blocks outside the view stay untouched; and `/help`
carries the verbs listed in `_SCRIBE_VERBS`.

Since 2026-08-08 it also proves the **tab lifecycle**, which is where the shell had been
lying: two views stay open together and `Esc` disposes of neither; a landed push re-derives
its tab so `edit → push → edit → push` works; a **partly** landed push still counts as landed;
a **refused** push is not reported as saved and leaves the buffer marked edited so `/close`
still guards it; and `view` on a tab with unpushed edits refuses to refresh over them.

Whether an edit landed is decided by comparing the **pile's bytes**, never by the exit code
and never by parsing scribe's prose. That is not defensiveness — a refused push used to exit
0, and reading the code instead of the file is what let the shell declare an edit saved that
had never left the tab.

**Known gap, stated rather than left to be discovered.** That assertion checks the verbs in its
tuple are **present**, not that the tuple is **complete** — so a verb added to scribe and not to
the tuple passes silently. It keeps happening — `backlinks`; then `keys` and `stamp`; then
`duplicates` (v1.3.0) and `verify` (v1.3.3) — and the list has grown again since, which is the
gap proving its own point.

**As of scribe v1.7.0, measured rather than remembered: 22 verbs, 13 forwarded, and these 7
are not** — `amend`, `duplicates`, `names`, `recall`, `seal`, `unseal`, `verify`. (`view` and
`push` are the shell's own and are meant to be absent from that tuple.) `/help` still lists
them, because `/help` is derived from `scribe --help` and cannot be wrong — but typing them
here will not forward them. Run those from the terminal.

Any hand-written count in this paragraph is the same species of defect as the tuple it
describes. **The real repair is a completeness assertion against `scribe --help`**, which
would make both the tuple and this sentence unable to drift; it is part of what "not ready"
above means. Recompute before quoting:

```sh
python3 - <<'EOF'
import re, subprocess, sys
src = open("viewer/scribe_viewer.py").read()
fwd = set(re.search(r"_FORWARDED_VERBS = \(([^)]*)\)", src, re.S).group(1)
          .replace('"','').replace("\n"," ").replace(" ","").split(",")) - {""}
out = subprocess.run([sys.executable,"scribe.py","--help"],capture_output=True,text=True).stdout
verbs = set(re.search(r"\{([a-z,\-]+)\}", out).group(1).split(","))
print("NOT forwarded:", ", ".join(sorted(verbs - fwd - {"view","push"})))
EOF
```

**Not covered by tests, and yours to judge:** layout, blocking and key capture on a real
terminal. The agent's viewer proved why — a modal that blocked the whole screen and an input
that ate `Ctrl+W` were both TTY-only catches.
