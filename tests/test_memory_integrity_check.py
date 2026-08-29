import json
import tempfile
import unittest
from pathlib import Path

from tools.memory_integrity_check import ManifestError, check_manifest


class MemoryIntegrityCheckTests(unittest.TestCase):
    def write(self, root: Path, rel: str, text: str = "x") -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def manifest(self, root: Path, data: dict) -> Path:
        path = root / "memory-integrity.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def base_manifest(self) -> dict:
        return {
            "version": 1,
            "core_memory": {"path": "memory-core.md", "max_bytes": 100},
            "authorities": [{"domain": "alpha", "path": "worklog.md"}],
            "bookmarks": [
                {
                    "path": "bookmark.md",
                    "target_domain": "alpha",
                    "target_path": "worklog.md",
                }
            ],
            "references": [{"source": "memory-core.md", "target": "worklog.md"}],
            "contradictions": [{"id": "decision-1", "status": "resolved"}],
        }

    def prepare_clean_files(self, root: Path) -> None:
        for name in ("memory-core.md", "worklog.md", "bookmark.md"):
            self.write(root, name)

    def test_clean_manifest_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.prepare_clean_files(root)
            findings = check_manifest(self.manifest(root, self.base_manifest()))
            self.assertEqual(findings, [])

    def test_duplicate_authority_and_orphan_bookmark_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.prepare_clean_files(root)
            self.write(root, "other.md")
            data = self.base_manifest()
            data["authorities"].append({"domain": "alpha", "path": "other.md"})
            data["bookmarks"][0]["target_domain"] = "missing"
            codes = {f.code for f in check_manifest(self.manifest(root, data))}
            self.assertIn("DUPLICATE_AUTHORITY_DOMAIN", codes)
            self.assertIn("ORPHAN_BOOKMARK", codes)

    def test_stale_reference_and_unresolved_contradiction_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.prepare_clean_files(root)
            data = self.base_manifest()
            data["references"][0]["target"] = "missing.md"
            data["contradictions"][0]["status"] = "unresolved"
            codes = {f.code for f in check_manifest(self.manifest(root, data))}
            self.assertIn("STALE_REFERENCE", codes)
            self.assertIn("UNRESOLVED_CONTRADICTION", codes)

    def test_oversized_core_memory_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "memory-core.md", "x" * 101)
            self.write(root, "worklog.md")
            self.write(root, "bookmark.md")
            codes = {f.code for f in check_manifest(self.manifest(root, self.base_manifest()))}
            self.assertIn("OVERSIZED_CORE_MEMORY", codes)

    def test_path_escape_is_invalid_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = self.base_manifest()
            data["core_memory"]["path"] = "../outside.md"
            with self.assertRaises(ManifestError):
                check_manifest(self.manifest(root, data))

    def test_path_aliases_are_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.prepare_clean_files(root)
            data = self.base_manifest()
            data["bookmarks"][0]["target_path"] = "./worklog.md"
            findings = check_manifest(self.manifest(root, data))
            self.assertNotIn("BOOKMARK_TARGET_MISMATCH", {f.code for f in findings})

    def test_reused_authority_path_alias_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.prepare_clean_files(root)
            data = self.base_manifest()
            data["authorities"].append({"domain": "beta", "path": "./worklog.md"})
            codes = {f.code for f in check_manifest(self.manifest(root, data))}
            self.assertIn("AUTHORITY_PATH_REUSED", codes)

    def test_duplicate_bookmark_and_contradiction_ids_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.prepare_clean_files(root)
            data = self.base_manifest()
            data["bookmarks"].append(
                {
                    "path": "./bookmark.md",
                    "target_domain": "alpha",
                    "target_path": "worklog.md",
                }
            )
            data["contradictions"].append({"id": " decision-1 ", "status": "resolved"})
            codes = {f.code for f in check_manifest(self.manifest(root, data))}
            self.assertIn("DUPLICATE_BOOKMARK", codes)
            self.assertIn("DUPLICATE_CONTRADICTION_ID", codes)

    def test_unknown_manifest_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.prepare_clean_files(root)
            data = self.base_manifest()
            data["mystery"] = True
            with self.assertRaises(ManifestError):
                check_manifest(self.manifest(root, data))


if __name__ == "__main__":
    unittest.main()
