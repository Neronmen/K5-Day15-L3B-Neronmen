"""Merge author-owned cases without changing their cells.

Run `python eval/build_benchmark.py --check` first, then the same command
without --check to atomically write eval/benchmark.csv. No data is invented.
Only Python's standard library is used. A source label is not evidence:
the team must verify the real-person references before final submission.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from run_eval import REAL_SOURCES, REQUIRED, SOURCE_CODES, TYPES, source_code

ROOT = Path(__file__).resolve().parents[1]
AUTHOR_RANGES = {"khoa": range(1, 7), "ninh": range(7, 14), "thang": range(14, 22), "nhai": range(22, 31)}
INPUT_FIELDS = {"assignment_id", "role", "asked_at", "message"}


class ValidationError(ValueError):
    """Invalid or incomplete benchmark; the destination must remain unchanged."""


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError("non-JSON numeric constant: " + value)


def parse_input(value):
    """Strict JSON envelope. Empty message is valid for deliberate empty-input cases."""
    try:
        request = json.loads(value, object_pairs_hook=_unique_keys, parse_constant=_invalid_constant)
    except (ValueError, TypeError, RecursionError) as error:
        raise ValidationError("input JSON invalid: " + str(error)) from error
    if not isinstance(request, dict) or set(request) != INPUT_FIELDS:
        raise ValidationError("input requires exactly assignment_id, role, asked_at, message")
    if any(not isinstance(request[field], str) for field in INPUT_FIELDS):
        raise ValidationError("all four input fields must be strings")
    if not request["assignment_id"].strip():
        raise ValidationError("assignment_id is empty")
    if request["role"] not in {"student", "teacher"}:
        raise ValidationError("role must be student or teacher")
    try:
        asked_at = datetime.fromisoformat(request["asked_at"].replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError("asked_at must be ISO-8601") from error
    if asked_at.tzinfo is None or asked_at.utcoffset() is None:
        raise ValidationError("asked_at must include a timezone")
    return request


def _read_author(path, allowed_ids):
    errors, rows = [], []
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, strict=True)
            if reader.fieldnames != REQUIRED:
                raise ValidationError(f"{path.name}: header must be {','.join(REQUIRED)}")
            for row in reader:
                where = f"{path.name}:line {reader.line_num}"
                if None in row or any(value is None for value in row.values()):
                    errors.append(where + ": expected exactly six cells")
                    continue
                if any(not row[field].strip() for field in REQUIRED):
                    errors.append(where + ": required CSV cell is empty")
                identity = row["id"]
                if not re.fullmatch(r"B\d{2}", identity) or identity not in allowed_ids:
                    errors.append(where + ": id outside author range: " + identity)
                if row["type"] not in TYPES:
                    errors.append(where + ": invalid type: " + row["type"])
                code = source_code(row["source"])
                if code not in SOURCE_CODES:
                    errors.append(where + ": invalid source code: " + row["source"])
                if "(ví dụ" in row["source"] or row["input"].lstrip().startswith("<"):
                    errors.append(where + ": starter placeholder is not a case")
                try:
                    parse_input(row["input"])
                except ValidationError as error:
                    errors.append(where + ": " + str(error))
                rows.append(row)
    except (OSError, UnicodeError, csv.Error) as error:
        raise ValidationError(f"{path.name}: cannot read CSV: {error}") from error
    counts = Counter(row["id"] for row in rows)
    duplicates = sorted(identity for identity, count in counts.items() if count > 1)
    if duplicates:
        errors.append(path.name + ": duplicate IDs: " + ", ".join(duplicates))
    missing = sorted(allowed_ids - counts.keys())
    if missing:
        errors.append(path.name + ": missing IDs: " + ", ".join(missing))
    if errors:
        raise ValidationError("\n".join(errors))
    return rows


def load_cases(cases_dir):
    cases_dir = Path(cases_dir)
    rows, errors = [], []
    for author, numbers in AUTHOR_RANGES.items():
        path = cases_dir / (author + ".csv")
        if not path.is_file():
            errors.append("Missing file: " + str(path))
            continue
        try:
            rows.extend(_read_author(path, {f"B{n:02d}" for n in numbers}))
        except ValidationError as error:
            errors.append(str(error))
    if errors:
        raise ValidationError("\n".join(errors))
    rows.sort(key=lambda row: row["id"])
    counts = Counter(row["type"] for row in rows)
    real = sum(source_code(row["source"]) in REAL_SOURCES for row in rows)
    if counts["kho"] < 5:
        errors.append(f"Need >=5 kho cases; got {counts['kho']}")
    if counts["tu_choi"] < 2:
        errors.append(f"Need >=2 tu_choi cases; got {counts['tu_choi']}")
    if real * 3 < len(rows):
        errors.append(f"Need >=1/3 real-source cases: {real}/{len(rows)}; 30 cases require >=10. B22-B30 alone supply only 9. Verify real evidence, never relabel synthetic cases.")
    if errors:
        raise ValidationError("\n".join(errors))
    return rows


def build_benchmark(cases_dir=ROOT / "eval/cases", output=ROOT / "eval/benchmark.csv", *, check=False):
    rows = load_cases(cases_dir)
    output = Path(output)
    source_paths = {(Path(cases_dir) / (author + ".csv")).resolve() for author in AUTHOR_RANGES}
    if output.resolve() in source_paths:
        raise ValidationError("Output cannot replace an author-owned case file")
    if check:
        return rows
    # Validate every source before touching even the destination directory.
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=output.parent, prefix=".benchmark-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            writer = csv.DictWriter(stream, fieldnames=REQUIRED, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases-dir", type=Path, default=ROOT / "eval/cases")
    parser.add_argument("--output", type=Path, default=ROOT / "eval/benchmark.csv")
    parser.add_argument("--check", action="store_true", help="validate only; write nothing")
    args = parser.parse_args(argv)
    try:
        rows = build_benchmark(args.cases_dir, args.output, check=args.check)
    except (ValidationError, OSError) as error:
        print("Benchmark not written:\n" + str(error), file=sys.stderr)
        return 1
    counts = Counter(row["type"] for row in rows)
    real = sum(source_code(row["source"]) in REAL_SOURCES for row in rows)
    print(f"Validated {len(rows)} cases; types={dict(counts)}; real-source labels={real}/{len(rows)}.")
    print("No files written." if args.check else "Written: " + str(args.output))
    print("Source labels must be verified against actual evidence by the team.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
