#!/usr/bin/env python3
"""Query the bundled Zoho Recruit API catalog locally.

The catalog documents what Zoho's Recruit REST API offers. It is not a list of
MCP tool names. Use `scripts/discover_tools.py` to see what a concrete MCP
server actually exposes.

Exit codes:
  0  success
  2  usage error
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

CATALOG_PATH = Path(__file__).resolve().parents[1] / "references" / "api_catalog.jsonl"

REQUIRED_FIELDS = ("operation", "method", "url", "category")


def load_catalog(path=CATALOG_PATH):
    """Load and validate the JSONL catalog. Raises ValueError on malformed rows."""
    entries = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{number}: invalid JSON: {exc}") from exc
            if not isinstance(entry, dict):
                raise ValueError(f"{path}:{number}: entry must be a JSON object")
            missing = [f for f in REQUIRED_FIELDS if not entry.get(f)]
            if missing:
                raise ValueError(f"{path}:{number}: missing field(s): {', '.join(missing)}")
            entries.append(entry)
    return entries


def search(entries, term):
    needle = term.lower()
    hits = []
    for entry in entries:
        haystack = " ".join(
            str(entry.get(f, ""))
            for f in ("operation", "purpose", "url", "category", "scopes", "doc")
        ).lower()
        if needle in haystack:
            hits.append(entry)
    return hits


def by_category(entries, category):
    needle = category.lower()
    return [e for e in entries if e["category"].lower() == needle]


def print_entry(entry, show_purpose=True):
    scopes = entry.get("scopes") or []
    line = f"{entry['method']:6} {entry['operation']}"
    if show_purpose and entry.get("purpose"):
        line += f" — {entry['purpose']}"
    print(line)
    print(f"       {entry['url']}")
    if scopes:
        print(f"       scope: {', '.join(scopes)}")
    print(f"       doc: {entry['doc']}")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Search the bundled Zoho Recruit API catalog (documented REST API, not MCP tool names)."
    )
    parser.add_argument("--search", metavar="TERM", help="free-text search across operation, purpose, URL, scope")
    parser.add_argument("--category", metavar="NAME", help="filter by catalog category")
    parser.add_argument("--operation", metavar="NAME", help="show entries whose operation contains NAME")
    parser.add_argument("--method", metavar="METHOD", choices=["GET", "POST", "PUT", "PATCH", "DELETE"], help="filter by HTTP method")
    parser.add_argument("--read-only", action="store_true", help="only show non-mutating operations")
    parser.add_argument("--names-only", action="store_true", help="print only operation names")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser.add_argument("--catalog", metavar="PATH", help="alternative catalog path")
    parser.add_argument("--validate", action="store_true", help="validate the catalog and report counts")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    path = Path(args.catalog) if args.catalog else CATALOG_PATH
    if not path.exists():
        print(f"Error: catalog not found: {path}", file=sys.stderr)
        return 2
    try:
        entries = load_catalog(path)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if args.validate:
        print(f"Catalog OK: {len(entries)} operations from {path}")
        categories = {}
        for entry in entries:
            categories[entry["category"]] = categories.get(entry["category"], 0) + 1
        for name in sorted(categories):
            print(f"  {name}: {categories[name]}")
        return 0

    selected = entries
    if args.search:
        selected = search(selected, args.search)
    if args.category:
        selected = by_category(selected, args.category)
    if args.operation:
        needle = args.operation.lower()
        selected = [e for e in selected if needle in e["operation"].lower()]
    if args.method:
        selected = [e for e in selected if e["method"] == args.method]
    if args.read_only:
        selected = [e for e in selected if e["method"] not in {"POST", "PUT", "PATCH", "DELETE"}]

    if not selected:
        print("No catalog entries matched.", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(selected, indent=2, ensure_ascii=False))
    elif args.names_only:
        for entry in selected:
            print(f"{entry['method']:6} {entry['operation']}")
    else:
        for entry in selected:
            print_entry(entry)
            print()
        print(f"{len(selected)} operation(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
