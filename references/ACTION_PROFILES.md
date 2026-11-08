# Action Profiles

Profiles describe which Recruit capabilities to enable on a Zoho Recruit MCP server. They are guidance for the person who builds the server in the Zoho MCP UI, and for the agent that uses it.

Scope strings follow Zoho's documented naming. `scope=ZohoRecruit.modules.{module_name}.{operation_type}` covers most record work; `scope=ZohoRecruit.settings.*` covers configuration.

Documented module names for record scopes: `candidate`, `application`, `jobopening`, `interview`, `client`, `contact`, `review`, `department`, `task`, `event`, `vendor`, `campaign`, `submission`, and `custommodule`.

Documented operation types: `ALL` (full access), `READ`, `CREATE`, `UPDATE`, `DELETE`.

## recruit-reader

Purpose: triage, CV review, reporting. No mutations.

Enable read scope for the modules the task needs:

| Scope | Covers |
|---|---|
| `scope=ZohoRecruit.modules.candidate.READ` | Candidates |
| `scope=ZohoRecruit.modules.jobopening.READ` | Job Openings |
| `scope=ZohoRecruit.modules.application.READ` | Applications |
| `scope=ZohoRecruit.modules.interview.READ` | Interviews |
| `scope=ZohoRecruit.modules.contact.READ` | Contacts |
| `scope=ZohoRecruit.search.READ` | Search Records |
| `scope=ZohoRecruit.modules.attachments.all` | Attachment listing and download |

Optional, only if the agent must read hiring configuration:

| Scope | Covers |
|---|---|
| `scope=ZohoRecruit.settings.modules.read` | Module metadata |
| `scope=ZohoRecruit.settings.fields.read` | Field metadata |
| `scope=ZohoRecruit.settings.profiles.READ` | Profiles |

Keep disabled: every `CREATE`, `UPDATE`, and `DELETE` operation, bulk read and bulk write, pipeline and stage management, tag creation and merge, blueprint revocation.

## recruit-coordinator

Purpose: day-to-day recruiting. Adds the minimum write surface needed to move candidates forward.

Reader scopes, plus:

| Scope | Covers |
|---|---|
| `scope=ZohoRecruit.modules.candidate.UPDATE` | Candidate record updates and stage changes |
| `scope=ZohoRecruit.modules.application.UPDATE` | Application updates and status changes |
| `scope=ZohoRecruit.modules.notes.CREATE` | Creating notes |
| `scope=ZohoRecruit.modules.notes.READ` | Reading notes |
| `scope=ZohoRecruit.modules.notes.UPDATE` | Updating notes |
| `scope=ZohoRecruit.settings.tags.all` | Adding and removing tags on records |

Keep disabled: `DELETE` on every module, bulk read and bulk write, pipeline and stage administration, tag creation and merge, submission status changes, assessments and reviews write access, blueprint revocation.

## recruit-admin

Purpose: server setup, pipeline and stage maintenance, corrective work.

Everything in `recruit-coordinator`, plus:

| Scope | Covers |
|---|---|
| `scope=ZohoRecruit.settings.pipeline.ALL` | Pipeline create, update, transfer, delete |
| `scope=ZohoRecruit.settings.stage.ALL` | Stage create, update, delete |
| `scope=ZohoRecruit.modules.candidate.ALL` | Full candidate access including delete |
| `scope=ZohoRecruit.bulk.read` | Bulk read jobs |
| `scope=ZohoRecruit.bulk.write` | Bulk write jobs |
| `scope=ZohoRecruit.modules.submission.ALL` | Submissions |
| `scope=ZohoRecruit.settings.modules.all` | Module metadata administration |
| `scope=ZohoRecruit.users.ALL` | Users |

This profile can delete applicant records and move whole pipelines. Use it for a specific authorized task, then disable it again. Do not leave it enabled on a production ATS endpoint.

## Developer setup profile

Purpose: build and verify a server. Read-heavy, and safe to enable temporarily.

| Scope | Covers |
|---|---|
| `scope=ZohoRecruit.setup.operation.all` | Modules API and setup metadata |
| `scope=ZohoRecruit.modules.candidate.READ` | Candidates |
| `scope=ZohoRecruit.modules.jobopening.READ` | Job Openings |
| `scope=ZohoRecruit.modules.interview.READ` | Interviews |
| `scope=ZohoRecruit.settings.modules.all` | Module metadata |
| `scope=ZohoRecruit.settings.fields.all` | Field metadata |
| `scope=ZohoRecruit.settings.related_lists.all` | Related list metadata |
| `scope=ZohoRecruit.settings.custom_views.all` | Custom view metadata |
| `scope=ZohoRecruit.settings.profiles.READ` | Profiles |
| `scope=ZohoRecruit.settings.roles.READ` | Roles |
| `scope=ZohoRecruit.users.READ` | Users |
| `scope=ZohoRecruit.org.all` | Organization details |

Use this profile to confirm that metadata endpoints answer correctly, then switch to the narrower runtime profile.

## Granting scopes in the Zoho MCP UI

1. Open the Recruit MCP server in the Zoho MCP console.
2. Add tools, then select the actions matching the profile.
3. Grant only the scopes listed above. A server with `ALL` scopes on every module is an admin server, not a reader.
4. Connect, copy the integration URL, and store it as a secret.
5. Confirm with live discovery:
   ```bash
   python3 scripts/discover_tools.py --json
   ```
6. Compare the discovered tool list against the intended profile. If a tool appears that should not be there, tighten the scope set in the Zoho MCP console and re-check.

## Reducing scope later

Recruit's documented scopes are granted per operation type, so a scope set can usually be narrowed without recreating the server. Always re-run live discovery after a scope change; the tool list is the only reliable confirmation.
