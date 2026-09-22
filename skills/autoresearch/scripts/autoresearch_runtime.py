#!/usr/bin/env python3
"""CLI boundary for deterministic AutoResearch state transitions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from autoresearch_runtime_core import RuntimeErrorResponse, RuntimeService


def _read_request(value: str | None) -> dict[str, Any]:
    if value is None:
        raise RuntimeErrorResponse(
            "MISSING_REQUEST",
            "Mutation commands require --request <path|->",
        )
    try:
        text = sys.stdin.read() if value == "-" else Path(value).read_text(encoding="utf-8")
        request = json.loads(text)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeErrorResponse("INVALID_REQUEST_JSON", str(error)) from error
    if not isinstance(request, dict):
        raise RuntimeErrorResponse(
            "INVALID_REQUEST_JSON", "Request JSON must be an object"
        )
    return request


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autoresearch-runtime",
        description="Validate and apply AutoResearch Graph/Experiment transitions.",
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Root of the concrete research project, not the skill package.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "propose", "start-run", "finish-run"):
        subparser = subcommands.add_parser(command)
        subparser.add_argument(
            "--request",
            required=True,
            help="JSON request file, or - to read from stdin.",
        )
    subcommands.add_parser("inspect")
    validate = subcommands.add_parser("validate")
    validate.add_argument(
        "--no-render",
        action="store_true",
        help="Validate without regenerating EXPERIMENT_GRAPH.html.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        service = RuntimeService(args.project_root)
        if args.command == "init":
            response = service.initialize(_read_request(args.request))
        elif args.command == "inspect":
            response = service.inspect()
        elif args.command == "propose":
            response = service.propose(_read_request(args.request))
        elif args.command == "start-run":
            response = service.start_run(_read_request(args.request))
        elif args.command == "finish-run":
            response = service.finish_run(_read_request(args.request))
        elif args.command == "validate":
            response = service.validate(render=not args.no_render)
        else:
            raise RuntimeErrorResponse("UNKNOWN_COMMAND", args.command)
    except RuntimeErrorResponse as error:
        response = error.response()
    except (FileNotFoundError, ValueError) as error:
        response = RuntimeErrorResponse("RUNTIME_ERROR", str(error)).response()
    json.dump(response, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if response.get("accepted") else 2


if __name__ == "__main__":
    raise SystemExit(main())
