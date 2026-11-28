"""Aggregate anonymized Q5 responses for H-05. Does not call a model.

python cost/analyze_q5.py --git-ref <survey-commit> --output cost/survey-q5-analysis.json
python cost/analyze_q5.py --survey evidence/survey/results.csv
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
SURVEY_PATH = "evidence/survey/results.csv"
BUCKETS = ("0", "1-2", "3-5", "6-10", "Trên 10")
MIDPOINTS = {"0": 0.0, "1-2": 1.5, "3-5": 4.0, "6-10": 8.0}
GROUPS = {
    "dung_it": ("0", "1-2"),
    "dung_vua": ("3-5",),
    "dung_nhieu": ("6-10", "Trên 10"),
}
WEEKS_PER_MONTH = 52 / 12


def canonical_bucket(value):
    value = unicodedata.normalize("NFKC", value or "").strip()
    value = re.sub(r"[–—−]", "-", value)
    value = re.sub(r"\s*-\s*", "-", value)
    if value.casefold() == "trên 10":
        return "Trên 10"
    return value if value in BUCKETS else None


def _column(fields, phrase):
    matches = [name for name in fields if phrase.casefold() in name.casefold()]
    if len(matches) != 1:
        raise ValueError("Need exactly one column containing " + phrase)
    return matches[0]


def _personas(counts, denominator, top_weekly):
    if not denominator:
        return []
    values = dict(MIDPOINTS, **{"Trên 10": top_weekly})
    result = []
    for name, buckets in GROUPS.items():
        count = sum(counts[bucket] for bucket in buckets)
        weekly = sum(counts[bucket] * values[bucket] for bucket in buckets) / count if count else 0.0
        result.append({
            "name": name, "buckets": list(buckets), "respondents": count,
            "share": count / denominator, "weekly_uses_assumed_mean": weekly,
            "uses_per_month": weekly * WEEKS_PER_MONTH,
            "turns_per_session": 1,
        })
    return result


def analyze_rows(rows, fields):
    """Count THPT respondents; keep zeros and report missing/invalid Q5 separately."""
    prohibited = ("email", "điện thoại", "họ tên", "họ và tên", "dấu thời gian", "timestamp")
    if any(term in name.casefold() for name in fields for term in prohibited):
        raise ValueError("Use an anonymized survey export; identifying columns are not accepted")
    if "ma" not in fields:
        raise ValueError("Anonymized respondent ID column ma is required")
    q1 = _column(fields, "Em đang học lớp")
    q5 = _column(fields, "Trong 1 tuần qua")
    ids = [row.get("ma", "").strip() for row in rows]
    if any(not re.fullmatch(r"R[0-9]+", identity) for identity in ids) or len(set(ids)) != len(ids):
        raise ValueError("Respondent IDs must be unique anonymized R-number values")
    thpt = [row for row in rows if (row.get(q1) or "").strip() in {"10", "11", "12"}]
    counts = Counter({bucket: 0 for bucket in BUCKETS})
    missing = invalid = 0
    for row in thpt:
        value = (row.get(q5) or "").strip()
        bucket = canonical_bucket(value)
        if not value:
            missing += 1
        elif bucket is None:
            invalid += 1
        else:
            counts[bucket] += 1
    valid = sum(counts.values())
    distribution = [{
        "bucket": bucket, "count": counts[bucket],
        "fraction_of_valid_q5": counts[bucket] / valid if valid else None,
        "fraction_of_thpt": counts[bucket] / len(thpt) if thpt else None,
    } for bucket in BUCKETS]
    sensitivities = []
    for label, top in [("minimum_integer_11", 11), ("baseline_assumed_12", 12), ("stress_assumed_20_not_upper_bound", 20)]:
        personas = _personas(counts, valid, top)
        sensitivities.append({
            "scenario": label, "top_bucket_weekly_assumption": top,
            "personas": personas,
            "population_uses_per_month": sum(p["share"] * p["uses_per_month"] for p in personas) if valid else None,
        })
    return {
        "total_records": len(rows), "valid_thpt_records": len(thpt),
        "excluded_non_thpt_records": len(rows) - len(thpt),
        "valid_q5_answers": valid, "missing_q5": missing, "invalid_q5": invalid,
        "zero_use_respondents_retained": counts["0"],
        "distribution": distribution,
        "personas": sensitivities[1]["personas"],
        "sensitivity": sensitivities,
        "assumptions": {
            "weeks_per_month": WEEKS_PER_MONTH, "conversion": "52 weeks / 12 months",
            "closed_band_midpoints_per_week": MIDPOINTS,
            "top_band_per_week": 12, "top_band_has_no_finite_upper_bound": True,
            "turns_per_session": 1, "turns_basis": "(tự ước tính) one independent question per session; Q5 does not measure turns",
            "adoption_fraction": 1.0,
            "adoption_basis": "(tự ước tính) pilot cohort replaces existing app use with tutor use; survey is not adoption evidence",
            "shares_denominator": "valid THPT Q5 answers, including zero-use respondents",
            "missing_answers": "not imputed; reported separately",
            "zero_within_dung_it": "zero-use members retained in within-group mean; no individual non-user is claimed to use the product",
        },
    }


def analyze_bytes(raw):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    fields = reader.fieldnames or []
    rows = list(reader)
    return analyze_rows(rows, fields)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--survey", type=Path)
    source.add_argument("--git-ref")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.git_ref:
        commit = subprocess.check_output(["git", "rev-parse", args.git_ref + "^{commit}"], cwd=ROOT, text=True).strip()
        raw = subprocess.check_output(["git", "show", commit + ":" + SURVEY_PATH], cwd=ROOT)
        provenance = {"git_commit": commit, "repo_path": SURVEY_PATH}
    else:
        raw = args.survey.read_bytes()
        provenance = {"file": str(args.survey), "git_commit": None}
    report = analyze_bytes(raw)
    report["source"] = dict(provenance, sha256=hashlib.sha256(raw).hexdigest())
    report["snapshot_recorded_at"] = datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="seconds")
    report["notice"] = "Aggregates from the author's anonymized survey snapshot. Not model usage, user adoption, interview evidence or simulation output."
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        # New snapshot only; keep earlier evidence intact.
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
