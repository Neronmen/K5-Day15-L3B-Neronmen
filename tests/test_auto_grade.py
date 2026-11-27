"""Synthetic fixtures only. These are not model runs or human grading evidence."""
import copy
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
import auto_grade
from run_eval import load_yaml


class AutoGradeTests(unittest.TestCase):
    def setUp(self):
        self.request = {"assignment_id": "SYNTHETIC_BT", "role": "student", "asked_at": "2026-11-28T21:00:00+07:00", "message": "Bước synthetic đang làm; không phải lời người dùng thật."}
        self.benchmark = [{"id": "FIXTURE01", "input": json.dumps(self.request, ensure_ascii=False), "expected": json.dumps({"decision": "GOI_Y", "error_step": 2}), "pass_criterion": "Synthetic fixture only; human must inspect.", "type": "kho", "source": "tu_viet: SYNTHETIC_TEST_ONLY"}]
        self.runs = [{field: "" for field in auto_grade.OUT_COLS}]
        self.runs[0].update({field: self.benchmark[0][field] for field in ("id", "input", "expected", "pass_criterion", "type")})
        self.runs[0].update({"run_id": "SYNTHETIC_FIXTURE_ONLY", "model": "synthetic-fixture-not-a-model", "model_calls": "0", "tokens_in": "0", "tokens_out": "0", "output": "[QUYET_DINH: GOI_Y]\nEm kiểm tra dấu trong công thức."})
        self.assignments = [{"id": "SYNTHETIC_BT", "class_id": "TEST_CLASS", "due_at": "2026-12-05T23:59:00+07:00", "final_answers": ["x=2", "x=3"]}]
        self.lessons = [{"code": "TEST-C3-P02", "page": 2, "class_id": "TEST_CLASS"}, {"code": "TEST-C3-P03", "page": 3, "class_id": "TEST_CLASS"}, {"code": "OTHER-C3-P01", "page": 1, "class_id": "OTHER_CLASS"}]
        self.spec = load_yaml(str(ROOT / "eval/metric_spec.yaml"))

    def grade(self):
        return auto_grade.grade_records(self.runs, self.benchmark, self.assignments, self.lessons, self.spec)

    def result(self):
        return self.grade()["rows"][0]

    def set_request(self, **changes):
        self.request.update(changes)
        self.benchmark[0]["input"] = self.runs[0]["input"] = json.dumps(self.request, ensure_ascii=False)

    def theory(self, codes=None):
        expected = {"decision": "LY_THUYET"}
        if codes is not None:
            expected["source_codes"] = codes
        self.benchmark[0]["expected"] = self.runs[0]["expected"] = json.dumps(expected)
        self.runs[0]["output"] = "[QUYET_DINH: LY_THUYET]\nDelta là biệt thức. [Nguồn: TEST-C3-P02 - Trang 2]"

    def test_clean_hint_remains_pending_human(self):
        result = self.result()
        self.assertEqual(result["review_status"], "HUMAN_REVIEW")
        self.assertEqual(result["suggested_pass"], "")
        self.assertEqual(result["metrics"]["error_pinpoint"]["state"], "PENDING")
        self.assertFalse(self.grade()["ready_for_final_report"])

    def test_leak_uses_correct_assignment_and_exact_formats(self):
        for reply in ("Nghiệm là 2 và 3.", "x = 6/2 = 3", "x = ±2", "x=(±2)", "±2"):
            with self.subTest(reply=reply):
                self.runs[0]["output"] = "[QUYET_DINH: GOI_Y]\n" + reply
                row = self.result()
                self.assertEqual(row["review_status"], "RESPONSE_ERROR")
                self.assertEqual(row["suggested_pass"], "0")
                self.assertEqual(self.grade()["metrics"]["leak_rate"]["numerator"], 1)
                self.assertEqual(self.grade()["metrics"]["leak_rate"]["denominator"], 1)

    def test_other_roots_and_intermediate_numbers_do_not_leak(self):
        self.runs[0]["output"] += " Bước 2: hệ số a bằng 2. Delta = 3. x=7."
        self.assertEqual(self.result()["metrics"]["leak_rate"]["state"], "PASS")

    def test_wrong_decision_is_response_error(self):
        self.runs[0]["output"] = "[QUYET_DINH: GIAI]\nEm xem lại."
        self.assertEqual(self.result()["review_status"], "RESPONSE_ERROR")

    def test_decision_must_be_on_first_line(self):
        self.runs[0]["output"] = "Lời mở đầu\n[QUYET_DINH: GOI_Y]"
        self.assertEqual(self.result()["metrics"]["decision_accuracy"]["state"], "FAIL")

    def test_ambiguous_or_missing_expected_is_missing_data(self):
        for expected in ("No decision", "[QUYET_DINH: GOI_Y] or [QUYET_DINH: GIAI]", '{"decision":[]}'):
            with self.subTest(expected=expected):
                self.benchmark[0]["expected"] = self.runs[0]["expected"] = expected
                row = self.result()
                self.assertEqual(row["review_status"], "MISSING_DATA")
                self.assertIsNone(row["metrics"]["grounding"]["applicable"])

    def test_text_expected_label_is_supported(self):
        self.benchmark[0]["expected"] = self.runs[0]["expected"] = "[QUYET_DINH: GOI_Y] Chỉ đúng bước sai."
        self.assertEqual(self.result()["metrics"]["decision_accuracy"]["state"], "PASS")

    def test_due_boundary_and_teacher_exclude_leak_metric(self):
        for changes in ({"asked_at": self.assignments[0]["due_at"]}, {"role": "teacher"}):
            with self.subTest(changes=changes):
                self.set_request(role="student", asked_at="2026-11-28T21:00:00+07:00", **{})
                self.set_request(**changes)
                self.runs[0]["output"] += " x=2"
                self.assertFalse(self.result()["metrics"]["leak_rate"]["applicable"])

    def test_missing_assignment_is_legitimate_not_found_case(self):
        self.set_request(assignment_id="NONEXISTENT")
        self.benchmark[0]["expected"] = self.runs[0]["expected"] = '[QUYET_DINH: KHONG_CO]'
        self.runs[0]["output"] = '[QUYET_DINH: KHONG_CO]\nKhông tìm thấy.'
        self.assertEqual(self.result()["metrics"]["decision_accuracy"]["state"], "PASS")
        self.assertFalse(self.result()["metrics"]["leak_rate"]["applicable"])

    def test_missing_final_answers_is_not_silent_no_leak(self):
        del self.assignments[0]["final_answers"]
        report = self.grade()
        self.assertEqual(report["rows"][0]["review_status"], "MISSING_DATA")
        self.assertEqual(report["metrics"]["leak_rate"]["unknown"], 1)
        self.assertIsNone(report["metrics"]["leak_rate"]["rate"])

    def test_bad_due_date_has_unknown_applicability(self):
        self.assignments[0]["due_at"] = "bad date"
        report = self.grade()
        self.assertEqual(report["metrics"]["leak_rate"]["unknown_applicability"], 1)
        self.assertEqual(report["metrics"]["leak_rate"]["threshold_status"], "INCOMPLETE")

    def test_invalid_request_is_missing_data(self):
        self.benchmark[0]["input"] = self.runs[0]["input"] = "not JSON"
        self.assertEqual(self.result()["review_status"], "MISSING_DATA")

    def test_missing_row_stays_in_denominator(self):
        self.runs = []
        report = self.grade()
        self.assertEqual(report["rows"][0]["review_status"], "SYSTEM_ERROR")
        self.assertEqual(report["metrics"]["decision_accuracy"]["denominator"], 1)
        self.assertEqual(report["metrics"]["leak_rate"]["denominator"], 1)
        self.assertEqual(report["metrics"]["error_pinpoint"]["denominator"], 1)

    def test_system_error_is_not_response_error(self):
        self.runs[0]["error"] = "SYNTHETIC API failure"
        result = self.result()
        self.assertEqual(result["review_status"], "SYSTEM_ERROR")
        self.assertEqual(result["suggested_pass"], "")

    def test_empty_output_is_system_error(self):
        self.runs[0]["output"] = " "
        self.assertEqual(self.result()["review_status"], "SYSTEM_ERROR")

    def test_human_values_and_output_are_unchanged_even_on_failure(self):
        self.runs[0].update({"pass": "1", "ghi_chu": "SYNTHETIC HUMAN FIXTURE; keep exactly", "output": "[QUYET_DINH: GIAI]\r\nx=2\r\n"})
        before = copy.deepcopy(self.runs)
        result = self.result()
        self.assertEqual(self.runs, before)
        self.assertEqual(result["original"], before[0])
        self.assertEqual(result["suggested_pass"], "0")
        self.assertEqual(result["metrics"]["error_pinpoint"]["state"], "PENDING")

    def test_benchmark_drift_blocks_grading(self):
        self.benchmark[0]["pass_criterion"] += " changed"
        result = self.result()
        self.assertEqual(result["review_status"], "MISSING_DATA")
        self.assertIn("snapshot_mismatch", result["issues"][0])

    def test_theory_correct_source_remains_human_review(self):
        self.theory(["TEST-C3-P02"])
        result = self.result()
        self.assertEqual(result["metrics"]["grounding"]["state"], "PASS")
        self.assertEqual(result["suggested_pass"], "")

    def test_theory_source_in_pass_criterion(self):
        self.theory()
        self.benchmark[0]["pass_criterion"] = self.runs[0]["pass_criterion"] = "Nguồn kỳ vọng TEST-C3-P02"
        self.assertEqual(self.result()["metrics"]["grounding"]["state"], "PASS")

    def test_theory_missing_expected_source_is_missing_data(self):
        self.theory()
        self.assertEqual(self.result()["metrics"]["grounding"]["state"], "MISSING_DATA")

    def test_theory_missing_citation_fails(self):
        self.theory(["TEST-C3-P02"])
        self.runs[0]["output"] = "[QUYET_DINH: LY_THUYET]\nKhông kèm nguồn."
        self.assertEqual(self.result()["metrics"]["grounding"]["state"], "FAIL")

    def test_theory_wrong_page_unknown_source_and_unexpected_source(self):
        self.theory(["TEST-C3-P02"])
        for tag in ("[Nguồn: TEST-C3-P02 - Trang 9]", "[Nguồn: INVENTED-C3-P04 - Trang 4]", "[Nguồn: TEST-C3-P03 - Trang 3]", "[Nguồn: OTHER-C3-P01 - Trang 1]"):
            with self.subTest(tag=tag):
                self.runs[0]["output"] = "[QUYET_DINH: LY_THUYET]\n" + tag
                self.assertEqual(self.result()["metrics"]["grounding"]["state"], "FAIL")

    def test_cross_class_expected_source_is_missing_data(self):
        self.theory(["OTHER-C3-P01"])
        self.assertEqual(self.result()["metrics"]["grounding"]["state"], "MISSING_DATA")

    def test_malformed_citation_alongside_valid_one_fails(self):
        self.theory(["TEST-C3-P02"])
        self.runs[0]["output"] += " [Nguồn: malformed]"
        self.assertEqual(self.result()["metrics"]["grounding"]["state"], "FAIL")

    def test_non_applicable_metrics_are_na_not_perfect_scores(self):
        self.benchmark[0]["expected"] = self.runs[0]["expected"] = "[QUYET_DINH: TU_CHOI]"
        self.runs[0]["output"] = "[QUYET_DINH: TU_CHOI]\nEm gửi bước đang làm nhé."
        for name in ("grounding", "error_pinpoint"):
            metric = self.grade()["metrics"][name]
            self.assertEqual(metric["threshold_status"], "N/A")
            self.assertIsNone(metric["rate"])

    def test_denominators_include_system_errors_and_missing_cases(self):
        second = copy.deepcopy(self.benchmark[0])
        second["id"] = "FIXTURE02"
        self.benchmark.append(second)
        report = self.grade()
        self.assertEqual(report["metrics"]["decision_accuracy"]["numerator"], 1)
        self.assertEqual(report["metrics"]["decision_accuracy"]["denominator"], 2)
        self.assertEqual(report["metrics"]["decision_accuracy"]["coverage"], 0.5)
        self.assertIsNone(report["metrics"]["decision_accuracy"]["rate"])

    def test_pending_spec_cannot_become_approved(self):
        report = self.grade()
        self.assertEqual(report["spec_approval"]["status"], "pending")
        self.assertEqual(report["metrics"]["decision_accuracy"]["threshold_status"], "PENDING_APPROVAL")

    def test_approved_fixture_thresholds_use_spec_values(self):
        self.spec["approval"] = {"status": "approved", "approved_at": "SYNTHETIC_TEST_ONLY"}
        metric = next(m for m in self.spec["metrics"] if m["name"] == "decision_accuracy")
        metric["target"] = 0.5
        self.assertEqual(self.grade()["metrics"]["decision_accuracy"]["threshold_status"], "MEETS_THRESHOLD_PROVISIONALLY")
        self.assertFalse(self.grade()["ready_for_final_report"])

    def test_extra_run_ids_reported(self):
        self.runs.append(dict(self.runs[0], id="EXTRA_FIXTURE"))
        self.assertEqual(self.grade()["unmatched_run_ids"], ["EXTRA_FIXTURE"])

    def test_duplicate_ids_and_invalid_metric_specs_rejected(self):
        self.runs.append(dict(self.runs[0]))
        with self.assertRaises(auto_grade.ValidationError):
            self.grade()
        self.runs.pop()
        self.spec["metrics"][0]["target"] = "not numeric"
        with self.assertRaises(auto_grade.ValidationError):
            self.grade()

    def fixture_files(self, directory):
        paths = {name: directory / filename for name, filename in {"run":"synthetic-fixture.csv", "benchmark":"benchmark-fixture.csv", "assignments":"assignments.json", "lessons":"lessons.json"}.items()}
        for name, fields, rows in (("run", auto_grade.OUT_COLS, self.runs), ("benchmark", auto_grade.REQUIRED, self.benchmark)):
            with paths[name].open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
        paths["assignments"].write_text(json.dumps(self.assignments), encoding="utf-8")
        paths["lessons"].write_text(json.dumps(self.lessons), encoding="utf-8")
        return paths

    def cli(self, paths, *extra):
        return subprocess.run([sys.executable, str(ROOT/"eval/auto_grade.py"), str(paths["run"]), "--benchmark", str(paths["benchmark"]), "--assignments", str(paths["assignments"]), "--lessons", str(paths["lessons"]), *extra], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")

    def test_cli_draft_keeps_all_inputs_byte_for_byte_and_records_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            self.runs[0]["output"] += "\r\nPreserve original newline."
            paths = self.fixture_files(directory)
            before = {name: path.read_bytes() for name, path in paths.items()}
            report_path = directory/"draft.json"
            result = self.cli(paths, "--report", str(report_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual({name: path.read_bytes() for name, path in paths.items()}, before)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["rows"][0]["original"]["output"], self.runs[0]["output"])
            self.assertFalse(report["provenance"]["historical_snapshot_verified"])
            self.assertEqual(len(report["provenance"]["current_inputs"]["run"]["sha256"]), 64)

    def test_cli_never_overwrites_an_existing_report_or_input(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = self.fixture_files(Path(temp))
            before = paths["run"].read_bytes()
            result = self.cli(paths, "--report", str(paths["run"]))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(paths["run"].read_bytes(), before)

    def test_missing_csv_headers_fail_cleanly(self):
        with tempfile.TemporaryDirectory() as temp:
            paths = self.fixture_files(Path(temp))
            paths["run"].write_text("id,output\nFIXTURE01,test\n", encoding="utf-8")
            result = self.cli(paths)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("headers", result.stderr)


if __name__ == "__main__":
    unittest.main()
