import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from tools.openai_recovery_pilot import (
    PilotError,
    _aggregate,
    build_request_payload,
    extract_output_text,
    parse_json_only,
    run_pilot,
)
from tools.recovery_eval import EvalError


class OpenAIRecoveryPilotTests(unittest.TestCase):
    def test_build_request_payload_records_explicit_model_and_reasoning(self):
        payload = build_request_payload("gpt-5.6-sol", "hello", "medium", 1200)
        self.assertEqual(payload["model"], "gpt-5.6-sol")
        self.assertEqual(payload["input"], "hello")
        self.assertEqual(payload["reasoning"], {"effort": "medium"})
        self.assertEqual(payload["max_output_tokens"], 1200)

    def test_build_request_rejects_unknown_reasoning_effort(self):
        with self.assertRaises(PilotError):
            build_request_payload("model", "prompt", "mystery", 1200)

    def test_extract_output_text_from_raw_responses_shape(self):
        response = {
            "model": "gpt-5.6-sol-2026-08-01",
            "output": [
                {"type": "reasoning", "summary": []},
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": '{"current_state":"ok"}'}
                    ],
                },
            ],
        }
        self.assertEqual(extract_output_text(response), '{"current_state":"ok"}')

    def test_extract_output_text_accepts_top_level_convenience_field(self):
        self.assertEqual(extract_output_text({"output_text": "{}"}), "{}")

    def test_parse_json_only_rejects_markdown_fence_instead_of_repairing(self):
        with self.assertRaises(EvalError):
            parse_json_only("```json\n{}\n```")

    def test_aggregate_reports_governed_minus_ungoverned(self):
        base_metrics = {
            "state_accuracy": 1,
            "authority_citation_accuracy": 1,
            "safe_evidence_selection": 1,
            "stale_path_identification": 1,
        }
        records = [
            {
                "condition": "governed",
                "score": {"points": 4, "max_points": 4, "metrics": base_metrics},
            },
            {
                "condition": "ungoverned",
                "score": {
                    "points": 2,
                    "max_points": 4,
                    "metrics": {
                        "state_accuracy": 1,
                        "authority_citation_accuracy": 1,
                        "safe_evidence_selection": 0,
                        "stale_path_identification": 0,
                    },
                },
            },
        ]
        aggregate = _aggregate(records)
        self.assertEqual(aggregate["by_condition"]["governed"]["point_rate"], 1.0)
        self.assertEqual(aggregate["by_condition"]["ungoverned"]["point_rate"], 0.5)
        self.assertEqual(aggregate["governed_minus_ungoverned_point_rate"], 0.5)

    def test_dry_run_writes_plan_without_api_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "pilot"
            args = Namespace(
                corpus=Path("eval/recovery-v0.1/tasks.json"),
                model="gpt-5.6-sol",
                reasoning_effort="medium",
                max_output_tokens=1200,
                seed=20260829,
                timeout_seconds=120.0,
                endpoint="https://api.openai.com/v1/responses",
                output_dir=output_dir,
                limit=2,
                dry_run=True,
            )
            self.assertEqual(run_pilot(args), 0)
            run = json.loads((output_dir / "run.json").read_text(encoding="utf-8"))
            summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertTrue(run["dry_run"])
            self.assertFalse(run["api_key_persisted"])
            self.assertEqual(summary["planned_cases"], 2)
            self.assertFalse(summary["complete_full_pilot"])
            case_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
            self.assertEqual(len(case_dirs), 2)
            self.assertTrue(all((path / "prompt.txt").exists() for path in case_dirs))
            self.assertTrue(all((path / "request.json").exists() for path in case_dirs))


if __name__ == "__main__":
    unittest.main()
