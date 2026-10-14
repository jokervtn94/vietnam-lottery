import csv
import tempfile
import unittest
from pathlib import Path
from src.data_quality import (MB_PRIZE_FIELDS, MULTI_PRIZE_FIELDS,
                              validate_mb_result, validate_prize_structure,
                              validate_csv)


class QualityTests(unittest.TestCase):
    def test_missing_prize_row_is_rejected_instead_of_zero(self):
        rows = {"ĐB": [9], "1": [20], "2": [30], "3": [45, 49],
                "4": list(range(7)), "5": [1], "6": [2, 3, 4], "7": [50], "8": [30]}
        validate_prize_structure(rows)
        rows.pop("8")
        with self.assertRaisesRegex(ValueError, "Prize 8"):
            validate_prize_structure(rows)

    def test_invalid_prize_counts_are_rejected(self):
        rows = {"ĐB": [1], "1": [1], "2": [1], "3": [1, 2],
                "4": [1]*7, "5": [1], "6": [1, 2, 3], "7": [1], "8": [1]}
        rows["6"] = [0]
        with self.assertRaisesRegex(ValueError, "Prize 6"):
            validate_prize_structure(rows)

    def test_mb_required_fields(self):
        rows = {key: 1 for key in MB_PRIZE_FIELDS}
        validate_mb_result(rows)
        del rows["prize3_5"]
        with self.assertRaisesRegex(ValueError, "prize3_5"):
            validate_mb_result(rows)

    def test_csv_validation_and_legacy_mapping_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "xsmb-2-digits.csv"
            with path.open("w", encoding="utf8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["date", *MB_PRIZE_FIELDS])
                writer.writeheader()
                for i in range(20):
                    row = {f: 15 for f in MB_PRIZE_FIELDS}
                    row["date"] = f"2026-01-{i+1:02d}"
                    writer.writerow(row)
            result = validate_csv("mb", Path(tmp))
            self.assertEqual(result["rows"], 20)
            self.assertEqual(result["issues"], [])
            self.assertTrue(result["warnings"])

    def test_zero_is_valid_two_digit_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "xsmn-2-digits.csv"
            with path.open("w", encoding="utf8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["date", "province", *MULTI_PRIZE_FIELDS])
                writer.writeheader()
                writer.writerow({"date": "2026-10-14", "province": "Cần Thơ",
                                 **{k: 0 for k in MULTI_PRIZE_FIELDS}})
            result = validate_csv("mn", Path(tmp))
            self.assertEqual(result["issues"], [])


if __name__ == "__main__":
    unittest.main()
