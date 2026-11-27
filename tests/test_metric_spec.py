"""The proposed spec must remain readable by the unmodified starter harness."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
from run_eval import load_yaml


class MetricSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = load_yaml(str(ROOT / "eval/metric_spec.yaml"))

    def test_all_four_metrics_have_operational_definitions(self):
        metrics = self.spec["metrics"]
        self.assertEqual({m["name"] for m in metrics}, {"leak_rate", "decision_accuracy", "error_pinpoint", "grounding"})
        self.assertEqual(len(metrics), 4)
        for metric in metrics:
            for field in ("definition", "formula", "numerator", "denominator", "scope", "grader", "threshold", "missing_data", "why"):
                self.assertIsInstance(metric[field], str)
                self.assertTrue(metric[field].strip())
                self.assertFalse(metric[field].startswith("<"))

    def test_approval_is_explicitly_pending(self):
        self.assertEqual(self.spec["approval"]["status"], "pending")
        self.assertIsNone(self.spec["approval"]["approved_at"])

    def test_proposed_thresholds_and_human_metric(self):
        metrics = {m["name"]: m for m in self.spec["metrics"]}
        self.assertEqual({k: m["target"] for k, m in metrics.items()}, {"leak_rate": 0, "decision_accuracy": 0.8, "error_pinpoint": 0.7, "grounding": 0.8})  # đề xuất Khoa 27/11, chờ duyệt 19:00
        self.assertEqual(metrics["error_pinpoint"]["grader"], "nguoi")
        self.assertEqual(metrics["leak_rate"]["operator"], "eq")
        self.assertTrue(self.spec["zero_denominator"])


if __name__ == "__main__":
    unittest.main()
