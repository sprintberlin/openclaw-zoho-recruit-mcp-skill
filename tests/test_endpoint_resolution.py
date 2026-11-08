"""Credential-free tests for shared multi-account MCP endpoint resolution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from mcp_endpoint import (  # noqa: E402
    EndpointResolutionError,
    add_endpoint_arguments,
    redact,
    resolve_mcp_url,
    resolve_organization_id,
)


def parse(*arguments):
    parser = add_endpoint_arguments(argparse.ArgumentParser())
    return parser.parse_args(list(arguments))


class EndpointResolutionTests(unittest.TestCase):
    def test_direct_url_argument_wins(self):
        args = parse("--mcp-url", "https://direct.example.org/mcp/1/message")
        resolved = resolve_mcp_url(
            args,
            service="recruit",
            env_vars=("ZOHO_RECRUIT_MCP_URL",),
            environ={"ZOHO_RECRUIT_MCP_URL": "https://env.example.org/mcp/env/message"},
        )
        self.assertEqual(resolved, "https://direct.example.org/mcp/1/message")

    def test_environment_variable_used_when_no_profile(self):
        args = parse()
        resolved = resolve_mcp_url(
            args,
            service="recruit",
            env_vars=("ZOHO_RECRUIT_MCP_URL",),
            environ={"ZOHO_RECRUIT_MCP_URL": "https://env.example.org/mcp/env/message"},
        )
        self.assertEqual(resolved, "https://env.example.org/mcp/env/message")

    def test_missing_endpoint_raises(self):
        args = parse()
        with self.assertRaises(EndpointResolutionError):
            resolve_mcp_url(args, service="recruit", env_vars=("ZOHO_RECRUIT_MCP_URL",), environ={})

    def test_non_http_url_rejected(self):
        args = parse("--mcp-url", "ftp://example.org/mcp")
        with self.assertRaises(EndpointResolutionError):
            resolve_mcp_url(args, service="recruit", environ={})

    def test_url_with_whitespace_rejected(self):
        args = parse("--mcp-url", "https://example.org/mcp/a b")
        with self.assertRaises(EndpointResolutionError):
            resolve_mcp_url(args, service="recruit", environ={})

    def test_profile_with_inline_url(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            profiles_path = Path(temp_dir) / "profiles.json"
            profiles_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "profiles": {
                            "acme": {
                                "services": {
                                    "recruit": {"url": "https://recruit-a.example.org/mcp/token/message"}
                                }
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            args = parse("--profile", "acme", "--profiles-file", str(profiles_path))
            resolved = resolve_mcp_url(args, service="recruit", environ={})
            self.assertEqual(resolved, "https://recruit-a.example.org/mcp/token/message")

    def test_profile_with_env_reference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            profiles_path = Path(temp_dir) / "profiles.json"
            profiles_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "profiles": {"acme": {"services": {"recruit": {"env": "ACME_RECRUIT_URL"}}}},
                    }
                ),
                encoding="utf-8",
            )
            args = parse("--profile", "acme", "--profiles-file", str(profiles_path))
            resolved = resolve_mcp_url(
                args,
                service="recruit",
                environ={"ACME_RECRUIT_URL": "https://recruit-env.example.org/mcp/x/message"},
            )
            self.assertEqual(resolved, "https://recruit-env.example.org/mcp/x/message")

    def test_profile_with_url_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            url_file = Path(temp_dir) / "endpoint.url"
            url_file.write_text("https://recruit-file.example.org/mcp/y/message\n", encoding="utf-8")
            profiles_path = Path(temp_dir) / "profiles.json"
            profiles_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "profiles": {"acme": {"services": {"recruit": {"url_file": str(url_file)}}}},
                    }
                ),
                encoding="utf-8",
            )
            args = parse("--profile", "acme", "--profiles-file", str(profiles_path))
            resolved = resolve_mcp_url(args, service="recruit", environ={})
            self.assertEqual(resolved, "https://recruit-file.example.org/mcp/y/message")

    def test_profile_without_recruit_service_raises(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            profiles_path = Path(temp_dir) / "profiles.json"
            profiles_path.write_text(
                json.dumps({"version": 1, "profiles": {"acme": {"services": {"crm": {"url": "https://c.example.org/x"}}}}}),
                encoding="utf-8",
            )
            args = parse("--profile", "acme", "--profiles-file", str(profiles_path))
            with self.assertRaises(EndpointResolutionError):
                resolve_mcp_url(args, service="recruit", environ={})

    def test_missing_profile_raises(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            profiles_path = Path(temp_dir) / "profiles.json"
            profiles_path.write_text(json.dumps({"version": 1, "profiles": {}}), encoding="utf-8")
            args = parse("--profile", "nope", "--profiles-file", str(profiles_path))
            with self.assertRaises(EndpointResolutionError):
                resolve_mcp_url(args, service="recruit", environ={})

    def test_invalid_json_profile_raises(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            profiles_path = Path(temp_dir) / "profiles.json"
            profiles_path.write_text("{not json", encoding="utf-8")
            args = parse("--profile", "acme", "--profiles-file", str(profiles_path))
            with self.assertRaises(EndpointResolutionError):
                resolve_mcp_url(args, service="recruit", environ={})

    def test_redact_removes_endpoint(self):
        secret = "https://recruit.example.org/mcp/secret/message"
        self.assertNotIn(secret, redact(f"failed for {secret}", secret))
        self.assertIn("<MCP_URL>", redact(f"failed for {secret}", secret))


class OrganizationIdTests(unittest.TestCase):
    def test_explicit_argument_wins(self):
        args = parse("--organization-id", "111")
        resolved = resolve_organization_id(
            args, service="recruit", environ={"ZOHO_ORGANIZATION_ID": "222"}
        )
        self.assertEqual(resolved, "111")

    def test_environment_fallback(self):
        args = parse()
        resolved = resolve_organization_id(
            args, service="recruit", environ={"ZOHO_RECRUIT_ORGANIZATION_ID": "222"}
        )
        self.assertEqual(resolved, "222")

    def test_generic_environment_fallback(self):
        args = parse()
        resolved = resolve_organization_id(
            args, service="recruit", environ={"ZOHO_ORGANIZATION_ID": "333"}
        )
        self.assertEqual(resolved, "333")

    def test_profile_value_is_used(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            profiles_path = Path(temp_dir) / "profiles.json"
            profiles_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "profiles": {
                            "acme": {"services": {"recruit": {"url": "https://a.example/x", "organization_id": "444"}}}
                        },
                    }
                ),
                encoding="utf-8",
            )
            args = parse("--profile", "acme", "--profiles-file", str(profiles_path))
            self.assertEqual(resolve_organization_id(args, service="recruit", environ={}), "444")

    def test_missing_returns_none(self):
        args = parse()
        self.assertIsNone(resolve_organization_id(args, service="recruit", environ={}))

    def test_invalid_id_rejected(self):
        args = parse("--organization-id", "bad id; rm -rf")
        with self.assertRaises(EndpointResolutionError):
            resolve_organization_id(args, service="recruit", environ={})


if __name__ == "__main__":
    unittest.main()
