---
name: "zoho-recruit-mcp"
description: "Zoho Recruit MCP endpoint setup, live tool discovery, documented API catalog lookup, least-privilege profiles, and safe applicant-tracking workflows."
---

# Zoho Recruit MCP

Use Zoho Recruit — an applicant tracking system (ATS) — through an MCP endpoint from `mcp.zoho.eu`. This skill is the canonical home for Recruit-specific setup guidance, live tool discovery, the documented API catalog, least-privilege profiles, and safe hiring workflows.

Source: [sprintberlin/openclaw-zoho-recruit-mcp-skill](https://github.com/sprintberlin/openclaw-zoho-recruit-mcp-skill)

## Requirements

- A Zoho Recruit MCP endpoint from `mcp.zoho.eu`
- `mcporter`
- Endpoint configuration via `ZOHO_RECRUIT_MCP_URL`, `--profile`, or `--mcp-url`
- A Zoho Recruit organization ID for organization-scoped calls

Treat the endpoint as a credential. Never print it, commit it, or copy it into tickets, prompts, or chats.

## Two different things: the API catalog vs. live MCP tools

These are separate and must never be conflated:

| | What it is | What it proves | Source |
|---|---|---|---|
| **Documented API catalog** (`references/api_catalog.jsonl`) | Zoho's public Recruit REST API (v2 / v2.1), extracted from the official developer guide | What Zoho's API *documents* | `https://www.zoho.com/recruit/developer-guide/apiv2/` |
| **Live MCP tools** | The tools a concrete MCP server actually exposes | What *this server* *can do* | `mcporter list` against the endpoint |

`references/api_catalog.jsonl` contains 65 verified operations with their HTTP method, URL, scope, and a link to the official documentation page. It is **not** a list of MCP tool names. Zoho MCP servers expose a configurable subset of actions under server-assigned tool names, so never invent a tool name and never claim an operation is enabled without a live check.

## First setup

1. Create or open a Zoho Recruit connection at `mcp.zoho.eu`.
2. Select only the actions the task needs. Start from a profile: `python3 scripts/lookup_api.py --category records --read-only`.
3. Configure one endpoint with `ZOHO_RECRUIT_MCP_URL`, or named accounts using [references/MULTI_ACCOUNT.md](references/MULTI_ACCOUNT.md).
4. Configure the organization ID with `ZOHO_RECRUIT_ORGANIZATION_ID` or the selected profile's `organization_id`.
5. Discover the live tools. This is mandatory before the first call:
   ```bash
   python3 scripts/discover_tools.py --json
   ```
   Do not proceed until you have seen the actual tool names this server exposes.

Runtime tool names are assigned by Zoho when the MCP server is created. Do not guess them from the REST API paths in the catalog.

## Live tool discovery (required before every first use)

```bash
python3 scripts/discover_tools.py
python3 scripts/discover_tools.py --json
python3 scripts/discover_tools.py --filter candidate
python3 scripts/discover_tools.py --require search --require read
python3 scripts/discover_tools.py --save /tmp/recruit-tools.json
```

`--require` checks that a capability is present using name/description heuristics, so it is a *smoke test*, not proof of an exact tool name. Exit codes: `0` all required capabilities found, `2` endpoint or usage error, `3` mcporter failed, `4` a required capability is missing.

The script never prints the endpoint. It redacts the URL from all error output.

## Calling a live tool

Use `scripts/call_tool.py`. It verifies the tool exists on the live server before calling it, so a stale or invented name fails fast instead of silently doing something unintended.

```bash
python3 scripts/call_tool.py "Exact_Tool_Name_From_Discovery" --args '{"module_api_name": "Candidates"}'
```

Put complex nested arguments in a file to avoid shell quoting problems:

```bash
cat > /tmp/recruit-args.json <<'JSON'
{
  "body": {
    "data": [{ "Last_Name": "Example" }]
  }
}
JSON
python3 scripts/call_tool.py "Exact_Tool_Name_From_Discovery" --args-file /tmp/recruit-args.json
```

Arguments must match the schema the live server reports. Inspect it first:

```bash
mcporter list "$ZOHO_RECRUIT_MCP_URL" --schema
```

## Documented API catalog lookup

Use the local CLI instead of loading the whole catalog into context:

```bash
python3 scripts/lookup_api.py --validate
python3 scripts/lookup_api.py --category records --names-only
python3 scripts/lookup_api.py --read-only
python3 scripts/lookup_api.py --search "candidate"
python3 scripts/lookup_api.py --operation "Change Status"
python3 scripts/lookup_api.py --method GET --json
```

`references/api_catalog.jsonl` is the source of truth. See [references/CATALOG_FORMAT.md](references/CATALOG_FORMAT.md) for the schema and the refresh procedure.

## Endpoint and organization selection

For one account, set `ZOHO_RECRUIT_MCP_URL` and `ZOHO_RECRUIT_ORGANIZATION_ID`. For multiple accounts, pass `--profile NAME` to a bundled helper. Profiles default to `~/.config/zoho-mcp/profiles.json` and can reference an environment variable, a local URL file, or a direct URL.

Endpoint resolution order:

1. `--mcp-url`
2. `--profile`, `ZOHO_RECRUIT_MCP_PROFILE`, or `ZOHO_MCP_PROFILE`
3. `ZOHO_RECRUIT_MCP_URL`

Organization resolution order:

1. `--organization-id`
2. selected profile's `organization_id`
3. `ZOHO_RECRUIT_ORGANIZATION_ID`
4. `ZOHO_ORGANIZATION_ID`

One-off `--mcp-url` can expose the credential in shell history or process listings. Prefer a profile backed by an injected environment variable or `url_file`.

## Safe workflow

1. Resolve the exact account and organization before reading data. Never reuse an endpoint or organization ID from another customer.
2. Discover the live tools and read the target tool's schema before the first call.
3. Read the candidate, job opening, application, interview, or offer before changing it.
4. Use IDs returned by a live read. Never fabricate candidate IDs, job opening IDs, application IDs, or organization IDs.
5. Send only intended fields, then read the affected record back and compare IDs, stages, statuses, and owners.
6. Keep delete, bulk, pipeline- and stage-management, blueprint, and administrative operations disabled unless the task explicitly requires them.
7. Treat candidate emails, interview scheduling, offer letters, and status notifications as external communication requiring the active approval policy.

## Least-privilege profiles

Three profiles cover the common cases. See [references/ACTION_PROFILES.md](references/ACTION_PROFILES.md) for the exact scope selection per profile.

| Profile | Use for | Write access |
|---|---|---|
| `recruit-reader` | Triage, reporting, CV review | Read only |
| `recruit-coordinator` | Day-to-day recruiting | Candidate and application status, notes, tags |
| `recruit-admin` | Setup, pipeline and stage maintenance | Full, including delete and pipeline edits |

Start read-only. Add write scopes only when the task requires them.

## Recruit safeguards

Recruit holds personal data about applicants and, in many regions, special-category data. Treat every record as sensitive.

- Read the record before acting on it. Applicant status, stage, and pipeline changes affect real people and real hiring decisions.
- Never send a candidate's personal data (contact details, CV content, assessment results, interview notes) into chats, logs, tickets, or repositories.
- Stage and status changes are externally visible. Confirm the target candidate and job opening IDs before any change.
- Search for duplicate candidates by email and name before creating a record.
- Bulk read and bulk write operations move large volumes of applicant data. Use them only for an explicit, authorized task, and treat the exported file as sensitive data.
- Deleting a candidate record is destructive and may conflict with retention obligations. Keep delete operations out of routine profiles.
- Attachments, photos, and documents are binary. Verify a transfer by reading it back; binary upload support varies by server.
- Pipeline and stage changes affect every candidate in that stage. Read the affected records before and after a pipeline change.

## Report skill defects and contribute

Contributions are explicitly welcome from humans and agents. A Recruit task is complete only after serving the user and filing or linking every reproducible skill defect found.

- **Issue**: For schema mismatches, broken helpers or workflows, incorrect parameters, or catalog drift. File via GitHub CLI: `gh issue create --repo sprintberlin/openclaw-zoho-recruit-mcp-skill --title "bug: ..." --body "..."`.
- **Pull request**: Preferred when you can fix and verify the defect. Follow the standard branch, test, and PR workflow.
- See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution rules and `gh` workflows.

Do not file skill issues for endpoint/auth/profile setup, rate limits, transient service failures, timeouts, organization-specific custom fields, or unsupported Recruit operations. Never include MCP URLs, tokens, candidate records, resumes, or personal data.

## References

- [Action profiles](references/ACTION_PROFILES.md): scope selection per profile, including the Developer setup profile
- [API catalog](references/api_catalog.jsonl): 65 verified Recruit REST API operations, one JSON object per line
- [Catalog format](references/CATALOG_FORMAT.md): schema, lookup, import, and refresh
- [Common workflows](references/COMMON_WORKFLOWS.md): ordered procedures for frequent recruiting tasks
- [Multi-account profiles](references/MULTI_ACCOUNT.md): portable routing for single-account and multi-tenant setups
- [Contributing guide](CONTRIBUTING.md): issue and pull request workflows for humans and agents

Use `scripts/lookup_api.py` while researching what an operation does. Load a workflow while performing that task. Do not load the full catalog unless maintaining it.

## Troubleshooting

- **No endpoint configured**: set `ZOHO_RECRUIT_MCP_URL`, select `--profile`, or pass `--mcp-url`; never print the value.
- **No organization ID configured**: use `--organization-id`, profile `organization_id`, or `ZOHO_RECRUIT_ORGANIZATION_ID`.
- **Profile not found or wrong app**: verify `--profiles-file`, profile name, and `services.recruit`.
- **Tool missing**: the live server decides. Re-run `scripts/discover_tools.py`. A documented API operation existing does not mean an MCP tool for it is enabled.
- **Call rejected by the server**: the tool exists but the arguments do not match its schema. Inspect with `mcporter list "$ZOHO_RECRUIT_MCP_URL" --schema`.
- **OAuth scope error**: reconnect the affected Recruit connection. Never switch to another customer's endpoint.
- **Unexpected status or stage**: stop, read the saved record, and compare the candidate, job opening, and current stage before another write.
