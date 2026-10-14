"""Validation and audit tools for Vietnam Lottery source data.

No historical outcome is inferred or repaired here. Missing values are errors,
not implicit zero prizes. This module is safe to import without network access.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

REGIONS = ("mb", "mn", "mt")
PRIZE_COUNTS = {"ĐB": 1, "1": 1, "2": 1, "3": 2, "4": 7, "5": 1, "6": 3, "7": 1, "8": 1}
MB_PRIZE_FIELDS = (
    ["special", "prize1"] + [f"prize2_{i}" for i in range(1, 3)]
    + [f"prize3_{i}" for i in range(1, 7)]
    + [f"prize4_{i}" for i in range(1, 5)]
    + [f"prize5_{i}" for i in range(1, 7)]
    + [f"prize6_{i}" for i in range(1, 4)]
    + [f"prize7_{i}" for i in range(1, 5)]
)
MULTI_PRIZE_FIELDS = (
    ["special", "prize1", "prize2", "prize3_1", "prize3_2"]
    + [f"prize4_{i}" for i in range(1, 8)] + ["prize5"]
    + [f"prize6_{i}" for i in range(1, 4)] + ["prize7", "prize8"]
)


def validate_prize_structure(prizes: dict) -> None:
    """Reject partial or malformed XSMN/XSMT prize tables."""
    for label, count in PRIZE_COUNTS.items():
        values = prizes.get(label)
        if not isinstance(values, list) or len(values) != count:
            raise ValueError(f"Prize {label}: expected {count} values; found {values!r}")
        if any(type(v) is not int or v < 0 for v in values):
            raise ValueError(f"Prize {label}: expected non-negative integers, found {values!r}")


def validate_mb_result(prizes: dict) -> None:
    missing = [field for field in MB_PRIZE_FIELDS if field not in prizes]
    if missing:
        raise ValueError(f"Missing XSMB prizes: {', '.join(missing)}")
    if any(type(prizes[name]) is not int or prizes[name] < 0 for name in MB_PRIZE_FIELDS):
        raise ValueError("Malformed XSMB prize value")


def validate_csv(region: str, data_dir: Path) -> dict:
    region = region.lower()
    if region not in REGIONS:
        raise ValueError(f"Unknown region: {region}")
    csv_path = data_dir / f"xs{region}-2-digits.csv"
    report = {"region": region.upper(), "file": str(csv_path), "rows": 0,
              "date_min": None, "date_max": None, "issues": [], "warnings": []}
    if not csv_path.exists():
        report["issues"].append("Missing CSV file")
        return report
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        expected = MB_PRIZE_FIELDS if region == "mb" else MULTI_PRIZE_FIELDS
        fields = set(reader.fieldnames or [])
        needed = {"date", *expected} | ({"province"} if region != "mb" else set())
        if missing := (needed - fields):
            report["issues"].append("Missing columns: " + ", ".join(sorted(missing)))
            return report
        seen, dates = set(), []
        equal_third = 0
        for line_no, row in enumerate(reader, 2):
            report["rows"] += 1
            try:
                d = date.fromisoformat(row["date"])
                dates.append(d)
            except (TypeError, ValueError):
                report["issues"].append(f"line {line_no}: invalid date")
                continue
            province = row.get("province", "")
            if region != "mb" and not province.strip():
                report["issues"].append(f"line {line_no}: missing province")
            identity = (d, province)
            if identity in seen:
                report["issues"].append(f"line {line_no}: duplicate date/province {identity}")
            seen.add(identity)
            for field in expected:
                raw = row.get(field)
                if raw is None or raw.strip() == "":
                    report["issues"].append(f"line {line_no}: missing {field}")
                    continue
                try:
                    number = int(raw)
                except ValueError:
                    report["issues"].append(f"line {line_no}: non-numeric {field}={raw}")
                    continue
                if number < 0 or number > 99:
                    report["issues"].append(f"line {line_no}: out of range {field}={number}")
            if region == "mb" and row["prize3_3"] == row["prize3_5"]:
                equal_third += 1
        if dates:
            report["date_min"], report["date_max"] = min(dates).isoformat(), max(dates).isoformat()
        if region == "mb" and report["rows"] >= 20 and equal_third == report["rows"]:
            report["warnings"].append(
                "XSMB prize3_3 == prize3_5 in EVERY row; legacy field mapping bug likely. "
                "Historical rows require independent re-fetch/verification."
            )
    raw_path = data_dir / f"xs{region}.csv"
    if raw_path.exists():
        with raw_path.open(encoding="utf-8-sig", newline="") as stream:
            raw_rows = list(csv.DictReader(stream))
        with csv_path.open(encoding="utf-8-sig", newline="") as stream:
            suffix_rows = list(csv.DictReader(stream))
        def row_key(row):
            return (row.get("date", ""), row.get("province", ""))
        raw_index = {row_key(row): row for row in raw_rows}
        suffix_index = {row_key(row): row for row in suffix_rows}
        if set(raw_index) != set(suffix_index):
            report["issues"].append("Raw CSV and 2-digits CSV have mismatched date/province keys")
        for key, row in suffix_index.items():
            original = raw_index.get(key)
            if original is None:
                continue
            for field in expected:
                try:
                    if int(original[field]) % 100 != int(row[field]):
                        report["issues"].append(f"Raw vs 2-digit mismatch at {key} {field}")
                except (KeyError, TypeError, ValueError):
                    report["issues"].append(f"Invalid raw/2-digit field at {key} {field}")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Audit the three region 2-digit CSVs")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--region", choices=["MB", "MN", "MT"])
    parser.add_argument("--strict", action="store_true", help="fail on warnings too")
    parser.add_argument("--output", help="optional report JSON file")
    args = parser.parse_args(argv)
    report = [validate_csv(r, Path(args.data_dir)) for r in ([args.region.lower()] if args.region else REGIONS)]
    message = json.dumps(report, indent=2, ensure_ascii=False)
    print(message)
    if args.output:
        Path(args.output).write_text(message + "\n", encoding="utf-8")
    return int(any(x["issues"] or (args.strict and x["warnings"]) for x in report))


if __name__ == "__main__":
    raise SystemExit(main())
