#!/usr/bin/env python3
"""Deterministic structural-governance checks for AI Memory Architecture manifests."""

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


def _reject_unknown_keys(data: dict[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ManifestError(f"{label} contains unknown field(s): {', '.join(unknown)}")


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"manifest not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError("manifest root must be a JSON object")
    _reject_unknown_keys(
        data,
        {"version", "core_memory", "authorities", "bookmarks", "references", "contradictions"},
        "manifest",
    )
    if data.get("version") != 1:
        raise ManifestError("manifest version must be 1")
    return data


def _safe_path(root: Path, raw: Any, label: str) -> tuple[Path, str]:
    if not isinstance(raw, str) or not raw.strip():
        raise ManifestError(f"{label} must be a non-empty relative path")
    candidate = Path(raw)
    if candidate.is_absolute():
        raise ManifestError(f"{label} must be relative: {raw}")
    resolved = (root / candidate).resolve()
    root_resolved = root.resolve()
    try:
        relative = resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ManifestError(f"{label} escapes project root: {raw}") from exc
    normalized = relative.as_posix()
    if normalized == ".":
        raise ManifestError(f"{label} must point to a file path: {raw}")
    return resolved, normalized


def _require_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key, [])
    if not isinstance(value, list):
        raise ManifestError(f"{key} must be a list")
    return value


def _required_text(item: dict[str, Any], key: str, label: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{label}.{key} must be a non-empty string")
    return value.strip()


def check_manifest(manifest_path: Path) -> list[Finding]:
    data = _load_manifest(manifest_path)
    root = manifest_path.parent.resolve()
    findings: list[Finding] = []

    core = data.get("core_memory")
    if core is not None:
        if not isinstance(core, dict):
            raise ManifestError("core_memory must be an object")
        _reject_unknown_keys(core, {"path", "max_bytes"}, "core_memory")
        core_path, _ = _safe_path(root, core.get("path"), "core_memory.path")
        max_bytes = core.get("max_bytes", 5000)
        if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes <= 0:
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
        label = f"authorities[{index}]"
        if not isinstance(item, dict):
            raise ManifestError(f"{label} must be an object")
        _reject_unknown_keys(item, {"domain", "path"}, label)
        domain = _required_text(item, "domain", label)
        raw_path = item.get("path")
        authority_path, normalized_path = _safe_path(root, raw_path, f"{label}.path")
        if domain in authority_by_domain:
            findings.append(Finding("DUPLICATE_AUTHORITY_DOMAIN", domain))
        else:
            authority_by_domain[domain] = normalized_path
        if normalized_path in authority_paths and authority_paths[normalized_path] != domain:
            findings.append(
                Finding(
                    "AUTHORITY_PATH_REUSED",
                    f"{normalized_path} is assigned to both {authority_paths[normalized_path]} and {domain}",
                )
            )
        else:
            authority_paths[normalized_path] = domain
        if not authority_path.is_file():
            findings.append(Finding("MISSING_AUTHORITY_FILE", str(raw_path)))

    bookmarks = _require_list(data, "bookmarks")
    bookmark_paths: set[str] = set()
    for index, item in enumerate(bookmarks):
        label = f"bookmarks[{index}]"
        if not isinstance(item, dict):
            raise ManifestError(f"{label} must be an object")
        _reject_unknown_keys(item, {"path", "target_domain", "target_path"}, label)
        bookmark_path, normalized_bookmark = _safe_path(root, item.get("path"), f"{label}.path")
        if normalized_bookmark in bookmark_paths:
            findings.append(Finding("DUPLICATE_BOOKMARK", normalized_bookmark))
        else:
            bookmark_paths.add(normalized_bookmark)
        if not bookmark_path.is_file():
            findings.append(Finding("MISSING_BOOKMARK_FILE", str(item.get("path"))))
        target_domain = _required_text(item, "target_domain", label)
        _, normalized_target = _safe_path(root, item.get("target_path"), f"{label}.target_path")
        authority_path = authority_by_domain.get(target_domain)
        if authority_path is None:
            findings.append(Finding("ORPHAN_BOOKMARK", f"{item.get('path')} -> {target_domain}"))
        elif authority_path != normalized_target:
            findings.append(
                Finding(
                    "BOOKMARK_TARGET_MISMATCH",
                    f"{item.get('path')} targets {normalized_target}; authority for {target_domain} is {authority_path}",
                )
            )

    references = _require_list(data, "references")
    for index, item in enumerate(references):
        label = f"references[{index}]"
        if not isinstance(item, dict):
            raise ManifestError(f"{label} must be an object")
        _reject_unknown_keys(item, {"source", "target"}, label)
        source, _ = _safe_path(root, item.get("source"), f"{label}.source")
        target, _ = _safe_path(root, item.get("target"), f"{label}.target")
        if not source.is_file():
            findings.append(Finding("MISSING_REFERENCE_SOURCE", str(item.get("source"))))
        if not target.is_file():
            findings.append(
                Finding("STALE_REFERENCE", f"{item.get('source')} -> missing {item.get('target')}")
            )

    contradictions = _require_list(data, "contradictions")
    contradiction_ids: set[str] = set()
    for index, item in enumerate(contradictions):
        label = f"contradictions[{index}]"
        if not isinstance(item, dict):
            raise ManifestError(f"{label} must be an object")
        _reject_unknown_keys(item, {"id", "status"}, label)
        contradiction_id = _required_text(item, "id", label)
        status = item.get("status")
        if status not in {"resolved", "unresolved"}:
            raise ManifestError(f"{label}.status must be 'resolved' or 'unresolved'")
        if contradiction_id in contradiction_ids:
            findings.append(Finding("DUPLICATE_CONTRADICTION_ID", contradiction_id))
        else:
            contradiction_ids.add(contradiction_id)
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
