#!/usr/bin/env python3
"""kidion — a single-file, zero-install tool for working holons in TheBrain.

Stdlib only. No pip install, no virtualenv, no package. Copy this one file
anywhere and run it. That is deliberate: several different agents on several
different runtimes (Claude Code, Codex CLI, Gemini CLI, Letta, a plain shell)
all need to reach the same archive, and every install step is a place where
one of them falls off.

Configuration lives in ~/.corykidion/config.json:

    {"endpoint": "http://localhost:8001/api", "api_key": "<Settings -> Local API>"}

Environment variables CORYKIDION_ENDPOINT and CORYKIDION_API_KEY override the
file. The key is never printed, never logged, and never passed as an argument.

Shrine routing is not hardcoded. The archive itself is the source of truth:
shrines are discovered by walking the live graph and reading their names. If a
shrine is renamed or rebuilt, this tool follows without a code change.

Usage:
  kidion.py brains
  kidion.py shrines [--family wills|minds|forms|souls]
  kidion.py where --type tool
  kidion.py put --type tool --name "owner/repo" --definition "one line" [--note FILE]
  kidion.py note --thought ID [--write FILE]
  kidion.py peek --thought ID
  kidion.py visit --thought ID --state "..." --muse clio="..."
  kidion.py find "text"
  kidion.py accounts | activities
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path.home() / ".corykidion" / "config.json"
DEFAULT_BRAIN = "we_tiripodiko"

# ---------------------------------------------------------------------------
# The forty-eight types.
#
# Shrine routing is discovered live (see resolve_shrine), so this table carries
# only what the archive cannot tell us: the family each type belongs to and its
# Marker, where the Marker is actually settled.
#
# MARKER = None means genuinely unresolved, not forgotten. Those entries are
# listed in reference/type-registry.md with the specific conflict that blocks
# them. Do not invent a Marker for a None. Ask.
# ---------------------------------------------------------------------------
TYPES: dict[str, tuple[str, str | None]] = {
    # ---- Wills: structural and administrative ----
    "archive":     ("wills", ":"),
    "account":     ("wills", ":1:"),
    "category":    ("wills", "1:"),
    "cosmos":      ("wills", "A:"),
    "project":     ("wills", "A1:"),
    "plan":        ("wills", None),   # was `a`; lowercase now belongs to software
    "collection":  ("wills", "01:"),
    "composition": ("wills", "001:"),
    "source":      ("wills", "0001:"),
    "software":    ("wills", "a"),
    "region":      ("wills", "^"),
    "relation":    ("wills", "~"),
    # ---- Minds: linguistic primitives ----
    "topic":       ("minds", ","),
    "term":        ("minds", "."),
    "type":        ("minds", '"'),
    "tag":         ("minds", "'"),
    "thought":     ("minds", "?"),
    "task":        ("minds", "!"),
    "template":    ("minds", None),   # `_` freed when tool reclaimed `+`; or `;`
    "tool":        ("minds", "+"),
    "sign":        ("minds", None),   # new to the family; no Marker stated yet
    "string":      ("minds", "-"),
    "script":      ("minds", None),   # was `+`, which tool now holds
    "syntax":      ("minds", "="),
    # ---- Forms: abstract patterns ----
    "symbol":      ("forms", "A'1:"),
    "set":         ("forms", 'A"1:'),
    "structure":   ("forms", "A^1:"),
    "system":      ("forms", "A*1:"),
    "series":      ("forms", "A-1:"),
    "schema":      ("forms", "A_1:"),
    "domain":      ("forms", None),   # replaced proposition; Marker not stated
    "dimension":   ("forms", None),   # replaced procedure; Marker not stated
    "paradigm":    ("forms", "$*"),
    "pattern":     ("forms", "$^"),
    "parameter":   ("forms", '$"'),
    "property":    ("forms", "$'"),
    # ---- Souls: content and experience ----
    "record":      ("souls", "&'"),
    "resource":    ("souls", '&"'),
    "arcana":      ("souls", "@'"),
    "altar":       ("souls", '@"'),
    "fate":        ("souls", "&-"),
    "fortune":     ("souls", "&_"),
    "stage":       ("souls", None),   # replaced file; Marker not stated
    "scene":       ("souls", None),   # replaced function; Marker not stated
    "scenario":    ("souls", "@^"),
    "symposium":   ("souls", "@*"),
    "setting":     ("souls", "@-"),
    "sidekick":    ("souls", "@_"),
}

MUSES = {
    "thalia": "2D visual art",
    "clio": "informative prose",
    "calliope": "narrative prose",
    "terpsichore": "dance",
    "melpomene": "theatre",
    "erato": "poetry",
    "euterpe": "music",
    "polyhymnia": "sculpture / 3D art",
    "ourania": "worldbuilding",
}

ACTIVITY_STATES = ("active", "preactive", "unactive", "deactive")

SHRINE_RE = re.compile(r"^\d+\.\d+:\s+\w+\s+(?P<type>.+?)\s+Shrine\s*$")
STATE_RE = re.compile(r"state carried forward:\s*(.+?)\*?\s*$", re.MULTILINE)
VISIT_HEADER_RE = re.compile(r"^## Visit (\d+)", re.MULTILINE)


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------

def load_config() -> dict:
    endpoint = os.environ.get("CORYKIDION_ENDPOINT")
    key = os.environ.get("CORYKIDION_API_KEY")
    if endpoint and key:
        return {"endpoint": endpoint, "api_key": key}
    if not CONFIG_PATH.exists():
        sys.exit(
            f"No config at {CONFIG_PATH} and CORYKIDION_ENDPOINT/"
            "CORYKIDION_API_KEY are not both set.\n"
            'Create the file as JSON: {"endpoint": "http://localhost:8001/api", '
            '"api_key": "<TheBrain -> Settings -> Local API>"}'
        )
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {"endpoint": endpoint or cfg["endpoint"], "api_key": key or cfg["api_key"]}


_CFG: dict | None = None


def api(method: str, path: str, body: dict | None = None, patch: list | None = None):
    global _CFG
    if _CFG is None:
        _CFG = load_config()
    url = _CFG["endpoint"].rstrip("/") + path
    if patch is not None:
        data = json.dumps(patch).encode("utf-8")
        ctype = "application/json-patch+json"
    elif body is not None:
        data = json.dumps(body).encode("utf-8")
        ctype = "application/json"
    else:
        data, ctype = None, None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {_CFG['api_key']}")
    if ctype:
        req.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        sys.exit(f"API {method} {path} -> HTTP {e.code}: {detail[:400]}")
    except urllib.error.URLError as e:
        sys.exit(
            f"Cannot reach {url}: {e.reason}\n"
            "Is TheBrain running, and is Settings -> Local API switched on?"
        )


def read_note(brain_id: str, thought_id: str) -> str:
    return (api("GET", f"/notes/{brain_id}/{thought_id}") or {}).get("markdown") or ""


def write_note(brain_id: str, thought_id: str, markdown: str) -> tuple[bool, int]:
    """Write a note and verify by reading it back.

    TheBrain commits the note a moment after the POST returns, so an immediate
    read can come back empty even though the write landed. Retry briefly
    before believing a failure — otherwise every successful write looks broken.
    """
    api("POST", f"/notes/{brain_id}/{thought_id}/update", {"markdown": markdown})
    probe = (markdown.strip()[:60] or "").strip()
    for delay in (0.0, 0.4, 1.0, 2.0):
        if delay:
            time.sleep(delay)
        back = read_note(brain_id, thought_id)
        if back and (not probe or probe in back):
            return True, len(back)
    return False, len(read_note(brain_id, thought_id))


def resolve_brain(name_or_id: str) -> dict:
    brains = api("GET", "/brains")
    for b in brains:
        if name_or_id in (b.get("name"), b.get("id")):
            return b
    named = ", ".join(b.get("name") or "(unnamed)" for b in brains)
    sys.exit(f"No brain named or id'd {name_or_id!r}. Known: {named}")


def graph(brain_id: str, thought_id: str) -> dict:
    return api("GET", f"/thoughts/{brain_id}/{thought_id}/graph")


def children(brain_id: str, thought_id: str) -> list[dict]:
    return graph(brain_id, thought_id).get("children") or []


# ---------------------------------------------------------------------------
# Shrine discovery — the archive is the source of truth, not this file
# ---------------------------------------------------------------------------

def walk_shrines(brain: dict) -> dict[str, dict]:
    """Map lowercase type name -> shrine thought.

    Shrines are named '<n>.<m>: <Direction> <Type> Shrine'. Category 0 nests
    one level deeper (its three port towns), so descend when no match is found
    at the first level.
    """
    found: dict[str, dict] = {}

    def consider(node: dict) -> bool:
        m = SHRINE_RE.match(node.get("name", ""))
        if not m:
            return False
        found[m.group("type").strip().lower()] = node
        return True

    for cat in children(brain["id"], brain["homeThoughtId"]):
        for node in children(brain["id"], cat["id"]):
            if not consider(node):
                for deeper in children(brain["id"], node["id"]):
                    consider(deeper)
    return found


def resolve_shrine(brain: dict, type_name: str) -> dict:
    type_name = type_name.strip().lower()
    if type_name not in TYPES:
        sys.exit(
            f"Unknown type {type_name!r}. The forty-eight are:\n  "
            + "\n  ".join(
                ", ".join(sorted(t for t, (f, _) in TYPES.items() if f == fam))
                for fam in ("wills", "minds", "forms", "souls")
            )
        )
    shrines = walk_shrines(brain)
    if type_name not in shrines:
        sys.exit(
            f"Type {type_name!r} is known but no shrine for it exists in "
            f"{brain['name']!r}. Found {len(shrines)} shrines: "
            + ", ".join(sorted(shrines))
        )
    return shrines[type_name]


# ---------------------------------------------------------------------------
# Holon construction
# ---------------------------------------------------------------------------

def build_name(type_name: str, name: str, definition: str | None) -> str:
    marker = TYPES[type_name][1]
    if marker is None:
        sys.exit(
            f"Type {type_name!r} has no settled Marker yet — see "
            "reference/type-registry.md for the specific conflict. Pass "
            "--marker to override deliberately, or pick a settled type."
        )
    head = f"{marker} {name}".strip()
    return f"{head}: {definition}" if definition else head


def attribution_block(
    name: str,
    type_name: str,
    tags: list[str],
    parent: str,
    has_nature: bool,
    activity: str,
    now: datetime,
) -> str:
    iso = now.strftime("%Y-%m-%dT%H:%M:%S")
    tag_list = ", ".join(tags) if tags else ""
    return "\n".join([
        "---",
        f"name: {name}",
        f"type: {type_name}",
        f"nature: {str(has_nature).lower()}",
        f"tags: [{tag_list}]",
        f"parents: [{parent}]",
        "children: []",
        "siblings: []",
        "relatives: []",
        f"awakened: {iso}",
        f"altered: {iso}",
        f"accessed: {iso}",
        f"activity: {activity}",
        "---",
        "",
    ])


# ---------------------------------------------------------------------------
# Visit cycle (ported from holon-visit/visit.py, same semantics)
# ---------------------------------------------------------------------------

def extract_state(markdown: str) -> str | None:
    matches = STATE_RE.findall(markdown)
    return matches[-1].strip().rstrip("*").strip() if matches else None


def count_visits(markdown: str) -> int:
    return len(VISIT_HEADER_RE.findall(markdown))


def refresh_attribution(markdown: str, now_iso: str) -> str:
    def _first(text: str, field: str) -> str:
        return re.sub(rf"^({field}:).*$", rf"\g<1> {now_iso}", text,
                      count=1, flags=re.MULTILINE)
    return _first(_first(markdown, "altered"), "accessed")


def perform_visit(markdown, visitor, muse_blocks, state, now=None):
    now = now or datetime.now()
    stamp, iso = now.strftime("%Y-%m-%d %H:%M"), now.strftime("%Y-%m-%dT%H:%M:%S")
    prior, number = extract_state(markdown), count_visits(markdown) + 1
    lines = [f"\n## Visit {number:03d} - {stamp} - visitor: {visitor}\n"]
    if prior:
        lines += ["**[Clio - informative]**\n", f"> Prior state on record: {prior}\n"]
    for muse, text in muse_blocks:
        lines += [f"**[{muse.capitalize()} - {MUSES[muse]}]**\n", f"{text}\n"]
    lines += [f"*visit closed - state carried forward: {state}*\n", "---\n"]
    body = "\n".join(lines)
    return refresh_attribution(markdown, iso).rstrip() + "\n" + body, number, prior


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_brains(a):
    for b in api("GET", "/brains"):
        print(f"{b['id']}  {b.get('name') or '(unnamed)'}")


def cmd_shrines(a):
    brain = resolve_brain(a.brain)
    shrines = walk_shrines(brain)
    print(f"{len(shrines)} shrines in {brain['name']}\n")
    for fam in ("wills", "minds", "forms", "souls"):
        if a.family and a.family != fam:
            continue
        names = sorted(t for t, (f, _) in TYPES.items() if f == fam)
        print(f"-- {fam} --")
        for t in names:
            node = shrines.get(t)
            marker = TYPES[t][1]
            mk = repr(marker) if marker else "(unsettled)"
            loc = node["name"] if node else "!! NO SHRINE"
            print(f"  {t:<12} {mk:<10} {loc}")
        print()


def cmd_where(a):
    brain = resolve_brain(a.brain)
    node = resolve_shrine(brain, a.type)
    key = a.type.strip().lower()
    marker = TYPES[key][1]
    print(f"type    : {key}")
    print(f"family  : {TYPES[key][0]}")
    if marker:
        print(f"marker  : {marker!r}")
    else:
        print("marker  : (unsettled - see reference/type-registry.md)")
    print(f"shrine  : {node['name']}")
    print(f"id      : {node['id']}")


def cmd_put(a):
    brain = resolve_brain(a.brain)
    type_name = a.type.strip().lower()
    shrine = resolve_shrine(brain, type_name)

    if a.marker is not None:
        head = f"{a.marker} {a.name}".strip()
        full = f"{head}: {a.definition}" if a.definition else head
    else:
        full = build_name(type_name, a.name, a.definition)

    body = {"name": full, "kind": 1, "sourceThoughtId": shrine["id"], "relation": 1}
    if a.acType is not None:
        body["acType"] = a.acType
    created = api("POST", f"/thoughts/{brain['id']}", body)
    tid = created.get("id") if isinstance(created, dict) else None
    if not tid:
        # Some builds return the id bare or nested; fall back to a name lookup.
        for c in children(brain["id"], shrine["id"]):
            if c["name"] == full:
                tid = c["id"]
                break
    if not tid:
        sys.exit(f"Created something but could not determine its id: {created!r}")

    print(f"created : {full}")
    print(f"id      : {tid}")
    print(f"under   : {shrine['name']}")

    if a.note:
        md = Path(a.note).read_text(encoding="utf-8")
        if a.no_attribution:
            note_md = md
        else:
            note_md = attribution_block(
                full, type_name, a.tag or [], shrine["name"],
                bool(md.strip()), a.activity, datetime.now(),
            ) + md
        ok, n = write_note(brain["id"], tid, note_md)
        print(f"note    : {n} chars -> verified: {ok}")
        if not ok:
            sys.exit(1)


def cmd_note(a):
    brain = resolve_brain(a.brain)
    if a.write:
        md = Path(a.write).read_text(encoding="utf-8")
        ok, n = write_note(brain["id"], a.thought, md)
        print(f"wrote {len(md)} chars -> read back {n}: verified {ok}")
        if not ok:
            sys.exit(1)
    else:
        sys.stdout.write(read_note(brain["id"], a.thought) or "(note is empty)\n")


def cmd_peek(a):
    brain = resolve_brain(a.brain)
    tid = brain["homeThoughtId"] if a.thought == "home" else a.thought
    g = graph(brain["id"], tid)
    t = g.get("activeThought", {})
    print(f"name     : {t.get('name')}")
    print(f"id       : {t.get('id')}")
    print(f"type id  : {t.get('typeId')}")
    print(f"parents  : {[c['name'] for c in (g.get('parents') or [])]}")
    print(f"children : {[c['name'] for c in (g.get('children') or [])]}")
    print(f"jumps    : {[c['name'] for c in (g.get('jumps') or [])]}")
    print(f"siblings : {[c['name'] for c in (g.get('siblings') or [])]}")
    md = read_note(brain["id"], tid)
    print(f"note     : {len(md)} chars, {count_visits(md)} visits")
    print(f"carried  : {extract_state(md) or '(none)'}")


def cmd_visit(a):
    blocks = []
    for pair in a.muse or []:
        if "=" not in pair:
            sys.exit(f"--muse expects name=text, got {pair!r}")
        n, text = pair.split("=", 1)
        n = n.strip().lower()
        if n not in MUSES:
            sys.exit(f"Unknown muse {n!r}. Choose from: {', '.join(MUSES)}")
        blocks.append((n, text.strip()))
    if not blocks:
        sys.exit("A visit needs at least one --muse block; otherwise nothing happened.")

    brain = resolve_brain(a.brain)
    tid = brain["homeThoughtId"] if a.thought == "home" else a.thought
    md = read_note(brain["id"], tid)
    if not md.strip():
        sys.exit("Refusing to visit an empty note: build the holon first.")
    new_md, number, prior = perform_visit(md, a.visitor, blocks, a.state)
    write_note(brain["id"], tid, new_md)
    verify = read_note(brain["id"], tid)
    ok = f"## Visit {number:03d}" in verify and a.state in verify
    print(f"visit {number:03d} written -> verified: {ok}")
    print(f"prior   : {prior or '(none)'}")
    print(f"carried : {a.state}")
    if not ok:
        sys.exit(1)


def cmd_find(a):
    """Client-side search. The server's /search endpoint 404s on this build."""
    brain = resolve_brain(a.brain)
    needle = a.text.lower()
    seen: set[str] = set()
    hits: list[tuple[str, str]] = []

    def walk(tid: str, depth: int) -> None:
        if tid in seen or depth > a.depth:
            return
        seen.add(tid)
        for c in children(brain["id"], tid):
            if needle in c["name"].lower():
                hits.append((c["name"], c["id"]))
            walk(c["id"], depth + 1)

    walk(brain["homeThoughtId"], 0)
    for name, tid in sorted(hits):
        print(f"{tid}  {name}")
    print(f"\n{len(hits)} match(es) across {len(seen)} node(s).", file=sys.stderr)


