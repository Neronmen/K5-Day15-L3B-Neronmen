"""Verify the actual synthetic dataset independently of its written answer keys."""
import json
import math
from pathlib import Path
import re
import sys
import unittest
from datetime import datetime
from fractions import Fraction
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))
import agent
import tools

ASKED_AT = "2026-11-28T21:00:00+07:00"
ROOTS = {
    "BT01": {Fraction(2), Fraction(3)}, "BT03": {Fraction(1, 2), Fraction(3)},
    "BT04": {Fraction(-2)}, "BT05": set(), "BT06": {Fraction(-1), Fraction(4)},
    "BT07": {Fraction(0), Fraction(4)}, "BT08": {Fraction(-3, 2), Fraction(3, 2)},
    "BT09": {Fraction(-3), Fraction(1, 2)}, "BT10": {Fraction(3)},
    "BT11": {Fraction(-2), Fraction(1)}, "BT12": {Fraction(-2), Fraction(3)},
    "BT13": {Fraction(3), Fraction(4)},
}


def coefficients(question):
    """Parse only the polynomial printed in the question, never answer_key."""
    equation = re.search(r"([+-]?\d*x\^2[^=]*)=\s*0", question).group(1).replace(" ", "")
    result = {2: Fraction(0), 1: Fraction(0), 0: Fraction(0)}
    for term in re.findall(r"[+-]?[^+-]+", equation):
        power = 2 if "x^2" in term else 1 if "x" in term else 0
        number = term.replace("x^2", "").replace("x", "")
        result[power] += Fraction({"": "1", "+": "1", "-": "-1"}.get(number, number))
    return result[2], result[1], result[0]


def final_value(text):
    text = text.replace("−", "-")
    text = re.sub(r"\\frac\{(\d+)\}\{(\d+)\}", r"\1/\2", text)
    match = re.fullmatch(r"x\s*(?:=|bằng)\s*([-+]?\d+(?:[.,]\d+)?(?:/\d+)?)", text)
    return Fraction(match[1].replace(",", ".")) if match else None


