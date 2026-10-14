"""Prevent accidental loss of historical data when JSON source is invalid."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from datetime import date
from unittest.mock import patch

from src.lotterymb import LotteryMB
from src.lotterymn import LotteryMN
from src import fetch as fetch_module


class SafeLoadTests(unittest.TestCase):
    def _corrupt_load(self, cls, prefix):
        with tempfile.TemporaryDirectory() as folder:
            old = Path.cwd()
            try:
                os.chdir(folder)
                instance = cls()
                (Path("data") / (prefix + ".json")).write_text("{broken json", encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "Historical data load failed"):
                    instance.load()
                self.assertEqual((Path("data") / (prefix + ".json")).read_text(encoding="utf-8"), "{broken json")
            finally:
                os.chdir(old)

    def test_mb_rejects_corrupted_json_without_replacing_it(self):
        self._corrupt_load(LotteryMB, "xsmb")

    def test_mn_rejects_corrupted_json_without_replacing_it(self):
        self._corrupt_load(LotteryMN, "xsmn")

    def test_partial_success_is_saved_and_failure_is_reported(self):
        first = date(2026, 10, 15)
        second = date(2026, 10, 16)
        fake = type("FakeLottery", (), {})
        class Storage(fake):
            last = None
            def __init__(self):
                self._data = {}
                self.saved = False
                Storage.last = self
            def load(self): pass
            def fetch(self, day):
                if day == second:
                    return None
                self._data[day] = "verified"
                return "verified"
            def generate_dataframes(self): pass
            def dump(self): self.saved = True
            def generate_and_dump_sparse_json(self): pass
        with patch.dict(fetch_module.REGION_CLASSES, {"MB": Storage}):
            result = fetch_module.fetch_region("MB", start=first, end=second, force=False, repair_gaps=False)
        self.assertEqual(result, (1, 0, 1))
        self.assertTrue(Storage.last.saved)
        self.assertEqual(Storage.last._data, {first: "verified"})

    def test_failed_refetch_restores_previous_record(self):
        first = date(2026, 10, 14)
        class Store:
            last = None
            def __init__(self):
                self._data = {first: "original"}
                self.saved = False
                Store.last = self
            def load(self): pass
            def fetch(self, day): return None
            def generate_dataframes(self): pass
            def dump(self): self.saved = True
            def generate_and_dump_sparse_json(self): pass
        with patch.dict(fetch_module.REGION_CLASSES, {"MB": Store}):
            result = fetch_module.fetch_region("MB", start=first, end=first, force=True, repair_gaps=False)
        self.assertEqual(result, (0, 0, 1))
        self.assertEqual(Store.last._data[first], "original")
        self.assertFalse(Store.last.saved)


if __name__ == "__main__":
    unittest.main()
