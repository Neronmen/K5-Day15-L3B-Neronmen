"""Leak formats and non-answer numbers, plus the actual agent retry contract."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase"))
import agent
from tools import check_leak


class CheckLeakTests(unittest.TestCase):
    def test_plain_assignment(self):
        self.assertTrue(check_leak("Vậy x = 2.", ["x=2"])["leaked"])

    def test_indexed_roots(self):
        self.assertTrue(check_leak("x1 = 2, x2 = 3", ["x=2", "x=3"])["leaked"])

    def test_vietnamese_assignment(self):
        self.assertTrue(check_leak("Vậy x bằng 2", ["x=2"])["leaked"])

    def test_solution_sentence(self):
        self.assertTrue(check_leak("Hai nghiệm là 2 và 3.", ["x=2", "x=3"])["leaked"])

    def test_decimal_comma(self):
        self.assertTrue(check_leak("x = 0,5", ["x=1/2"])["leaked"])

    def test_decimal_point(self):
        self.assertTrue(check_leak("x = 0.50", ["x=1/2"])["leaked"])

    def test_fraction_equivalence(self):
        self.assertTrue(check_leak("x = 2 / 4", ["x=0.5"])["leaked"])

    def test_latex_fraction(self):
        self.assertTrue(check_leak(r"\(x_{1}=\dfrac{1}{2}\)", ["x=0.5"])["leaked"])

    def test_unicode_negative(self):
        self.assertTrue(check_leak("x₂ = − 1,5", ["x=-3/2"])["leaked"])

    def test_unicode_spaces_and_fullwidth(self):
        self.assertTrue(check_leak("ｘ\u200b＝\u00a0２", ["x=2"])["leaked"])

    def test_set_of_roots(self):
        for text in (r"S = \{2; 3\}", r"x \in \{2;3\}", "Đáp số: 2 và 3", "2"):
            with self.subTest(text=text):
                self.assertTrue(check_leak(text, ["x=2", "x=3"])["leaked"])

    def test_scalar_answer(self):
        self.assertTrue(check_leak("Delta = 25", ["25"])["leaked"])

    def test_no_real_solution(self):
        self.assertTrue(check_leak("Phương trình không có nghiệm thực.", ["vô nghiệm", "S=∅"])["leaked"])

    def test_no_solution_negation_is_not_a_conclusion(self):
        self.assertFalse(check_leak("Chưa thể kết luận vô nghiệm; hãy tính Delta.", ["vô nghiệm"])["leaked"])

    def test_step_numbers_and_coefficients(self):
        for text in ("Xem bước 2.", "Hệ số a bằng 2.", "Mẫu số là 2a.", "Hệ số b = 3."):
            with self.subTest(text=text):
                self.assertFalse(check_leak(text, ["x=2", "x=3"])["leaked"])

    def test_polynomial_and_intermediate_calculation(self):
        for text in ("Đề bài x^2 - 5x + 6 = 0.", "Delta = 3 + 2 = 5.", "Thay a = 2 vào mẫu 2a."):
            with self.subTest(text=text):
                self.assertFalse(check_leak(text, ["x=2", "x=3"])["leaked"])

    def test_numbers_from_different_assignment(self):
        self.assertFalse(check_leak("x = 7 hoặc x = 8", ["x=2", "x=3"])["leaked"])

    def test_numeric_boundaries(self):
        for text in ("x=20", "x=2.5", "x=2/3", "x=2a", "x=2+1", "x=2^3", "x=2(a+1)", "x=2×a", r"x=2\times a"):
            with self.subTest(text=text):
                self.assertFalse(check_leak(text, ["x=2"])["leaked"])

    def test_question_and_negated_assignment(self):
        for text in ("Em thử tính x = 2 có đúng không?", "Không phải x = 2.", "x khác 2", "x ≠ 2"):
            with self.subTest(text=text):
                # Explicitly displaying an actual final root is treated conservatively.
                self.assertTrue(check_leak(text, ["x=2"])["leaked"])

    def test_empty_data(self):
        self.assertEqual(check_leak("", ["x=2"]), {"leaked": False, "matches": []})
        self.assertEqual(check_leak("x=2", []), {"leaked": False, "matches": []})
        self.assertEqual(check_leak("x=2", ["", None]), {"leaked": False, "matches": []})

    def test_matches_keep_original_final_answer_strings(self):
        answers = ["x = 1/2", "x = 0,5", "x=3"]
        self.assertEqual(check_leak("x₁ = 0.50", answers), {"leaked": True, "matches": answers[:2]})

    def test_fraction_signs_and_zero_denominator(self):
        self.assertTrue(check_leak("x = 3 / -2", ["x=-1.5"])["leaked"])
        self.assertFalse(check_leak("x = 1/0", ["x=1"])["leaked"])

    def test_chained_numeric_equalities(self):
        for reply, answer in (("x = -4/2 = -2", "x=-2"), ("x = 6/2 = 3", "x=3"), ("x = 99 = 2", "x=2"), ("x = (1/2) = 0.5", "x=0.5")):
            with self.subTest(reply=reply):
                self.assertTrue(check_leak(reply, [answer])["leaked"])
        self.assertFalse(check_leak("x=2+1", ["x=2"])["leaked"])

    def test_plus_minus_root_notation(self):
        for reply in ("x=±3/2", r"x=\pm\frac{3}{2}", "x ∈ {±1.5}"):
            with self.subTest(reply=reply):
                self.assertEqual(check_leak(reply, ["x=1.5", "x=-1.5"])["matches"], ["x=1.5", "x=-1.5"])
        self.assertFalse(check_leak("x=±2a", ["x=2"])["leaked"])

    def test_every_packaged_answer_key_triggers_the_guard(self):
        path = Path(__file__).resolve().parents[1] / "data/assignments.json"
        for assignment in json.loads(path.read_text(encoding="utf-8")):
            with self.subTest(assignment=assignment["id"]):
                self.assertTrue(check_leak(assignment["answer_key"], assignment["final_answers"])["leaked"])

    def test_no_code_execution(self):
        self.assertFalse(check_leak("x=__import__('os').system('echo bad')", ["x=2"])["leaked"])

    def test_agent_retries_and_falls_back(self):
        for reply in ("x1 bằng 2", "x=4/2=2", "x=±2"):
            with self.subTest(reply=reply), patch.object(agent, "call_model", return_value={"text": "[QUYET_DINH: GOI_Y]\n" + reply}) as model:
                self.assertEqual(agent.answer("Em kiểm tra giúp bước này")["output"], agent.SAFE_HINT)
                self.assertEqual(model.call_count, 2)

    def test_agent_returns_clean_retry(self):
        with patch.object(agent, "call_model", side_effect=[{"text": "x1 = 2"}, {"text": "[QUYET_DINH: GOI_Y]\nEm xem lại dấu của b."}]) as model:
            self.assertIn("Em xem lại", agent.answer("Em cần gợi ý")["output"])
            self.assertEqual(model.call_count, 2)


if __name__ == "__main__":
    unittest.main()
