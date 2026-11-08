# Contributing to openclaw-zoho-recruit-mcp-skill

Contributions from humans and agents are explicitly welcome. Issues and pull requests are both wanted. Prefer a pull request when you can implement and verify the fix.

## Issue

Use an issue for a reproducible defect, incomplete documentation, a live-schema mismatch, a broken helper or workflow, incorrect parameter guidance, or catalog drift.

1. Search open issues on GitHub first to link an existing match and avoid duplicates:
   ```bash
   gh issue list --repo sprintberlin/openclaw-zoho-recruit-mcp-skill --state open
   ```
2. If none exists, write a sanitized body file and create the issue with GitHub CLI (`gh`):
   ```bash
   cat > /tmp/zoho-recruit-issue.md <<'EOF'
   ### What happened
   ...

   ### Expected behavior
   ...

   ### Reproduction / Environment
   ...
   EOF
   gh issue create \
     --repo sprintberlin/openclaw-zoho-recruit-mcp-skill \
     --title "bug(schema): <short description>" \
     --body-file /tmp/zoho-recruit-issue.md
   ```
3. State expected and actual behavior plus minimal reproduction details.
4. Return the issue URL.

Do not file skill issues for endpoint, authentication or profile setup, rate limits, transient service failures, timeouts, organization-specific custom fields, or unsupported Recruit operations.

## Pull request

Use a pull request for a verified improvement or fix.

1. Branch from `main` and keep the change focused.
2. Add or update tests for behavior changes under `tests/`.
3. Run the test suite:
   ```bash
   python3 -m unittest discover -s tests
   ```
4. Verify that no credentials, tokens, candidate records, or personal data are included:
   ```bash
   grep -rnEi 'zoho-oauthtoken|password|client_secret|ghp_|[0-9]{12,}|@zohomcp\.' .
   ```
   This must produce no output outside of test fixtures.
5. Write a sanitized PR body file, then open the pull request with `gh pr create` and link its issue when present:
   ```bash
   cat > /tmp/zoho-recruit-pr.md <<'EOF'
   Resolves #<issue-number>

   ### Summary
   ...
   EOF
   gh pr create \
     --repo sprintberlin/openclaw-zoho-recruit-mcp-skill \
     --title "feat(discovery): add capability requirement checks" \
     --body-file /tmp/zoho-recruit-pr.md
   ```

## Refreshing the API catalog

The catalog in `references/api_catalog.jsonl` is derived from Zoho's public Recruit API documentation. When refreshing it, follow [`references/CATALOG_FORMAT.md`](references/CATALOG_FORMAT.md). Never add MCP tool names to the catalog and never add an operation that Zoho does not document publicly.

## Requirements

- Use an authenticated GitHub CLI (`gh`) with the required repository access.
- Never submit MCP URLs, tokens, live credentials, customer-specific identifiers, personal data, resumes, or applicant record content in issues, PRs, comments, or commits.
- Keep `SKILL.md` short, actionable, and imperative. Put reference material in `references/` and deterministic logic in `scripts/`.
- Preserve compatibility with `mcporter` and existing helper interfaces.
- Keep the documented API and live MCP tool discovery clearly separated. A tool name that was not observed on a live server must not appear in the catalog or in documentation as an available tool.
