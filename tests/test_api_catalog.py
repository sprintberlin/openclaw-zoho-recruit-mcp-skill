"""Tests for the bundled Zoho Recruit API catalog and its lookup CLI."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lookup_api import CATALOG_PATH, load_catalog, search  # noqa: E402

VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}
MUTATING = {"POST", "PUT", "PATCH", "DELETE"}


class CatalogContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = load_catalog()

    def test_catalog_is_not_empty(self):
        self.assertGreater(len(self.entries), 40)

    def test_every_entry_has_required_fields(self):
        for entry in self.entries:
            for field in ("operation", "method", "url", "category", "doc"):
                self.assertTrue(entry.get(field), f"{field} missing in {entry}")

    def test_methods_are_valid_http_methods(self):
        for entry in self.entries:
            self.assertIn(entry["method"], VALID_METHODS)

    def test_urls_are_absolute_https_zoho_urls(self):
        for entry in self.entries:
            self.assertTrue(
                entry["url"].startswith("https://"),
                f"non-absolute URL: {entry['url']}",
            )
            self.assertIn("zoho.com", entry["url"])

    def test_doc_links_point_at_zoho_recruit_docs(self):
        for entry in self.entries:
            self.assertTrue(entry["doc"].startswith("https://www.zoho.com/recruit/developer-guide/apiv2/"))

    def test_catalog_contains_no_credentials(self):
        raw = CATALOG_PATH.read_text(encoding="utf-8").lower()
        for needle in ("zoho-oauthtoken", "password", "client_secret", "ghp_", "zohomcp.eu"):
            self.assertNotIn(needle, raw, f"catalog must not contain {needle!r}")

    def test_catalog_contains_no_long_numeric_record_ids(self):
        import re

        raw = CATALOG_PATH.read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"\b\d{12,}\b", raw), "catalog must not embed record IDs")

    def test_read_and_write_operations_are_both_present(self):
        read = [e for e in self.entries if e["method"] not in MUTATING]
        write = [e for e in self.entries if e["method"] in MUTATING]
        self.assertGreater(len(read), 10)
        self.assertGreater(len(write), 10)

    def test_core_record_operations_present(self):
        operations = {e["operation"].lower() for e in self.entries}
        for expected in ("get list of records", "insert records", "update records", "delete records", "search records"):
            self.assertIn(expected, operations)

    def test_search_matches_operation_and_purpose(self):
        hits = search(self.entries, "candidate")
        self.assertTrue(hits)
        self.assertTrue(any(e["category"] == "records" for e in hits))


class LookupCliTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "lookup_api.py"), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_validate_succeeds(self):
        result = self.run_cli("--validate")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Catalog OK", result.stdout)

    def test_names_only(self):
        result = self.run_cli("--names-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("GET", result.stdout)

    def test_read_only_filter_excludes_mutations(self):
        result = self.run_cli("--read-only", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        entries = json.loads(result.stdout)
        self.assertTrue(entries)
        for entry in entries:
            self.assertNotIn(entry["method"], MUTATING)

    def test_json_output_is_valid(self):
        result = self.run_cli("--category", "records", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        entries = json.loads(result.stdout)
        self.assertTrue(entries)
        for entry in entries:
            self.assertEqual(entry["category"], "records")

    def test_no_match_exits_with_two(self):
        result = self.run_cli("--search", "zzzz-not-a-real-operation")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
