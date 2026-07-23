"""The CLI transport.

Per invariant 15, this adapter receives no authority the core doesn't
already grant: every command is a thin call into ReadModel/export, with the
same safety gate and capability registry any other transport would use.
"""

from __future__ import annotations

import argparse
import sys

from corykidion.client import LocalBrainClient
from corykidion.config import load_config
from corykidion.errors import CorykidionError
from corykidion.export import export_thought, write_export
from corykidion.operations import JournalWriter, WriteOperations
from corykidion.read import ReadModel
from corykidion.safety import SafetyGate


def _build_read_model(args: argparse.Namespace) -> ReadModel:
    config = load_config(args.config)
    client = LocalBrainClient(config)
    scope = frozenset(args.allow_brain) if args.allow_brain else frozenset()
    safety = SafetyGate(allowed_brain_ids=scope)
    return ReadModel(client, safety=safety)


def _cmd_status(args: argparse.Namespace) -> int:
    read_model = _build_read_model(args)
    status = read_model.connectivity()
    print(f"app running: {status.app_running}")
    print(f"active brain id: {status.active_brain_id or '(none open)'}")
    print(f"brains visible: {status.brain_count}")
    for brain in status.brains:
        print(f"  - {brain.id}  {brain.name}")
    return 0


def _cmd_capabilities(args: argparse.Namespace) -> int:
    read_model = _build_read_model(args)
    caps = read_model.known_capabilities()
    print("evidenced (usable now):")
    for name in caps["evidenced"]:
        print(f"  - {name}")
    print("candidate (not yet supported, raises CapabilityUnknown):")
    for name in caps["candidate"]:
        print(f"  - {name}")
    return 0


def _cmd_thought_get(args: argparse.Namespace) -> int:
    read_model = _build_read_model(args)
    thought = read_model.get_thought(args.brain_id, args.thought_id)
    print(f"id:    {thought.id}")
    print(f"name:  {thought.name}")
    print(f"label: {thought.label or ''}")
    return 0

def _cmd_thought_find_url(args: argparse.Namespace) -> int:
    read_model = _build_read_model(args)
    matches = read_model.find_existing_url(args.brain_id, args.url)
    if not matches:
        print("no existing attachment found for this URL")
        return 0
    for attachment in matches:
        print(f"{attachment.thought_id}  {attachment.location}")
    return 0


def _cmd_thought_search(args: argparse.Namespace) -> int:
    read_model = _build_read_model(args)
    results = read_model.search(args.brain_id, args.query, max_results=args.max_results)
    if not results:
        print("no matches")
        return 0
    for result in results:
        print(f"{result.thought.id}  {result.name}")
    return 0


def _cmd_thought_graph(args: argparse.Namespace) -> int:
    read_model = _build_read_model(args)
    graph = read_model.get_graph(args.brain_id, args.thought_id)
    print(f"active: {graph.active_thought.id}  {graph.active_thought.name}")
    print(f"parents:  {', '.join(f'{t.id} {t.name}' for t in graph.parents) or '(none)'}")
    print(f"children: {', '.join(f'{t.id} {t.name}' for t in graph.children) or '(none)'}")
    print(f"jumps:    {', '.join(f'{t.id} {t.name}' for t in graph.jumps) or '(none)'}")
    print(f"links: {len(graph.links)}  attachments: {len(graph.attachments)}")
    return 0


def _cmd_thought_notes(args: argparse.Namespace) -> int:
    read_model = _build_read_model(args)
    note = read_model.get_notes(args.brain_id, args.thought_id)
    print(note.markdown or "(empty note)")
    return 0


def _cmd_activity(args: argparse.Namespace) -> int:
    read_model = _build_read_model(args)
    entries = read_model.recent_activity(args.brain_id, max_logs=args.max_logs)
    if not entries:
        print("no recent activity")
        return 0
    for entry in entries:
        print(f"{entry.creation_datetime}  mod_type={entry.mod_type}  source={entry.source_id}")
    return 0


def _cmd_export_thought(args: argparse.Namespace) -> int:
    read_model = _build_read_model(args)
    document = export_thought(read_model, args.brain_id, args.thought_id)
    path = write_export(document, args.out)
    print(f"wrote {path}")
    return 0


def _build_write_operations(args: argparse.Namespace) -> WriteOperations:
    config = load_config(args.config)
    client = LocalBrainClient(config)
    scope = frozenset(args.allow_brain) if args.allow_brain else frozenset()
    # read_only=False only because --approve was required to reach this
    # function at all (see build_parser) — there is no code path that
    # constructs a write-enabled gate without that flag having been set.
    safety = SafetyGate(read_only=False, allowed_brain_ids=scope)
    journal = JournalWriter(args.journal)
    return WriteOperations(client, journal, safety=safety)


