# The Forty-Eight Types

Four families of twelve. Every holon is exactly one of these, and every type
has exactly one shrine in `we_tiripodiko`.

**Shrine column verified live** against the running archive on 2026-08-02 —
all 48 shrines exist and all 48 resolve. **Marker column is the incomplete
one.** Where a marker reads *(unsettled)*, that is a real open question, not a
gap in the transcription. The specific conflict is named below the table.

---

## Wills — structural and administrative

| Type | Marker | Shrine |
|---|---|---|
| archive | `:` | 0.01: East Archive Shrine |
| account | `:1:` | 0.02: South Account Shrine |
| category | `1:` | 0.03: West Category Shrine |
| cosmos | `A:` | 0.04: North Cosmos Shrine |
| project | `A1:` | 0.05: East Project Shrine |
| plan | *(unsettled)* | 0.06: South Plan Shrine |
| collection | `01:` | 0.07: West Collection Shrine |
| composition | `001:` | 0.08: North Composition Shrine |
| source | `0001:` | 0.09: East Source Shrine |
| software | `a` | 0.10: South Software Shrine |
| region | `^` | 0.11: West Region Shrine |
| relation | `~` | 0.12: North Relation Shrine |

The numeric ladder is the elegant part: one digit is a top-level category, two
a collection, three a composition, four a source. Ten thousand sources before
the string rolls over.

## Minds — linguistic primitives

| Type | Marker | Shrine |
|---|---|---|
| topic | `,` | 1.1: East Topic Shrine |
| term | `.` | 1.2: South Term Shrine |
| type | `"` | 1.3: West Type Shrine |
| tag | `'` | 1.4: North Tag Shrine |
| thought | `?` | 2.1: East Thought Shrine |
| task | `!` | 2.2: South Task Shrine |
| template | *(unsettled)* | 2.3: West Template Shrine |
| tool | `+` | 2.4: North Tool Shrine |
| sign | *(unsettled)* | 3.1: East Sign Shrine |
| string | `-` | 3.2: South String Shrine |
| script | *(unsettled)* | 3.3: West Script Shrine |
| syntax | `=` | 3.4: North Syntax Shrine |

Eight T-words then sign/string/script/syntax. A **sign** underlies everything —
a symbol is a sign and a meaning fused, which is why symbol sits in Forms and
sign sits here at the floor.

## Forms — abstract patterns

| Type | Marker | Shrine |
|---|---|---|
| symbol | `A'1:` | 4.1: East Symbol Shrine |
| set | `A"1:` | 4.2: South Set Shrine |
| structure | `A^1:` | 4.3: West Structure Shrine |
| system | `A*1:` | 4.4: North System Shrine |
| series | `A-1:` | 5.1: East Series Shrine |
| schema | `A_1:` | 5.2: South Schema Shrine |
| domain | *(unsettled)* | 5.3: West Domain Shrine |
| dimension | *(unsettled)* | 5.4: North Dimension Shrine |
| paradigm | `$*` | 6.1: East Paradigm Shrine |
| pattern | `$^` | 6.2: South Pattern Shrine |
| parameter | `$"` | 6.3: West Parameter Shrine |
| property | `$'` | 6.4: North Property Shrine |

## Souls — content and experience

| Type | Marker | Shrine |
|---|---|---|
| record | `&'` | 7.1: East Record Shrine |
| resource | `&"` | 7.2: South Resource Shrine |
| arcana | `@'` | 7.3: West Arcana Shrine |
| altar | `@"` | 7.4: North Altar Shrine |
| fate | `&-` | 8.1: East Fate Shrine |
| fortune | `&_` | 8.2: South Fortune Shrine |
| stage | *(unsettled)* | 8.3: West Stage Shrine |
| scene | *(unsettled)* | 8.4: North Scene Shrine |
| scenario | `@^` | 9.1: East Scenario Shrine |
| symposium | `@*` | 9.2: South Symposium Shrine |
| setting | `@-` | 9.3: West Setting Shrine |
| sidekick | `@_` | 9.4: North Sidekick Shrine |

A clean arc: record/resource are dry academic entries, arcana/altar are
book-adjacent and edging esoteric, fate/fortune are full tarot. Then the
performative six, where the actual RPG content will live — Meri, Core, the
Seekers as Sidekicks; Riverfront-type places as Settings.

---

## The eight unsettled markers, and why

These are blocked on a specific collision, not on forgetfulness. `kidion.py`
refuses to construct a name for them unless `--marker` is passed deliberately.

**`plan`** — held `a` in the earlier registry. Lowercase English letters have
since been assigned to **software**, so `plan` needs a new marker or software
needs a different one. Both can't have it.

**`tool` / `template` / `script`** — a three-way knot from one swap.
Originally: template `_`, tool `+`. During Letta work the pair was switched so
tool took `_` and template took `;`. Current instruction returns **tool to
`+`** — which is settled and in use. But `+` was also **script**'s marker in
the interim registry, and it is not stated whether template returns to `_`,
keeps `;`, or something else. Two of the three are now floating.

**`sign`** — newly added to the Minds family. No marker has ever been stated.

**`domain` / `dimension`** — these replaced *proposition* (`$_`) and
*procedure* (`$-`) in Forms. The vacated markers are unclaimed and it is not
stated whether the new pair inherits them or gets its own.

**`stage` / `scene`** — these replaced *file* (`&^`) and *function* (`&*`) in
Souls. Same situation: vacated markers unclaimed, inheritance not stated.

## One structural oddity worth a decision

The Archive holon's **parent is `0.01: East Archive Shrine`** — which is its
own great-grandchild, since the shrine descends from the Archive through
`0: Anawaro → 0.1: Joroko`.

This may be exactly right: the archive is typed by sitting in the shrine where
archive-type holons go, and it is the only one that will ever be there. A
self-representation properly filed under itself. But it does mean the Archive
holon is *subsumed*, which the stated design says shouldn't happen. Loop or
oversight — worth a deliberate call rather than leaving it ambiguous.

## A spacing tension carried forward

The anatomy names **fifteen privileged marks** (`.` `,` `?` `!` `;` `:` `'`
`"` `^` `*` `-` `_` `+` `=` `~`) that can occupy head or relational spacing.
But the Forms and Souls families use `$`, `&`, and `@` as family prefixes, and
none of those three are among the fifteen. Either the list grows to eighteen,
or those three are doing a structurally different job — a family prefix
stacked on a Minds-punctuation suffix — than the other fifteen. Unresolved.
