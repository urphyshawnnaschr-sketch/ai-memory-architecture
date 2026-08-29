import json
import tempfile
import unittest
from pathlib import Path

from tools.adapters.cline_memory_bank import REQUIRED_FILES, build_manifest
from tools.memory_integrity_check import check_manifest
from tools.run_governance_benchmark import run_suite


class GovernanceBenchmarkTests(unittest.TestCase):
    def test_v0_1_suite_passes(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        suite = repo_root / "benchmarks" / "governance-v0.1" / "cases.json"
        results = run_suite(suite)
        failed = [result for result in results if not result.passed]
        self.assertEqual(failed, [])
        self.assertEqual(len(results), 16)


class ClineMemoryBankAdapterTests(unittest.TestCase):
    def write_core_files(self, root: Path, *, omit: str | None = None) -> None:
        for name in REQUIRED_FILES:
            if name == omit:
                continue
            (root / name).write_text(f"# {name}\n", encoding="utf-8")

    def write_manifest(self, root: Path) -> Path:
        path = root / "memory-integrity.json"
        path.write_text(json.dumps(build_manifest()), encoding="utf-8")
        return path

    def test_clean_cline_memory_bank_passes_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_core_files(root)
            findings = check_manifest(self.write_manifest(root))
            self.assertEqual(findings, [])

    def test_missing_progress_is_not_hidden_by_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_core_files(root, omit="progress.md")
            codes = {finding.code for finding in check_manifest(self.write_manifest(root))}
            self.assertIn("MISSING_AUTHORITY_FILE", codes)
            self.assertIn("MISSING_REFERENCE_SOURCE", codes)

    def test_overlay_keeps_scope_and_progress_separate(self) -> None:
        manifest = build_manifest()
        authorities = {item["domain"]: item["path"] for item in manifest["authorities"]}
        self.assertEqual(authorities["project-scope"], "projectBrief.md")
        self.assertEqual(authorities["project-progress"], "progress.md")
        self.assertEqual(manifest["bookmarks"], [])


if __name__ == "__main__":
    unittest.main()