def _cmd_write_attach_url(args: argparse.Namespace) -> int:
    ops = _build_write_operations(args)
    plan = ops.plan_attach_url(args.brain_id, args.thought_id, args.url, args.name)
    print(f"plan {plan.plan_id}: {plan.description}")
    receipt = ops.apply(plan, approved=True)
    print(f"status: {receipt.status}  verified: {receipt.verified}  ({receipt.verification_note})")
    if receipt.error:
        print(f"error: {receipt.error}", file=sys.stderr)
        return 1
    return 0


def _cmd_write_activate(args: argparse.Namespace) -> int:
    ops = _build_write_operations(args)
    plan = ops.plan_activate_thought(args.brain_id, args.thought_id)
    print(f"plan {plan.plan_id}: {plan.description}")
    receipt = ops.apply(plan, approved=True)
    print(f"status: {receipt.status}  verified: {receipt.verified}  ({receipt.verification_note})")
    if receipt.error:
        print(f"error: {receipt.error}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="corykidion",
        description=(
            "A small, local-first, read-only-first bridge to TheBrain. "
            "See WORKING_ARCHITECTURE.md for the design this implements."
        ),
    )
    parser.add_argument(
        "--config", default=None, help="path to a TOML config file (optional; env vars work too)"
    )
    parser.add_argument(
        "--allow-brain",
        action="append",
        default=[],
        help="restrict operations to this brain_id; repeatable. Omit for no scope restriction.",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="check the app is running and list visible brains")
    p_status.set_defaults(func=_cmd_status)

    p_caps = sub.add_parser("capabilities", help="list evidenced vs candidate operations")
    p_caps.set_defaults(func=_cmd_capabilities)

    p_thought = sub.add_parser("thought", help="Thought operations")
    thought_sub = p_thought.add_subparsers(dest="thought_command", required=True)

    p_thought_get = thought_sub.add_parser("get", help="retrieve one Thought")
    p_thought_get.add_argument("brain_id")
    p_thought_get.add_argument("thought_id")
    p_thought_get.set_defaults(func=_cmd_thought_get)

    p_thought_find = thought_sub.add_parser("find-url", help="find an attachment by URL")
    p_thought_find.add_argument("brain_id")
    p_thought_find.add_argument("url")
    p_thought_find.set_defaults(func=_cmd_thought_find_url)

    p_thought_search = thought_sub.add_parser("search", help="search Thoughts by name/label")
    p_thought_search.add_argument("brain_id")
    p_thought_search.add_argument("query")
    p_thought_search.add_argument("--max-results", type=int, default=10)
    p_thought_search.set_defaults(func=_cmd_thought_search)

    p_thought_graph = thought_sub.add_parser(
        "graph", help="compound context: parents, children, jumps, links, attachments"
    )
    p_thought_graph.add_argument("brain_id")
    p_thought_graph.add_argument("thought_id")
    p_thought_graph.set_defaults(func=_cmd_thought_graph)

    p_thought_notes = thought_sub.add_parser("notes", help="read a Thought's note content")
    p_thought_notes.add_argument("brain_id")
    p_thought_notes.add_argument("thought_id")
    p_thought_notes.set_defaults(func=_cmd_thought_notes)

    p_activity = sub.add_parser("activity", help="recent modification log for a Brain")
    p_activity.add_argument("brain_id")
    p_activity.add_argument("--max-logs", type=int, default=20)
    p_activity.set_defaults(func=_cmd_activity)

    p_export = sub.add_parser("export", help="export operations")
    export_sub = p_export.add_subparsers(dest="export_command", required=True)
    p_export_thought = export_sub.add_parser("thought", help="export one Thought as JSON")
    p_export_thought.add_argument("brain_id")
    p_export_thought.add_argument("thought_id")
    p_export_thought.add_argument("out", help="output file path")
    p_export_thought.set_defaults(func=_cmd_export_thought)

    p_write = sub.add_parser(
        "write",
        help=(
            "Phase 2: mutating operations. Every subcommand requires --approve "
            "and --journal explicitly; there is no default-approve path."
        ),
    )
    write_sub = p_write.add_subparsers(dest="write_command", required=True)

    p_write_attach = write_sub.add_parser("attach-url", help="attach a URL to a Thought")
    p_write_attach.add_argument("brain_id")
    p_write_attach.add_argument("thought_id")
    p_write_attach.add_argument("url")
    p_write_attach.add_argument("name")
    p_write_attach.add_argument("--approve", action="store_true", required=True)
    p_write_attach.add_argument("--journal", required=True, help="path to the operation journal")
    p_write_attach.set_defaults(func=_cmd_write_attach_url)

    p_write_activate = write_sub.add_parser("activate", help="activate a Thought")
    p_write_activate.add_argument("brain_id")
    p_write_activate.add_argument("thought_id")
    p_write_activate.add_argument("--approve", action="store_true", required=True)
    p_write_activate.add_argument("--journal", required=True, help="path to the operation journal")
    p_write_activate.set_defaults(func=_cmd_write_activate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except CorykidionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
