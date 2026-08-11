
me>make this documentation exploitable by scribe - meaning, tag the sections and capture this document.  So - first write out, then walk back and see what can be made into blocks.  This document should be an example of what it recommends. 

.txt vs .md
Scribe and the viewer do not care about the extension. Both would work. .txt is simply the conventional choice.

# Proposed Workflow:

a) A bash command terminal to get things up and running.
b) A simple text editor
c) A Viewer that works with scribe. 
d) Recommended Practice
e) Tag Hygiene

...

a+)
At your terminal prompt, cd to the target directory (mine as an example): 

schnee@HP:/mnt/data/ProjectNamirha_git/scribe-workbench/viewer$

Start a venv environment (mine as eg):

source ~/vessel-env/bin/activate

my output:
(vessel-env) schnee@HP:/mnt/data/ProjectNamirha_git/scribe-workbench/viewer$

Verify that 'Textual' has been installed in this environment, type:
python3 -c "import textual; print(textual.__version__)"

Confirm the core (scribe) is visible from where you are:
ls -l ../scribe.py

My output for the above two commands:
(vessel-env) schnee@HP:/mnt/data/ProjectNamirha_git/scribe-workbench/viewer$ python3 -c "import textual; print(textual.__version__)"
8.2.8
(vessel-env) schnee@HP:/mnt/data/ProjectNamirha_git/scribe-workbench/viewer$ ls -l ../scribe.py
-rw-rw-r-- 1 schnee schnee 182855 Aug  9 07:01 ../scribe.py
(vessel-env) schnee@HP:/mnt/data/ProjectNamirha_git/scribe-workbench/viewer$ 


The venv environment is only for the viewer because it pulls in textual (a full TUI framework), scribe does not need the viewer or the venv environment because core scribe.py is pure standard library.

ref# block #<id> another_pile.txt for how to setup venv and install textual in it - if textual not installed in venv then install it:
pip install textual
Pip should not be used without venv.

...

c+) 
Starting the viewer requires a pile file as its argument:

python3 scribe_viewer.py /path/to/your/pile.txt

You only need to give the viewer a correct path to the file. It does not have to live inside the viewer/ directory.
How it works:
The viewer receives the path you pass on the command line.
It then shells out to scribe.py (which it finds relative to its own location) and hands that same path to every scribe command.
It does not make a copy of the pile. It works directly with the file you pointed at.
Therefore every command (view, push, blocks, etc.) operates on the real file, wherever it sits on disk.
The viewer needs a filename argument to start, but it does not itself save or create the file.  The shell simply stored that path string and opened. Nothing was written to disk. The first time a real file appears is when a scribe command that writes is run from the viewer.

No tab appears for an empty / new file
This is by design, even if it feels odd at first.
The right-hand tabs are only for derived views that you request with a command such as:textview topic:something

c+_extra-info)
The viewer is a gentler more recognizable way in to familiarizing oneself with scribe as the terminal experience can feel like it isn't dedicated to what you're doing.  So the viewer helps with orientation; enabling new users to benefit from a more dedicated interactive envirnoment.  Scribe does not need it.

The viewer never imports scribe.py.  The viewer always shells out to scribe as a subprocess.

The viewer calculates the location of scribe.py and will find the core (scribe) correctly as long as the directory structure is intact (scribe-workbench/scribe.py and scribe-workbench/viewer/scribe_viewer.py).

Textual was chosen as the code-base for the viewer.  It is a popular open-source Rapid Application Development framework for Python designed to build interactive Text User Interfaces (TUIs) inside terminal windows.  It is open source released under the MIT license: github.com/Textualize/textual](https://github.com/Textualize/textual


...

d)
Single steps that can be done all at once, but let's go through them separately at first:

1. Birth Certificate, stamp your pile.txt first (this can be done later - genesis is when you want to activate it and not necessarily when the file is first saved - sovereign feature):

scribe stamp pile.txt

If you do this again later by mistake, scribe will not 'stamp' again (what is the stderr??? report then, or is there none?)

This adds a short pre-amble with comment tags (called the header) at the top of your file.  It also incl. @genesis:<64-hex> (genesis hash is minted from the current time + absolute path - ??? absolute path ???, does this influence referencing other piles in relational ways ... or did we not think of using that - because an identity should never be determined by its location (is that in the charter?) ... does it break something if the pile is moved to another location ... how does it generate numbers from path?)

2. You now want to write something.  Give it the basics using scribe i.e., a timestamp, and an id number (derived from the longer timestamp for easier reference); this the scribe command 'capture --append) does on its own ... however there is one tag that is required (if you omit source, scribe puts it in but records it as @source:unknown .... but i will change that code so that if no source is recorded then instead of 'unknown' it will be @source:not-yet-declared.   Otherwise, if you will be the source of the text in the block then write @source:self otherwise put whoever will be the source - this can be changed later ... (although sealing requires care: I will leave 'sealing' out for the moment - for ordinary unsealed blocks, omitting --source is perfectly fine).  The following command works for both first block of a new pile and later blocks.

The source value is not part of identity generation at all. It only becomes relevant if you later seal the block (the seal covers body + certain header claims, including @source:).
So for ordinary unsealed blocks, omitting --source is perfectly fine.

scribe capture --append pile.txt --source self

Whenever you use 'capture' with scribe, you will notice that after typing the command, the cursor will stay blinking until you press ctrl-d because the capture command process is waiting for you to type the body of your block on stdin (standard intput channel).  This allows you to type something into the block's body - but it is not a nice way to write as there are not editor features, meaning you can't use arrow keys and you need to press 'return' before you press ctrl-d.  Sure, it is nice to have as a quick option to enter something immediately and fast into the body of a block - but I like to use the editor if I am typing something substantial.  So you can press crtl-d to end the waiting process, or, in the original command you can force an empty body so stdin does not wait for an interactive input, you have to give it empty stdin. 
You can prefix the scribe command with either:
 echo -n | 
or
 printf '' |

But I prefer to affix </dev/null at the end.

So ... after that, this is what appears in your pile.txt:

@@ #<id-from-timestamp> 2026-08-10T… @source:self

