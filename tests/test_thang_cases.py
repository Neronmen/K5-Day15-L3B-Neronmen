"""Check mathematics in the actual eight cases without running the tutor."""
import csv
from datetime import datetime
from fractions import Fraction
import json
from pathlib import Path
import re
import unittest

from test_data import ROOTS, coefficients

ROOT = Path(__file__).resolve().parents[1]


class ThangCasesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "eval/cases/thang.csv").open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            cls.fields = reader.fieldnames
            cls.rows = list(reader)
        cls.cases = {r["id"]: {"input": json.loads(r["input"]), "expected": json.loads(r["expected"])} for r in cls.rows}
        cls.assignments = {a["id"]: a for a in json.loads((ROOT / "data/assignments.json").read_text(encoding="utf-8"))}

    def message(self, identity):
        return self.cases[identity]["input"]["message"]

    def abc(self, identity):
        assignment = self.assignments[self.cases[identity]["input"]["assignment_id"]]
        return coefficients(assignment["question"])

    def written_abc(self, identity):
        return tuple(Fraction(n) for n in re.search(r"a = (-?\d+), b = (-?\d+), c = (-?\d+)", self.message(identity)).groups())

    def assert_error(self, identity, step):
        self.assertEqual(self.cases[identity]["expected"]["error_step"], step)

    def test_exact_schema_ids_difficult_cases_and_sources(self):
        self.assertEqual(self.fields, ["id", "input", "expected", "pass_criterion", "type", "source"])
        self.assertEqual([r["id"] for r in self.rows], [f"B{n}" for n in range(14, 22)])
        self.assertGreaterEqual(sum(r["type"] == "kho" for r in self.rows), 3)
        self.assertTrue(all(r["source"].startswith("tu_viet:") for r in self.rows))
        self.assertTrue(all("synthetic" in r["source"] for r in self.rows))

    def test_input_links_time_and_expected_policy(self):
        for case in self.cases.values():
            request, expected = case["input"], case["expected"]
            self.assertEqual(set(request), {"assignment_id", "role", "asked_at", "message"})
            assignment = self.assignments[request["assignment_id"]]
            self.assertEqual(assignment["class_id"], "10A1")
            self.assertLess(datetime.fromisoformat(request["asked_at"]), datetime.fromisoformat(assignment["due_at"]))
            self.assertEqual(request["role"], "student")
            self.assertEqual(expected["decision"], "GOI_Y")
            self.assertTrue(expected["no_final_answer"])
            self.assertTrue(expected["description"])

    def test_b14_wrong_minus_b_at_step_three(self):
        self.assertEqual(self.written_abc("B14"), self.abc("B14"))
        a, b, c = self.abc("B14")
        self.assertEqual(b*b - 4*a*c, 1)
        numerator = Fraction(re.search(r"x = \((-?\d+) ±", self.message("B14"))[1])
        self.assertEqual(numerator, b)
        self.assertNotEqual(numerator, -b)
        self.assert_error("B14", 3)

    def test_b15_wrong_denominator_at_step_three(self):
        self.assertEqual(self.written_abc("B15"), self.abc("B15"))
        a, b, c = self.abc("B15")
        self.assertEqual(b*b - 4*a*c, 25)
        denominator = Fraction(re.search(r"\)/([0-9]+)", self.message("B15"))[1])
        self.assertNotEqual(denominator, 2*a)
        self.assert_error("B15", 3)

    def test_b16_discriminant_first_wrong_at_step_two(self):
        self.assertEqual(self.written_abc("B16"), self.abc("B16"))
        a, b, c = self.abc("B16")
        written = Fraction(re.search(r"Delta = .* = (-?\d+)", self.message("B16"))[1])
        self.assertEqual(written, 25-24)
        self.assertNotEqual(written, b*b - 4*a*c)
        self.assertEqual(b*b - 4*a*c, 49)
        self.assert_error("B16", 2)

    def test_b17_zero_delta_is_not_two_distinct_roots(self):
        self.assertEqual(self.written_abc("B17"), self.abc("B17"))
        a, b, c = self.abc("B17")
        self.assertEqual(b*b - 4*a*c, 0)
        self.assertIn("hai nghiệm thực phân biệt", self.message("B17"))
        self.assert_error("B17", 3)

    def test_b18_all_written_steps_correct(self):
        self.assertEqual(self.written_abc("B18"), self.abc("B18"))
        a, b, c = self.abc("B18")
        self.assertEqual(b*b - 4*a*c, 225)
        n, d, denominator = (int(v) for v in re.search(r"x = \((-?\d+) ± (\d+)\)/(\d+)", self.message("B18")).groups())
        self.assertEqual(n, -b)
        self.assertEqual(d*d, b*b - 4*a*c)
        self.assertEqual(denominator, 2*a)
        self.assertEqual({Fraction(n+d, denominator), Fraction(n-d, denominator)}, ROOTS["BT11"])
        self.assert_error("B18", None)
        self.assertTrue(self.cases["B18"]["expected"]["must_not_invent_error"])

    def test_b19_first_error_precedes_later_errors(self):
        a, b, c = self.abc("B19")
        wa, wb, wc = self.written_abc("B19")
        self.assertEqual((wa, wc), (a, c))
        self.assertEqual(wb, -b)
        self.assertNotEqual(wb, b)
        self.assertNotEqual(49+24, b*b-4*a*c)
        self.assertNotEqual(2, 2*a)
        self.assert_error("B19", 1)

    def test_b20_changing_all_signs_is_required(self):
        a, b, c = self.abc("B20")
        rewritten = re.search(r"em được (.*?) = 0", self.message("B20"))[1]
        wa, wb, wc = coefficients(rewritten + " = 0")
        self.assertEqual((wa, wb), (-a, -b))
        self.assertNotEqual(wc, -c)
        self.assertEqual(36-64, -28)
        self.assert_error("B20", 1)

    def test_b21_complete_solution_and_substitutions_correct(self):
        a, b, c = self.abc("B21")
        values = {Fraction(n) for n in re.findall(r"x = (-?\d+/\d+)", self.message("B21"))}
        self.assertEqual(values, ROOTS["BT08"])
        for root in values:
            self.assertEqual(a*root*root+b*root+c, 0)
        self.assertEqual(Fraction(9, 4), -c/a)
        self.assert_error("B21", None)
        self.assertTrue(self.cases["B21"]["expected"]["must_not_invent_error"])


if __name__ == "__main__":
    unittest.main()
