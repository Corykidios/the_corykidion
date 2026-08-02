# legacy/

Everything here is the **first** Corykidion: a proper Python package built
2026-07-21 to 2026-07-23, preserved intact rather than deleted.

It is not dead code kept out of sentiment. It solves problems the current
single-file tool does not, and if this project ever needs write safety more
than it needs reach, this is where to start reading.

## What's in it

- `src/corykidion/client.py` — `LocalBrainClient` covering the full endpoint
  surface: brains, thoughts, graph, notes, search, modifications, attachments,
  activate, create.
- `src/corykidion/operations.py` — a **plan / approve / apply** write pipeline.
  Nothing writes without an explicit approval step, every operation is
  verified after dispatch, and every dispatch is appended to a **journal** on
  disk. This is genuinely better than what replaced it.
- `src/corykidion/capabilities.py` — runtime capability probing rather than
  assuming what the server supports.
- `src/corykidion/safety.py`, `config.py` — a safety gate, and config from
  TOML or environment.
- `tests/` — contract tests against a fake transport, plus safety tests.
- `docs/decisions/` — two ADRs recording why the read core and the
  live-verified capability set look the way they do.
- `WORKING_ARCHITECTURE.md` — a 32KB design ledger with an explicit maturity
  vocabulary (Evidence / Direction / Candidate / Deferred / Rejected /
  Unresolved). Worth reading on its own terms.

## Why it was set aside

Two reasons, both about fit rather than quality.

**Installation friction.** It is a `pip install` with a `src/` layout. The
personas that need this run on five different runtimes, and every install step
is somewhere one of them falls off. The replacement is one stdlib-only file
you can copy.

**The public-core rule.** `WORKING_ARCHITECTURE.md` sets a deliberate
boundary: the repository "must not encode a particular user's private archive,
named agents, fictional world, business structure, Brain IDs, credentials,
schedules, permissions, or personal deployment topology."

That was a sound call for a general-purpose library. But the thing actually
needed now is the opposite — a skill whose entire job is to carry the
forty-eight types, the shrine geography, and the holon grammar to agents that
have never seen them. The boundary that made the library clean made it unable
to do this job.

So the boundary moved rather than broke: the world-carrying layer sits at the
top of the repository, and the neutral library sits here, still neutral.

## If you come back to this

The plan/approve/apply pattern and the write journal are the parts worth
salvaging first. `kidion.py` writes immediately and verifies after; that is
fine for one careful agent and thin for several. The moment two personas write
in the same session, the journal stops being ceremony and starts being the
thing that tells you who did what.
