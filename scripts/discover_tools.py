#!/usr/bin/env python3
"""Discover the live tools a Zoho Recruit MCP server actually exposes.

This is the authoritative source of truth for tool names. The bundled
`references/api_catalog.jsonl` documents Zoho's Recruit REST API; it never
proves which MCP tools a concrete server has enabled.

Exit codes:
  0  required capabilities found
  2  usage / endpoint resolution error
  3  mcporter failed or returned unusable output
  4  required capabilities missing
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from mcp_endpoint import (  # noqa: E402
    EndpointResolutionError,
    add_endpoint_arguments,
    redact,
    resolve_mcp_url,
)

DEFAULT_TIMEOUT = 60

# Capability hints are search patterns, never asserted tool names.
CAPABILITY_HINTS = {
    "search": ["search"],
    "read": ["get", "list", "fetch", "retrieve", "read"],
    "create": ["create", "insert", "add"],
    "update": ["update", "edit", "modify"],
    "status": ["status", "stage"],
    "notes": ["note"],
    "tag": ["tag"],
    "attachment": ["attach", "file", "document", "photo"],
    "pipeline": ["pipeline", "stage"],
}


def build_parser():
    parser = argparse.ArgumentParser(
        description="Discover live tools on a Zoho Recruit MCP server (never prints the endpoint)."
    )
    add_endpoint_arguments(parser)
    parser.add_argument(
        "--require",
        metavar="CAP",
        action="append",
        default=[],
        help="capability that must be present (repeatable): " + ", ".join(sorted(CAPABILITY_HINTS)),
    )
    parser.add_argument(
        "--filter",
        metavar="TERM",
        help="only show tools whose name or description contains TERM (case-insensitive)",
    )
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument(
        "--save",
        metavar="PATH",
        help="write the discovered tool inventory to PATH",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"mcporter timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    return parser


def run_mcporter_list(mcp_url, timeout=DEFAULT_TIMEOUT):
    """Run `mcporter list <url> --json` without a shell and never echo the URL."""
    command = ["mcporter", "list", mcp_url, "--json", "--no-oauth", "--timeout", str(timeout * 1000)]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout + 15, check=False
        )
    except FileNotFoundError as exc:
        raise McporterDiscoveryError("mcporter executable not found") from exc
    except subprocess.TimeoutExpired as exc:
        raise McporterDiscoveryError("mcporter list timed out") from exc

    if result.returncode != 0:
        raise McporterDiscoveryError(redact(result.stderr or result.stdout, mcp_url) or "mcporter list failed")

    raw = redact(result.stdout, mcp_url)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise McporterDiscoveryError(redact(result.stderr, mcp_url) or "mcporter returned invalid JSON") from exc
    return payload


class McporterDiscoveryError(RuntimeError):
    """Raised when live tool discovery cannot produce a usable inventory."""


def extract_tools(payload):
    """Normalize mcporter's list payloads into (name, description) tuples.

    mcporter emits `{"mode": "server", ...}` for a single target and
    `{"mode": "list", "servers": [...]}` for multi-server listings.
    """
    if not isinstance(payload, dict):
        return []

    if isinstance(payload.get("tools"), list):
        return [
            (str(t.get("name", "")).strip(), str(t.get("description") or "").strip())
            for t in payload["tools"]
            if isinstance(t, dict) and t.get("name")
        ]

    tools = []
    for server in payload.get("servers") or []:
        if not isinstance(server, dict):
            continue
        for tool in server.get("tools") or []:
            if isinstance(tool, dict) and tool.get("name"):
                tools.append(
                    (str(tool.get("name", "")).strip(), str(tool.get("description") or "").strip())
                )
    return tools


def server_status(payload):
    if not isinstance(payload, dict):
        return "unknown"
    if payload.get("status"):
        return str(payload["status"])
    servers = payload.get("servers")
    if isinstance(servers, list) and servers:
        statuses = {str(s.get("status")) for s in servers if isinstance(s, dict)}
        if len(statuses) == 1:
            return statuses.pop()
        if statuses:
            return "/".join(sorted(statuses))
    return "unknown"


def matches_capability(name, description, capability):
    """True when a live tool plausibly covers a capability.

    This is a discovery aid, not proof of an exact tool name.
    """
    hints = CAPABILITY_HINTS.get(capability)
    if not hints:
        return False
    haystack = f"{name} {description}".lower()
    return any(hint in haystack for hint in hints)


def filter_tools(tools, term):
    if not term:
        return tools
    needle = term.lower()
    return [(n, d) for n, d in tools if needle in n.lower() or needle in d.lower()]


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    unknown = [c for c in args.require if c not in CAPABILITY_HINTS]
    if unknown:
        parser.error("unknown capability: " + ", ".join(unknown))

    try:
        mcp_url = resolve_mcp_url(args, service="recruit", env_vars=("ZOHO_RECRUIT_MCP_URL",))
    except EndpointResolutionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    try:
        payload = run_mcporter_list(mcp_url, timeout=args.timeout)
    except McporterDiscoveryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 3

    tools = extract_tools(payload)
    if not tools:
        print(
            f"Error: no tools discovered (server status: {server_status(payload)})",
            file=sys.stderr,
        )
        return 3

    visible = filter_tools(tools, args.filter)
    missing = [
        cap
        for cap in args.require
        if not any(matches_capability(n, d, cap) for n, d in tools)
    ]

    if args.save:
        inventory = {
            "service": "recruit",
            "status": server_status(payload),
            "tool_count": len(tools),
            "tools": [{"name": n, "description": d} for n, d in sorted(set(tools))],
        }
        Path(args.save).write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.json:
        print(
            json.dumps(
                {
                    "service": "recruit",
                    "status": server_status(payload),
                    "tool_count": len(tools),
                    "matched": len(visible),
                    "missing_capabilities": missing,
                    "tools": [{"name": n, "description": d} for n, d in visible],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print(f"Live tools discovered: {len(tools)} (server status: {server_status(payload)})")
        for name, description in visible:
            line = f"  {name}"
            if description:
                line += f" — {description[:110]}"
            print(line)
        if args.filter and not visible:
            print(f"  (no tool matches '{args.filter}')")
        if missing:
            print("\nMissing capabilities: " + ", ".join(missing))
        elif args.require:
            print("\nAll required capabilities found.")

    return 4 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
