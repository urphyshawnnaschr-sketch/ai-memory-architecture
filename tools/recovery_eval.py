#!/usr/bin/env python3
"""Generate and score Authoritative-State Recovery Evaluation V0.1 tasks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = REPO_ROOT / "eval" / "recovery-v0.1" / "tasks.json"
CONDITIONS = {"governed", "ungoverned"}
OUTPUT_KEYS = {
    "current_state",
    "authority_path",
    "current_evidence_paths",
    "stale_or_non_authoritative_paths",
}


class EvalError(ValueError):
    pass


@dataclass(frozen=True)
class Score:
    task_id: str
    condition: str
    state_accuracy: int
    authority_citation_accuracy: int
    safe_evidence_selection: int
    stale_path_identification: int

    @property
    def points(self) -> int:
        return (
            self.state_accuracy
            + self.authority_citation_accuracy
            + self.safe_evidence_selection
            + self.stale_path_identification
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "condition": self.condition,
            "points": self.points,
            "max_points": 4,
            "metrics": {
                "state_accuracy": self.state_accuracy,
                "authority_citation_accuracy": self.authority_citation_accuracy,
                "safe_evidence_selection": self.safe_evidence_selection,
                "stale_path_identification": self.stale_path_identification,
            },
        }


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise EvalError(f"{label} must be a list of strings")
    if len(set(value)) != len(value):
        raise EvalError(f"{label} must not contain duplicates")
    return value


def load_corpus(path: Path = DEFAULT_CORPUS) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvalError(f"corpus not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EvalError(f"invalid corpus JSON: {exc}") from exc

    if not isinstance(data, dict) or data.get("version") != 1:
        raise EvalError("corpus version must be 1")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or len(tasks) < 1:
        raise EvalError("corpus must contain tasks")

    seen_ids: set[str] = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            raise EvalError(f"tasks[{index}] must be an object")
        task_id = task.get("id")
        if not isinstance(task_id, str) or not re.fullmatch(r"[a-z0-9_]+", task_id):
            raise EvalError(f"tasks[{index}].id is invalid")
        if task_id in seen_ids:
            raise EvalError(f"duplicate task id: {task_id}")
        seen_ids.add(task_id)

        question = task.get("question")
        documents = task.get("documents")
        governance = task.get("governance")
        ground_truth = task.get("ground_truth")
        if not isinstance(question, str) or not question.strip():
            raise EvalError(f"{task_id}: question must be non-empty")
        if not isinstance(documents, dict) or len(documents) < 2:
            raise EvalError(f"{task_id}: documents must contain at least two files")
        if not all(isinstance(k, str) and isinstance(v, str) for k, v in documents.items()):
            raise EvalError(f"{task_id}: document paths and contents must be strings")
        if not isinstance(governance, dict) or not isinstance(ground_truth, dict):
            raise EvalError(f"{task_id}: governance and ground_truth must be objects")

        authority = governance.get("authority_path")
        truth_authority = ground_truth.get("authority_path")
        if authority != truth_authority or authority not in documents:
            raise EvalError(f"{task_id}: governance/ground-truth authority must match a document")
        stale = _string_list(
            ground_truth.get("stale_or_non_authoritative_paths"),
            f"{task_id}.ground_truth.stale_or_non_authoritative_paths",
        )
        governance_stale = _string_list(
            governance.get("non_authoritative_paths"),
            f"{task_id}.governance.non_authoritative_paths",
        )
        if set(stale) != set(governance_stale):
            raise EvalError(f"{task_id}: governance and ground-truth non-authoritative paths differ")
        if authority in stale:
            raise EvalError(f"{task_id}: authority cannot also be non-authoritative")
        if any(path not in documents for path in stale):
            raise EvalError(f"{task_id}: all non-authoritative paths must exist in documents")
        state = ground_truth.get("current_state")
        if not isinstance(state, str) or not state.strip():
            raise EvalError(f"{task_id}: current_state must be non-empty")

    return data


def task_by_id(corpus: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in corpus["tasks"]:
        if task["id"] == task_id:
            return task
    raise EvalError(f"unknown task id: {task_id}")


def render_prompt(task: dict[str, Any], condition: str) -> str:
    if condition not in CONDITIONS:
        raise EvalError(f"condition must be one of: {', '.join(sorted(CONDITIONS))}")

    sections = [
        "You are evaluating the current authoritative state of a long-running project.",
        "Use only the supplied documents. Do not invent missing facts.",
    ]
    if condition == "governed":
        governance = task["governance"]
        non_auth = ", ".join(governance["non_authoritative_paths"]) or "(none)"
        sections.extend(
            [
                "",
                "GOVERNANCE CONTRACT",
                f"Domain: {governance['domain']}",
                f"Authoritative path: {governance['authority_path']}",
                f"Non-authoritative context paths: {non_auth}",
                "For current state, the authoritative path wins when documents conflict.",
            ]
        )
    else:
        sections.extend(
            [
                "",
                "No explicit governance contract is provided. Infer which document best represents current state from the documents themselves.",
            ]
        )

    sections.extend(["", "QUESTION", task["question"], "", "DOCUMENTS"])
    for path, content in task["documents"].items():
        sections.extend([f"--- {path} ---", content.rstrip(), ""])

    sections.extend(
        [
            "OUTPUT FORMAT",
            "Return JSON only, with exactly these keys:",
            '{"current_state":"...","authority_path":"...","current_evidence_paths":["..."],"stale_or_non_authoritative_paths":["..."]}',
            "current_evidence_paths should contain only files you treated as evidence for the current state.",
        ]
    )
    return "\n".join(sections).rstrip() + "\n"


def parse_model_output(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvalError(f"model output not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EvalError(f"model output is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise EvalError("model output must be a JSON object")
    unknown = set(data) - OUTPUT_KEYS
    missing = OUTPUT_KEYS - set(data)
    if unknown:
        raise EvalError(f"model output has unknown keys: {', '.join(sorted(unknown))}")
    if missing:
        raise EvalError(f"model output is missing keys: {', '.join(sorted(missing))}")
    if not isinstance(data["current_state"], str) or not isinstance(data["authority_path"], str):
        raise EvalError("current_state and authority_path must be strings")
    _string_list(data["current_evidence_paths"], "current_evidence_paths")
    _string_list(data["stale_or_non_authoritative_paths"], "stale_or_non_authoritative_paths")
    return data


def score_output(task: dict[str, Any], condition: str, output: dict[str, Any]) -> Score:
    if condition not in CONDITIONS:
        raise EvalError(f"condition must be one of: {', '.join(sorted(CONDITIONS))}")
    truth = task["ground_truth"]
    stale_truth = set(truth["stale_or_non_authoritative_paths"])
    evidence = set(_string_list(output["current_evidence_paths"], "current_evidence_paths"))
    stale_output = set(
        _string_list(output["stale_or_non_authoritative_paths"], "stale_or_non_authoritative_paths")
    )
    authority = truth["authority_path"]

    state_accuracy = int(
        _normalize_text(output["current_state"]) == _normalize_text(truth["current_state"])
    )
    authority_accuracy = int(output["authority_path"].strip() == authority)
    safe_evidence = int(authority in evidence and not (evidence & stale_truth))
    stale_accuracy = int(stale_output == stale_truth)

    return Score(
        task_id=task["id"],
        condition=condition,
        state_accuracy=state_accuracy,
        authority_citation_accuracy=authority_accuracy,
        safe_evidence_selection=safe_evidence,
        stale_path_identification=stale_accuracy,
    )


def oracle_output(task: dict[str, Any]) -> dict[str, Any]:
    truth = task["ground_truth"]
    return {
        "current_state": truth["current_state"],
        "authority_path": truth["authority_path"],
        "current_evidence_paths": [truth["authority_path"]],
        "stale_or_non_authoritative_paths": truth["stale_or_non_authoritative_paths"],
    }


def bundle_prompts(corpus: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, str]] = []
    for task in corpus["tasks"]:
        for condition in sorted(CONDITIONS):
            filename = f"{task['id']}__{condition}.txt"
            (output_dir / filename).write_text(render_prompt(task, condition), encoding="utf-8")
            manifest.append({"task_id": task["id"], "condition": condition, "prompt_file": filename})
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def selftest(corpus: dict[str, Any]) -> None:
    for task in corpus["tasks"]:
        for condition in CONDITIONS:
            score = score_output(task, condition, oracle_output(task))
            if score.points != 4:
                raise EvalError(f"oracle self-test failed for {task['id']} / {condition}")
    first = corpus["tasks"][0]
    wrong = oracle_output(first)
    wrong["current_state"] = "Definitely the wrong state."
    wrong["authority_path"] = next(path for path in first["documents"] if path != first["ground_truth"]["authority_path"])
    wrong["current_evidence_paths"] = [wrong["authority_path"]]
    if score_output(first, "ungoverned", wrong).points == 4:
        raise EvalError("negative self-test unexpectedly received a perfect score")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list task ids")

    prompt_parser = sub.add_parser("prompt", help="render one model prompt")
    prompt_parser.add_argument("task_id")
    prompt_parser.add_argument("condition", choices=sorted(CONDITIONS))

    bundle_parser = sub.add_parser("bundle", help="write all governed/ungoverned prompts")
    bundle_parser.add_argument("output_dir", type=Path)

    score_parser = sub.add_parser("score", help="score one structured model output")
    score_parser.add_argument("task_id")
    score_parser.add_argument("condition", choices=sorted(CONDITIONS))
    score_parser.add_argument("output", type=Path)

    sub.add_parser("selftest", help="validate corpus and scorer using oracle and negative outputs")

    args = parser.parse_args(argv)
    try:
        corpus = load_corpus(args.corpus)
        if args.command == "list":
            for task in corpus["tasks"]:
                print(task["id"])
            return 0
        if args.command == "prompt":
            print(render_prompt(task_by_id(corpus, args.task_id), args.condition), end="")
            return 0
        if args.command == "bundle":
            bundle_prompts(corpus, args.output_dir)
            print(f"WROTE: {len(corpus['tasks']) * 2} prompts to {args.output_dir}")
            return 0
        if args.command == "score":
            task = task_by_id(corpus, args.task_id)
            output = parse_model_output(args.output)
            score = score_output(task, args.condition, output)
            print(json.dumps(score.as_dict(), indent=2))
            return 0
        if args.command == "selftest":
            selftest(corpus)
            print(f"PASS: recovery evaluation self-test ({len(corpus['tasks'])} tasks, 2 conditions each)")
            return 0
    except (OSError, EvalError) as exc:
        print(f"EVAL_ERROR: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
