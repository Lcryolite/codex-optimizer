from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))

from optimizer_matrix import ARMS, arm_texts, load_json, verify_implementations  # noqa: E402


class OptimizerMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.matrix = load_json(ROOT / "benchmarks" / "optimizer_matrix.json")
        cls.transcript = load_json(
            ROOT / "benchmarks" / "combined_rtk_caveman.json"
        )

    def test_both_implementations_satisfy_the_same_contract(self) -> None:
        verify_implementations(self.matrix)

    def test_each_single_arm_changes_only_its_registered_component(self) -> None:
        baseline = arm_texts(self.matrix, self.transcript, "baseline")
        expected_changes = {
            "rtk": {"command", "tool_output"},
            "caveman": {"assistant"},
            "ponytail": {"implementation"},
        }
        for arm, changed_parts in expected_changes.items():
            with self.subTest(arm=arm):
                candidate = arm_texts(self.matrix, self.transcript, arm)
                actual = {
                    part for part in baseline if candidate[part] != baseline[part]
                }
                self.assertEqual(actual, changed_parts)

    def test_combined_arm_applies_all_registered_changes(self) -> None:
        baseline = arm_texts(self.matrix, self.transcript, "baseline")
        combined = arm_texts(self.matrix, self.transcript, "combined")

        self.assertEqual(
            {part for part in baseline if combined[part] != baseline[part]},
            {"implementation", "assistant", "command", "tool_output"},
        )
        self.assertEqual(set(ARMS), {"baseline", "rtk", "caveman", "ponytail", "combined"})


if __name__ == "__main__":
    unittest.main()
