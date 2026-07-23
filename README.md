# The Corykidion

A small, local-first, read-only-first bridge between AI agents and [TheBrain](https://www.thebrain.com/).

It talks to TheBrain's desktop app over its local HTTP API — which is only reachable while the app is open on your machine. It can check that a Brain is open, look up a Thought, search by name, retrieve a Thought's full context (parents, children, jumps, links, attachments) and notes, check recent activity, and export a deterministic snapshot. It also has a write pipeline — attaching URLs, activating Thoughts, and creating Thoughts — that is fully built and unit-tested but has not yet been run against a real Brain. Every capability this package does not fully support is documented as unsupported rather than left ambiguous.

Not affiliated with or endorsed by TheBrain Technologies.

## Why this exists

Before any code was written, this project surveyed eighteen public repositories that touch TheBrain in some way — MCP servers, SDKs, migration scripts, a PowerShell audit tool, a UUID codec — to determine which ideas were worth building on. That survey is preserved in full in [`WORKING_ARCHITECTURE.md`](WORKING_ARCHITECTURE.md): what each repository got right, what it got wrong, and what specifically was worth reusing versus rejecting. No code from those eighteen repositories was copied into this one. A small number of design patterns were reused, with attribution recorded in the ledger; most repositories contributed nothing directly.

Summary of what that survey found: most of the eighteen repositories are bound to TheBrain's *cloud* API, which cannot reach a Brain that exists only on your machine. Several write directly to TheBrain's private files, which risks corrupting the Brain's stored data. One official repository — [`TheBrainTech/send-to-thebrain`](https://github.com/TheBrainTech/send-to-thebrain) — was judged the most reliable foundation: it is TheBrain's own reference implementation of the local API, and this package's client is built directly against the endpoints that repository documents.

## What actually works right now

### Reads

Every read below has been verified against a real, running TheBrain instance, not just against fixtures.

| Capability | What it does |
|---|---|
| `status` | Confirms TheBrain's desktop app is reachable, reports which Brain is currently open, and lists every Brain visible on the machine. |
| `thought get` | Retrieves one Thought by ID: its name and label. |
| `thought find-url` | Checks whether a URL is already attached to something in a Brain, using the same duplicate-detection approach as the official browser extension, so you don't create the same Thought twice. |
| `thought search` | Searches Thoughts by name/label within a Brain. |
| `thought graph` | Retrieves a Thought's full context in one call: identity, parents, children, jumps, links, and attachment metadata. |
| `thought notes` | Retrieves a Thought's note content. |
| `activity` | Lists a Brain's recent modification-log entries, newest first. |
| `export thought` | Writes a deterministic, provenance-stamped JSON snapshot of one Thought. This is a projection for inspection, not a backup — TheBrain's own dated backups remain the source of truth. |
| `capabilities` | Lists exactly what's implemented versus what's planned, so you (or an agent) never have to guess. |

Two capabilities remain unresolved even after live testing: `thought.links` and `thought.neighbors` are retired as separate operations, because `thought graph`'s response already contains both (TheBrain's link model is parent/child/jump, so links and neighbors are the same data). Calling either old name now points you to `thought graph` instead of failing silently.

### Writes

A write pipeline exists — plan, explicit approval, journal, apply, read-back verification — implemented in `src/corykidion/operations.py` and covered by unit tests against fabricated fixtures. It has not been run against a real Brain.

| Capability | What it does | Status |
|---|---|---|
| `write attach-url` | Attaches a URL to a Thought. | Route and parameters documented by TheBrain's own reference client; not yet exercised live. |
| `write activate` | Activates (opens/focuses) a Thought. | Route documented by TheBrain's own reference client; not yet exercised live. Verification is Brain-level only — no evidenced endpoint currently exposes which specific Thought is active. |
| Create a Thought | Available as a library call (`WriteOperations.plan_create_thought`), not exposed on the CLI yet. | The route is documented; the request body schema is not verified against a real instance. The caller must supply the complete body explicitly — this package will not guess field names for a write. |

Both CLI write subcommands require `--approve` and `--journal PATH` explicitly. There is no default-approve path, and no write happens without both.

Two more writes described in the design ledger — appending a note and creating a link directly — have no verified request shape at all and are not implemented.

Run `corykidion capabilities` for the live, authoritative list of what's evidenced versus what's still unverified.

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

A configuration boundary that keeps your endpoint and API key out of source control; a minimal HTTP client that speaks exactly the documented endpoints and nothing else; a capability registry that fails closed on anything unverified and flags which operations mutate data; a safety gate that enforces target scope and, for writes, requires explicit opt-in independent of whatever transport is calling it; a read model and a write-operations pipeline (plan, approve, journal, apply, verify) built on top of that; and a CLI. Every one of those pieces is unit-tested against fabricated fixtures — the test suite never touches a real network socket or a real Brain.

```text
src/corykidion/
  config.py         configuration boundary — env vars or a gitignored TOML file
  client.py         the local API client — eleven evidenced endpoints, stdlib only
  capabilities.py   the evidenced/candidate registry — fails closed by design
  safety.py         target-scope and write-gate enforcement, independent of transport
  read.py           the agent-facing read model
  operations.py     the Phase 2 write pipeline: plan, approve, journal, apply, verify
  export.py         deterministic, provenance-stamped JSON export
  cli.py            the CLI transport
tests/
  contract/         client, capability, read-model, export, and operations tests
  safety/           config and safety-gate tests
  fixtures/         fabricated responses — nothing here is a real Brain
```

Run the tests yourself:

```bash
pytest
```

For the full reasoning behind these choices — including the fifteen safety invariants this package holds itself to, why certain donor-repository patterns were adopted or rejected, and exactly what was and wasn't verified against a real running instance — see:

- [`WORKING_ARCHITECTURE.md`](WORKING_ARCHITECTURE.md) — the living design ledger, including the full eighteen-repository survey and disposition table.
- [`docs/decisions/0001-phase-1-implementation.md`](docs/decisions/0001-phase-1-implementation.md) — the language, transport, and initial capability-scope decisions.
- [`docs/decisions/0002-live-verified-read-capabilities.md`](docs/decisions/0002-live-verified-read-capabilities.md) — what was verified live against a running local API, what was probed and blocked, and how the write pipeline is scoped.

The short version of the safety posture: loopback-only by default, read-only by default, no ambient targets (every call names its Brain explicitly), no writing to TheBrain's private files under any circumstances, and no transport — CLI, library, or a future MCP server — is ever allowed more authority than the core safety gate grants it.

## What this is not

- Not a replacement for TheBrain, its sync service, or its native backups.
- Not a credential broker, a SQLite writer, or an autonomous bulk editor.
- Not affiliated with, endorsed by, or supported by TheBrain Technologies.
- Not finished. Read `corykidion capabilities` before assuming something works.

## Contributing to it

Two things are most useful right now. First, capturing the request body TheBrain's own desktop app sends when creating a Thought by hand (so `thought.create`'s write body can be verified instead of left as a caller-supplied dict). Second, running one supervised live write — `write attach-url` or `write activate` — against a disposable test Brain, with `--approve` and a real journal file, to confirm the write pipeline behaves the same outside of fixtures as it does inside them. Either way: capture the real shape, turn it into a fixture, add a contract test, and only then promote the capability (the procedure is documented in `capabilities.py`). Adding an endpoint without a fixture and a test is exactly the pattern this project surveyed eighteen other repositories to avoid repeating.

## License

MIT. See [`LICENSE`](LICENSE).
