#!/usr/bin/env python3
"""Deterministic integrity checks for AI Memory Architecture manifests."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Finding:
    code: str
    message: str

    def render(self) -> str:
        return f"{self.code}: {self.message}"


class ManifestError(ValueError):
    pass


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError("manifest root must be a JSON object")
    if data.get("version") != 1:
        raise ManifestError("manifest version must be 1")
    return data


def _safe_path(root: Path, raw: Any, label: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ManifestError(f"{label} must be a non-empty relative path")
    candidate = Path(raw)
    if candidate.is_absolute():
        raise ManifestError(f"{label} must be relative: {raw}")
    resolved = (root / candidate).resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ManifestError(f"{label} escapes project root: {raw}") from exc
    return resolved


def _require_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key, [])
    if not isinstance(value, list):
        raise ManifestError(f"{key} must be a list")
    return value


def check_manifest(manifest_path: Path) -> list[Finding]:
    data = _load_manifest(manifest_path)
    root = manifest_path.parent.resolve()
    findings: list[Finding] = []

    core = data.get("core_memory")
    if core is not None:
        if not isinstance(core, dict):
            raise ManifestError("core_memory must be an object")
        core_path = _safe_path(root, core.get("path"), "core_memory.path")
        max_bytes = core.get("max_bytes", 5000)
        if not isinstance(max_bytes, int) or max_bytes <= 0:
            raise ManifestError("core_memory.max_bytes must be a positive integer")
        if not core_path.is_file():
            findings.append(Finding("MISSING_CORE_MEMORY", str(core.get("path"))))
        elif core_path.stat().st_size > max_bytes:
            findings.append(
                Finding(
                    "OVERSIZED_CORE_MEMORY",
                    f"{core.get('path')} is {core_path.stat().st_size} bytes; limit is {max_bytes}",
                )
            )

    authorities = _require_list(data, "authorities")
    authority_by_domain: dict[str, str] = {}
    authority_paths: dict[str, str] = {}

    for index, item in enumerate(authorities):
        if not isinstance(item, dict):
            raise ManifestError(f"authorities[{index}] must be an object")
        domain = item.get("domain")
        raw_path = item.get("path")
        if not isinstance(domain, str) or not domain.strip():
            raise ManifestError(f"authorities[{index}].domain must be a non-empty string")
        authority_path = _safe_path(root, raw_path, f"authorities[{index}].path")
        if domain in authority_by_domain:
            findings.append(Finding("DUPLICATE_AUTHORITY_DOMAIN", domain))
        else:
            authority_by_domain[domain] = str(raw_path)
        if str(raw_path) in authority_paths and authority_paths[str(raw_path)] != domain:
            findings.append(
                Finding(
                    "AUTHORITY_PATH_REUSED",
                    f"{raw_path} is assigned to both {authority_paths[str(raw_path)]} and {domain}",
                )
            )
        else:
            authority_paths[str(raw_path)] = domain
        if not authority_path.is_file():
            findings.append(Finding("MISSING_AUTHORITY_FILE", str(raw_path)))

    bookmarks = _require_list(data, "bookmarks")
    for index, item in enumerate(bookmarks):
        if not isinstance(item, dict):
            raise ManifestError(f"bookmarks[{index}] must be an object")
        bookmark_path = _safe_path(root, item.get("path"), f"bookmarks[{index}].path")
        if not bookmark_path.is_file():
            findings.append(Finding("MISSING_BOOKMARK_FILE", str(item.get("path"))))
        target_domain = item.get("target_domain")
        target_path = item.get("target_path")
        if not isinstance(target_domain, str) or not target_domain.strip():
            raise ManifestError(f"bookmarks[{index}].target_domain must be a non-empty string")
        _safe_path(root, target_path, f"bookmarks[{index}].target_path")
        authority_path = authority_by_domain.get(target_domain)
        if authority_path is None:
            findings.append(Finding("ORPHAN_BOOKMARK", f"{item.get('path')} -> {target_domain}"))
        elif authority_path != target_path:
            findings.append(
                Finding(
                    "BOOKMARK_TARGET_MISMATCH",
                    f"{item.get('path')} targets {target_path}; authority for {target_domain} is {authority_path}",
                )
            )

    references = _require_list(data, "references")
    for index, item in enumerate(references):
        if not isinstance(item, dict):
            raise ManifestError(f"references[{index}] must be an object")
        source = _safe_path(root, item.get("source"), f"references[{index}].source")
        target = _safe_path(root, item.get("target"), f"references[{index}].target")
        if not source.is_file():
            findings.append(Finding("MISSING_REFERENCE_SOURCE", str(item.get("source"))))
        if not target.is_file():
            findings.append(
                Finding("STALE_REFERENCE", f"{item.get('source')} -> missing {item.get('target')}")
            )

    contradictions = _require_list(data, "contradictions")
    for index, item in enumerate(contradictions):
        if not isinstance(item, dict):
            raise ManifestError(f"contradictions[{index}] must be an object")
        contradiction_id = item.get("id")
        status = item.get("status")
        if not isinstance(contradiction_id, str) or not contradiction_id.strip():
            raise ManifestError(f"contradictions[{index}].id must be a non-empty string")
        if status not in {"resolved", "unresolved"}:
            raise ManifestError(
                f"contradictions[{index}].status must be 'resolved' or 'unresolved'"
            )
        if status == "unresolved":
            findings.append(Finding("UNRESOLVED_CONTRADICTION", contradiction_id))

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest",
        nargs="?",
        default="memory-integrity.json",
        help="path to the v1 JSON manifest (default: memory-integrity.json)",
    )
    args = parser.parse_args(argv)

    try:
        findings = check_manifest(Path(args.manifest))
    except ManifestError as exc:
        print(f"INVALID_MANIFEST: {exc}", file=sys.stderr)
        return 2

    if findings:
        print(f"FAIL: {len(findings)} integrity finding(s)")
        for finding in findings:
            print(f"- {finding.render()}")
        return 1

    print("PASS: memory integrity checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
