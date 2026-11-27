"""Synthetic fixtures for H-05 aggregation, never respondent evidence."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cost_analyze_q5", ROOT / "cost/analyze_q5.py")
q5 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q5)
FIELDS = ["ma", "Em đang học lớp", "Trong 1 tuần qua, dùng khoảng mấy lần?"]


def fixture(values):
    return [dict(zip(FIELDS, ["R" + str(i), grade, answer])) for i, (grade, answer) in enumerate(values, 1)]


class SurveyCostTests(unittest.TestCase):
    def test_zero_use_is_kept_in_the_population_and_mean(self):
        report = q5.analyze_rows(fixture([("10", "0"), ("11", "1–2")]), FIELDS)
        self.assertEqual(report["valid_q5_answers"], 2)
        self.assertEqual(report["zero_use_respondents_retained"], 1)
        self.assertEqual(report["personas"][0]["share"], 1)
        self.assertAlmostEqual(report["personas"][0]["uses_per_month"], 3.25)

    def test_requested_three_groups_use_the_right_bands(self):
        report = q5.analyze_rows(fixture([("12", v) for v in ["0", "1–2", "3–5", "6–10", "Trên 10"]]), FIELDS)
        self.assertEqual([p["respondents"] for p in report["personas"]], [2, 1, 2])
        self.assertAlmostEqual(sum(p["share"] for p in report["personas"]), 1)

    def test_non_thpt_does_not_change_the_target_population(self):
        report = q5.analyze_rows(fixture([("9", "Trên 10"), ("10", "0")]), FIELDS)
        self.assertEqual(report["total_records"], 2)
        self.assertEqual(report["excluded_non_thpt_records"], 1)
        self.assertEqual(report["valid_q5_answers"], 1)

    def test_missing_and_unknown_answers_are_not_silently_imputed(self):
        report = q5.analyze_rows(fixture([("10", ""), ("11", "often"), ("12", "0")]), FIELDS)
        self.assertEqual((report["missing_q5"], report["invalid_q5"]), (1, 1))
        self.assertEqual(report["distribution"][0]["fraction_of_valid_q5"], 1)
        self.assertAlmostEqual(report["distribution"][0]["fraction_of_thpt"], 1 / 3)

    def test_empty_valid_denominator_has_no_invented_rate(self):
        report = q5.analyze_rows(fixture([("10", "")]), FIELDS)
        self.assertEqual(report["personas"], [])
        self.assertIsNone(report["distribution"][0]["fraction_of_valid_q5"])

    def test_top_bucket_stress_is_not_an_observed_upper_bound(self):
        report = q5.analyze_rows(fixture([("10", "Trên 10")]), FIELDS)
        monthly = [s["population_uses_per_month"] for s in report["sensitivity"]]
        self.assertAlmostEqual(monthly[0], 11 * 52 / 12)
        self.assertTrue(monthly[0] < monthly[1] < monthly[2])
        self.assertTrue(report["assumptions"]["top_band_has_no_finite_upper_bound"])

    def test_duplicate_ids_are_rejected(self):
        rows = fixture([("10", "0"), ("10", "1–2")])
        rows[1]["ma"] = rows[0]["ma"]
        with self.assertRaisesRegex(ValueError, "unique"):
            q5.analyze_rows(rows, FIELDS)

    def test_identifying_columns_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "anonymized"):
            q5.analyze_rows([], FIELDS + ["Email"])


if __name__ == "__main__":
    unittest.main()