class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = json.loads((ROOT / "data/lesson.json").read_text(encoding="utf-8"))
        cls.assignments = json.loads((ROOT / "data/assignments.json").read_text(encoding="utf-8"))

    def test_lesson_schema_and_identifiers(self):
        pages = self.pages
        self.assertEqual(len(pages), 16)
        self.assertEqual(len({p["code"] for p in pages}), len(pages))
        self.assertEqual(len({(p["class_id"], p["page"]) for p in pages}), len(pages))
        for p in pages:
            self.assertEqual(set(p), {"code", "class_id", "page", "title", "text"})
            self.assertIs(type(p["page"]), int)
            self.assertGreater(p["page"], 0)
            for k in ("code", "class_id", "title", "text"):
                self.assertIsInstance(p[k], str)
                self.assertTrue(p[k].strip())
        self.assertEqual([p["page"] for p in pages if p["class_id"] == "10A1"], list(range(1, 16)))

    def test_assignment_schema_and_links(self):
        assignments = self.assignments
        self.assertGreaterEqual(len(assignments), 12)
        self.assertEqual(len({a["id"] for a in assignments}), len(assignments))
        classes = {p["code"]: p["class_id"] for p in self.pages}
        for a in assignments:
            self.assertEqual(set(a), {"id", "class_id", "title", "question", "due_at", "answer_key", "final_answers", "lesson_codes"})
            for k in ("id", "class_id", "title", "question", "due_at", "answer_key"):
                self.assertIsInstance(a[k], str)
                self.assertTrue(a[k].strip())
            self.assertTrue(a["final_answers"])
            self.assertTrue(all(isinstance(v, str) and v.strip() for v in a["final_answers"]))
            self.assertTrue(a["lesson_codes"])
            for code in a["lesson_codes"]:
                self.assertEqual(classes[code], a["class_id"])
            self.assertIsNotNone(datetime.fromisoformat(a["due_at"]).tzinfo)

    def test_status_distribution_at_benchmark_time(self):
        now = datetime.fromisoformat(ASKED_AT)
        main = [a for a in self.assignments if a["class_id"] == "10A1"]
        self.assertGreaterEqual(sum(datetime.fromisoformat(a["due_at"]) > now for a in main), 8)
        self.assertGreaterEqual(sum(datetime.fromisoformat(a["due_at"]) <= now for a in main), 2)
        self.assertTrue(any(a["class_id"] != "10A1" for a in self.assignments))

    def test_all_roots_by_discriminant_substitution_and_viete(self):
        for assignment in self.assignments:
            with self.subTest(assignment=assignment["id"]):
                a, b, c = coefficients(assignment["question"])
                delta = b * b - 4 * a * c
                if assignment["id"] == "BT02":
                    self.assertEqual(delta, 25)
                    self.assertEqual(assignment["final_answers"], ["25"])
                    continue
                roots = ROOTS[assignment["id"]]
                computed = set()
                if delta >= 0:
                    square_root = math.isqrt(delta.numerator)
                    self.assertEqual(square_root ** 2, delta)
                    computed = {(-b + square_root) / (2 * a), (-b - square_root) / (2 * a)}
                self.assertEqual(computed, roots)
                for root in roots:
                    self.assertEqual(a * root * root + b * root + c, 0)
                if roots:
                    r, s = (list(roots) * 2)[:2]
                    self.assertEqual(r + s, -b / a)
                    self.assertEqual(r * s, c / a)
                else:
                    self.assertLess(delta, 0)

    def test_final_answer_variants_are_exact(self):
        for assignment in self.assignments:
            if assignment["id"] == "BT02":
                continue
            roots = ROOTS[assignment["id"]]
            if not roots:
                self.assertEqual(set(assignment["final_answers"]), {"vô nghiệm", "không có nghiệm thực", "S = ∅"})
            else:
                values = {final_value(v) for v in assignment["final_answers"]}
                self.assertNotIn(None, values)
                self.assertEqual(values, roots)

    def test_private_answers_not_returned_before_due(self):
        for assignment in self.assignments:
            public = tools.get_assignment(assignment["id"], "2026-11-01T00:00:00+07:00")
            self.assertNotIn("answer_key", public)
            self.assertNotIn("final_answers", public)
            self.assertEqual(set(public), {"id", "class_id", "title", "question", "due_at", "lesson_codes"})

    def test_answer_key_available_at_due_boundary(self):
        for assignment in self.assignments:
            public = tools.get_assignment(assignment["id"], assignment["due_at"])
            self.assertEqual(public["answer_key"], assignment["answer_key"])

    def test_delta_search_preserves_page_two(self):
        for query in ("Delta là gì", "Delta la gi", "biệt thức Delta"):
            chunks = tools.search_lesson(query, "10A1")
            self.assertTrue(any(c["code"] == "T10-C3-P02" and c["page"] == 2 for c in chunks))
            self.assertTrue(all(c["class_id"] == "10A1" for c in chunks))

    def test_other_class_retrieval_is_isolated(self):
        chunks = tools.search_lesson("phương trình bậc hai", "10B1")
        self.assertEqual([c["code"] for c in chunks], ["T10B-C3-P01"])
        self.assertEqual(tools.search_lesson("Delta", "UNKNOWN"), [])

    def test_hint_prompt_never_contains_private_answer_key(self):
        calls = []

        def model(system, user):
            calls.append(user)
            return {"text": "[QUYET_DINH: GOI_Y]\nEm kiểm tra lại dấu trong công thức nhé."}

        with patch.object(agent, "call_model", side_effect=model):
            for a in self.assignments:
                if datetime.fromisoformat(a["due_at"]) > datetime.fromisoformat(ASKED_AT):
                    result = agent.answer(json.dumps({"assignment_id": a["id"], "role": "student", "asked_at": ASKED_AT, "message": "Em cần kiểm tra công thức."}))
                    self.assertIn("output", result)
                    self.assertNotIn("ĐÁP ÁN MẪU", calls[-1])
                    self.assertNotIn(a["answer_key"], calls[-1])


if __name__ == "__main__":
    unittest.main()
