# Sources

Every factual claim in this repository traces to one of the public sources below. Each was fetched and checked when the catalog was generated on 2026-11-08. Re-run the checks to confirm they still hold.

## Primary: Zoho Recruit API documentation

Base: `https://www.zoho.com/recruit/developer-guide/apiv2/`

| Source | URL | Used for |
|---|---|---|
| Documentation navigation manifest | `https://www.zohowebstatic.com/sites/zweb/json/api/recruit-api-menu.json` | Complete, authoritative list of API documentation pages |
| API index | `https://www.zoho.com/recruit/developer-guide/apiv2/` | Section structure: REST API, Bulk API, Hiring Pipeline, OAuth, limits |
| Modules API | `https://www.zoho.com/recruit/developer-guide/apiv2/modules-api.html` | Module listing endpoint, `api_name` semantics, module metadata |
| Record APIs | `.../get-records.html`, `.../insert-records.html`, `.../update-records.html`, `.../delete-records.html`, `.../search-records.html`, `.../upsert-records.html`, `.../change-status.html` | Record read, write, search, and status operations with scopes |
| Notes APIs | `.../get-notes.html`, `.../create-notes.html`, `.../update-notes.html`, `.../delete-notes.html` | Note operations |
| Tags APIs | `.../add-tags.html`, `.../remove-tags.html`, `.../create-tag.html`, `.../delete-tag.html`, `.../merge-tag.html`, `.../get-tag-list.html`, `.../update-tags.html`, `.../tag-record-count.html` | Tag operations |
| Files & Attachments | `.../get-attachments.html`, `.../upload-attachment.html`, `.../download-attachments.html`, `.../delete-attachments.html`, `.../upload-image.html`, `.../download-image.html`, `.../delete-image.html`, `.../upload-document.html` | Binary and document operations |
| Hiring Pipeline | `.../create-pipeline.html`, `.../update-pipeline.html`, `.../change-pipeline.html`, `.../get-all-stages.html`, `.../add-new-stage.html`, `.../update-stage.html`, `.../delete-stage.html`, `.../get-hiring-pipeline-of-a-record.html` | Pipeline and stage operations |
| Bulk APIs | `.../bulk-read/*.html`, `.../bulk-write/*.html` | Bulk read and bulk write jobs |
| Submissions, Assessments, Reviews | `.../create-submission.html`, `.../change-submission-status.html`, `.../create-assessment.html`, `.../update-assessment.html`, `.../create-review.html`, `.../update-review.html` | Assessment and review operations |
| Metadata, Users, Roles, Profiles, Organization | `.../module-meta.html`, `.../field-meta.html`, `.../custom-view-meta.html`, `.../related-list-meta.html`, `.../get-users.html`, `.../get-roles.html`, `.../get-profiles.html`, `.../get-org-data.html` | Configuration and directory reads |

Verify with:

```bash
curl -sS -A 'Mozilla/5.0' https://www.zohowebstatic.com/sites/zweb/json/api/recruit-api-menu.json -o /tmp/recruit-menu.json
python3 -c "import json;d=json.load(open('/tmp/recruit-menu.json'));print(len(d['apiMenu']))"
```

## Primary: Zoho Recruit MCP

| Source | URL | Verified |
|---|---|---|
| Zoho Recruit MCP product page | `https://www.zoho.com/recruit/mcp.html` | Product exists; describes MCP clients (Claude, Cursor, Windsurf, VS Code) and that the integration URL comes from Zoho's MCP console |
| Zoho MCP service list | `https://www.zoho.com/mcp/services/zoho-services.html` | `Recruit` is listed among supported Zoho MCP services |
| Zoho MCP overview | `https://www.zoho.com/mcp/` | Zoho MCP exposes app tools and actions through MCP servers built in a configuration UI |
| Zoho MCP portal | `https://mcp.zoho.eu` | Where a Recruit MCP server and endpoint are created |

Verify with:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' -A 'Mozilla/5.0' https://www.zoho.com/recruit/mcp.html
curl -sS -A 'Mozilla/5.0' https://www.zoho.com/mcp/services/zoho-services.html | grep -io recruit | head -3
```

Both return `200` and a `Recruit` hit respectively.

## Runtime: mcporter

`mcporter` is the MCP client CLI bundled with OpenClaw. This repository's scripts call it as a subprocess without a shell and redact the endpoint from its output.

Discoverable behavior used by these scripts:

```bash
mcporter list --help
mcporter list <URL> --json --no-oauth
mcporter list <URL> --schema
mcporter call "<URL>.<tool>" --args '<json>'
```

`mcporter list ... --json` emits `{"mode": "server", ..., "tools": [...]}` for a single target and `{"mode": "list", "servers": [...]}` for a multi-server listing. Both shapes are handled by `scripts/discover_tools.py`.

## What is deliberately not asserted

- **No MCP tool names are published in this repository.** Tool names are assigned when a Zoho MCP server is created in the Zoho MCP console, and the set of enabled actions is configurable per server. Publishing guessed names would be wrong for every real endpoint. Live discovery with `scripts/discover_tools.py` is the only reliable source.
- **No claim that the 65 catalog operations are all MCP-exposed.** The catalog documents the REST API; a server exposes a configurable subset.
- **No claim that any tool is available on a particular customer endpoint.** Endpoint availability depends on the tenant, the connection's OAuth scopes, and the enabled action set.
- **No example or sample record IDs.** Zoho's documentation pages embed sample IDs; these were stripped during extraction so no one mistakes them for real records.

## Third-party write-ups

Not used as a source for this repository. Product pages and the official API documentation above are sufficient and authoritative, so no secondary description of Zoho's MCP tool set was relied upon.
