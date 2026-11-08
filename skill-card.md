## Description: <br>
Connects an agent to Zoho Recruit — an applicant tracking system (ATS) — through MCP. It provides a verified catalog of 65 documented Recruit API operations, live tool discovery against a concrete MCP server, three least-privilege scope profiles plus a Developer setup profile, guarded tool invocation, and safe hiring workflows. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[sprintcx](https://clawhub.ai/user/sprintcx) <br>

### License/Terms of Use: <br>
MIT <br>

## Use Case: <br>
Developers, recruiting teams, and service providers use this skill to discover which tools a Zoho Recruit MCP server actually exposes, research what a documented Recruit API operation does, select least-privilege scopes for a connection, and execute applicant-tracking tasks such as triaging applicants, advancing a candidate stage, adding recruiter notes, and checking attachments. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: A Zoho Recruit MCP endpoint is credential-bearing and could expose applicant data if logged or shared. <br>
Mitigation: Treat endpoints like passwords, prefer profile indirection through environment variables or local URL files, never commit real profile files, and redact the endpoint from all helper output. <br>
Risk: Selecting the wrong account can read or change another organization's hiring pipeline. <br>
Mitigation: Resolve an explicit profile, discover the live tools before use, and verify the target record before any write. <br>
Risk: Write operations change candidate stages, notes, tags, and pipelines, which affects real people and real hiring decisions. <br>
Mitigation: Use least privilege, read before writing, keep delete, bulk, and pipeline-management operations out of routine profiles, and read results back. <br>
Risk: Recruit stores applicant personal data, including CVs, contact details, assessment results, and interview notes, and in some regions special-category data. <br>
Mitigation: Load only required records, keep candidate data out of chats, logs, tickets, and repositories, and treat bulk exports and attachments as sensitive data. <br>
Risk: Stale or invented MCP tool names cause failed calls or unintended actions. <br>
Mitigation: The skill publishes no tool names, discovers them live, and refuses to call a tool the live server does not expose. <br>

## Reference(s): <br>
- [GitHub source repository](https://github.com/sprintberlin/openclaw-zoho-recruit-mcp-skill) <br>
- [Zoho Recruit MCP](https://www.zoho.com/recruit/mcp.html) <br>
- [Zoho Recruit API documentation](https://www.zoho.com/recruit/developer-guide/apiv2/) <br>
- [Zoho MCP portal](https://mcp.zoho.eu) <br>

## Skill Output: <br>
The skill produces live tool inventories, documented API operation lookups, guarded MCP calls against a chosen Zoho Recruit account, and recruiter task reports that reference records by ID and never reproduce applicant personal data in output. <br>
