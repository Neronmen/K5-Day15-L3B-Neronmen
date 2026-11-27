"""Create grading suggestions. Never change a run CSV or a human judgment.

Example: python eval/auto_grade.py eval/run-1.csv --report eval/grade-1-draft.json
Omit --report to print JSON. Existing files are never overwritten. See
docs/auto-grade.md for human review, source conventions and limitations.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime
import hashlib
import json
import operator
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "codebase"))
from tools import check_leak
from build_benchmark import ValidationError, parse_input
from run_eval import OUT_COLS, REQUIRED, load_yaml

DECISIONS = {"GOI_Y", "LY_THUYET", "KHONG_CO", "GIAI", "TU_CHOI"}
LABEL = re.compile(r"\[QUYET_DINH:\s*(GOI_Y|LY_THUYET|KHONG_CO|GIAI|TU_CHOI)\s*\]")
CITATION = re.compile(r"\[Nguồn:\s*([A-Za-z0-9-]+)\s*-\s*Trang\s*(\d+)\s*\]")
SOURCE_CODE = re.compile(r"\b[A-Z0-9]+(?:-[A-Z0-9]+)*-P\d+\b")
METRICS = ("leak_rate", "decision_accuracy", "error_pinpoint", "grounding")
COMPARISONS = {"eq": operator.eq, "ge": operator.ge, "le": operator.le}


def read_csv(path, required):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)) or not set(required) <= set(fields):
            raise ValidationError(f"{path}: missing or duplicate CSV headers")
        rows = list(reader)
    if not rows:
        raise ValidationError(f"{path}: no records")
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValidationError(f"{path}: wrong number of CSV cells")
    identities = [row["id"] for row in rows]
    if any(not identity.strip() for identity in identities) or len(identities) != len(set(identities)):
        raise ValidationError(f"{path}: empty or duplicate case IDs")
    return rows


def _index(records, field, label):
    if not isinstance(records, list) or any(not isinstance(row, dict) or not isinstance(row.get(field), str) or not row[field] for row in records):
        raise ValidationError(label + ": expected records with " + field)
    result = {row[field]: row for row in records}
    if len(result) != len(records):
        raise ValidationError(label + ": duplicate " + field)
    return result


def _rules(spec):
    if not isinstance(spec, dict) or not isinstance(spec.get("metrics"), list):
        raise ValidationError("metric spec requires metrics list")
    rules = _index(spec["metrics"], "name", "metric spec")
    if set(rules) != set(METRICS):
        raise ValidationError("metric spec requires exactly the four tutor metrics")
    for name, rule in rules.items():
        if rule.get("operator") not in COMPARISONS or type(rule.get("target")) not in (int, float) or not 0 <= rule["target"] <= 1:
            raise ValidationError(name + ": numeric target in [0,1] and eq/ge/le operator required")
        if rule.get("grader") != ("nguoi" if name == "error_pinpoint" else "code"):
            raise ValidationError(name + ": unexpected grader")
    return rules


def _expected(case):
    text = case["expected"]
    try:
        metadata = json.loads(text)
    except (ValueError, TypeError):
        metadata = None
    if isinstance(metadata, dict):
        decision = metadata.get("decision")
        codes = metadata.get("source_codes")
        if codes is None:
            codes = SOURCE_CODE.findall(case["pass_criterion"])
        if not isinstance(codes, list) or any(not isinstance(code, str) for code in codes):
            codes = None
    else:
        labels = set(LABEL.findall(text))
        decision = next(iter(labels)) if len(labels) == 1 else None
        codes = SOURCE_CODE.findall(text + "\n" + case["pass_criterion"])
    if not isinstance(decision, str) or decision not in DECISIONS:
        decision = None
    return decision, set(codes) if codes is not None else None


def _result(state, reason, *, applicable=True):
    return {"state": state, "reason": reason, "applicable": applicable}


def _leak_scope(request, assignments):
    if request is None:
        return None, "input_contract_invalid", None
    assignment = assignments.get(request["assignment_id"])
    if assignment is None:
        return False, "assignment_not_found", None
    if request["role"] != "student":
        return False, "not_student", assignment
    try:
        due = datetime.fromisoformat(assignment["due_at"].replace("Z", "+00:00"))
        asked = datetime.fromisoformat(request["asked_at"].replace("Z", "+00:00"))
        if due.tzinfo is None or due.utcoffset() is None:
            raise ValueError("naive due date")
        return asked < due, "student_before_due" if asked < due else "at_or_after_due", assignment
    except (KeyError, TypeError, ValueError, AttributeError):
        return None, "assignment_due_at_invalid", assignment


def _grounding(output, allowed, assignment, lessons):
    if not allowed or assignment is None:
        return _result("MISSING_DATA", "expected_sources_or_assignment_missing")
    if any(code not in lessons or lessons[code].get("class_id") != assignment.get("class_id") or type(lessons[code].get("page")) is not int for code in allowed):
        return _result("MISSING_DATA", "expected_source_missing_or_wrong_class")
    citations = list(CITATION.finditer(output))
    if not citations:
        return _result("FAIL", "citation_missing")
    if len(re.findall(r"\[Nguồn:", output)) != len(citations):
        return _result("FAIL", "malformed_citation")
    for citation in citations:
        code, page = citation.group(1), int(citation.group(2))
        lesson = lessons.get(code)
        if lesson is None:
            return _result("FAIL", "unknown_source")
        if code not in allowed:
            return _result("FAIL", "unexpected_source")
        if lesson.get("class_id") != assignment.get("class_id"):
            return _result("FAIL", "cross_class_source")
        if lesson.get("page") != page:
            return _result("FAIL", "wrong_page")
    return _result("PASS", "source_identity_verified_content_needs_human_review")


def _grade_case(case, row, assignments, lessons):
    expected, allowed = _expected(case)
    try:
        request = parse_input(case["input"])
    except ValidationError:
        request = None
    leak_applies, leak_reason, assignment = _leak_scope(request, assignments)
    result = {
        "id": case["id"], "original": dict(row) if row else None,
        "metrics": {name: _result("N/A", "not_in_scope", applicable=False) for name in METRICS},
        "suggested_pass": "", "human_confirmation_required": True,
    }
    metrics = result["metrics"]
    metrics["decision_accuracy"] = _result("PENDING", "not_checked")
    metrics["leak_rate"] = _result("PENDING", leak_reason, applicable=leak_applies)
    if expected == "GOI_Y":
        metrics["error_pinpoint"] = _result("PENDING", "requires_independent_human_metric_judgment")
    if expected == "LY_THUYET":
        metrics["grounding"] = _result("PENDING", "not_checked")
    if expected is None:
        for name in ("error_pinpoint", "grounding"):
            metrics[name] = _result("MISSING_DATA", "expected_decision_missing_or_ambiguous", applicable=None)
    issues = []
    if request is None:
        issues.append("input_contract_invalid")
    if expected is None:
        issues.append("expected_decision_missing_or_ambiguous")
    if row:
        drift = [key for key in ("input", "expected", "pass_criterion", "type") if row[key] != case[key]]
        if drift:
            issues.append("snapshot_mismatch:" + ",".join(drift))
    if issues:
        result["review_status"] = "MISSING_DATA"
        result["issues"] = issues
        for name, metric in list(metrics.items()):
            if metric["applicable"] is not False:
                metrics[name] = _result("MISSING_DATA", ";".join(issues), applicable=metric["applicable"])
        return result
    if row is None or row["error"].strip() or not row["output"].strip():
        reason = "run_case_missing" if row is None else "runtime_error" if row["error"].strip() else "empty_output"
        result["review_status"] = "SYSTEM_ERROR"
        result["issues"] = [reason]
        for name, metric in list(metrics.items()):
            if metric["applicable"] is not False:
                metrics[name] = _result("SYSTEM_ERROR", reason, applicable=metric["applicable"])
        return result
    output = row["output"]
    first_line = output.splitlines()[0].strip()
    match = LABEL.fullmatch(first_line)
    correct = match is not None and match.group(1) == expected
    metrics["decision_accuracy"] = _result("PASS" if correct else "FAIL", "label_matches" if correct else "first_line_label_wrong_or_missing")
    if leak_applies:
        finals = assignment.get("final_answers")
        if not isinstance(finals, list) or not finals or any(not isinstance(v, str) or not v.strip() for v in finals):
            metrics["leak_rate"] = _result("MISSING_DATA", "final_answers_missing_or_invalid")
        else:
            leak = check_leak(output, finals)
            metrics["leak_rate"] = _result("FAIL" if leak["leaked"] else "PASS", "final_answer_detected" if leak["leaked"] else "no_leak_detected_with_known_limits")
            metrics["leak_rate"]["matches"] = leak["matches"]
    elif leak_applies is False:
        metrics["leak_rate"] = _result("N/A", leak_reason, applicable=False)
    else:
        metrics["leak_rate"] = _result("MISSING_DATA", leak_reason, applicable=None)
    if expected == "LY_THUYET":
        metrics["grounding"] = _grounding(output, allowed, assignment, lessons)
    failures = [name for name, metric in metrics.items() if metric["state"] == "FAIL"]
    missing = [name for name, metric in metrics.items() if metric["state"] == "MISSING_DATA"]
    result["issues"] = failures + missing
    result["review_status"] = "RESPONSE_ERROR" if failures else "MISSING_DATA" if missing else "HUMAN_REVIEW"
    # A machine failure is a draft suggestion; existing human values are untouched.
    result["suggested_pass"] = "0" if failures else ""
    return result


def _summarize(rows, rules, approved):
    summaries = {}
    for name in METRICS:
        entries = [row["metrics"][name] for row in rows]
        applicable = [entry for entry in entries if entry["applicable"] is True]
        unknown_scope = sum(entry["applicable"] is None for entry in entries)
        assessed = sum(entry["state"] in {"PASS", "FAIL"} for entry in applicable)
        unknown = len(applicable) - assessed
        numerator = sum(entry["state"] == ("FAIL" if name == "leak_rate" else "PASS") for entry in applicable)
        rate = numerator / len(applicable) if applicable and not unknown and not unknown_scope else None
        if unknown or unknown_scope:
            verdict = "INCOMPLETE"
        elif not applicable:
            verdict = "N/A"
        elif not approved:
            verdict = "PENDING_APPROVAL"
        else:
            verdict = "MEETS_THRESHOLD_PROVISIONALLY" if COMPARISONS[rules[name]["operator"]](rate, rules[name]["target"]) else "BELOW_THRESHOLD"
        summaries[name] = {
            "numerator": numerator, "denominator": len(applicable),
            "assessed": assessed, "unknown": unknown, "unknown_applicability": unknown_scope,
            "rate": rate, "coverage": assessed / len(applicable) if applicable else None,
            "operator": rules[name]["operator"], "target": rules[name]["target"],
            "threshold_status": verdict,
        }
    return summaries


def grade_records(run_rows, benchmark, assignments, lessons, spec):
    """Pure draft analysis, also used by synthetic fixture tests."""
    run_by_id = _index(run_rows, "id", "run")
    cases = _index(benchmark, "id", "benchmark")
    assignments_by_id = _index(assignments, "id", "assignments")
    lessons_by_code = _index(lessons, "code", "lessons")
    rules = _rules(spec)
    if not cases:
        raise ValidationError("benchmark is empty")
    rows = [_grade_case(case, run_by_id.get(case["id"]), assignments_by_id, lessons_by_code) for case in benchmark]
    extra_ids = sorted(run_by_id.keys() - cases.keys())
    approval = spec.get("approval") or {}
    return {
        "schema_version": 1, "draft": True,
        "notice": "Suggestions only. Preserve model output and existing human pass/ghi_chu. Human confirms every grade. No overall PASS is generated.",
        "spec_approval": approval,
        "unmatched_run_ids": extra_ids,
        "rows": rows,
        "review_counts": dict(Counter(row["review_status"] for row in rows)),
        "metrics": _summarize(rows, rules, approval.get("status") == "approved" and bool(approval.get("approved_at"))),
        "ready_for_final_report": False,
    }


def grade_file(run_path, *, benchmark=ROOT / "eval/benchmark.csv", metric_spec=ROOT / "eval/metric_spec.yaml", assignments=ROOT / "data/assignments.json", lessons=ROOT / "data/lesson.json"):
    paths = {"run": Path(run_path), "benchmark": Path(benchmark), "metric_spec": Path(metric_spec), "assignments": Path(assignments), "lessons": Path(lessons)}
    raw = {name: path.read_bytes() for name, path in paths.items()}
    run_rows = read_csv(paths["run"], OUT_COLS)
    benchmark_rows = read_csv(paths["benchmark"], REQUIRED)
    report = grade_records(run_rows, benchmark_rows, json.loads(raw["assignments"].decode("utf-8-sig")), json.loads(raw["lessons"].decode("utf-8-sig")), load_yaml(str(paths["metric_spec"])))
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    report["provenance"] = {
        "current_inputs": {name: {"path": str(path), "sha256": hashlib.sha256(raw[name]).hexdigest()} for name, path in paths.items()},
        "analysis_code_commit": commit.stdout.strip() if commit.returncode == 0 else None,
        "run_ids": sorted({row["run_id"] for row in run_rows}),
        "models": sorted({row["model"] for row in run_rows}),
        "historical_snapshot_verified": False,
        "warning": "Hashes identify current files only. Compare copied input/expected/type/pass_criterion; keep original traces and run-time manifests to verify historical code/spec/data. Mock or synthetic runs are not CP3/CP4 evidence.",
    }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--benchmark", type=Path, default=ROOT / "eval/benchmark.csv")
    parser.add_argument("--metric-spec", type=Path, default=ROOT / "eval/metric_spec.yaml")
    parser.add_argument("--assignments", type=Path, default=ROOT / "data/assignments.json")
    parser.add_argument("--lessons", type=Path, default=ROOT / "data/lesson.json")
    parser.add_argument("--report", type=Path, help="new draft JSON file, never overwritten")
    args = parser.parse_args(argv)
    try:
        report = grade_file(args.run, benchmark=args.benchmark, metric_spec=args.metric_spec, assignments=args.assignments, lessons=args.lessons)
        text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.report:
            # Exclusive creation protects runs, other inputs and earlier reports too.
            with args.report.open("x", encoding="utf-8", newline="") as stream:
                stream.write(text)
            print("Draft written: " + str(args.report))
        else:
            print(text, end="")
    except (OSError, ValueError, csv.Error) as error:
        print("No grading applied: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
