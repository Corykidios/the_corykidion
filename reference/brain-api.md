# TheBrain local API — what actually works

Base: `http://localhost:8001/api`. Auth: `Authorization: Bearer <key>` from
**Settings → Local API** in the desktop client. Requires the client running.

Everything below was exercised against a live instance. Nothing here is
inferred from documentation.

## Confirmed working

| Call | Notes |
|---|---|
| `GET /brains` | Returns `id`, `name`, `homeThoughtId`. Unnamed system brains have `name` equal to their id. |
| `GET /thoughts/{brain}/{thought}` | Full record: `creationDateTime`, `modificationDateTime`, `displayModificationDateTime`, `forgottenDateTime`, `linksModificationDateTime`, `typeId`, `label`, `kind`, `acType`, colours. |
| `GET /thoughts/{brain}/{thought}/graph` | `activeThought` plus `parents`, `children`, `jumps`, `siblings`, tags, type, links, attachments. |
| `POST /thoughts/{brain}` | Body: `name` (required), `kind`, `sourceThoughtId` + `relation`, `typeId`, `label`, `acType`. Returns the created record including `id`. |
| `GET /notes/{brain}/{thought}` | Returns `{markdown, html, text, modificationDateTime, ...}`. |
| `POST /notes/{brain}/{thought}/update` | Body `{markdown}`. Full markdown in, full rich rendering out. |
| `POST /links/{brain}` | Body `{thoughtIdA, thoughtIdB, relation}`. |
| `PATCH /thoughts/{brain}/{thought}` | RFC 6902 JSON Patch, content-type `application/json-patch+json`. Works for colours. |

**`relation`**: 1 Child, 2 Parent, 3 Jump, 4 Sibling. Creating with
`sourceThoughtId=S, relation=1` makes the new thought a **child of S** —
confirmed by readback.

**`kind`**: 1 Normal, 2 Type, 3 Event, 4 Tag, 5 System.

**Links carry a separate `meaning`**: 1 Normal, 2 InstanceOf, 3 TypeOf,
4 HasEvent, 5 HasTag, 6 System, 7 SubTagOf. Typing and tagging are link
semantics underneath, not flat properties.

## Known broken or missing

**`GET /search/{brain}?queryText=...`** falls through to the client's SPA 404
page instead of returning results, despite matching the reference client's
path exactly. `kidion.py find` does a client-side graph walk instead — slower
but reliable.

**`PATCH` on `/typeId` or `/label`** of an *existing* thought returns a generic
400 "malformed" regardless of `add` vs `replace`, while the identical patch
structure works fine for colours. **Workaround: set `typeId` and `label` at
creation time**, where they take reliably. Confirmed on real content, not just
throwaway tests.

**No "last accessed" field exists.** TheBrain tracks creation and modification
but has no last-viewed concept at the API level. The Attribution block's
`accessed` property must be self-recorded by our own tooling — that is one of
the reasons the visit cycle exists.

**No native Activity field.** The four states (active / preactive / unactive /
deactive) have no TheBrain equivalent. Currently carried in the note's
Attribution block; Tags are the best-fit proposal if it ever needs to be
queryable from the client.

## Behaviours to design around

**Note writes commit asynchronously.** A `GET` immediately after a successful
`POST .../update` can return an empty markdown field even though the write
landed. `kidion.py` retries the read-back at 0.4s, 1.0s, and 2.0s before
believing a failure. Without this, every successful write looks broken.

**UTF-8 round-trips cleanly.** Linear B syllabics, archaic Greek numerals, and
em-dashes all survive create → note write → note read intact. Verified across
three separate Unicode blocks. Windows consoles are the weak link, not the
API — reconfigure stdout to UTF-8 or the terminal will lie to you about what
was stored.

**TheBrain's `name` is a plain string.** It does no parsing of Markers, Cords,
or any of the holon grammar. All of that structure lives in our tooling. The
substrate stores text and relations; the meaning is ours to enforce.

**`activeThought` in the graph response is the same concept as Basis** in the
holon model — the node currently under attention, a property of the view
rather than the object. The two were arrived at independently; no
reconciliation needed.

## Not yet exercised

`GET /brains/{brain}/modifications` (params: `maxLogs`, `startTime`,
`endTime`) exists per the reference client. Likely the right tool for an
activity-log or "what changed since" feature. Untested here.