Either you then begin to type the body under this line and/or you add more tags along the line (don't press return between tags!)

And, if you did not stamp your pile.txt yet, this command will also do that unless you opt out by using the command because you don't want the preamble (however I recommend it because @genesis is generated which identifies your whole pile with something other than the pile file name - and as of writing this, we might use genesis hash for referencing between piles where there is some relation):

scribe capture --append pile.txt --source self --no-stamp


If you want to automate things all together:

echo "Put here the first phrase or word or sentence of the block." | \
  scribe capture --append pile.txt \
                 --source self \
                 --tag topic:scribe-workflow-proposal

Output in your file:

@@ #<id-from-timestamp> 2026-08-10T… @source:self @topic:scribe-workflow-proposal @act:clarify-birth-of-pile
This is the first saying in this pile.

Important formatting considerations:  

No spaces inside a tag value@topic:my topic is illegal. Use @topic:my-topicNo spaces or : inside a tag key@my key:value or @my:key:value will not parseNo empty value@source: (nothing after the colon) is refused

Tags must sit on the same line as the @@  
A tag on its own line is treated as body text.  This means you must not press return while tagging in the sigil line ... only press return once you are finished.  If you want to return, and add more tags, then do so.  

(Isn't there a tag validator that runs that stops you from making any of the above format mistakes except the last?)

But you have a tool to help:
At capture time at the command line, if you type a space where there shouldn't be one:
"topic:my topic"
Then validate_tag checks and there is a Hard refusal (TagRefused) + clear message on stderr (standard error), and nothing is written to your pile.txt.

However if you are not using the command line to edit your pile.txt and maybe editing it directly in your text editor, then if you do the same:
"topic:my topic"
Nothing automatic will stop this being written nor saved.
However you have recourse to run a command yourself (scribe blocks, scribe doctor, etc.). The malformed headers will be announced on read the pile.txt You will then have to make a note and change it yourself.


Moment,What is checked,How it reports,Can it stop you?
At capture time (tags given on the command line),Full validate_tag,Hard refusal (TagRefused) + clear message on stderr. Nothing is written.,Yes – it stops the write
After the block is already in the file (hand-editing in xed),Nothing automatic,"You must run a command yourself (scribe blocks, scribe doctor, etc.). Malformed headers are announced on read but the tool continues.",No – it does not stop you


................................................

 Use a simple text editor to edit files as usual but with a twist, and also run commands on that file from the terminal using scribe (see below for why and how).

## One-time setup 

Scribe is a single python file in whichever directory you cloned it into. To use it from the command line in your terminal, it is easiest if you first install it on your PATH.

If not, whichever directory you are in in bash, you will need to write the full path to scribe every time to use the command. (maybe even then it doesn't work ... right? .. something about 'bin')

**1. Give it a short name.** Add this to the end of `~/.bashrc` (explain what .bashrc is and why it has a dot infront and how to view it with ls):

```bash
alias scribe='python3 /mnt/data/ProjectNamirha_git/scribe-workbench/scribe.py'
```

Change the path (confusing ... you mean in your terminal? .. so change directory to ... so cd?)to wherever your copy of `scribe.py` actually lives. Then `source ~/.bashrc` (explain what this command does that the alias command didn't do already ... it is all very confusing for non linux command geeks).
(or open a new terminal). Now you type `scribe`, not the long path.

**2. Give the pile (people don't understand this word: The reason why your text file might be referred to as a 'pile' by scribe, is because even though it exits as the only one keeping its data ... as you write to and edit your text file recording your live stream of thoughts and ideas, it might start to resemble a disorganized unstructured linear (???) - and thus a pile of text heaped on top of other text.  However what the pile has written in it are plain text tags that can be used to derive a hidden structure even though not visible in the pile itself.  

Scribe developed out of the realization that a simple text editor - although giving you the maximum soveriegnty over your data with the least dependencies - does not provide any solutions in and of itself to delivering a structured organized view.  Traditionally such views might be implemented inside the file by using embedded formats which then have related dependencies.  Markdown might be the closest to providing some solution but misses others (confirm how this is).  As you work and the text file gets bigger - you begin to lose the overview of what you have done and where.  That's when you start to get even sloppier as there is not method to use to organize your simple text file.   Your important ideas that could have be used more effectively to do or create something, start to lose something as your file becomes more chaotic - because even though you are there as a presence that hovers over the text file with a will - your will can't enter into the text in a meaningful, decisive and effective way anymore.  So the idea behind scribe is that as you go along, you add meta-tags to text blocks (sections of text that share something) as you go along and as the seeming 'pile-like' nature of the text file chaos grows - but now you got a way back in ... because scribe can derive views for you based on how effectively you tagged as you went.  So you can re-enter with intention into what would have remained as chaos and derive meaning from it and even keep adding to what otherwise would have seemed like a lost cause.

A good rule is to add scribe to path etc etc of a directory where you will be writing and editing these future 'pile' text files.  I have a directory called 'deadpool' to remind me that all computer data is dead in a way (even though scribe is an effort to counter that deadening force with some life - and so deadpool is an incentive and reminder to be vigilant and guard against this tendency).  
 
```bash
mkdir -p ~/deadpool
cd ~/deadpool          # do your Scribe work in a terminal from here & save and open your 'pile' text files here. 
```

Once you have changed your 'cwd' - 'current working directory' to your deadpool directory:
e.g. for me I type the following at the command line:  'cd /mnt/data/deadpool' then you are ready to work with scribe commands aimed at whatever 'pile' text file you will have open in your favourite simple text editor.


  


So, say you want to create a new text file called: research_ai-llms.txt

You could do that in the normal ways, or you could do it with scribe.  The reason you might do it with scribe is because using the command:

 `scribe capture --append research_ai-llms.txt`  - creates the file, and formats the file with a text header and generates a hash

Check the tool is alive and see its freeze fingerprint any time:

```bash
scribe doctor
```

**And the one command that always tells you everything else: `scribe --help`.** It lists
every verb scribe has, one line each, straight from the tool itself — never a second copy
of the list that this guide could drift out of sync with. Forgotten a verb's exact
arguments? `scribe <verb> --help` (e.g. `scribe backlinks --help`) shows that one verb's
full usage. This guide teaches the *daily rhythm* — when to reach for which verb, and why —
`--help` is the *reference*, and it can never go stale because it's generated from the code
that runs, not written down separately.

```bash
scribe --help              # every verb, one line each
scribe backlinks --help    # one verb, full argument detail
```

---

## The mental model — pile vs view

There are exactly two kinds of file, and keeping them straight is the one thing to
internalise:

| | **The pile** (`pile.txt`) | **A view** (`nas.view`, `live.view`, …) |
|---|---|---|
| what it is | the **truth** — every block, in arrival order | a **disposable** filter of the pile |
| how many | **one**, forever | as many as you like, thrown away freely |
| do you edit it? | rarely, and carefully | **yes — this is where you work** |
| how edits get home | — | `scribe push nas.view pile.txt` — matched by `#id`, landed as a new block |
| lose it? | back it up; it's everything | shrug — `scribe view …` rebuilds it |

The block header looks like this and is plain text you can read with Scribe switched off:

```
@@ #2904 2026-07-07T19:48:03.112904 @act:protect-against-bit-rot @path:toward-integrity-over-convenience @topic:nas @source:gemini
ZFS vs ext4: use ZFS on the NAS for checksums and snapshots.
```

`@@` starts a block; `#2904` is its **id**; the `@key:value` tags are what views filter
on. Everything after the header line, until the next `@@`, is your verbatim text.

**The two tags carrying the meaning are `@act:` and `@path:`** — what the block *does*, and
what it *reaches toward*. `@topic:` is the label on the drawer: it helps you find the block,
it does not say what the block means. A block tagged with a topic and nothing else is what the
bench sheet calls a dead tag, *a noun in a drawer*. Which tags to write is that sheet's
business, not this guide's — but the example above is the shape to copy.

**The `#2904` at the front is the whole of the block's identity (changed in v1.4.0).** This
is worth one minute, because it changes what you can safely do.

It is the **right-hand digits of the timestamp beside it** — look: `…03.112904` ends in
`2904`. That is deliberate, so you can tell at a glance that a header has not been made up.
If a shorter form is already taken in this pile, capture issues a longer one and says so.

**It says nothing about what the block contains, and that is the point.** Correcting a word
does not make a block a different block. Two blocks saying exactly the same thing are still
two sayings, because identity comes from *when it was declared*, never from *what it says*.

Three practical upshots:

- **You can abbreviate an id**, git-style: `scribe tag 290 pile.txt …` works if `290` names
  exactly one block. If it names two, scribe **refuses and lists them** instead of guessing —
  type another character.
- **Ids are unique inside their own pile, not across piles.** The pile is the namespace, the
  way a folder is for a filename. Two piles may hold a `#2904`; when you need to point across,
  write `pile.txt#2904`, which is what `scribe backlinks` already speaks.
- **Older blocks carry a long `@mint:` hash and a few carry nothing.** Both are fine. `@mint:`
  was the identity scheme used between 2026-08-01 and 08-04; it is kept readable, it is
  reported as *legacy* by `scribe verify`, and it is **never upgraded behind you**.

### If you want a body frozen: `--seal`

```sh
scribe capture --seal --append pile.txt …
```

That adds a long `@sealed:` hash at the end of the header, over the body, the moment and
`@source:`. Then `scribe verify pile.txt` will tell you if any of the three changed.

**It is opt-in, per block, and most blocks should not have it.** Until v1.4.0 every block was
effectively sealed — the identity itself covered the body — which meant every typo you fixed
was reported forever as an edit, and the only way to avoid the report was to add a whole new
block. Sealing is now something you *ask for*, on the few blocks where you want the wording
held as it stands. `scribe verify` always says how many blocks it did **not** check, so a
quiet result never reads as a clean bill for the whole pile.

### Saying a thing again, without paperwork: `@name:`

This is the one worth knowing. Most of what you write is a redraft of what you just wrote.

```sh
echo "Structure never informs its material." |
  scribe capture --name coupling-law --append pile.txt --tag act:… --tag path:…

# a week later, you say it better:
echo "A structure cannot tell its material what to be; a person couples them." |
  scribe capture --name coupling-law --append pile.txt --tag act:… --tag path:…
#   redefined coupling-law — 1 earlier definition(s) in pile.txt: #6308
#   They are UNTOUCHED and still resolve by handle; nothing was marked and nothing is owed.
```

**Nothing is written onto the earlier block. There is no chain to keep in step. Nothing is
owed.** The earlier blocks sit exactly where they were, unmarked, still reachable by their
own ids. What moved is what the *name* finds:

```sh
scribe recall coupling-law pile.txt          # the live one — and it says how many it didn't show
scribe recall coupling-law pile.txt --all    # the whole lineage, oldest first
scribe names pile.txt                        # every name, and which definition is live
```

This is Forth's dictionary, which has worked this way since 1970: define a word twice and it
prints `redefined foo`, leaves the old definition standing, and moves the **name** rather than
the thing.

**Names have no rules.** Unlike `@act:` and `@path:` — which are a shared vocabulary and only
work if they compare — a name is yours and singular. Scribe refuses only what would break the
header (a space, for instance). Beyond that, write what you like.

### Fixing a typo: `scribe amend`

```sh
echo "the quick brown fox" | scribe amend '#2904' pile.txt
```

In place. **Nothing appended, nothing superseded, nothing recorded** — a typo is not an event,
and the history of how a sentence reached its wording lives in your backups, which is where
this project has always put it.

It **refuses** in two cases, and both are the tool declining to act on your behalf rather than
protecting you from yourself:

- **Something points at the block.** Someone wrote `@ref:#2904` *about the wording that is
  there now*; changing it silently rewrites their citation. That is precisely what `push` is
  for, and the refusal says so and names what points at it. Add `--also other.txt` to check
  more piles — it only sees the piles you name, and it tells you which ones those were.
- **The block is sealed.** You declared that body should be held as it stands. Breaking your
  own seal is your act, not the tool's.

### So there are four ways to change something, and choosing is yours

| | when | what it costs the pile |
|---|---|---|
| `capture` | a new saying | one block |
| `amend` | a typo. Nothing happened. | nothing |
| `--name` | *I say this better now* | one block, no marks, no chain |
| `push` | a revision where the *supersession itself* is worth recording in the file | one block + one `@superseded:` |

`push` is still right whenever you want the reader who wanders into the outdated block to be
warned **in the file, with the tool off**. It is no longer the only way to say a thing twice.

**Which tags to write is a separate sheet, deliberately.** Scribe accepts *any* `@key:value` —
there is no list of approved keys in the code — so the vocabulary is a discipline you keep, not
something the tool enforces. Keep
`tagging/TAGS-bench-sheet.md` (in this repo) open beside this guide; it is the working list.
(`TAG-KEYS-reference-v1-DRAFT.md` beside it explains *why* each key exists — read it later, not
while you work.)

**You can write any tag from the command line** — `--tag key:value`, as many as you like:

```bash
xsel -b | scribe capture --tag act:keeps-the-thread-alive --tag path:toward-one-pile \
                         --tag aspect:manifesting --topic nas --source gemini --append pile.txt
```

`--topic` and `--source` still work as before; `--tag` is simply the door to every other key.
You no longer have to type headers by hand in xed to use the vocabulary. (You still *can* —
hand-editing the tag run is safe; the `#id` and the timestamp are the two things not to touch.)

**Two things about tags that used to bite you in the terminal — one is now caught for you.**
A tag value must contain **no spaces** — hyphenate. A space stops scribe recognising the
header, and the block then folds into the one above it. As of **v1.1.0** scribe will not
write such a value at all: it refuses, names the line, and shows you the hyphenated form —

```
REFUSED: tag value 'two words' for @topic: contains whitespace. … Use hyphens: @topic:two-words
```

and if it meets one already in a pile (typed by hand, or written by an older scribe) it says so
loudly on every read, names the line number, and warns that the block count is short. It will
**not refuse to open the pile** — your material always stays reachable — but `scribe tag` and
`scribe push` refuse to *rewrite* a pile in that state, because a rewrite would make the loss
permanent. Fix the line it names, then re-run.

And `@state:` is **retired**: it is now `@aspect:` with exactly three values (`manifesting`,
`manifested`, `prospective`). Old piles carrying `@state:` still parse fine, and `--state`
still writes it if you ask — but scribe now announces the retirement every time, on writing
and on reading, so a dead key can never look like a live one. One thing that changed with it:
a view selected on `state:` used to quietly sort newest-first. It no longer does; **ordering
now comes from `--recent` only**, and every view says out loud which order it used.

---

## Job 3, dissolved — moving the scratchpad into the pile

You don't convert the old scratchpad in one shot (that would need your eye on every block
boundary — Scribe won't guess where your blocks split). You do it **the same way you'll use
it going forward: one block at a time, as you touch each topic.**

Say you're looking at the NAS section of your old scratchpad in a xed tab. Select that one
block, and get it into the pile. Two ways, depending on whether you'd rather hand Scribe a
**file** or a **clipboard**:

**A — via a file (most robust, zero extra tools).** In xed, save the fragment as its own
little file (or just save the whole tab), then:

```bash
scribe capture zfs-note.txt --topic nas --topic zfs --tag aspect:manifesting --source gemini --append pile.txt
```

Scribe cleans it into a block, stamps the arrival time, and appends it to the pile. It
prints something like `captured block #c98b (1 lines)` and tells you honestly whether its
loss-auditor flagged anything — it never silently alters your words.

**B — via the clipboard (fewer keystrokes once set up).** Scribe reads standard input when
you don't give it a file, so you can pipe your clipboard straight in. This needs a tiny
clipboard tool (one-time install on Mint/LMDE):

```bash
sudo apt install xsel        # one time only
```

Then, after selecting-and-copying the block in xed:

```bash
xsel -b | scribe capture --topic nas --topic zfs --tag aspect:manifesting --source gemini --append pile.txt
```

(`xclip -selection clipboard -o | scribe capture …` works identically if you have `xclip`
instead.) Path B is the closest thing to "grab from xed, drop in the pile" in one motion.

**Tagging is yours, and only yours.** Scribe will never guess a topic for you (that's the
sovereignty line it won't cross). The `--topic`/`--tag` flags are you telling it what the
block *is*. A block with no topic just lives in arrival order and shows up in no topic view
— which is fine; tag it later with `scribe tag c98b pile.txt --topic nas` when you decide.
(Two tags are not yours: `scribe tag … --tag sealed:…` and `--tag mint:…` are **refused**.
A seal is issued by `scribe seal` or `capture --seal` over the body actually in the pile;
writing one by hand would be asserting the check instead of performing it. A `@mint:` is a
retired identity, kept readable on the blocks that carry one and never yours to edit.)

**And one tag of yours is inside a seal, where you take one: `@source:`.** On a **sealed**
block, changing it is a visible act — `scribe verify` reports the block as `changed since it
was sealed`. That is deliberate: re-attributing a saying, relabelling handed-in material as
your own or your own as an AI's, is a different claim rather than a better wording.

**On an ordinary block it is not, and that is the ruling, not a gap.** Sealing is opt-in
(`scribe seal '#id' pile.txt`, or `capture --seal`), so most blocks report nothing — and
`verify` says so on every run rather than letting silence read as a clean bill.

**It is the only tag inside a seal.** `@topic:`, `@act:` and the rest you may revise freely
with no trace — re-filing a pile as your thinking moves is ordinary work. So are `@origin:`
and `@attests:`, deliberately: which *kind* of mind made a thing is a judgement that can
honestly change, and who vouches for it is a stance you are allowed to withdraw.

Repeat, block by block, whenever you're already touching that material. There's no
"migration day" — the pile fills as you work.

---

## Job 2, the experiment — a view instead of a staging tab

Here's the daily loop that replaces "keep five tabs open to hold things." Suppose you want
to work on everything NAS-related.

**1. Derive a clean view file and open it in xed:**

```bash
scribe view topic:nas pile.txt > nas.view 2>/dev/null
xed nas.view &
```

The `> nas.view 2>/dev/null` part matters: it sends the **view** into the file and Scribe's
chatter (`1 block(s) in view…`) to the terminal, so the file opens **clean** in xed. The
`&` hands the terminal back to you.

Now `nas.view` holds every NAS block, **gathered together**, even though in the pile they're
scattered among router notes and git notes and philosophy. **None of them moved in the
pile.** This is your staging tab — except you didn't have to keep it open all week; you
summoned it in one line and you'll throw it away at the end.

**2. Work in it in xed** — develop a thought, add a `NOTE-TO-SELF:` line under a block, fix a
typo. Edit the **bodies**; leave the `@@ #id …` header lines alone (they're how edits find
their way home). Save the file in xed as usual.

**3. Push your edits home:**

```bash
scribe push nas.view pile.txt
```

Scribe matches each block by its `#id` and — **as of v1.3.1** — *appends* your edited version
as a new block rather than writing over the old one. (The output below is from a real run, so
its handles are real too; yours will differ.)

```
pushed home: 1 block(s) superseded — nothing was overwritten
  #2ea7 -> #b344   (#2ea7 keeps its body and its id, and gains one tag: @superseded:#b344)
  The old blocks are still there and still say what they said. To correct one
  WITHOUT leaving that history in the pile, edit it directly in your editor —
  restic keeps that history instead. Both doors are yours; this one is push's.
```

The router block you didn't touch stays untouched. The thought you developed in the view is
now in the canonical pile and you can delete `nas.view` without a second thought.

**This is the one change most worth internalising, so here is what the pile actually looks
like afterwards.** Your edit did not replace anything. There are now two blocks:

```
@@ #2ea7 …  @topic:nas @source:gemini @superseded:#b344
ZFS vs ext4: use ZFS on the NAS for checksums and snapshots.       ← untouched, and marked stale

@@ #b344 …  @topic:nas @source:gemini @replaces:#2ea7
ZFS vs ext4: use ZFS on the NAS for checksums and snapshots.
Also: scrub monthly.                                               ← your edit, as its own block
```

Four things follow, and they are all things you will meet in a normal week:

- **The old block keeps its words.** Push never rewrites a body and never reissues an
  identity. The only mark it may add to an existing block is `@superseded:`, once.
- **The new block inherits the old one's tags**, so it turns up in every view the original
  did. A correction that fell out of its own topic would be a quiet loss.
- **`@superseded:` is written into the file, not worked out on demand** — so if you open the
  pile in xed a year from now with no tool running, the stale block *tells you itself* that
  something replaced it, and names what.
- **Pushing the same view twice is skipped, not doubled.** Scribe notices the block is
  already superseded, tells you your view is stale, and names the block to edit instead:

  ```
  SKIPPED 1 block(s) already superseded — your view is stale, and pushing it would fork the chain:
      #2ea7 was superseded by #b344. Regenerate the view and edit #b344 instead.
  ```

**Don't want that history in the pile?** Then don't use `push`. Open `pile.txt` in xed and
fix the block in place — it is a plain text file and always was, and restic keeps *that*
history instead. **Two doors, and you pick per edit:** history-in-the-pile through `push`,
history-in-your-backups through your editor. Scribe binds *itself* to append-only; it does
not bind you.

**Reading a pile that has supersessions in it.** A view shows both blocks and says so in its
own header, because hiding them by default would be exactly the silent exclusion this tool
refuses:

```bash
scribe view topic:nas pile.txt
#   # 1 block(s) here carry @superseded: — a later block has replaced them.
#   # Shown, not hidden; use --current to drop them.

scribe view topic:nas pile.txt --current       # just the live ones
#   # --current: 1 superseded block(s) HIDDEN from this view. They are still in the pile.
```

Use `--current` when you want to *work*; leave it off when you want to see how a thought
moved. Either way the pile keeps everything.

*One rough edge, said plainly:* `toc` and `export` do **not** know about supersession and
have no `--current`. So `scribe export topic:nas pile.txt --bare` hands the next mind **both**
the old wording and the new. When you export a topic you have pushed to, check what came out
before you paste it.

**To hand a batch to an AI** (the "copy the staging tab into ChatGPT" move), export instead
of view — `--bare` strips every header and back-link so there's nothing to scroll-and-delete
on the other end:

```bash
scribe export topic:nas pile.txt --bare > for-ai.txt
xed for-ai.txt &          # copy from here into the browser input box
```

Notice this respects **Job 1**: you're pasting *out of a local file into the browser*, the
safe direction you already trust.

---

## The daily rhythm, in one glance

```
   ┌─ Job 1: still a xed tab. Compose long input here, safe from the browser. Unchanged. ─┐

   capture   :  (saved fragment | xsel -b)  →  scribe capture … --append pile.txt
   explain   :  scribe stamp pile.txt               # once, for a pile made before v1.1.0 —
                                                    #   also gives an old pile its @genesis:
   look      :  scribe toc pile.txt                 # contents by subject (the default)
   look again:  scribe toc pile.txt --by path       # …the SAME pile, ordered by reaching
   what keys :  scribe keys pile.txt                # what your vocabulary has become
   gather    :  scribe view topic:X pile.txt > X.view 2>/dev/null ; xed X.view &
   live only :  scribe view topic:X pile.txt --current   # v1.3.1 — hide superseded blocks
   work      :  edit bodies in xed, save
   land      :  scribe push X.view pile.txt         # v1.3.1 — APPENDS a superseding block,
                                                    #   never overwrites ; delete the view
   hand off  :  scribe export topic:X pile.txt --bare > for-ai.txt ; xed for-ai.txt &
   who points at it: scribe backlinks '#c98b' pile.txt   # v1.1.2 — see below
   two blocks, one name: scribe duplicates pile.txt      # v1.3.0 — see below
   what did I change: scribe verify pile.txt             # of the blocks you SEALED:
                                                         #   as sealed, or edited? see below
```

`scribe toc pile.txt` any time prints the whole table of contents from your tags — the list
you used to hand-maintain at the top of the scratchpad, now free and always current.

**The contents page opens by any key you name.** `--by topic` is only the default, kept so
nothing you already do changes. `--by act`, `--by path`, `--by aspect` index the same pile
along a different axis — the pile never moves; only the way in does. And every index now says
at the top which key it grouped by and **which keys it is not showing you**, so a contents
page can never quietly suggest that subjects are all there is:

```
# grouped by @topic: — 13 blocks, 8 distinct @topic: values
# NOT shown by this index: @source:(13) @act:(9) @path:(9) @aspect:(6)
# 2 of 13 blocks carry no @topic: — listed under (no @topic:) below
```

`scribe keys pile.txt` lists every key in the pile with its values and counts — use it to see
what you actually reach for, and to find the axes worth indexing by. (It replaces the
`grep | tr | sed | sort -u` recipe this guide used to carry: a practice living in a paragraph
of prose belongs in the tool.)

**`scribe backlinks` (v1.1.2) — "what points at this block?"** The moment you start using
relational tags — `@ref:`, `@overrules:`, `@corrects:`, `@superseded:`, or any key you invent
that names another block's id — you'll want the REVERSE question answered: not "what does
block c98b point at" (that's just reading its own header) but "what points *at* c98b?" That's
what this derives, fresh, every time you ask — never written back into the pile:

```bash
scribe backlinks '#c98b' pile.txt
#   What points at pile.txt#c98b (1):
#     #d4e1 (2026-08-01T09:00) via @corrects:#c98b
#
# nothing pointing at it yet?
scribe backlinks '#a1a1' pile.txt
#   (nothing points at pile.txt#a1a1)
```

It also works **across piles**, if you ever split your work into more than one — say a work
pile and a personal one, or one pile per project. Name the other pile in the target, `pile#id`:

```bash
scribe backlinks 'work.txt#c98b' work.txt personal.txt
```

Any tag value shaped `#id` or `otherpile.txt#id` counts, on any key — there's no fixed list of
"relational" keys to remember; if a value names a real block id, `backlinks` finds it.

**`scribe activate` (v1.2.0) — "who is currently waiting on this?"** If you use `@awaits:` to
mark a block as blocked on some condition (the way `RIPE-LEDGER.txt` does), this answers "which
blocks, right now, are waiting on exactly this" without you having to eyeball a `toc --by awaits`
grouping by hand:

```bash
scribe activate the-sovereigns-ruling pile.txt
#   What is @awaits:the-sovereigns-ruling (1):
#     pile.txt#a2 (2026-01-01T00:01)
```

It never edits anything — you still resolve the block yourself with `scribe tag`, once you've
acted on what was waiting. `--key dissolves` asks the same question of `@dissolves:` (a block's
own named retirement condition) instead.

**`scribe verify-export` (v1.2.0) — "has the pile moved since I saved this?"** Every non-bare
`export` now stamps its trailing manifest with a content fingerprint. If you keep an exported
view around — pasted into another tool, or tangled into a running file — this tells you whether
the pile it came from has since changed underneath it:

```bash
scribe export topic:nas pile.txt > nas.export.txt
# ... later, after editing pile.txt ...
scribe verify-export nas.export.txt topic:nas pile.txt
#   DRIFT — topic:nas has changed in the pile since export: was content:sha256:86829acf,
#   now content:sha256:0fae1347.
#     same 1 block(s) by id — body content changed
#     the exported file is stale; re-run `scribe export` to refresh it.
```

It never re-exports or repairs anything for you — MATCH, DRIFT, or NO MANIFEST (if the file was
exported `--bare`) is all it reports.

**`scribe converges` (v1.2.0) — "does this pile share DNA with a different one?"** If you keep
more than one pile — one per project — this looks for blocks in DIFFERENT piles that share a
literal tag value or a literal Charter-clause-shaped citation, without either side ever having
written a pointer to the other:

```bash
scribe converges projectA.txt projectB.txt
#   ## Shared tag-values across different piles (1)
#     @act:guard-against-drift  — 2 block(s) across 2 pile(s): projectA.txt, projectB.txt
#       projectA.txt#a1 (...)
#       projectB.txt#b1 (...)
```

Every line is a candidate to go READ, never an asserted relation — nothing here is merged or
written back, and a shared value can be a real convergence or just a coincidence; that judgment
stays yours. `--by act` (or any key) narrows the scan to one key; `--no-cites` skips the
citation half if you only want the tag-value scan.

**`scribe duplicates` (v1.3.0) — "do two blocks answer to the same name?"** In a pile made by
v1.3.0 or later this should always come back empty, because handles are checked as they are
issued. It matters for the piles you already had: those were made by a scribe that could issue
the same id twice, and this is how you find out whether yours did.

```bash
scribe duplicates pile.txt
#   pile.txt — 42 block(s), 0 duplicated handle(s)
#   no duplicated handles
```

On a pile that *did* collide, it shows you both blocks with their declaring moments, so you
can see whether they are one saying recorded twice or two different sayings:

```bash
scribe duplicates old-pile.txt
#   old-pile.txt — 2 block(s), 1 duplicated handle(s), no @genesis: line
#     #aaaa — 2 blocks
#         2026-01-01T00:00  'first saying'
#         2026-01-02T00:00  'second saying'
#         ^ distinct declaring moments — these ARE different sayings that happen to share
#           a handle. Lengthen one by hand to disambiguate.
```

Two blocks sharing an id *and* a moment is the one case it will not rule on: it says so and
leaves it to you.

**It never repairs anything, and that is deliberate** — reissuing an id would break every
`@ref:` already pointing at it. It reports; the ruling is yours. While a handle is ambiguous,
`push` and `tag` **refuse to write to it at all** and list the candidates, rather than picking
one and getting it wrong silently. That refusal is the actual protection; `duplicates` is just
how you go looking before you get refused.

**Old piles, and what to do about them.** A pile started before 2026-08-01 has no `@genesis:`
line. Nothing is wrong with it, nothing depends on that line any more, and scribe will **not**
change it behind your back. Verbs that meet one mention it and move on:

```
NOTE: pile.txt carries no @genesis: line (a pile born before 2026-08-01), so it carries no
birth moment. Nothing now depends on that — identity stopped folding the genesis in on
2026-08-05 — so this is a note about the pile's history, not a defect.
```

`scribe stamp pile.txt` adds one if you want the record of when the pile began. Leaving it
alone is equally fine.

**`scribe verify` — "is this sealed block still the one I sealed?"** You have two doorways for
changing a block: `push`, which appends and leaves a trail, and your own editor, which leaves
none in the pile. On the blocks you asked to have **sealed**, this tells you afterwards which
door each one went through.

```bash
scribe verify pile.txt
#   pile.txt — 3 block(s): 1 as sealed, 1 changed since sealing, 1 not sealed
#       #5178  2026-08-02T13:36:51.552200  changed since it was sealed
#         'Original sentence one. Rewritten final sentence.'
#     1 of 3 block(s) carry no @sealed:, so THE CHECK DID NOT RUN for them. …
```

It works because the seal was computed from the block's own body, timestamp and `@source:` —
so re-computing it from what is in the file now says whether any of the three moved. No
database, no history, no copy of your old text anywhere.

**It always tells you how many blocks it did not check**, and blocks carrying the retired
`@mint:` are reported as *legacy* rather than checked: a mint needed the pile's genesis and
the block's frozen position, so it cannot be re-derived from what the file alone says, and
scribe does not pretend otherwise.

**Read the wording carefully, because it is deliberate.** `changed since it was sealed` is a
**statement of fact, not a complaint.** Editing a block by hand is a door the tool deliberately
leaves open for you; scribe has no business grading you for walking through it. That is why
this verb has no severities, no "invalid", no warnings — and a test enforces that, so it
cannot drift into scolding you later.

Four things it will tell you:

- **`as sealed`** — untouched since you sealed it.
- **`changed since it was sealed`** — the body, timestamp or `@source:` changed in the file.
  It cannot tell you *what* changed: the pile keeps no earlier copy, by design, so only restic
  or git holds the before.
- **`not sealed — this check did not run`** — the ordinary case, since sealing is opt-in.
  Not a fault, and deliberately *not* reported as a clean pass either.
- **`legacy`** — the block carries the retired `@mint:` and no seal. A mint needed the pile's
  genesis and the block's frozen position, so it cannot be re-derived from what the file alone
  says. Reported as uncheckable rather than as absent, and never upgraded behind you.

**Only the first two set the exit code**, and that is on purpose. Unsealed and legacy blocks
are permanent conditions of ordinary piles, so a nonzero exit for either would fire on every
run forever — which teaches you to stop reading exit codes, and then the one that matters gets
ignored too.

**If you cut a block out of the pile, nothing else notices.** That was not always true. Until
v1.4.0 a block's identity contained its *position*, so deleting one made every later block
fail to re-derive, and the tool needed a whole extra mechanism to recognise that pattern and
report *"1 block removed"* rather than a wave of false alarm. Identity no longer contains a
position, so removing a block is simply invisible to every other block — which is what an
append-only file of independent sayings should have meant all along. The clever machinery went
with the thing that made it necessary.

On an ordinary pile it will say most blocks are not sealed and that the check therefore did
not run on them. That is honest rather than reassuring, which is the point — and under an
opt-in seal it is the normal state of affairs, not a gap to close.

**Your pile explains itself to whoever opens it.** A pile created from v1.1.0 onward starts with
a short comment header saying what the format is, which commands search it properly, and why a
plain `grep` over it hands back fragments — a body line with no id or tags, or a header with no
claim, never a whole record. It also explains what the `#id` is, how `@name:` lets a saying be
said again, and what a `@sealed:` hash means where one appears. It carries the pile's own
`@genesis:` line too: the moment this pile began, kept as a record worth having rather than as
something the tool depends on. That matters beyond your own use: if you ever point an AI assistant
at the drive where your piles live, it meets the instruction **in the file** rather than needing
you to remember to explain it. For a pile you made before this, run `scribe stamp pile.txt` once.
It is only ever written when a pile is *created* (or when you run `stamp` yourself), so if you
delete the header it stays deleted — and `--no-stamp` declines it up front. It is all comment
lines above the first `@@`, so it changes no count, no index and nothing you can push home.

**One thing no command can do for you.** Whichever index you open habitually is the one you
will quietly start writing *for*. That is why the axis is now plural rather than merely
better — so that no single one pulls. Watching whether your own `@path:` values start being
chosen for how tidily they group, rather than for whether they are true, is yours alone; no
tool can check it.

---

## Gotchas that bite in the terminal (all real, all avoidable)

- **Always redirect a view to a file with `2>/dev/null`.** Without it, Scribe's status line
  lands in the file too and clutters what you open in xed. With it, the file is clean.
- **Edit views, not the pile — with one deliberate exception.** The pile is safe to read and
  safe to `push` into; but if you hand-edit a block's `@@ #id …` header you can orphan it.
  Change tags with `scribe tag <id> pile.txt --tag act:… ` / `--remove topic:…`, not by
  retyping the header. **Three things on that line are never yours to retype:** the `#id`, the
  timestamp, and any digest (`@sealed:`, or a legacy `@mint:`). For a body, you no longer need
  to hand-edit at all — `scribe amend '#id' pile.txt` does exactly that, in place and without a
  trail, and refuses in the two cases where doing it silently would cost someone else
  something.
- **A push adds a block; it does not change one.** If your pile got longer after a push,
  nothing went wrong — that is the design. `scribe view … --current` gives you the tidy read;
  the pile itself keeps the whole movement.
- **An export can contain a stale body.** `export` and `toc` don't filter superseded blocks,
  so a topic you have pushed to exports both wordings. Eyeball `for-ai.txt` before pasting.
- **A non-zero exit is not always a failure.** Exit `1` means scribe refused to do what you
  asked. Exit `2` means it *did* the job and has something to disclose — a malformed header
  line, most often. Only `1` means nothing happened.
- **A view is a snapshot.** If you derive `nas.view`, then capture new NAS blocks, the old
  `nas.view` won't know about them — re-derive it. Views are cheap; regenerate freely.
- **`--append` vs no `--append`.** With `--append pile.txt`, the block goes into the pile.
  *Without* it, `capture` just prints the block to the terminal so you can eyeball it first.
  Use the print form when you're unsure and want to check before committing it to the pile.
- **Back up the pile; ignore the views.** The pile is the only irreplaceable file. This is
  exactly where the restic-plain backup tool (the sibling project) earns its keep — point it
  at `~/scribe/` and your whole thinking-pile is preserved, plainly, checksummed.

---

## What to actually test first

Don't adopt this wholesale. Take **one** real topic out of your current scratchpad — NAS is
the obvious one, since it's the scattered case that hurts. Capture its blocks into a fresh
`pile.txt`, derive `topic:nas` into xed, develop one note, push it home. Then ask the only
question that matters: *did that feel better in the hand than the five tabs did?* If yes,
Job 2 is yours to keep. If it felt like a step sideways, keep Scribe for Job 3 (the
scratchpad it plainly dissolves) and leave Job 2 to your tabs. Either answer is a good one.

---
---

# APPENDIX — Editing the pile directly in your own editor

*Appended 2026-08-09 (scribe v1.7.1). Draft material for the "can I just edit it myself?"
question — deliberately over-written, with the same point made several ways so the fluent
version can be assembled from it. Nothing above this line was changed.*

## The one-paragraph version

Your pile is a plain text file and editing it directly is a supported way to work, not a
loophole. There is exactly one thing in it that a typo can genuinely break — the `@@ #id …`
header line at the start of each block — and when that breaks, the block is silently
absorbed into the one above it. Scribe cannot warn you at the moment you save, because it
isn't running then. What it does instead is **tell you the next time it reads the file, and
refuse to write to the file until you have fixed it**. So the habit that makes direct
editing safe is one command: **`scribe blocks pile.txt`** after you save.

## The two doors, and why the choice is yours

Scribe gives you two ways to change what a block says, and neither is the "proper" one.

**Door one — `scribe push`.** You derive a view, edit it, push it home. Scribe appends a new
block carrying your new wording, marks the old one `@superseded:`, and leaves the old body
exactly as it was. **The history lives in the pile.** Anyone reading that file later, with
no tool at all, sees both what you said and that you changed your mind.

**Door two — open the pile and type.** You change the words in place. **No history is left
behind.** If you want that history, it lives in your backups instead — which is the right
place for it when the change is a typo, a reformat, or something you'd rather not memorialise
in the artifact itself.

The tool binds *itself* to append-only. It does not bind you. That asymmetry is deliberate:
a pile you cannot edit by hand is a database wearing a text file's clothes, and the whole
premise here is that it isn't one.

## What can actually go wrong (it is a short list)

Almost nothing you type in a block's **body** can hurt you. Markdown, code, quotes, blank
lines, lines beginning with `#`, even a pasted diff — all fine. The body is just text.

The risk is confined to the **header line**, the one that starts `@@ #`:

```
@@ #a4f2 2026-03-01T09:00:00 @topic:nas @source:schnee
```

Two mistakes break it, and they account for essentially all real cases:

1. **A space inside a tag value.** `@source:claude code` instead of `@source:claude-code`.
   This is by far the commonest. Tag values cannot contain spaces — a space ends the value
   and starts what scribe expects to be the next tag.
2. **A missing or mistyped `#` before the id.** `@@ a4f2 …` instead of `@@ #a4f2 …`.

## Why a broken header is invisible rather than loud

This is the part worth explaining carefully, because it is counter-intuitive and it is the
reason the check matters.

A block runs from its header line to the next header line. If a header fails to parse,
scribe does not see a header there — so that line, and everything under it, becomes **part
of the previous block's body**. Two blocks silently become one.

Nothing looks wrong. Open the file and you still see what appear to be three blocks, neatly
separated, each with a header. Your eye counts three. Scribe counts one. **The file looks
perfect and reads wrong**, and that is precisely why a human eyeballing it is not a
substitute for the check.

## What scribe guarantees, and what it does not

It is worth being exact here, because "editing directly has no safeguards" is not true and
undersells the tool:

| | direct edit in your editor | edit via a derived view + `push` |
|---|---|---|
| told at the moment you save | **no** — scribe isn't running | no — scribe isn't running then either |
| told the next time scribe reads the file | **yes**, with line numbers and cause | yes |
| scribe will write to a broken pile | **never** | never |
| the view you are editing is itself checked | n/a | **yes**, before anything is written |
| history of the change left in the pile | no | yes |

So the honest contrast is not *guarded versus unguarded*. It is **told at save time versus
told at next read** — and neither door tells you at save time, because scribe is a command
you run, not a daemon watching your files. What `push` adds is that it also checks *the view
you edited* before it will touch the pile, so a typo made in a derived view is caught before
it can land anywhere.

## The command to run after a hand edit

```sh
scribe blocks pile.txt
```

On a healthy pile that prints the block count and exits `0`. On a pile with two broken
headers it prints this:

```
1 block(s)
[[scribe:malformed-header pile.txt:4]] not read as a header — absorbed into the PREVIOUS
  block's body: @@ #a002 2026-03-02T09:00:00 @topic:nas @source:claude code
[[scribe:malformed-header pile.txt:7]] not read as a header — absorbed into the PREVIOUS
  block's body: @@ b003 2026-03-03T09:00:00 @topic:nas @source:schnee
  2 malformed header line(s): any block count reported here is SHORT by that many. Two
  causes, in order of how often they bite: a SPACE INSIDE A TAG VALUE (`@source:claude
  code` — write `claude-code`), or a missing or mistyped `#` before the id. Fix the
  line(s) above, then re-run.
```

Read it in three parts. **The line number** tells you exactly where to look. **The quoted
line** shows you what scribe saw, so you can spot the space or the missing `#` by eye.
**The count** is the diagnosis: `1 block(s)` where you can plainly see three is the shape of
the damage, stated as a number.

Exit code `2` means findings, so it works in a script or a git pre-commit hook:

```sh
scribe blocks pile.txt || echo "fix the pile before committing"
```

## `blocks` is not special — most read verbs do this

`blocks`, `toc`, `keys`, `view` and `duplicates` all announce broken headers, because they
all parse the pile. `blocks` is only the one to *reach for*, because it does the least else
and its output is short.

This also means you often find out without asking. Derive a view the morning after a hand
edit and the warning is there waiting for you. **And a derived view carries the warning
inside itself** — in the `#` comment header at the top — so it survives even when you send
the view somewhere scribe's messages cannot follow, such as piping it into an editor tab:

```sh
scribe view topic:nas pile.txt | xed -
```

The tab you get will say, in its own first lines, how many blocks it holds and whether the
count is short.

## One trap to know about: `scribe check` does not check this

If you have just hand-edited a pile, the word your fingers reach for is `check`. **It is the
wrong verb**, and it will tell you everything is fine:

```
$ scribe check pile.txt
0 finding(s):
```

`check` runs the *capture-time loss auditor* over raw text — it is for inspecting material
you are about to bring **into** a pile, to see what would be flagged as lost or mangled
during capture. It has nothing to say about the structure of an existing pile, and it is not
broken; it simply answers a different question.

`scribe verify` used to have the same trap. As of **v1.7.1 it announces broken headers too**
— which matters, because `verify`'s job is to say whether sealed blocks still hold, and a
swallowed block changes its neighbour's body. Before the fix, `verify` would tell you a
sealed block had *"changed since it was sealed"* — true, alarming, and with no hint that a
mistyped header one line above was the cause. You got the alarm without the diagnosis.

**So: `blocks` to check structure. `check` for material you are about to capture. `verify`
for seals — and it will now mention broken headers on its way past.**

## Fixing one when you find it

There is nothing clever to it. Open the pile, go to the line number, and repair the header:

- **space in a tag value** → hyphenate it. `@source:claude code` becomes
  `@source:claude-code`. Values may contain hyphens, dots, colons in ids — anything but
  whitespace.
- **missing `#`** → put it back. `@@ a4f2 …` becomes `@@ #a4f2 …`.

Then re-run `scribe blocks pile.txt` and confirm the count is what you expect.

Nothing was lost while it was broken. The text was always in the file; scribe was simply
reading it as part of the block above. Fixing the header restores the boundary and the block
returns, with its id, its timestamp, its tags, and its place in every view it belonged to.

## Which editor

Any of them. The pile is UTF-8 text with no special encoding, no length limits, no trailing
requirements. `xed`, `gedit`, `kate`, `vim`, `nano`, `micro`, VS Code — all fine.

If you want to *read* a derived view in a tab without leaving a file on disk anywhere, most
editors accept `-` to mean standard input and will open it as an unsaved, untitled buffer:

```sh
scribe view topic:nas pile.txt | xed -
```

Note the direction: that is a **one-way door, good for reading**. You cannot push back out of
an unsaved buffer, because there is no file for scribe to read. If you want to edit and push
using your own editor, use a temporary file and let the editor block until you close it:

```sh
tmp=$(mktemp) && scribe view topic:nas pile.txt > "$tmp" && xed -w "$tmp" \
  && scribe push "$tmp" pile.txt; rm -f "$tmp"
```

`-w` (`--wait`) is xed's flag for "block until the file is closed"; most graphical editors
have an equivalent (`gedit -w`, `code --wait`, and terminal editors block by nature). The
temporary file is deleted afterwards — a view is disposable, so nothing is lost by throwing
it away.

## The short habit, if you remember nothing else

1. Edit the pile in whatever editor you like.
2. Run `scribe blocks pile.txt`.
3. If it names a line, fix that line and run it again.

That is the whole of it. And if you forget step 2, the worst case is not data loss — it is
that scribe refuses to push, tag or amend until you fix the line it names, and tells you
which one.

..............................

So scribe holds no state at all between your commands. The only things that persist are the pile file on
  disk, and the viewer's own in-memory list of open tabs.

  Exactly four things pass between them

     viewer  ──── argv (the command + arguments) ────►  scribe
             ──── stdin (an edited view, for push) ──►
             ◄─── stdout (the derived view) ──────────
             ◄─── stderr (counts, warnings, refusals) ─
             ◄─── exit code (0 / 1 / 2) ──────────────

                both read and write the same pile file on disk

  That's the whole interface. No shared memory, no callbacks, no plugin API.

  Why it's built this way

  The comment on that function says it: "Invoke FROZEN scribe as a subprocess. Never an import — the freeze 
  holds by construction."

  If the viewer imported scribe, it would have scribe's functions in its own memory and could redefine any
  of them — monkey-patch a check away, wrap a verb, change what push means. Then "scribe is frozen" would be
  a promise someone could break by accident. As a subprocess it isn't a promise, it's a fact: the viewer 
  has no more power over scribe than you do at a shell prompt.

  Scribe, for its part, does not know the viewer exists. I grepped it: one single match for "viewer" in
  3,300 lines, and it's a comment I wrote yesterday explaining why a message matters — not a dependency, not
  a flag, not a mode. Scribe has no viewer-awareness to remove.

  What that buys you, practically

  - The viewer is genuinely optional. Delete the whole viewer/ directory and scribe is untouched. That's
  §4.6, the "view-never-doorway" law.
  - Anything the viewer does, you can type. There's no hidden capability. Its /help even asks scribe --help
  rather than keeping its own list, so it can't drift.
  - A bug in the viewer cannot corrupt your pile through scribe. The worst it can do is run a wrong command
  — and scribe applies all its own refusals regardless of who called it. Yesterday's view-side
  malformed-header guard protects the viewer for free, without a line of viewer code, for exactly this
  reason.
  - You can watch what it's doing. Every command it runs is one you could paste into a terminal.

  Two real couplings, worth knowing

  1. Path. SCRIBE is computed as the directory above viewer/ plus scribe.py. So viewer/ must stay sitting
  next to scribe.py. Move the folder elsewhere and it won't find it.
  2. Interpreter. It uses sys.executable — whichever Python is running the viewer also runs scribe. Since
  you launch the viewer with the venv Python (for Textual), scribe runs under that too. Harmless, because
  scribe is stdlib-only and needs nothing installed — but that's why it works despite scribe having no
  relationship to the venv.

....
me>
The scribe command writes standard output (stdout) and writes standard error (stderr) to screen (even though they look like they are together, they are really two separate streams presented as one).  So the idea may come into your head that you want to use an ordinary Unix pipe | to view what seems to be a single output,  somewhere else other than in your terminal screen, for example in a simple text editor, however bear the following in mind:

Scribe was invisioned to be primarily a reporter and other related functions have grown from that one.  Scribe was meant to look at the text you point it at, and then report on what it can see taking advantage of meta tags you structured your text with.  Initially I was after a tool that would generate a kind of TOC 'Table of Contents' list that doesn't care if a single topic is scattered around in different places in a text file.  These reports were to be by their very nature, disposable views of something that changes, and can be derived and re-derived etc.

So if you wanted such a report to be generated in a window other than your terminal, then you might think to type the following command:

 scribe view topic:dolphins my-text.txt | xed my-text_topic-dolphins.txt

Then you might see every block of text you tagged with @topic:dolphins listed together in your xed editor as a derived view derived from your my-text.txt; however, you now have also saved file on your hard drive for something you only wanted in a disposable way in a kind of temporary buffer.

So then you might type:

scribe view topic:dolphins my-text.txt | xed - 

Putting just a dash after your editor's name and not a file-name, means there is no path or name attached for the text to be written to.  This gives you a buffer with nowhere to save itself - which seems like all is solved.  The caveat is 



If you have a simple text editor that can read standard input (stdin), then since scribe writes something to the standard output



.

If your editor reads standard input, you already have half of this

  Nothing in Scribe knows what an editor is. scribe view writes the derived view to standard
  output and its disclosures to standard error, which is all an ordinary Unix pipe needs. If your
  editor accepts - as a filename meaning "read standard input", the two compose without anyone
  having designed them to:

  scribe view topic:nas pile.txt | xed -

  You get the view in a tab that is not backed by any file. There is no path attached to it,
  so Ctrl-S has nothing to write to and escalates to Save As. That is not a trick or a workaround
  — it is the direct consequence of the text arriving through a pipe, and it happens to be
  exactly the property you want for a derived view. A view is disposable by definition; a buffer
  with nowhere to save itself is that fact made visible.

  - for standard input is a broad convention but it is per-program, not universal. xed,
  gedit, pluma, kate, vim, nano, micro and code all accept it. emacs does not.
  Test yours once and you will know for good.

  Do not add 2>/dev/null. Older notes on this pipe included it. It was always cosmetic —
  standard error never entered the pipe in the first place — and since v1.6.0 it is actively
  unhelpful, because that is the channel carrying the block count and any malformed-header
  warning. Let those print in your terminal where you can see them. The view itself also carries
  its count and any damage report in its own # comment header, so even the tab you are looking
  at can tell you if the pile is short.

  The honest limit of the pipe: it is a one-way door

  You can pipe into an editor buffer. You cannot pipe back out of one. There is no file
  for scribe push to read, so the moment you want your edits to go home by #id, the pipe has
  nothing left to offer you.

  That makes it excellent for what it is: reading a derived view without leaving a file lying
  about. Pull up everything tagged topic:nas, read it, think, close the tab, nothing to clean
  up. For that job it is perfect and you need nothing else.

  Closing the loop with your own editor, if you want to

  If you want to edit and push using your own editor, use a temporary file and have the editor
  block until you close it:

  tmp=$(mktemp) && scribe view topic:nas pile.txt > "$tmp" && xed -w "$tmp" \
    && scribe push "$tmp" pile.txt; rm -f "$tmp"

  -w (--wait) is xed's flag for "block until the file is closed"; gedit -w and
  code --wait are the equivalents, and terminal editors block by nature. The temporary file is
  deleted afterwards, so nothing persists — a view is disposable, and throwing it away costs
  nothing.

  Verify this once on your own machine before relying on it. Whether a graphical editor
  actually blocks depends on how it was started and whether an instance is already running; some
  hand off to an existing process and return immediately, which would push an unedited file.
  One test tells you which behaviour yours has.

  So why is there a Textual viewer at all?

  Because the pipe answers one question well and a different question not at all.

  The pipe gives you one view at a time. To look at topic:nas and aspect:ripe and
  topic:github-push together — glancing between them while you think, keeping all three
  open — the pipe offers you three separate editor windows, none of which can push, each holding
  text that scribe cannot see. Add a fourth and you are managing windows instead of thinking.

  And you cannot click back into a terminal's scrollback. Scrollback is a river: output
  flows past and is gone upstream. Anything you want to return to and switch between has to
  be held somewhere that persists on screen. That single requirement — several derived views open
  at once, switched between, none of them closing — is what selects a full-screen terminal
  application. It is not a preference. Nothing else in a terminal can hold it.

  So the viewer exists to add exactly three things, and nothing else:

  1. Several derived views open together as tabs, clicked between, none of them files.
  2. push from inside a tab, by #id, without saving anything out first.
  3. A prompt underneath them all, so you run Scribe commands without leaving what you are
  reading.

  Some designs were tried and rejected, and the reasons are worth knowing because they are the
  reasons the thing looks as it does:

  - One view filling the screen, closed to get back. This is what a modal does, and it is
  just the pipe again with extra steps: one view at a time, and re-derived every time you
  switch. Rejected.
  - A command-line REPL that prints views into scrollback. Elegant, keeps your terminal
  yours, and has no tabs whatsoever — so it lands back at one view at a time. Rejected for the
  same reason.
  - The log beside the tabs, sharing the screen. This is what the viewer originally did, and
  every view arrived by halving the space everything else had. Now the log is simply the first
  tab, and each view opens beside it at full width.

  What the viewer costs you, plainly

  You are editing in a text box, not in your editor. No xed search-and-replace, no macros,
  no muscle memory, no plugins. For a small edit to one block this is a fair trade for being able
  to push it home in the same breath. For serious rewriting it is not, and you should use the
  temp-file route above, or edit the pile directly.

  It needs textual installed. Scribe itself has no dependencies at all — it is one Python
  file using nothing outside the standard library — and that stays true. The viewer is the one
  optional piece that asks for something.

  It is a workbench tool, not a finished product. Some Scribe verbs are not yet forwarded
  through it and must be run from a terminal.

  The rule that keeps this honest

  The viewer runs Scribe the same way you do — it launches scribe.py as a separate program
  and types commands at it. It never loads Scribe as a library, so it cannot change what any
  command means. Whatever refusals and checks Scribe applies at your terminal, it applies
  identically when the viewer asks. Scribe, for its part, contains no knowledge that the viewer
  exists.

  Which means the viewer is optional in the strict sense: delete it and you lose exactly the
  three conveniences listed above, and nothing else. Every capability it has, you can reach by
  typing.

  The pipe at the top of this section is the proof of that, and it is why it is documented
  first. If scribe view … | xed - stops being enough for you, the viewer is there. If it never
  does, you have lost nothing at all.



