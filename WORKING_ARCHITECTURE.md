# The Corykidion: Working Architecture Ledger

**Status:** pre-implementation working document  
**First recorded:** 2026-07-21  
**Repository:** [`Corykidios/the_corykidion`](https://github.com/Corykidios/the_corykidion)

The Corykidion is a proposed, independent integration layer between AI agents and [TheBrain](https://www.thebrain.com/). Its initial direction is a small, local-first, read-only-first system built over TheBrain's supported local API. It should make a selected Brain useful to an agent without treating an existing third-party repository as the whole product and without making unsafe assumptions about TheBrain's private storage.

This is a living orientation document, not a claim that working software already exists. It records the evidence surveyed so far, the parts currently imagined, the safety constraints already earned, and the decisions that remain open.

The Corykidion is not affiliated with or endorsed by TheBrain Technologies.

## How to read this ledger

Entries use the following maturity labels:

- **Evidence:** observed in source, official examples, or documented API behavior.
- **Direction:** the present design choice; strong enough to build toward, but still revisable.
- **Candidate:** a plausible part or structure that has not yet earned implementation.
- **Deferred:** potentially useful, but deliberately excluded from the first working core.
- **Rejected:** examined and intentionally excluded.
- **Unresolved:** a boundary or choice that must remain visible until evidence or use clarifies it.

## Product boundary

### Current public-core rule

**Direction:** the repository should contain reusable software, neutral documentation, and fabricated examples. It must not encode a particular user's private archive, named agents, fictional world, business structure, Brain IDs, credentials, schedules, permissions, or personal deployment topology.

An operator may supply those things through private configuration outside the repository. The software should consume explicit configuration; it should never infer a private world from branding, bundled examples, or hidden defaults.

Until the boundary is fully designed, use these conservative rules:

1. Prefer a narrow general abstraction over a project-specific one.
2. Put deployment facts in ignored local configuration, not source.
3. Use obviously fabricated data in tests and examples.
4. Record where an idea came from without importing private context with it.
5. Do not publish secrets, personal records, private Brain structure, or identifying exports.
6. Do not invent a generalized feature merely to preserve symmetry with one deployment.

### Still unresolved

- Whether optional deployment adapters belong here or in separate private repositories.
- Whether the first public interface should be a library, CLI, stdio MCP server, or a small combination of those.
- Whether cloud API support should ever exist; it is not required for the local-first core.
- Which operating systems the first supported release will promise.
- The implementation language and package structure.
- The final license, including compatibility with any reused code.
- How much multi-Brain coordination is broadly useful rather than specific to one operator.

## Current thesis

> Build one small, local, read-only-first bridge over TheBrain's supported local API. Let existing repositories donate well-understood parts; let none of them become the body.

The first useful system should:

- connect only to an explicitly selected local TheBrain instance;
- expose compact, agent-useful reads rather than a raw explosion of API calls;
- default to read-only and fail closed when a capability is unknown;
- separate planning from mutation;
- journal, verify, and report every approved write;
- support deterministic import and export without writing TheBrain's private database directly;
- keep MCP or any other transport outside the trusted core rather than making the protocol adapter the architecture.

The Corykidion is **not** intended to be:

- a replacement for TheBrain, its sync service, or its native backups;
- a hosted credential broker;
- a direct SQLite or private-file writer;
- an autonomous bulk editor with ambient authority;
- a persona or agent-identity framework;
- a public mirror of a private Brain;
- a second canonical database disguised as an export cache.

## Access routes found in the surveyed repositories

The eighteen surveyed repositories are not eighteen interchangeable MCP servers. They divide into four access families:

| Access family | Repositories | Architectural consequence |
|---|---:|---|
| TheBrain cloud API (`api.bra.in`) | 1-5, 8, 9, 12 | Cannot reach an unsynced local-only Brain; introduces cloud credential and custody concerns. |
| TheBrain local HTTP API | 10, 13, 14 | Best-supported route for the initial local-first core while the desktop app is running. |
| Direct files, exports, or ID formats | 7, 11, 16, 18 | Useful for diagnostics, escape hatches, and format research; direct writes carry high version and corruption risk. |
| No relevant implementation | 6, 15, 17 | One is documentation without code; two are naming false positives, though one contributes governance ideas. |

## Donor repository ledger

The review was static and read-only. No donor repository was installed, executed, given credentials, or connected to a live Brain. "Use" below means study or adapt a specific idea subject to license review and independent tests; it does not mean wholesale adoption.

| # | Repository | Useful evidence or candidate contribution | Current disposition |
|---:|---|---|---|
| 1 | [`lonniev/thebrain-mcp`](https://github.com/lonniev/thebrain-mcp) | BrainQuery graph language; bounded traversal; mutation limits; preview-first deletion; post-write confirmation through modifications. | **Mine selectively.** Cloud-bound and surrounded by hosted identity/payment infrastructure that the local core does not need. |
| 2 | [`jalalahmad/mcp-thebrain`](https://github.com/jalalahmad/mcp-thebrain) | Broad tool/resource catalogue, relationship summaries, bulk-operation shapes, and prompts. | **Reference only.** Its real stdio path is cloud-bound; its HTTP surface was found to be largely placeholder behavior. |
| 3 | [`redmorestudio/thebrain-mcp`](https://github.com/redmorestudio/thebrain-mcp) | Honest notes about cloud API rough edges. | **Reject as a server.** Arbitrary local file paths and direct destructive tools violate the intended safety boundary. |
| 4 | [`jqlts1/thebrain-mcp-server`](https://github.com/jqlts1/thebrain-mcp-server) | Agent-oriented `get_context`, bounded neighbors, query-budget discipline, note append/overwrite distinction, and separate spaced-repetition state. | **Mine and rewrite.** Valuable product shapes, but cloud-bound with disqualifying network/authentication defaults. |
| 5 | [`jalalahmad/npm-thebrain-sdk`](https://github.com/jalalahmad/npm-thebrain-sdk) | Endpoint inventory and TypeScript DTO comparisons. | **Do not use as the client foundation.** Contract and model inconsistencies outweigh the convenience of the wrapper. |
| 6 | [`enogrob/project-thebrain-mcp-server`](https://github.com/enogrob/project-thebrain-mcp-server) | Layered architecture diagrams and a requirements-style README. | **Catalog and close.** The described implementation is absent from the repository. |
| 7 | [`chriskyfung/My-PowerShell-Scripts/theBrain`](https://github.com/chriskyfung/My-PowerShell-Scripts/tree/master/theBrain) | Windows data-directory discovery and read-only link-audit patterns. | **Pattern only.** Targets an older TheBrain layout; do not reuse its note mutators against current data. |
| 8 | [`MattGyverLee/TheBrainGraph`](https://github.com/MattGyverLee/TheBrainGraph) | The distant idea of a query-driven semantic projection rather than a full graph clone. | **Reject the codebase.** API routes, SPARQL behavior, cache wiring, security defaults, and performance claims were not supported by the implementation. |
| 9 | [`constpb2394/thebrain-date-thoughts`](https://github.com/constpb2394/thebrain-date-thoughts) | Record-created-IDs-and-compensate pattern; linked calendar generation. | **Pattern only.** Rebuild with explicit timezone/year, private defaults, idempotency, a persistent journal, and reliable failure status. |
| 10 | [`jupdike/brain-gal`](https://github.com/jupdike/brain-gal) | Read-only local subtree traversal and curated publishing projections. | **Adapt as an export pattern.** Replace its outline/parser shortcuts with typed, escaped, provenance-preserving output. A projection is not a backup. |
| 11 | [`jmmcmx/obsidian-to-thebrain`](https://github.com/jmmcmx/obsidian-to-thebrain) | Migration requirements for folders, notes, frontmatter, aliases, and wikilinks. | **Reject direct database writing.** Rebuild migration as a deterministic specification applied through the supported API. |
| 12 | [`BlueBalou/keep_to_thebrain`](https://github.com/BlueBalou/keep_to_thebrain) | A minimal field checklist for a future Keep migration. | **Quarantine.** The repository exposed credential-like and private-looking material; its dry-run, idempotency, and partial-failure behavior are unsafe. Copy no secrets or data. |
| 13 | [`milescarroll-yoley/claude-to-thebrain`](https://github.com/milescarroll-yoley/claude-to-thebrain) | Clean separation between an offline declarative graph specification and a small deterministic local-API importer. | **Closest importer prototype.** Harden with target confirmation, cycle checks, source IDs, collision detection, idempotent resume, journaling, compensation, and read-back verification. |
| 14 | [`TheBrainTech/send-to-thebrain`](https://github.com/TheBrainTech/send-to-thebrain) | Official local-API client shapes, app-state checks, URL deduplication, title normalization, and a narrow useful capture workflow. | **Canonical prior art for the local client.** Keep loopback-only access and add explicit targets plus operation journaling for the broader bridge. |
| 15 | [`Moenn-ai/fastapi-moenn-vps`](https://github.com/Moenn-ai/fastapi-moenn-vps) | Security warning: unauthenticated status pages must not reveal secret state or infrastructure paths. | **Unrelated naming false positive; otherwise ignore.** |
| 16 | [`japer-technology/the-brain-actuator`](https://github.com/japer-technology/the-brain-actuator) | Read-only default, fail-closed capability gates, whole-Brain backup doctrine, schema discovery, unknown-field surfacing, operation journals, and validation before/after mutation. | **Adopt the safety constitution, not the adapters.** Current storage mappings are based on synthetic fixtures and conflict with observed current formats. |
| 17 | [`cattailfarmer/TheBrain`](https://github.com/cattailfarmer/TheBrain) | Separation of proposal, approval, execution, verification, acceptance, evidence, and rollback. | **Mine lightweight governance concepts only.** It is an unrelated coding-agent system, not a TheBrain integration, and its full ceremony is excessive here. |
| 18 | [`OpenGlobalMind/uuid-base64-codec`](https://github.com/OpenGlobalMind/uuid-base64-codec) | .NET-compatible conversion between TheBrain UUIDs and compact 22-character URL-safe identifiers. | **Retain and test.** Use canonical UUIDs internally; add known vectors, validation, and corrected padding before compact-link support. |

### License boundary

**Direction:** architectural lessons may be reimplemented from understanding, but code must not be copied merely because a repository is public. Several surveyed projects have absent, inconsistent, restrictive, or unclear licenses. Any direct reuse requires a recorded license check, compatibility decision, attribution, and tests proving that the adapted behavior fits the supported local API.

## Proposed working parts

These are logical parts, not yet a committed folder structure.

| Part | Responsibility | Status |
|---|---|---|
| Configuration boundary | Load endpoint and operator-supplied settings locally; keep credentials and deployment facts out of source and logs. | **Direction** |
| Local API client | Minimal typed wrapper over the supported loopback API; normalize endpoints and distinguish app, user, Brain, and entity errors. | **Direction** |
| Capability registry | Discover supported operations and fail closed when an API or version is unknown. | **Direction** |
| Read model | Search; Thought retrieval; notes and attachment metadata; compound context; bounded neighbor exploration; recent activity where supported. | **Direction** |
| Safety gate | Enforce read-only default, target scope, operation limits, path restrictions, and prohibited actions independent of transport. | **Direction** |
| Planner and approval boundary | Turn a requested mutation into a deterministic preview that identifies target, effects, limits, and required approval. | **Direction** |
| Operation executor | Apply only approved constructive operations and refuse any operation outside its declared capability. | **Candidate for Phase 2** |
| Journal and provenance | Record request, plan, approval scope, source keys, results, errors, and verification receipts without recording secrets. | **Direction** |
| Verification and recovery | Read back mutations, detect partial failure, support idempotent resume, and produce bounded compensation instructions. | **Direction** |
| Import pipeline | Validate a declarative graph specification offline; report collisions/cycles; plan, resume, and verify supported imports. | **Candidate for Phase 3** |
| Export/projection pipeline | Produce deterministic typed exports with stable IDs and provenance for inspection or curated publication. | **Candidate for Phase 1/3** |
| Compact-ID codec | Convert canonical UUIDs only where internal links or exports require compact identifiers. | **Deferred utility** |
| Transport adapters | CLI, library API, stdio MCP, or other narrow surfaces calling the same core. No transport receives extra authority. | **Unresolved** |
| Advanced modules | Graph query language, calendars, spaced repetition/game state, and publishing views. | **Deferred** |

### Candidate source layout

This layout is a discussion aid, not a decision:

```text
src/
  client/        # supported local API contract
  model/         # normalized internal types
  safety/        # capabilities, policy, limits, target scope
  operations/    # plans, approvals, execution, receipts
  import/        # declarative specifications and migration adapters
  export/        # deterministic exports and projections
  transports/    # CLI, stdio MCP, or later adapters
tests/
  contract/      # captured behavior of supported TheBrain versions
  fixtures/      # fabricated Brains/specifications; never private exports
  safety/        # fail-closed and mutation-boundary tests
docs/
  decisions/     # dated architectural decisions once this ledger becomes too large
  research/      # evidence notes and donor-repository findings
examples/        # fabricated configurations and workflows
```

## Safety invariants already earned

1. **Loopback by default.** The initial data plane communicates with the local app, not an internet-exposed service.
2. **Read-only by default.** Write capabilities must be explicitly enabled and narrowly scoped.
3. **Supported API before private storage.** Do not write `Brain.db`, note files, attachments, or undocumented sync bookkeeping directly.
4. **No ambient target.** Every operation identifies the Brain and relevant Thought/link targets by stable ID and human-readable name.
5. **Plan before mutation.** A dry run performs no network or filesystem mutation and produces a deterministic operation plan.
6. **Scoped approval.** Approval applies to the displayed plan, not to an open-ended session.
7. **Journal before and during execution.** A recoverable record exists before the first mutation and advances with each result.
8. **Verify after mutation.** Success is not inferred from an HTTP status alone; results are read back and compared with the plan.
9. **Idempotency or explicit resumability.** Retrying an interrupted operation must not silently duplicate structure.
10. **No destructive first release.** Delete, arbitrary overwrite, reparenting, arbitrary local-file attachment, and unconstrained bulk mutation remain unavailable.
11. **No arbitrary paths.** File operations, if ever added, use an explicit staging area and cannot read or overwrite arbitrary filesystem locations.
12. **Secrets stay local.** Credentials never enter Git, examples, journals, logs, command history, URLs, or agent-visible prose.
13. **Backups are external truth.** Exports and journals help recovery but do not replace TheBrain's native, dated whole-Brain backups.
14. **Projection is not authority.** A generated gallery, index, semantic cache, or public view is derived and cannot silently become canonical.
15. **Transport does not enlarge power.** MCP, CLI, HTTP, or another adapter may reduce exposed capabilities; none may bypass the core safety gate.

## Proposed implementation sequence

### Phase 0: prove the ground

- Capture the installed local API endpoint and version behavior from official/current sources.
- Create a disposable test Brain containing each entity and relation type needed for contract fixtures.
- Establish fabricated test data and secret-free configuration examples.
- Decide language, license, initial operating-system promise, and first transport.
- Define what constitutes a native backup and a safe disposable test target.
- Use the official Send to TheBrain extension separately where its narrow capture workflow is useful; do not absorb it wholesale.

### Phase 1: read-only core

- Connect to the local app and report app/user/open-Brain state.
- Search Thoughts.
- Retrieve a compound Thought context: identity, relations, note, and attachment metadata.
- Explore neighbors with explicit direction, depth, result, and query budgets.
- Read recent modifications or activity if the supported local API exposes it.
- Produce a deterministic subtree export with stable IDs and provenance.
- Expose the core through one narrow transport only after its safety boundary is tested.

### Phase 2: bounded constructive writes

Initially consider only:

- create Thought;
- create link;
- append note;
- attach URL.

Every mutating workflow must follow:

```text
request -> resolve target -> plan -> preview -> scoped approval
        -> journal -> apply bounded steps -> read-back verification -> receipt
```

Partial failure must stop further writes, preserve the journal, and report a resumable or compensating plan. Delete, overwrite, reparent, arbitrary files, and open-ended bulk edits remain out of scope.

### Phase 3: deterministic movement

- Harden the declarative graph specification.
- Add collision detection, provenance keys, idempotent resume, and import receipts.
- Build typed export and curated projection formats.
- Rebuild any Obsidian, Keep, calendar, or other migration as a source adapter that emits the neutral specification; adapters do not write TheBrain directly.
- Add compact-ID support only with fixtures and round-trip tests.

### Phase 4: advanced capabilities

Only after the core is stable, evaluate:

- bounded graph query language;
- calendar and recurring-structure generators;
- spaced repetition or game state stored separately from canonical knowledge;
- authorized publishing projections;
- multi-Brain routing and composite read-only views, if these prove broadly useful.

## What was about to be scaffolded

Before this single-ledger approach was chosen, the likely founding scaffold included a README, purpose and boundary documents, architectural decisions, donor-repository research, generic examples, implementation phases, and test/fixture directories. Creating all of those now would make provisional distinctions look settled.

**Current decision:** keep this one file as the landing place until the first implementation choice creates a real need for another artifact. Split material out only when it has a stable consumer:

- a README when the project can truthfully say what can be installed or run;
- an ADR when a consequential technical choice is made;
- a research note when evidence is too detailed for this ledger;
- a security document when an executable attack surface exists;
- source and tests together when the first behavior is implemented.

## Immediate decisions waiting for evidence

1. What is the smallest useful read-only vertical slice?
2. Which language best matches the official local client evidence and intended contributors?
3. Is the first transport a CLI, stdio MCP server, or library call surface?
4. Which current TheBrain versions and operating systems can be tested honestly?
5. What local API behavior needs captured contract fixtures before implementation?
6. Which configuration belongs to the reusable product, and which must remain deployment-private?
7. Which open-source license fits both the intended project and any code considered for reuse?
8. What explicit evidence would justify multi-Brain coordination in the public core?

## Maintenance rule

Until this ledger is split into stable documents, every substantial update should include:

- date;
- maturity label;
- evidence or motivating use case;
- affected part;
- decision or open question;
- safety and boundary impact;
- next test or action.

Do not silently convert a candidate into a feature, a private use case into a public default, a static-source observation into a runtime claim, or an attractive donor repository into a dependency.

---

The Corykidion begins here as a disciplined synthesis: one public tool, explicit private deployments, small trusted parts, and enough empty margin to discover what the general user actually needs.
