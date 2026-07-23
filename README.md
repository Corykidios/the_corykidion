# The Corykidion

A small, local-first, read-only-first bridge between AI agents and [TheBrain](https://www.thebrain.com/).

It talks to TheBrain's desktop app over its local HTTP API — the one that only exists while the app is open on your machine — and gives an agent a narrow, honest set of things it can do: check that a Brain is open, look up one Thought, list the Brains you have, and check whether a URL is already attached somewhere before creating a duplicate. That's it, today. Nothing here writes to your Brain yet, and nothing here pretends to do more than it can prove.

Not affiliated with or endorsed by TheBrain Technologies.

## Why this exists

Before any code was written, this project surveyed eighteen public repositories that touch TheBrain in some way — MCP servers, SDKs, migration scripts, a PowerShell audit tool, a UUID codec — to find out which ideas were actually worth building on. That survey is preserved in full in [`WORKING_ARCHITECTURE.md`](WORKING_ARCHITECTURE.md): what each repo got right, what it got wrong, and what specifically was worth reusing versus rejecting. Nothing from those eighteen repos was copied wholesale into this one. A few patterns were mined; most were left where they were.

The short version of what that survey found: most of those eighteen repos are bound to TheBrain's *cloud* API, which can't reach a Brain that only exists on your machine. A few write directly to TheBrain's private files, which is a fast way to corrupt a decade of notes. One official repository — [`TheBrainTech/send-to-thebrain`](https://github.com/TheBrainTech/send-to-thebrain) — turned out to be the most trustworthy foundation: it's TheBrain's own reference implementation of the local API, and everything this package's client does is built directly against what that repository documents.

## What actually works right now

| Capability | What it does |
|---|---|
| `status` | Confirms TheBrain's desktop app is reachable, reports which Brain is currently open, and lists every Brain visible on the machine. |
| `thought get` | Retrieves one Thought by ID: its name and label. |
| `thought find-url` | Checks whether a URL is already attached to something in a Brain — the same dedup trick the official browser extension uses, so you don't create the same Thought twice. |
| `export thought` | Writes a deterministic, provenance-stamped JSON snapshot of one Thought. This is a projection for inspection, not a backup — TheBrain's own dated backups remain the source of truth. |
| `capabilities` | Lists exactly what's implemented versus what's planned, so you (or an agent) never have to guess. |

Everything else that sounds like it should exist — searching Thoughts by name, reading notes, walking links, exploring neighbors — is deliberately **not implemented yet**. TheBrain states that its local API "speaks the same shape" as its documented cloud API, which makes those operations *plausible*, but no source available while building this had a captured request/response for them against a real local instance. Rather than guess at a shape and ship something that quietly breaks on a real Brain, this package registers those operations as known-but-unverified and refuses to call them — you'll get a clear `CapabilityUnknown` error instead of a wrong answer. Run `corykidion capabilities` to see the live list of what's evidenced versus what's still candidate.

There is also no write path. Creating Thoughts, attaching URLs, adding notes — all of that is designed for (see the Phase 2 section of the architecture ledger) but not built, on purpose. A tool that only reads is much cheaper to trust.

## Installing it

You need Python 3.11 or later and a running copy of TheBrain's desktop app (version 15.0.534+, which is when the local API shipped).

```bash
git clone https://github.com/Corykidios/the_corykidion.git
cd the_corykidion
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # macOS/Linux
pip install -e ".[dev]"
```

Then find your local API endpoint and key: open TheBrain, go to **Settings → User → Local API**, and copy both the endpoint (something like `http://localhost:52341/api`) and the API key.

Set them as environment variables:

```bash
set CORYKIDION_ENDPOINT=http://localhost:52341/api      # Windows (cmd)
set CORYKIDION_API_KEY=your-key-here

$env:CORYKIDION_ENDPOINT = "http://localhost:52341/api" # Windows (PowerShell)
$env:CORYKIDION_API_KEY = "your-key-here"
```

...or copy [`examples/config.example.toml`](examples/config.example.toml) to `config.toml` (already `.gitignore`'d — it will never accidentally get committed) and fill in your own values.

Then:

```bash
corykidion status
```

If TheBrain isn't running, you'll get a plain-English error telling you so, not a stack trace.

## Using it

```bash
# What's open, what's visible
corykidion status

# One Thought, by Brain ID and Thought ID
corykidion thought get <brain-id> <thought-id>

# Has this URL already been captured somewhere in this Brain?
corykidion thought find-url <brain-id> "https://example.com/some-article"

# A deterministic JSON snapshot of one Thought
corykidion export thought <brain-id> <thought-id> out/thought.json

# What's implemented vs. still candidate
corykidion capabilities

# Restrict every operation to a specific Brain, refusing anything else
corykidion --allow-brain <brain-id> status
```

It's also a plain Python library, if you'd rather call it from your own agent code than shell out:

```python
from corykidion.client import LocalBrainClient
from corykidion.config import load_config
from corykidion.read import ReadModel

config = load_config()  # reads env vars, or pass a path to a TOML file
read_model = ReadModel(LocalBrainClient(config))

status = read_model.connectivity()
print(f"{status.brain_count} brains visible, active: {status.active_brain_id}")
```

## How it's put together

The short version: a configuration boundary that keeps your endpoint and API key out of source control, a minimal HTTP client that speaks exactly four documented endpoints and nothing else, a capability registry that fails closed on anything unverified, a safety gate that enforces target scope independent of whatever transport is calling it, a read model that composes all of that into agent-useful calls, and a CLI on top. Every one of those pieces is unit-tested against fabricated fixtures — the test suite never touches a real network socket or a real Brain.

```text
src/corykidion/
  config.py         configuration boundary — env vars or a gitignored TOML file
  client.py         the local API client — four evidenced endpoints, stdlib only
  capabilities.py   the evidenced/candidate registry — fails closed by design
  safety.py         target-scope enforcement, independent of transport
  read.py           the agent-facing read model
  export.py         deterministic, provenance-stamped JSON export
  cli.py            the CLI transport
tests/
  contract/         client, capability, read-model, and export tests
  safety/           config and safety-gate tests
  fixtures/         fabricated responses — nothing here is a real Brain
```

Run the tests yourself:

```bash
pytest
```

For the full reasoning behind these choices — including the fifteen safety invariants this package holds itself to, and why certain donor-repository patterns were adopted or rejected — see:

- [`WORKING_ARCHITECTURE.md`](WORKING_ARCHITECTURE.md) — the living design ledger, including the full eighteen-repository survey and disposition table.
- [`docs/decisions/0001-phase-1-implementation.md`](docs/decisions/0001-phase-1-implementation.md) — the specific decisions (language, transport, capability scope) that turned that ledger into this codebase.

The short version of the safety posture: loopback-only by default, read-only by default, no ambient targets (every call names its Brain explicitly), no writing to TheBrain's private files under any circumstances, and no transport — CLI, library, or a future MCP server — is ever allowed more authority than the core safety gate grants it.

## What this is not

- Not a replacement for TheBrain, its sync service, or its native backups.
- Not a credential broker, a SQLite writer, or an autonomous bulk editor.
- Not affiliated with, endorsed by, or supported by TheBrain Technologies.
- Not finished. Read `corykidion capabilities` before assuming something works.

## Contributing to it

The most useful thing you can do right now is run this against a real, disposable test Brain and capture what `thought.search`, `thought.notes`, and neighbor traversal actually return — then turn that into a fixture and a contract test, and promote the capability from candidate to evidenced (the procedure is documented in `capabilities.py`). Adding an endpoint without a fixture and a test is exactly the pattern this project surveyed eighteen other repositories to avoid repeating.

## License

MIT. See [`LICENSE`](LICENSE).

---

*The technical ledger stops here. Everything above is meant to stay accurate and a little dry on purpose — it's the part a stranger, or an agent, needs to trust before touching your Brain. What this project means, what to call the things it talks to, the story of the eighteen repos and the one that turned out to matter — that part's still unwritten, and it's not this document's to write.*
