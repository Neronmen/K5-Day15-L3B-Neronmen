"""All records and source labels here are synthetic fixtures, never evidence."""
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
from build_benchmark import AUTHOR_RANGES, REQUIRED, ValidationError, build_benchmark


class BuildBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.output = self.directory / "benchmark.csv"
        self.groups = {}
        for author, numbers in AUTHOR_RANGES.items():
            self.groups[author] = [{
                "id": f"B{n:02d}",
                "input": json.dumps({"assignment_id": "BT01", "role": "student", "asked_at": "2026-11-28T21:00:00+07:00", "message": f"Synthetic fixture {n}, not a real user"}),
                "expected": "[QUYET_DINH: GOI_Y] Synthetic fixture",
                "pass_criterion": "Synthetic test only",
                "type": "thuong" if n < 21 else "kho" if n < 26 else "tu_choi",
                "source": "nguoi_dung: SYNTHETIC_TEST_ONLY" if n <= 10 else "tu_viet: SYNTHETIC_TEST_ONLY",
            } for n in reversed(list(numbers))]
        self.save()

    def save(self, author=None, fields=None):
        for name in ([author] if author else self.groups):
            with (self.directory / (name + ".csv")).open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields or REQUIRED)
                writer.writeheader()
                writer.writerows(self.groups[name])

    def build(self, **kwargs):
        return build_benchmark(self.directory, self.output, **kwargs)

    def invalid(self, message=None):
        self.output.write_bytes(b"EXISTING COMPLETE BENCHMARK\r\n")
        before = self.output.read_bytes()
        with self.assertRaises(ValidationError) as raised:
            self.build()
        if message:
            self.assertIn(message, str(raised.exception))
        self.assertEqual(self.output.read_bytes(), before)

    def test_sorted_deterministic_and_preserves_every_cell(self):
        row = self.groups["thang"][0]
        row["expected"] = 'A "quote", comma\nand newline. Vietnamese: bước đúng.'
        self.save("thang")
        originals = {row["id"]: dict(row) for group in self.groups.values() for row in group}
        self.build()
        before = self.output.read_bytes()
        self.build()
        self.assertEqual(self.output.read_bytes(), before)
        with self.output.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([row["id"] for row in rows], [f"B{n:02d}" for n in range(1, 31)])
        self.assertEqual({row["id"]: row for row in rows}, originals)

    def test_check_only_creates_no_output(self):
        self.assertEqual(len(self.build(check=True)), 30)
        self.assertFalse(self.output.exists())

    def test_missing_files_reported_together(self):
        (self.directory / "khoa.csv").unlink()
        (self.directory / "ninh.csv").unlink()
        self.invalid("Missing file")

    def test_duplicate_ids(self):
        self.groups["thang"].append(dict(self.groups["thang"][0]))
        self.save("thang")
        self.invalid("duplicate IDs")

    def test_missing_id(self):
        self.groups["thang"].pop()
        self.save("thang")
        self.invalid("missing IDs")

    def test_outside_range(self):
        self.groups["thang"][0]["id"] = "B31"
        self.save("thang")
        self.invalid("outside author range")

    def test_wrong_author_range(self):
        self.groups["thang"][0]["id"] = "B01"
        self.save("thang")
        self.invalid("outside author range")

    def test_header_order_and_extra_header(self):
        for fields in (list(reversed(REQUIRED)), REQUIRED + ["extra"]):
            with self.subTest(fields=fields):
                self.save("thang", fields)
                self.invalid("header must be")

    def test_duplicate_header(self):
        self.save("thang", REQUIRED + ["id"])
        self.invalid("header must be")

    def test_extra_and_missing_csv_cell(self):
        for text in ("B14,bad,expected,criterion,kho,tu_viet,extra\n", "B14,bad,expected\n"):
            with self.subTest(text=text):
                (self.directory / "thang.csv").write_text(",".join(REQUIRED) + "\n" + text, encoding="utf-8")
                self.invalid("six cells")

    def test_malformed_csv(self):
        (self.directory / "thang.csv").write_text(",".join(REQUIRED) + '\nB14,"unclosed', encoding="utf-8")
        self.invalid("cannot read CSV")

    def test_invalid_json_and_duplicate_keys(self):
        for text in ('not json', '[]', '{"assignment_id":"BT01","assignment_id":"BT02"}', '{"a":NaN}'):
            with self.subTest(text=text):
                self.groups["thang"][0]["input"] = text
                self.save("thang")
                self.invalid("input")

    def test_required_input_fields_and_types(self):
        original = json.loads(self.groups["thang"][0]["input"])
        for field in original:
            for value in (None, 5, [], {}):
                with self.subTest(field=field, value=value):
                    self.groups["thang"][0]["input"] = json.dumps(dict(original, **{field: value}))
                    self.save("thang")
                    self.invalid("must be strings")
        self.groups["thang"][0]["input"] = json.dumps({k: v for k, v in original.items() if k != "role"})
        self.save("thang")
        self.invalid("exactly")

    def test_empty_message_is_valid_negative_case(self):
        request = json.loads(self.groups["thang"][0]["input"])
        request["message"] = ""
        self.groups["thang"][0]["input"] = json.dumps(request)
        self.save("thang")
        self.assertEqual(len(self.build(check=True)), 30)

    def test_invalid_role_empty_assignment_and_naive_time(self):
        original = json.loads(self.groups["thang"][0]["input"])
        for field, value in (("role", "admin"), ("assignment_id", " "), ("asked_at", "2026-11-28T21:00:00"), ("asked_at", "bad")):
            with self.subTest(field=field):
                self.groups["thang"][0]["input"] = json.dumps(dict(original, **{field: value}))
                self.save("thang")
                self.invalid()

    def test_empty_required_csv_field(self):
        self.groups["thang"][0]["expected"] = " "
        self.save("thang")
        self.invalid("empty")

    def test_source_and_type_validation(self):
        for field, value in (("source", "unknown: fixture"), ("type", "hard"), ("source", "tu_viet (ví dụ — xoá dòng này)")):
            with self.subTest(field=field):
                self.groups["thang"][0][field] = value
                self.save("thang")
                self.invalid()
                self.groups["thang"][0][field] = "kho" if field == "type" else "tu_viet: fixture"

    def test_nine_real_source_labels_are_not_one_third(self):
        self.groups["ninh"][3]["source"] = "tu_viet: SYNTHETIC_TEST_ONLY"  # B10
        self.save("ninh")
        self.invalid("require >=10")

    def test_minimum_difficult_and_refusal_coverage(self):
        for group in self.groups.values():
            for row in group:
                row["type"] = "thuong"
        self.save()
        self.invalid("Need >=5 kho")

    def test_utf8_bom_is_accepted(self):
        path = self.directory / "thang.csv"
        path.write_bytes(b'\xef\xbb\xbf' + path.read_bytes())
        self.assertEqual(len(self.build(check=True)), 30)

    def test_no_partial_output_on_replace_failure(self):
        self.output.write_bytes(b'previous')
        with patch("build_benchmark.os.replace", side_effect=OSError("synthetic disk error")):
            with self.assertRaises(OSError):
                self.build()
        self.assertEqual(self.output.read_bytes(), b'previous')
        self.assertEqual(list(self.directory.glob(".benchmark-*.tmp")), [])

    def test_cannot_overwrite_member_source(self):
        path = self.directory / "thang.csv"
        before = path.read_bytes()
        with self.assertRaises(ValidationError):
            build_benchmark(self.directory, path)
        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