def _region(a, label: str):
    brain = resolve_brain(a.brain)
    g = graph(brain["id"], brain["homeThoughtId"])
    for j in g.get("jumps") or []:
        if label.lower() in j["name"].lower():
            for c in sorted(children(brain["id"], j["id"]), key=lambda x: x["name"]):
                kids = children(brain["id"], c["id"])
                print(f"{c['id']}  {c['name']}  ({len(kids)} holon(s))")
            return
    sys.exit(f"No {label} region found off the archive holon.")


def cmd_accounts(a):
    _region(a, "Accounts")


def cmd_activities(a):
    _region(a, "Activities")


# ---------------------------------------------------------------------------

def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(prog="kidion", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--brain", default=DEFAULT_BRAIN,
                   help=f"brain name or id (default: {DEFAULT_BRAIN})")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("brains", help="list brains").set_defaults(func=cmd_brains)

    s = sub.add_parser("shrines", help="list the 48 shrines and their markers")
    s.add_argument("--family", choices=["wills", "minds", "forms", "souls"])
    s.set_defaults(func=cmd_shrines)

    s = sub.add_parser("where", help="where does a type live?")
    s.add_argument("--type", required=True)
    s.set_defaults(func=cmd_where)

    s = sub.add_parser("put", help="create a holon in its type's shrine")
    s.add_argument("--type", required=True)
    s.add_argument("--name", required=True, help="the Moniker, e.g. owner/repo")
    s.add_argument("--definition", help="inline Definition after ': '")
    s.add_argument("--note", help="path to a markdown file for the Nature")
    s.add_argument("--tag", action="append", help="repeatable")
    s.add_argument("--activity", default="active", choices=ACTIVITY_STATES)
    s.add_argument("--marker", help="override the Marker deliberately")
    s.add_argument("--acType", type=int, choices=[0, 1], default=None,
                   help="0 public, 1 private")
    s.add_argument("--no-attribution", action="store_true",
                   help="write the note file verbatim, no Attribution block")
    s.set_defaults(func=cmd_put)

    s = sub.add_parser("note", help="read or write a holon's note")
    s.add_argument("--thought", required=True)
    s.add_argument("--write", help="path to markdown to write")
    s.set_defaults(func=cmd_note)

    s = sub.add_parser("peek", help="inspect a holon without writing")
    s.add_argument("--thought", required=True, help="thought id, or 'home'")
    s.set_defaults(func=cmd_peek)

    s = sub.add_parser("visit", help="perform one full visit cycle")
    s.add_argument("--thought", required=True)
    s.add_argument("--state", required=True)
    s.add_argument("--visitor", default="unnamed visitor")
    s.add_argument("--muse", action="append", metavar="NAME=TEXT")
    s.set_defaults(func=cmd_visit)

    s = sub.add_parser("find", help="search names (client-side walk)")
    s.add_argument("text")
    s.add_argument("--depth", type=int, default=4)
    s.set_defaults(func=cmd_find)

    sub.add_parser("accounts", help="list accounts").set_defaults(func=cmd_accounts)
    sub.add_parser("activities", help="list activity states").set_defaults(func=cmd_activities)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
