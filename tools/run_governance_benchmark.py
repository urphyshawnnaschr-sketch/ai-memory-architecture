#!/usr/bin/env python3
"""Run the synthetic Memory Governance Benchmark V0.1 corpus."""

from __future__ import annotations

import argparse
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.memory_integrity_check import ManifestError, check_manifest


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    passed: bool
    expected: str
    observed: str


def _safe_case_path(root: Path, raw: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute():
        raise ValueError(f"benchmark file path must be relative: {raw}")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"benchmark file path escapes case root: {raw}") from exc
    return resolved


def _load_suite(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("benchmark suite version must be 1")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("benchmark suite must contain a non-empty cases list")
    return data


def run_case(case: dict[str, Any]) -> CaseResult:
    case_id = case.get("id")
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError("benchmark case id must be a non-empty string")
    files = case.get("files", {})
    manifest = case.get("manifest")
    expect = case.get("expect")
    if not isinstance(files, dict):
        raise ValueError(f"{case_id}: files must be an object")
    if not isinstance(manifest, dict):
        raise ValueError(f"{case_id}: manifest must be an object")
    if not isinstance(expect, dict):
        raise ValueError(f"{case_id}: expect must be an object")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for raw_path, content in files.items():
            if not isinstance(raw_path, str) or not isinstance(content, str):
                raise ValueError(f"{case_id}: file paths and contents must be strings")
            path = _safe_case_path(root, raw_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        manifest_path = root / "memory-integrity.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        kind = expect.get("kind")
        if kind == "findings":
            expected_codes = expect.get("codes")
            if not isinstance(expected_codes, list) or not all(
                isinstance(code, str) for code in expected_codes
            ):
                raise ValueError(f"{case_id}: expected codes must be a list of strings")
            try:
                findings = check_manifest(manifest_path)
            except ManifestError as exc:
                return CaseResult(
                    case_id,
                    False,
                    f"findings={sorted(expected_codes)}",
                    f"manifest_error={exc}",
                )
            observed_codes = sorted(finding.code for finding in findings)
            expected_sorted = sorted(expected_codes)
            return CaseResult(
                case_id,
                observed_codes == expected_sorted,
                f"findings={expected_sorted}",
                f"findings={observed_codes}",
            )

        if kind == "manifest_error":
            expected_text = expect.get("contains", "")
            if not isinstance(expected_text, str):
                raise ValueError(f"{case_id}: manifest_error contains must be a string")
            try:
                findings = check_manifest(manifest_path)
            except ManifestError as exc:
                observed = str(exc)
                return CaseResult(
                    case_id,
                    expected_text in observed,
                    f"manifest_error contains {expected_text!r}",
                    f"manifest_error={observed}",
                )
            return CaseResult(
                case_id,
                False,
                f"manifest_error contains {expected_text!r}",
                f"findings={[finding.code for finding in findings]}",
            )

        raise ValueError(f"{case_id}: unsupported expectation kind: {kind!r}")


def run_suite(path: Path) -> list[CaseResult]:
    suite = _load_suite(path)
    results: list[CaseResult] = []
    seen_ids: set[str] = set()
    for raw_case in suite["cases"]:
        if not isinstance(raw_case, dict):
            raise ValueError("benchmark cases must be objects")
        case_id = raw_case.get("id")
        if case_id in seen_ids:
            raise ValueError(f"duplicate benchmark case id: {case_id}")
        if isinstance(case_id, str):
            seen_ids.add(case_id)
        results.append(run_case(raw_case))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "suite",
        nargs="?",
        default="benchmarks/governance-v0.1/cases.json",
        help="path to benchmark cases JSON",
    )
    args = parser.parse_args(argv)

    try:
        results = run_suite(Path(args.suite))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"INVALID_BENCHMARK: {exc}")
        return 2

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {result.case_id}: expected {result.expected}; observed {result.observed}")

    passed = sum(result.passed for result in results)
    total = len(results)
    print(f"SUMMARY: {passed}/{total} benchmark cases passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
