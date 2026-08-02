# ADR 0001: Phase 0/1 implementation choices

**Date:** 2026-07-23
**Status:** accepted
**Affects:** implementation language, first transport, initial capability set

## Context

WORKING_ARCHITECTURE.md left several "immediate decisions waiting for
evidence" open, including implementation language, first transport, and
which local-API behavior to trust before writing code against it. This ADR
records the choices made to move from ledger to a working Phase 0/1 core,
and why.

## Decisions

**Language: Python 3.11+.** Matches the rest of this operator's tooling
(other repos under the same account lean on Python + httpx-family stacks
for MCP servers and local watchers), keeps the dependency footprint at
zero for the core (standard library only — `urllib`, `tomllib`,
`dataclasses`), and makes a future stdio MCP transport a thin addition
rather than a rewrite.

**First transport: CLI + library, not MCP.** The ledger's own invariant 15
("transport does not enlarge power") only holds if the core's safety
boundary is proven before a transport sits on top of it. A CLI is the
cheapest way to exercise that boundary by hand. An MCP stdio adapter
remains a near-term candidate once the CLI has seen real use against a
running local API — see "Still unresolved" in WORKING_ARCHITECTURE.md.

**Capability set: four evidenced endpoints only.** `GET /app/state`,
`GET /brains`, `GET /thoughts/{brainId}/{thoughtId}`, and
`GET /attachments/{brainId}/by-location` are documented, with request/response
shape, in TheBrainTech/send-to-thebrain's README (donor #14 — "canonical
prior art for the local client"). TheBrain's own announcement post states
the local API "speaks the same shape" as the cloud API at api.bra.in, which
makes search, notes, links, and neighbor traversal *plausible* — but no
source available to this implementation pass showed a captured request or
response for those endpoints against a running local instance. They are
registered as candidates in `capabilities.py` and raise `CapabilityUnknown`
if called, rather than being implemented against a guessed shape. This is a
direct application of safety invariant 3 ("supported API before private
storage") to the client itself, not just to storage.

**No write path.** Phase 2 (bounded constructive writes: create Thought,
create link, append note, attach URL) is deliberately not attempted in this
pass, consistent with "no destructive first release." `SafetyGate.assert_write_allowed()`
exists now, unused, so Phase 2 has a gate to plug into rather than
improvising one under time pressure later.

**README now exists.** Per the ledger's own maintenance rule ("a README
when the project can truthfully say what can be installed or run"): after
this pass, that's true — `pip install -e .` plus a config file or env vars
gets you a working `corykidion status` against a real local API, and a
passing test suite that never touches a socket. See root `README.md`.

## Consequences

- The four evidenced endpoints only cover connectivity checks, single-Thought
  retrieval, brain listing, and URL-dedup lookup. That is a real but modest
  read slice — not the full "search; Thought retrieval; notes and attachment
  metadata; compound context; bounded neighbor exploration" scope Phase 1
  aspired to in the ledger. Promoting a candidate capability requires
  verifying it against a running local API response first (see
  `capabilities.py` docstring for the promotion procedure).
- Anyone extending this package inherits the fail-closed pattern: adding an
  endpoint means adding a fixture, a contract test, and a capability-registry
  entry together, not just a new client method.
