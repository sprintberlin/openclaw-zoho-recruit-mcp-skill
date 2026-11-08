# Zoho Recruit MCP

Connect your agent to Zoho Recruit — an applicant tracking system (ATS) — through the Model Context Protocol (MCP). This skill provides a verified catalog of Zoho's documented Recruit REST API, live tool discovery against a concrete MCP server, least-privilege scope profiles, and safe hiring workflows.

Zoho Recruit is a supported [Zoho MCP service](https://www.zoho.com/mcp/services/zoho-services.html). The endpoint comes from the Zoho MCP console at [mcp.zoho.eu](https://mcp.zoho.eu).

## What This Skill Includes

- Agent Skill instructions in `SKILL.md`
- A verified catalog of **65 documented Recruit API operations** in `references/api_catalog.jsonl`, each with HTTP method, URL, scope, purpose, and a link to the official documentation page
- Three least-privilege scope profiles plus a Developer setup profile in `references/ACTION_PROFILES.md`
- `scripts/discover_tools.py` — discovers the tools a live MCP server actually exposes, with capability checks and endpoint redaction
- `scripts/call_tool.py` — calls an explicitly named tool, refusing names the live server does not expose
- `scripts/lookup_api.py` — token-efficient local queries over the API catalog
- Multi-account profile support for single-account and multi-tenant setups
- Credential-free tests covering catalog integrity, endpoint resolution, and discovery logic

## Documented API vs. live MCP tools

These are two different things, and the skill keeps them apart:

| | What it is | Source of truth |
|---|---|---|
| **API catalog** | Zoho's documented Recruit REST API (v2 / v2.1) | `references/api_catalog.jsonl`, derived from the official developer guide |
| **Live MCP tools** | The tools *this* server exposes | `mcporter list` against the endpoint |

**No MCP tool names are published in this repository.** Zoho assigns tool names when a server is created, and the enabled action set is configurable per server. Guessed names would be wrong for every real endpoint — so the skill discovers them instead:

```bash
python3 scripts/discover_tools.py --json
```

## Requirements

| Requirement | Details |
|---|---|
| Zoho Recruit MCP server | A configured endpoint from [mcp.zoho.eu](https://mcp.zoho.eu) |
| mcporter | MCP client CLI (bundled with OpenClaw; elsewhere `npm i -g mcporter`) |
| Endpoint selection | `ZOHO_RECRUIT_MCP_URL` for one account; named profiles or `--mcp-url` for multiple accounts |
| Organization ID | `ZOHO_RECRUIT_ORGANIZATION_ID` or profile `organization_id` for scoped calls |

### Single-account setup

```bash
export ZOHO_RECRUIT_MCP_URL="https://your-org-zoho-recruit-xxxxx.zohomcp.eu/mcp/YOUR_TOKEN/message"
export ZOHO_RECRUIT_ORGANIZATION_ID="123456789"
```

To verify without printing credentials:

```bash
if [ -n "$ZOHO_RECRUIT_MCP_URL" ]; then echo "ZOHO_RECRUIT_MCP_URL is set"; else echo "ZOHO_RECRUIT_MCP_URL is not set"; fi
```

### Multiple accounts

Use one shared profile file instead of changing global environment variables:

```json
{
  "version": 1,
  "profiles": {
    "acme": {
      "services": {
        "recruit": { "env": "ACME_RECRUIT_MCP_URL", "organization_id": "123456789" }
      }
    }
  }
}
```

```bash
python3 scripts/discover_tools.py --profile acme
```

The default file is `~/.config/zoho-mcp/profiles.json`. Full format: [`references/MULTI_ACCOUNT.md`](references/MULTI_ACCOUNT.md).

## Quick Start

### Discover the live tools

```bash
python3 scripts/discover_tools.py
python3 scripts/discover_tools.py --filter candidate
python3 scripts/discover_tools.py --require search --require read
python3 scripts/discover_tools.py --save /tmp/recruit-tools.json
```

### Call a discovered tool

```bash
python3 scripts/call_tool.py "Exact_Tool_Name_From_Discovery" --args '{"module_api_name": "Candidates"}'
```

The script verifies the tool exists on the live server first, so a stale or invented name fails fast.

### Search the documented API catalog

```bash
python3 scripts/lookup_api.py --validate
python3 scripts/lookup_api.py --category records --names-only
python3 scripts/lookup_api.py --read-only
python3 scripts/lookup_api.py --search "attachment"
python3 scripts/lookup_api.py --operation "Change Status"
```

## Repository Files

- `CONTRIBUTING.md`: Direct GitHub issue and pull request workflow for humans and agents.
- `SKILL.md`: Agent Skill instructions.
- `references/ACTION_PROFILES.md`: Scope selection per profile, including the Developer setup profile.
- `references/api_catalog.jsonl`: 65 verified Recruit API operations with method, URL, scope, and doc link.
- `references/CATALOG_FORMAT.md`: Catalog schema, validation, and refresh procedure.
- `references/COMMON_WORKFLOWS.md`: Ordered workflows for frequent recruiting tasks.
- `references/MULTI_ACCOUNT.md`: Portable single-account and multi-account endpoint profiles.
- `references/SOURCES.md`: Every source with a verification command.
- `scripts/discover_tools.py`: Live MCP tool discovery with capability checks.
- `scripts/call_tool.py`: Guarded call of an explicitly named, live-verified tool.
- `scripts/lookup_api.py`: Local catalog queries.
- `scripts/mcp_endpoint.py`: Shared endpoint and profile resolver.
- `tests/`: Credential-free helper, resolver, and catalog tests.

## Security Notes

The bundled scripts call `mcporter` directly through `subprocess.run([...])` without shell expansion, and redact the endpoint from any error output. Applicant data is sensitive: it includes contact details, CVs, assessment results, and interview notes, and in some regions special-category data. Load only required records and never copy contents into chats, logs, tickets, or repositories. This repository publishes no endpoints, tokens, customer data, or record IDs.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The suite runs without credentials and without network access.

## Contributing

Bug reports, documentation corrections, catalog drift, and pull requests are welcome. Agents using this skill must file or link reproducible skill defects as part of completing the task. Use the normal GitHub CLI workflow described in [`CONTRIBUTING.md`](CONTRIBUTING.md); never include MCP URLs, tokens, candidate records, resumes, or personal data.

## Sources

All factual claims trace to public sources listed in [`references/SOURCES.md`](references/SOURCES.md), each with a verification command.
