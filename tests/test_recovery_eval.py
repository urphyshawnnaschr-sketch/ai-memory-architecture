import json
import tempfile
import unittest
from pathlib import Path

from tools.recovery_eval import (
    CONDITIONS,
    bundle_prompts,
    load_corpus,
    oracle_output,
    render_prompt,
    score_output,
    selftest,
)


class RecoveryEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = load_corpus()

    def test_corpus_has_eight_tasks(self) -> None:
        self.assertEqual(len(self.corpus["tasks"]), 8)

    def test_oracle_scores_perfectly_in_both_conditions(self) -> None:
        for task in self.corpus["tasks"]:
            for condition in CONDITIONS:
                score = score_output(task, condition, oracle_output(task))
                self.assertEqual(score.points, 4)

    def test_governed_prompt_exposes_authority_contract(self) -> None:
        task = self.corpus["tasks"][0]
        prompt = render_prompt(task, "governed")
        self.assertIn("GOVERNANCE CONTRACT", prompt)
        self.assertIn(task["ground_truth"]["authority_path"], prompt)

    def test_ungoverned_prompt_hides_explicit_contract(self) -> None:
        task = self.corpus["tasks"][0]
        prompt = render_prompt(task, "ungoverned")
        self.assertNotIn("GOVERNANCE CONTRACT", prompt)
        self.assertIn("No explicit governance contract is provided", prompt)

    def test_wrong_state_and_evidence_do_not_score_perfectly(self) -> None:
        task = self.corpus["tasks"][0]
        output = oracle_output(task)
        output["current_state"] = "Wrong state"
        output["authority_path"] = "bookmark.md"
        output["current_evidence_paths"] = ["bookmark.md"]
        score = score_output(task, "ungoverned", output)
        self.assertLess(score.points, 4)
        self.assertEqual(score.state_accuracy, 0)
        self.assertEqual(score.authority_citation_accuracy, 0)
        self.assertEqual(score.safe_evidence_selection, 0)

    def test_bundle_writes_sixteen_prompts_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_prompts(self.corpus, root)
            manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest), 16)
            prompt_files = list(root.glob("*.txt"))
            self.assertEqual(len(prompt_files), 16)

    def test_selftest_passes(self) -> None:
        selftest(self.corpus)


if __name__ == "__main__":
    unittest.main()
