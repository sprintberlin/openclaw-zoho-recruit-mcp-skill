#!/usr/bin/env python3
"""Call one explicitly named tool on a Zoho Recruit MCP server.

Tool names are never guessed. Pass the exact name returned by
`scripts/discover_tools.py`; this script refuses to call anything not
present on the live server, so a stale or invented name fails fast
instead of hitting an unknown tool.

Exit codes:
  0  success
  2  usage / endpoint / resolution error
  3  mcporter or server error
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from discover_tools import McporterDiscoveryError, run_mcporter_list  # noqa: E402
from mcp_endpoint import (  # noqa: E402
    EndpointResolutionError,
    add_endpoint_arguments,
    redact,
    resolve_mcp_url,
)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Call an explicitly named, live-verified tool on a Zoho Recruit MCP server."
    )
    parser.add_argument("tool", help="exact tool name from discover_tools.py")
    add_endpoint_arguments(parser)
    parser.add_argument("--args", metavar="JSON", help="JSON object of arguments")
    parser.add_argument("--args-file", metavar="PATH", help="file containing the JSON object of arguments")
    parser.add_argument("--skip-verify", action="store_true", help="skip the live tool check (not recommended)")
    parser.add_argument("--timeout", type=int, default=30, help="timeout in seconds (default: 30)")
    return parser


def load_arguments(args, parser):
    if args.args and args.args_file:
        parser.error("use either --args or --args-file, not both")
    raw = args.args
    if args.args_file:
        try:
            raw = Path(args.args_file).read_text(encoding="utf-8")
        except OSError as exc:
            parser.error(f"cannot read --args-file: {exc}")
    if not raw:
        return {}
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        parser.error(f"arguments are not valid JSON: {exc}")
    if not isinstance(document, dict):
        parser.error("arguments must be a JSON object")
    return document


def verify_tool(mcp_url, tool_name, timeout=60, lister=None):
    """Confirm the tool exists on the live server before calling it.

    ``lister`` is injectable for credential-free tests; production callers
    use the real ``run_mcporter_list``.
    """
    payload = (lister or run_mcporter_list)(mcp_url, timeout=timeout)
    if isinstance(payload, dict) and isinstance(payload.get("tools"), list):
        names = {str(t.get("name", "")) for t in payload["tools"] if isinstance(t, dict)}
    else:
        names = set()
        for server in payload.get("servers") or [] if isinstance(payload, dict) else []:
            if isinstance(server, dict):
                for tool in server.get("tools") or []:
                    if isinstance(tool, dict):
                        names.add(str(tool.get("name", "")))
    return tool_name in names


def call_tool(mcp_url, tool_name, arguments, timeout=30):
    command = [
        "mcporter",
        "call",
        f"{mcp_url}.{tool_name}",
        "--args",
        json.dumps(arguments, ensure_ascii=False),
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError:
        raise McporterDiscoveryError("mcporter executable not found")
    except subprocess.TimeoutExpired:
        raise McporterDiscoveryError("mcporter call timed out")

    if result.returncode != 0:
        raise McporterDiscoveryError(redact(result.stderr or result.stdout, mcp_url) or "mcporter call failed")

    raw = redact(result.stdout, mcp_url)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise McporterDiscoveryError(redact(result.stderr, mcp_url) or "mcporter returned invalid JSON")
    return unwrap_content(payload)


def unwrap_content(payload):
    """Unwrap raw MCP content when mcporter returns the complete envelope."""
    if not isinstance(payload, dict):
        return payload
    result = payload.get("result")
    if not isinstance(result, dict):
        return payload
    content = result.get("content")
    if not isinstance(content, list) or not content:
        return payload
    first = content[0]
    if not isinstance(first, dict) or "text" not in first:
        return payload
    text = first["text"]
    if not isinstance(text, str):
        return text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"text": text}


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    arguments = load_arguments(args, parser)

    try:
        mcp_url = resolve_mcp_url(args, service="recruit", env_vars=("ZOHO_RECRUIT_MCP_URL",))
    except EndpointResolutionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if not args.skip_verify:
        try:
            if not verify_tool(mcp_url, args.tool, timeout=max(args.timeout, 60)):
                print(
                    f"Error: tool '{args.tool}' is not exposed by the live server. "
                    "Run scripts/discover_tools.py and use an exact discovered name.",
                    file=sys.stderr,
                )
                return 2
        except McporterDiscoveryError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 3

    try:
        payload = call_tool(mcp_url, args.tool, arguments, timeout=args.timeout)
    except McporterDiscoveryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 3

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
