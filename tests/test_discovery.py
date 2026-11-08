"""Tests for live tool discovery and the guarded caller.

These tests never contact a real MCP server. They exercise the parsing and
guarding logic against captured mcporter payload shapes.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import call_tool  # noqa: E402
import discover_tools  # noqa: E402


SERVER_PAYLOAD = {
    "mode": "server",
    "name": "recruit",
    "status": "ok",
    "tools": [
        {"name": "ZohoRecruit_search_records", "description": "Search records in a module using a criteria filter."},
        {"name": "ZohoRecruit_get_records", "description": "Get the list of available records from a module."},
        {"name": "ZohoRecruit_insert_records", "description": "Insert a record into a module."},
        {"name": "ZohoRecruit_update_record_status", "description": "Change the status of a candidate."},
        {"name": "ZohoRecruit_get_notes", "description": "Get notes data for a module."},
        {"name": "ZohoRecruit_add_tags", "description": "Add tags to a record."},
        {"name": "ZohoRecruit_upload_attachment", "description": "Upload an attachment to a record."},
    ],
}

MULTI_PAYLOAD = {
    "mode": "list",
    "servers": [
        {"name": "recruit", "status": "ok", "tools": [{"name": "A_tool", "description": "alpha"}]},
        {"name": "other", "status": "auth", "tools": [{"name": "B_tool", "description": "beta"}]},
    ],
}


class ExtractToolsTests(unittest.TestCase):
    def test_single_server_payload(self):
        tools = discover_tools.extract_tools(SERVER_PAYLOAD)
        self.assertEqual(len(tools), 7)
        self.assertIn("ZohoRecruit_get_records", [n for n, _ in tools])

    def test_multi_server_payload(self):
        tools = discover_tools.extract_tools(MULTI_PAYLOAD)
        self.assertEqual(len(tools), 2)

    def test_empty_payload(self):
        self.assertEqual(discover_tools.extract_tools({}), [])
        self.assertEqual(discover_tools.extract_tools({"tools": []}), [])
        self.assertEqual(discover_tools.extract_tools(None), [])

    def test_malformed_tool_entries_ignored(self):
        payload = {"tools": [{"name": "ok_tool"}, "not-a-dict", {"description": "no name"}]}
        tools = discover_tools.extract_tools(payload)
        self.assertEqual([n for n, _ in tools], ["ok_tool"])


class ServerStatusTests(unittest.TestCase):
    def test_single_server(self):
        self.assertEqual(discover_tools.server_status(SERVER_PAYLOAD), "ok")

    def test_multi_server_mixed(self):
        self.assertEqual(discover_tools.server_status(MULTI_PAYLOAD), "auth/ok")

    def test_unknown(self):
        self.assertEqual(discover_tools.server_status({}), "unknown")


class CapabilityTests(unittest.TestCase):
    def test_capabilities_detected(self):
        tools = discover_tools.extract_tools(SERVER_PAYLOAD)
        for capability in ("search", "read", "create", "update", "status", "notes", "tag", "attachment"):
            self.assertTrue(
                any(discover_tools.matches_capability(n, d, capability) for n, d in tools),
                f"capability {capability} not detected",
            )

    def test_unknown_capability_matches_nothing(self):
        self.assertFalse(discover_tools.matches_capability("X_tool", "", "not-a-capability"))


class FilterTests(unittest.TestCase):
    def test_filter_by_term(self):
        tools = discover_tools.extract_tools(SERVER_PAYLOAD)
        filtered = discover_tools.filter_tools(tools, "notes")
        self.assertEqual(len(filtered), 1)

    def test_filter_case_insensitive(self):
        tools = discover_tools.extract_tools(SERVER_PAYLOAD)
        self.assertEqual(len(discover_tools.filter_tools(tools, "ZOHORECRUIT")), len(tools))

    def test_no_filter_returns_all(self):
        tools = discover_tools.extract_tools(SERVER_PAYLOAD)
        self.assertEqual(discover_tools.filter_tools(tools, None), tools)


class CallToolGuardTests(unittest.TestCase):
    """Guard logic runs against an injected lister, never a real server."""

    def _lister(self, *_args, **_kwargs):
        return SERVER_PAYLOAD

    def test_verify_tool_accepts_discovered_name(self):
        self.assertTrue(
            call_tool.verify_tool(
                "https://x.example/mcp/1/message", "ZohoRecruit_get_records", lister=self._lister
            )
        )

    def test_verify_tool_rejects_unknown_name(self):
        self.assertFalse(
            call_tool.verify_tool(
                "https://x.example/mcp/1/message", "ZohoRecruit_invented", lister=self._lister
            )
        )

    def test_verify_tool_rejects_similar_but_absent_name(self):
        self.assertFalse(
            call_tool.verify_tool(
                "https://x.example/mcp/1/message", "ZohoRecruit_get_record", lister=self._lister
            )
        )

    def test_unwrap_content_parses_text_payload(self):
        payload = {"result": {"content": [{"type": "text", "text": json.dumps({"ok": True})}]}}
        self.assertEqual(call_tool.unwrap_content(payload), {"ok": True})

    def test_unwrap_content_passes_through_plain_payload(self):
        payload = {"data": [{"id": "1"}]}
        self.assertEqual(call_tool.unwrap_content(payload), payload)


class DiscoverCliTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "discover_tools.py"), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_missing_endpoint_exits_two(self):
        env = {"PATH": "/usr/bin:/bin", "HOME": "/tmp/nonexistent-recruit-home"}
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "discover_tools.py")],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("MCP_URL", result.stdout)

    def test_unknown_capability_is_usage_error(self):
        result = self.run_cli("--require", "not-a-capability")
        self.assertEqual(result.returncode, 2)

    def test_help_runs_without_credentials(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--require", result.stdout)


if __name__ == "__main__":
    unittest.main()
