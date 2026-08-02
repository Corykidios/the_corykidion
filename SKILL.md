---
name: corykidion
description: Read and write holons in Cory Childs' TheBrain archive. Use when asked to catalogue a repo/tool/source, record research findings, file something into the archive, look up where a holon type belongs, or perform a visit. Covers the local API, the holon format, the 48-type registry, and shrine routing.
---

# Corykidion

You have hands in a real archive. This skill teaches you to use them without
breaking anything and without inventing structure that isn't there.

## What this is

Cory Childs keeps a knowledge archive in **TheBrain** (a graph database with a
desktop client). The archive is not a filing cabinet — it has a geography, a
grammar, and a fixed vocabulary of forty-eight types. Several different AI
personas write into the same archive from different runtimes. This skill is the
shared protocol so that what you write is legible to the ones who come after.

**Only one agent should touch the archive at a time.** There is no locking. If
you are unsure whether another session is active, ask before writing.

## Setup (once per machine)

The tool is a single stdlib-only Python file, `kidion.py`. No install.

1. In TheBrain: **Settings → Local API**, switch it on, copy the key.
2. Create `~/.corykidion/config.json`:
   ```json
   {"endpoint": "http://localhost:8001/api", "api_key": "PASTE_KEY_HERE"}
   ```
   Or set `CORYKIDION_ENDPOINT` and `CORYKIDION_API_KEY` instead.
3. Verify: `python kidion.py brains`

Never print the key, never paste it into chat, never pass it as an argument.

## The shape of the archive

One **Archive** exists conceptually. **Accounts** are the concrete stores that
touch it — a Brain, a vault, a repo, an agent profile. The main archive is
`we_tiripodiko`; the tool defaults to it.

Inside, the geography is Mycenaean. Ten top-level categories: a river centre
(`0: Anawaro`) holding three port towns, then nine islands across the Scaled
Seas, each named for a landfall in the *Orphic Argonautica*, ending at
`9: Koki` (Colchis).

Every category is quartered into **shrines** — 12 in the port towns, 36 across
the islands, **48 total**, one per holon type. This is the routing rule:

> **Every holon has exactly one type, and every type has exactly one shrine.
> If you don't know where something goes, its type tells you.**

Use `python kidion.py shrines` to see all 48 live. Do not hardcode the list —
the tool discovers it by walking the graph, so it stays correct if Cory
rebuilds.

Off the Archive holon hang two jump regions:

- **`^ Accounts`** — one per store. `:0: Memento Meri` is the hidden zeroth
  account; do not write there unless told to.
- **`^ Activities`** — four states a holon can be pulled into when withdrawn
  from participation: `Preactives` (never yet active, activation intended),
  `Unactives` (was active, temporarily withdrawn, return intended),
  `Deactives` (retired, no future participation intended — *not* deletion,
  history is preserved), `Activating` (ready to participate, not yet
  reconnected). Nothing is ever orphaned; a holon disconnected from its place
  connects here instead.

## The holon format

Two separate systems. Don't conflate them.

**Anatomy** is what the *name line* may contain:

```
<Marker> <Moniker>: <Definition> [<Description>]
```

- **Marker** — read logically. Opens the line and carries the Type. A *Free*
  marker is punctuation plus a space (`. ` types a term). A *Fixed* marker ends
  in a colon and carries durable identity (`A: ` types a cosmos).
- **Moniker** — read lexically. Ordinary language.
- **Definition** — after `: `, an inline explanation.
- **Description** — in brackets: translation, transliteration, glyph.

**Attribution** is what the *note* records, as a YAML block at the top. Twelve
properties in three tetrads:

```yaml
---
name: + owner/repo: what it is
type: tool
nature: true
tags: [example, another]
parents: [2.4: North Tool Shrine]
children: []
siblings: []
relatives: []
awakened: 2026-08-02T02:10:04
altered: 2026-08-02T02:10:04
accessed: 2026-08-02T02:10:04
activity: active
---
```

- **Being** — name, type, nature, tags. Minimum for existence is name + type.
- **Bonding** — parents, children, siblings, relatives. These map onto
  TheBrain's own relation types; `relatives` is the Jump relation.
- **Becoming** — awakened (first recordable existence, **never rewrite it**),
  altered, accessed, activity.

Below the block comes the **Nature**: an *Explanation* (the body) and an
*Extension* (References pointing outward to sources, Relevancies pointing
inward as reading guidance).

`kidion.py put` generates the Attribution block for you. Write the Nature.

## Cataloguing a repo or tool

The common task. A GitHub repository is a **tool** (marker `+`), named by its
`owner/repo` slug — not the full URL, which is ugly and not the object.

```bash
python kidion.py put --type tool \
  --name "Blushyes/coro-code" \
  --definition "Rust CLI coding agent with a rich terminal UI" \
  --note nature.md --tag ship-candidate --tag rust
```

The Nature file should carry, in order:

1. **A verdict.** One of four: `not` (irrelevant, unfinished, dangerous, or
   the weaker sibling of something already covered — these don't get filed at
   all), `THOT` (interesting, no current use), `HOT` (exciting, relevant), or
   `GOT!` (forgetting it would cost something real).
2. **Technological account** — what it actually is. Language, architecture,
   install path, license, dependencies.
3. **Functional account** — what it's *for*, here, in this system.
4. **Opinion** — yours, plainly. Strong is fine. Funny is fine. Hedging is not.
5. **The full README**, if useful, as the body of the Explanation.
6. **Extension** — References (always the source URL) and Relevancies.

**Never grade a repo you haven't actually opened and read.** Reporting that
something is uninteresting when it would have mattered is the expensive
failure mode here — much worse than being slow. If you didn't read it, say so
instead of guessing from the name.

## Doing a visit

A visit is a read-and-record cycle: refresh the timestamps, append a numbered
block with Muse expression channels, and close with a carried-forward state
line that the next visitor will read.

```bash
python kidion.py visit --thought <id> --visitor "Your Name" \
  --state "what this place remembers after this visit" \
  --muse clio="what the object is" \
  --muse calliope="what happened here"
```

The nine Muses and their media: thalia (2D art), clio (informative prose),
calliope (narrative prose), terpsichore (dance), melpomene (theatre), erato
(poetry), euterpe (music), polyhymnia (sculpture/3D), ourania (worldbuilding).

## Rules that are not negotiable

1. **Run before you report.** Do the write, read it back, *then* say it's done.
   Every write path in `kidion.py` verifies by reading back; trust that, not
   your expectation.
2. **Never rewrite `awakened`.** It is the holon's first recordable existence.
3. **Flag inference as inference.** This archive distinguishes what Cory said
   from what an assistant elaborated. If you're guessing, label it.
4. **Do not invent a Marker.** Several types have genuinely unsettled markers
   (see `reference/type-registry.md`). The tool refuses those on purpose. Ask
   rather than pick.
5. **Deactive is not delete.** Withdrawal preserves history.
6. **One agent at a time.**

## Reference

- `reference/type-registry.md` — all 48 types, families, markers, and the
  specific open conflicts
- `reference/brain-api.md` — endpoints confirmed working, and the ones that
  don't
- `legacy/` — an earlier, fuller Python package (plan/approve/apply pipeline
  with a write journal). Not required; worth reading if this skill needs to
  grow up.
