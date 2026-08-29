#!/usr/bin/env python3
"""Run Authoritative-State Recovery Evaluation V0.1 via OpenAI Responses API.

The runner is deliberately evidence-first:
- every case is an independent API request;
- no hidden retry turns a failure into a success;
- prompts, raw API responses, parsed model outputs, scores, and run metadata are saved;
- OPENAI_API_KEY is read from the environment and is never written to disk.

Use --dry-run to validate the run plan without making network requests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.recovery_eval import (  # noqa: E402
    CONDITIONS,
    EvalError,
    load_corpus,
    render_prompt,
    score_output,
)

DEFAULT_ENDPOINT = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.6-sol"
DEFAULT_REASONING_EFFORT = "medium"
DEFAULT_SEED = 20260829
DEFAULT_MAX_OUTPUT_TOKENS = 1200
REASONING_EFFORTS = {"none", "low", "medium", "high", "xhigh", "max"}


class PilotError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
    return cleaned or "model"


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    return value or None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_request_payload(
    model: str,
    prompt: str,
    reasoning_effort: str,
    max_output_tokens: int,
) -> dict[str, Any]:
    if reasoning_effort not in REASONING_EFFORTS:
        raise PilotError(f"unsupported reasoning effort: {reasoning_effort}")
    if max_output_tokens < 64:
        raise PilotError("max_output_tokens must be at least 64")
    return {
        "model": model,
        "input": prompt,
        "reasoning": {"effort": reasoning_effort},
        "max_output_tokens": max_output_tokens,
    }


def extract_output_text(response: dict[str, Any]) -> str:
    top_level = response.get("output_text")
    if isinstance(top_level, str) and top_level.strip():
        return top_level

    pieces: list[str] = []
    output = response.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                    pieces.append(part["text"])
    text = "".join(pieces)
    if not text.strip():
        raise PilotError("Responses API payload contained no output_text")
    return text


def parse_json_only(text: str) -> dict[str, Any]:
    """Require literal JSON output; markdown fences are intentionally not repaired."""
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EvalError(f"model output is not literal JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise EvalError("model output must be a JSON object")
    return value


def call_openai(
    *,
    api_key: str,
    endpoint: str,
    payload: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ai-memory-architecture-recovery-pilot/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise PilotError(f"OpenAI HTTP {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise PilotError(f"OpenAI request failed: {exc}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PilotError(f"OpenAI response was not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise PilotError("OpenAI response must be a JSON object")
    return parsed


def _score_dict(task: dict[str, Any], condition: str, model_output: dict[str, Any]) -> dict[str, Any]:
    score = score_output(task, condition, model_output)
    return score.as_dict()


def _zero_score(task_id: str, condition: str, error_type: str, detail: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "condition": condition,
        "points": 0,
        "max_points": 4,
        "metrics": {
            "state_accuracy": 0,
            "authority_citation_accuracy": 0,
            "safe_evidence_selection": 0,
            "stale_path_identification": 0,
        },
        "error_type": error_type,
        "detail": detail,
    }


def _aggregate(case_records: list[dict[str, Any]]) -> dict[str, Any]:
    by_condition: dict[str, dict[str, Any]] = {}
    metric_names = [
        "state_accuracy",
        "authority_citation_accuracy",
        "safe_evidence_selection",
        "stale_path_identification",
    ]
    for condition in sorted(CONDITIONS):
        records = [record for record in case_records if record["condition"] == condition]
        points = sum(record["score"]["points"] for record in records)
        max_points = sum(record["score"]["max_points"] for record in records)
        metric_totals = {
            name: sum(record["score"]["metrics"][name] for record in records)
            for name in metric_names
        }
        by_condition[condition] = {
            "cases": len(records),
            "points": points,
            "max_points": max_points,
            "point_rate": (points / max_points) if max_points else 0.0,
            "metrics": {
                name: {
                    "correct": metric_totals[name],
                    "total": len(records),
                    "rate": (metric_totals[name] / len(records)) if records else 0.0,
                }
                for name in metric_names
            },
        }

    governed = by_condition.get("governed", {})
    ungoverned = by_condition.get("ungoverned", {})
    return {
        "by_condition": by_condition,
        "governed_minus_ungoverned_point_rate": (
            governed.get("point_rate", 0.0) - ungoverned.get("point_rate", 0.0)
        ),
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_pilot(args: argparse.Namespace) -> int:
    corpus_path = args.corpus.resolve()
    corpus = load_corpus(corpus_path)
    expected_cases = len(corpus["tasks"]) * len(CONDITIONS)

    pairs = [(task, condition) for task in corpus["tasks"] for condition in sorted(CONDITIONS)]
    random.Random(args.seed).shuffle(pairs)
    if args.limit is not None:
        if args.limit < 1:
            raise PilotError("--limit must be >= 1")
        pairs = pairs[: args.limit]

    started_at = _utc_now()
    if args.output_dir is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_dir = REPO_ROOT / "eval-runs" / "openai" / f"{stamp}_{_safe_name(args.model)}_seed{args.seed}"
    else:
        output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=False)

    api_key = None if args.dry_run else os.environ.get("OPENAI_API_KEY")
    if not args.dry_run and not api_key:
        raise PilotError("OPENAI_API_KEY is required unless --dry-run is used")

    run_metadata: dict[str, Any] = {
        "format_version": 1,
        "evaluation": "authoritative-state-recovery-v0.1",
        "provider": "openai",
        "endpoint": args.endpoint,
        "requested_model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "max_output_tokens": args.max_output_tokens,
        "seed": args.seed,
        "dry_run": args.dry_run,
        "started_at": started_at,
        "repository_commit": _git_commit(),
        "corpus_path": str(corpus_path.relative_to(REPO_ROOT)) if corpus_path.is_relative_to(REPO_ROOT) else str(corpus_path),
        "corpus_sha256": _sha256_file(corpus_path),
        "expected_full_run_cases": expected_cases,
        "planned_cases": len(pairs),
        "api_key_persisted": False,
        "retry_policy": "none",
        "independent_requests": True,
    }
    _write_json(output_dir / "run.json", run_metadata)

    case_records: list[dict[str, Any]] = []
    resolved_models: set[str] = set()
    api_errors = 0
    invalid_outputs = 0

    for index, (task, condition) in enumerate(pairs, start=1):
        case_name = f"{index:02d}_{task['id']}__{condition}"
        case_dir = output_dir / case_name
        case_dir.mkdir()
        prompt = render_prompt(task, condition)
        (case_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

        payload = build_request_payload(
            args.model,
            prompt,
            args.reasoning_effort,
            args.max_output_tokens,
        )
        safe_request = dict(payload)
        _write_json(case_dir / "request.json", safe_request)

        record: dict[str, Any] = {
            "index": index,
            "task_id": task["id"],
            "condition": condition,
            "case_dir": case_name,
            "started_at": _utc_now(),
        }

        if args.dry_run:
            record["status"] = "dry_run"
            record["score"] = _zero_score(task["id"], condition, "dry_run", "No API request was made")
            record["finished_at"] = _utc_now()
            case_records.append(record)
            continue

        try:
            response = call_openai(
                api_key=api_key or "",
                endpoint=args.endpoint,
                payload=payload,
                timeout_seconds=args.timeout_seconds,
            )
            _write_json(case_dir / "response.json", response)
            resolved = response.get("model")
            if isinstance(resolved, str) and resolved:
                resolved_models.add(resolved)
            output_text = extract_output_text(response)
            (case_dir / "model-output.txt").write_text(output_text, encoding="utf-8")
            try:
                model_output = parse_json_only(output_text)
                _write_json(case_dir / "model-output.json", model_output)
                score = _score_dict(task, condition, model_output)
                record["status"] = "scored"
            except (EvalError, KeyError, TypeError) as exc:
                invalid_outputs += 1
                score = _zero_score(task["id"], condition, "invalid_model_output", str(exc))
                record["status"] = "invalid_model_output"
        except PilotError as exc:
            api_errors += 1
            score = _zero_score(task["id"], condition, "api_error", str(exc))
            record["status"] = "api_error"
            _write_json(case_dir / "api-error.json", {"error": str(exc), "recorded_at": _utc_now()})

        record["score"] = score
        record["finished_at"] = _utc_now()
        _write_json(case_dir / "score.json", score)
        case_records.append(record)
        print(
            f"{index:02d}/{len(pairs):02d} {task['id']} {condition}: "
            f"{record['status']} {score['points']}/{score['max_points']}"
        )

    summary = {
        "format_version": 1,
        "evaluation": "authoritative-state-recovery-v0.1",
        "provider": "openai",
        "requested_model": args.model,
        "resolved_models": sorted(resolved_models),
        "started_at": started_at,
        "finished_at": _utc_now(),
        "dry_run": args.dry_run,
        "repository_commit": run_metadata["repository_commit"],
        "corpus_sha256": run_metadata["corpus_sha256"],
        "seed": args.seed,
        "expected_full_run_cases": expected_cases,
        "planned_cases": len(pairs),
        "recorded_cases": len(case_records),
        "api_errors": api_errors,
        "invalid_model_outputs": invalid_outputs,
        "complete_full_pilot": (
            not args.dry_run
            and len(pairs) == expected_cases
            and len(case_records) == expected_cases
            and api_errors == 0
        ),
        "aggregate": _aggregate(case_records),
        "cases": case_records,
    }
    _write_json(output_dir / "summary.json", summary)
    print(f"WROTE: {output_dir}")
    print(json.dumps(summary["aggregate"], indent=2))

    if args.dry_run:
        return 0
    if api_errors:
        return 2
    if invalid_outputs:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=REPO_ROOT / "eval" / "recovery-v0.1" / "tasks.json",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--reasoning-effort", choices=sorted(REASONING_EFFORTS), default=DEFAULT_REASONING_EFFORT)
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--limit", type=int, help="run only N shuffled cases; incomplete runs are never marked complete")
    parser.add_argument("--dry-run", action="store_true", help="write the exact run plan without making API calls")
    args = parser.parse_args(argv)

    try:
        return run_pilot(args)
    except (OSError, EvalError, PilotError) as exc:
        print(f"PILOT_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
