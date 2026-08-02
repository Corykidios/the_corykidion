# the_corykidion

A portable skill that lets any AI agent read and write holons in Cory Childs'
TheBrain archive, plus the single-file tool that does the work.

Several personas run on several different runtimes — Claude Code, Codex CLI,
Gemini CLI, Letta agents, a bare shell — and they all need to write into the
same archive in the same shape. This repository is that shared protocol.

## Layout

```
SKILL.md                     the skill itself — start here
kidion.py                    the tool: stdlib only, zero install
reference/type-registry.md   all 48 holon types, markers, shrines, open questions
reference/brain-api.md       endpoints confirmed working, and the ones that aren't
legacy/                      the earlier Python package, preserved
```

## Install

Copy `kidion.py` anywhere. That is the whole install. It imports nothing
outside the standard library, deliberately: every `pip install` is a place
where one of the runtimes falls off.

Then, once per machine:

1. TheBrain → **Settings → Local API** → switch on, copy the key
2. Create `~/.corykidion/config.json`:
   ```json
   {"endpoint": "http://localhost:8001/api", "api_key": "PASTE_KEY_HERE"}
   ```
3. `python kidion.py brains`

`CORYKIDION_ENDPOINT` and `CORYKIDION_API_KEY` work instead of the file.

## Using it as a skill

**Claude Code / Cowork** — drop the repo into a skills directory; `SKILL.md`
carries its own frontmatter.

**Anything else** — paste `SKILL.md` into the system prompt or hand it over as
a document. It is written to be read cold by an agent that has never seen the
archive, and it names the routing rule and the non-negotiables explicitly.

## Quick tour

```bash
python kidion.py brains                    # what archives exist
python kidion.py shrines                   # all 48 types and where they live
python kidion.py shrines --family souls    # just one family
python kidion.py where --type tool         # where does a repo entry go?

python kidion.py put --type tool \
  --name "owner/repo" \
  --definition "one line about it" \
  --note nature.md --tag some-tag

python kidion.py peek --thought <id>
python kidion.py note --thought <id>
python kidion.py find "coro"
python kidion.py accounts
python kidion.py activities

python kidion.py visit --thought <id> \
  --visitor "Your Name" \
  --state "what this place remembers now" \
  --muse clio="what it is" --muse calliope="what happened"
```

Shrine routing is **discovered live** by walking the graph, not hardcoded. If
the archive is renamed or rebuilt, the tool follows without a code change.

## Design notes

**Why a single file instead of the package in `legacy/`.** The legacy package
is better architected in several real ways — a plan/approve/apply write
pipeline, a write journal, a safety gate, a proper test suite, and a
deliberate boundary keeping private-world specifics out of the source. It is
worth returning to if this ever needs to grow up.

It is also a `pip install` with a `src/` layout and a config format that
differs from what is already on disk, and it deliberately refuses to encode
the forty-eight types or the shrine geography — which is precisely what the
personas need to share. The trade taken here is portability and world-carrying
over ceremony. If write safety starts to matter more than reach, invert it.

**Verification is not optional.** Every write path reads back and confirms
before reporting success. TheBrain commits notes asynchronously, so a naive
read-after-write returns empty and makes every successful write look broken.
Do the thing, then check the thing, then say the thing was done.

**Unsettled markers are refused, not guessed.** Eight of the forty-eight types
have genuinely open markers because of specific collisions documented in
`reference/type-registry.md`. `kidion.py` will not construct a name for those
without an explicit `--marker` override. Inventing structure that isn't there
is worse than stopping.

## License

MIT. See `LICENSE`.

Not affiliated with or endorsed by TheBrain Technologies.
