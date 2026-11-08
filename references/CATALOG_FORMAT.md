# Catalog Format

`references/api_catalog.jsonl` is the machine-readable catalog of Zoho's documented Recruit REST API. One JSON object per line.

## Schema

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | Slug derived from operation and URL. Stable identifier for referencing an entry. |
| `operation` | string | yes | Human-readable operation name, cleaned from the documentation page title. |
| `method` | string | yes | HTTP method: `GET`, `POST`, `PUT`, `PATCH`, or `DELETE`. |
| `url` | string | yes | Documented request URL, with placeholders like `{module_api_name}` and `{record_id}` left unexpanded. |
| `purpose` | string | yes | The documented "Purpose" sentence, trimmed. |
| `scopes` | array of strings | yes | Documented scope expressions. Empty when the page documents no scope. |
| `section` | string | yes | Documentation path, for example `REST API > Record APIs > Get Records`. |
| `category` | string | yes | Normalized grouping used by `--category`. |
| `doc` | string | yes | Canonical URL of the official documentation page. |

Categories: `records`, `notes`, `tags`, `metadata`, `modules`, `files`, `pipeline`, `bulk`, `submissions`, `assessments`, `reviews`, `roles`, `profiles`, `organization`, `users`.

## What the catalog is and is not

The catalog is derived from Zoho's public Recruit API documentation. It describes the REST API surface.

It is **not**:

- a list of MCP tool names
- proof that any operation is enabled on a specific MCP server
- a guarantee that a given Zoho tenant exposes every documented operation

Use `scripts/discover_tools.py` for what a server actually exposes, and `scripts/lookup_api.py` for what an operation does.

## Querying the catalog

```bash
python3 scripts/lookup_api.py --validate
python3 scripts/lookup_api.py --category records --names-only
python3 scripts/lookup_api.py --read-only --json
python3 scripts/lookup_api.py --search "attachment"
python3 scripts/lookup_api.py --operation "Change Status"
python3 scripts/lookup_api.py --method GET
```

`--read-only` selects every operation whose method is not `POST`, `PUT`, `PATCH`, or `DELETE`. Use it to build a read-only scope proposal.

## Refreshing the catalog

The catalog is derived from the official documentation navigation manifest at `https://www.zohowebstatic.com/sites/zweb/json/api/recruit-api-menu.json`. The manifest lists every page in the `apiv2` documentation tree.

Refresh procedure:

1. Download the manifest and collect every link under `/recruit/developer-guide/apiv2/`.
2. Fetch each documentation page.
3. Extract the `Purpose`, `Request URL`, `Request Method`, and `Scope` sections.
4. Write one JSON object per line, following the schema above.
5. Validate:
   ```bash
   python3 scripts/lookup_api.py --validate
   ```
6. Confirm no credentials or record IDs leaked into the file:
   ```bash
   grep -nEi 'zoho-oauthtoken|password|client_secret|ghp_|[0-9]{12,}' references/api_catalog.jsonl
   ```
   This must produce no output.
7. Run the test suite:
   ```bash
   python3 -m unittest discover -s tests -v
   ```

## Invariants the tests enforce

- Every entry has all required fields.
- Every `method` is a valid HTTP method.
- Every `url` is an absolute `https://` Zoho URL.
- Every `doc` link points into `https://www.zoho.com/recruit/developer-guide/apiv2/`.
- The file contains no credential-like strings and no long numeric record IDs.
- Read and write operations are both represented.

## Adding an entry by hand

If a documented operation is missing, add a line by hand with the same field set, cite the documentation URL in `doc`, and keep `purpose` to one sentence. Never add an operation that is not documented in Zoho's public developer guide, and never add MCP tool names to this file.
