import unittest
from datetime import date
import pandas as pd
from src.lottery_analyzer import frequency_counts, draw_frequency, days_since_last_seen


class AnalyzerTests(unittest.TestCase):
    def test_leading_zero_and_draw_frequency(self):
        df = pd.DataFrame({"date": pd.to_datetime(["2026-10-10", "2026-10-11"]),
                           "province": ["Cần Thơ", "Cần Thơ"],
                           "special": [0, 7], "prize1": [0, 0]})
        self.assertEqual(int(frequency_counts(df)["00"]), 3)
        self.assertEqual(int(draw_frequency(df)["00"]), 2)
        self.assertEqual(days_since_last_seen(df, date(2026, 10, 12))["00"], 1)
        self.assertIsNone(days_since_last_seen(df, date(2026, 10, 12))["99"])

    def test_respects_as_of_no_future_leakage(self):
        df = pd.DataFrame({"date": pd.to_datetime(["2026-10-10", "2026-10-11"]),
                           "special": [1, 99]})
        self.assertIsNone(days_since_last_seen(df, date(2026, 10, 10))["99"])


if __name__ == "__main__":
    unittest.main()
