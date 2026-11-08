# Multi-Account Profiles

One shared profile file lets a single agent serve several Zoho Recruit accounts without re-exporting environment variables or editing helper scripts.

## Profile file

Default location: `~/.config/zoho-mcp/profiles.json`
Override: `--profiles-file PATH` or `ZOHO_MCP_PROFILES_FILE`

```json
{
  "version": 1,
  "profiles": {
    "acme": {
      "services": {
        "recruit": {
          "env": "ACME_RECRUIT_MCP_URL",
          "organization_id": "123456789"
        }
      }
    },
    "globex": {
      "services": {
        "recruit": {
          "url_file": "~/.config/zoho-mcp/globex-recruit.url",
          "organization_id": "987654321"
        }
      }
    },
    "initech": {
      "services": {
        "recruit": {
          "url": "https://example.invalid/mcp/PLACEHOLDER/message"
        }
      }
    }
  }
}
```

The `url` value above is a placeholder. Never commit a real endpoint.

## Service entry fields

| Field | Meaning |
|---|---|
| `url` | Direct endpoint URL. Visible in the file, so only use it for placeholders. |
| `env` | Name of an environment variable holding the endpoint. Preferred. |
| `url_file` | Path to a file whose only content is the endpoint. Keeps it out of shell history and version control. |
| `organization_id` | Optional Zoho Recruit organization ID for organization-scoped calls. |

`url`, `env`, and `url_file` are alternatives; the resolver uses the first one that yields a value.

## Resolution order

Endpoint:

1. `--mcp-url`
2. `--profile`, then `ZOHO_RECRUIT_MCP_PROFILE`, then `ZOHO_MCP_PROFILE`
3. `ZOHO_RECRUIT_MCP_URL`

Organization ID:

1. `--organization-id`
2. selected profile's `organization_id`
3. `ZOHO_RECRUIT_ORGANIZATION_ID`
4. `ZOHO_ORGANIZATION_ID`

## Usage

```bash
python3 scripts/discover_tools.py --profile acme
python3 scripts/call_tool.py "Exact_Tool_Name" --profile acme --args '{"module_api_name": "Candidates"}'
python3 scripts/discover_tools.py --profile globex --json
```

## Security rules

- Never commit `~/.config/zoho-mcp/profiles.json` with real endpoints. It holds credentials.
- Prefer `env` over `url`. An environment variable can be injected by a secret manager at run time and never touches disk.
- Prefer `url_file` over `url` when an environment variable is not available. Keep the file readable only by the agent user.
- `--mcp-url` on the command line exposes the endpoint in shell history and process listings. Use it only for a one-off diagnostic with a throwaway endpoint.
- Never pass one account's endpoint or organization ID to another account's profile.
- The helper scripts redact the endpoint from all error output, but a chat message that echoes a tool result can still leak record data. Keep candidate data out of shared channels.

## Sharing one profile file across services

A profile can hold several services, so one profile can serve both Recruit and other Zoho apps:

```json
{
  "version": 1,
  "profiles": {
    "acme": {
      "services": {
        "recruit": { "env": "ACME_RECRUIT_MCP_URL" },
        "crm": { "env": "ACME_CRM_MCP_URL" }
      }
    }
  }
}
```

Each helper selects its own service key, so `--profile acme` resolves the Recruit endpoint for Recruit scripts and the CRM endpoint for CRM scripts.
