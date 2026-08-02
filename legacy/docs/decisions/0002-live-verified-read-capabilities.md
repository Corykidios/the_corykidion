# ADR 0002: live verification pass, read-capability promotion, and the Phase 2 write pipeline

**Date:** 2026-07-23
**Status:** accepted
**Affects:** capability registry, client, read model, CLI, a new `operations.py`

## Context

ADR 0001 deliberately shipped a narrow read slice: four endpoints evidenced
from TheBrainTech/send-to-thebrain's documentation, with search, notes,
neighbor traversal, and activity registered as unverified candidates rather
than implemented against a guessed shape.

The operator then made TheBrain's real running local API available for this
implementation to call directly, and asked for the remaining candidates to
be resolved and for Phase 2 (writes) to be built out, not left as a
standing "candidate" list.

## What was verified live, and how

Every probe below was a **read-only GET** against a real, running local API
instance, using the operator-supplied endpoint and API key. Responses were
observed, captured, and turned into fabricated fixtures under
`tests/fixtures/` — the real Brain content itself (thought names, note text,
brain IDs) is not stored anywhere in this repository, per the product
boundary's rule against publishing private Brain structure.

| Capability | Method verified | What was learned |
|---|---|---|
| `thought.search` | `GET /search/{brainId}?queryText=&maxResults=` | A 400 with `{"errors":{"queryText":["...required"]}}` first confirmed the parameter name, then a real query returned an array of `{"sourceThought": {...}, "name", "isFromOtherBrain", ...}` |
| `thought.graph` | `GET /thoughts/{brainId}/{thoughtId}/graph` | Full compound context in one call: `activeThought`, `parents`, `children`, `jumps`, `siblings`, `tags`, `type`, `links`, `attachments`. This single endpoint covers what the original ledger split into three separate future capabilities — see "Design consequence" below. |
| `thought.notes` | `GET /notes/{brainId}/{thoughtId}` | `{"brainId", "sourceId", "sourceType", "modificationDateTime", "markdown", "html", "text"}`. An empty note returns `markdown=""`, not a 404. |
| `activity.recent` | `GET /brains/{brainId}/modifications?maxLogs=` | A 400 first confirmed the parameter is `maxLogs`, not `maxLogItems` as originally guessed in the ledger's own prose; a real call returned an array of raw modification-log entries. |

A fifth probe, `GET /attachments/{brainId}/{thoughtId}`, returned HTTP 200
but the app's own SPA shell (`index.html`), not JSON — that path is not a
real API route; it fell through to a catch-all. Per-Thought attachment
metadata is available anyway, via the `attachments` array already present
in the `thought.graph` response, so no separate endpoint was needed.

## Design consequence: `thought.links` and `thought.neighbors` are retired as separate capabilities

The original ledger listed "notes and attachment metadata," "bounded
neighbor exploration," and "link enumeration" as three distinct future
reads. Live evidence shows they are one endpoint: TheBrain's link model
*is* parent/child/jump, so a Thought's neighbors and its links are the same
underlying data. `thought.graph` now covers all three. `thought.links` and
`thought.neighbors` remain in `CANDIDATE_CAPABILITIES` only so that calling
either by name raises a helpful "superseded — use thought.graph" message
instead of a bare "not registered."

## What was not verified, and why

The operator's request included finishing Phase 2 (writes). This codebase
already had route-level evidence for three writes from
TheBrainTech/send-to-thebrain's own documentation: `POST /thoughts/{brainId}`
(create Thought), `POST /attachments/{brainId}/{thoughtId}/url` (attach
URL, with documented query parameters `url` and `name`), and
`POST /app/brain/{brainId}/thought/{thoughtId}/activate`.

An attempt was made to verify `thought.create`'s request *body* schema
safely — by sending an intentionally invalid/empty body, the same technique
that successfully revealed `queryText` and `maxLogs` as required parameter
names for the read endpoints above, on the theory that ASP.NET's model
validation runs before a handler's side effects. That attempt was blocked
before it ran, by policy, correctly: it was still an unreviewed POST
against a live personal Brain, and probing-via-deliberate-failure is not
the same guarantee for a write as it is for a read. Two `OPTIONS` requests
(to `/notes/{brainId}/{thoughtId}` and `/links/{brainId}`) were tried as a
non-mutating alternative; the server does not return route-specific `Allow`
headers, so that path was a dead end too.

**Decision:** `thought.create`'s route and method are registered as
evidenced (for routing/dispatch purposes); its request body is explicitly
documented as unverified everywhere it appears — the capability registry's
`evidence` string, the client method's docstring, and the operations
module's `plan_create_thought` docstring all say so. `WriteOperations.plan_create_thought`
requires the caller to supply the complete body dict themselves; nothing in
this codebase invents, defaults, or guesses field names for it.
`note.append` and `link.create` have no route-level evidence at all and
remain full candidates.

No live write was executed against the operator's real Brains during this
pass. The write pipeline below was built and tested entirely against
fabricated fixtures.

## The Phase 2 write pipeline

`src/corykidion/operations.py` implements the exact pattern
WORKING_ARCHITECTURE.md specified and this codebase had not yet built:

```text
request -> resolve target -> plan -> preview -> scoped approval
        -> journal -> apply bounded steps -> read-back verification -> receipt
```

- `WriteOperations.plan_*` methods are pure and side-effect-free; producing
  a plan never touches the network.
- `WriteOperations.apply(plan, approved=...)` is the only method that does.
  It raises `SafetyViolation` if `approved` is not `True`, and separately
  raises if the `SafetyGate` it was constructed with is not explicitly
  write-enabled (`SafetyGate(read_only=False)`) — a `WriteOperations`
  constructed without an explicit gate defaults to the same read-only
  `SafetyGate()` every other part of this codebase defaults to.
- Every apply journals before dispatch, after dispatch, and after
  verification, to an append-only JSON-lines file (`JournalWriter`) that
  never contains the API key or endpoint.
- Verification is operation-specific and honestly scoped: attaching a URL
  is verified by reading it back via `attachment.by_location`; creating a
  Thought is verified by reading the new Thought back by the ID the create
  call returned; activating a Thought can only be verified at the
  Brain level (`app.state` confirms the right Brain is open) because no
  evidenced endpoint currently exposes which *Thought* is active — the
  receipt's `verification_note` says this explicitly rather than reporting
  an unqualified `verified=True`.
- The CLI exposes `corykidion write attach-url` and `corykidion write
  activate`, both requiring `--approve` and `--journal PATH` explicitly.
  `create-thought` is deliberately not exposed as a CLI command yet — its
  body schema is unverified, and a CLI flag combination would invite
  guessing at field names in a way a library call, where the caller must
  construct the dict themselves, does not.

## Next test or action

Whoever next has live write access and operator consent should: verify
`thought.create`'s actual required body fields (ideally by capturing the
UI's own outgoing request when creating a Thought by hand, rather than by
probing the API destructively), and attempt `note.append` / `link.create`
discovery the same way. Both should get fixtures and contract tests before
being promoted, exactly like the read endpoints in this pass.
