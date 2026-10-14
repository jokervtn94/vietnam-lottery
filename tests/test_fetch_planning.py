import sys
import types
import unittest
from datetime import date
from unittest.mock import patch

fakes = {}
for code, name in [("mb", "LotteryMB"), ("mn", "LotteryMN"), ("mt", "LotteryMT")]:
    module = types.ModuleType(f"src.lottery{code}")
    setattr(module, name, type(name, (), {}))
    fakes[module.__name__] = module
with patch.dict(sys.modules, fakes):
    from src.fetch import choose_dates


class DatePlanningTests(unittest.TestCase):
    def test_new_region_increments_from_own_data(self):
        known = [date(2026, 10, 10), date(2026, 10, 11)]
        self.assertEqual(choose_dates(known, date(2026, 10, 14), None, None),
                         [date(2026, 10, 12), date(2026, 10, 13), date(2026, 10, 14)])

    def test_gap_repair_only_picks_missing_dates(self):
        known = [date(2026, 2, 16), date(2026, 2, 18)]
        self.assertEqual(choose_dates(known, date(2026, 2, 20), date(2026, 2, 16),
                                      date(2026, 2, 19), True),
                         [date(2026, 2, 17), date(2026, 2, 19)])

    def test_no_new_dates_after_catching_up(self):
        self.assertEqual(choose_dates([date(2026, 10, 14)],
                                      date(2026, 10, 14), None, None), [])

    def test_empty_storage_defaults_to_recent_week(self):
        self.assertEqual(len(choose_dates([], date(2026, 10, 14), None, None)), 7)

    def test_gap_repair_requires_bounds(self):
        with self.assertRaisesRegex(ValueError, "--start"):
            choose_dates([], date(2026, 10, 14), None, None, True)


if __name__ == "__main__":
    unittest.main()
