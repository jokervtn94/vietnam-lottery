"""Offline regression fixtures for XSMB HTML parsing."""
import os
import tempfile
import unittest
from pathlib import Path
from datetime import date
from src.lotterymb import LotteryMB


class FakeResponse:
    status_code = 200
    def __init__(self, text): self.text = text


class FakeHttp:
    def __init__(self, text): self.text = text
    def get(self, url): return FakeResponse(self.text)


def fixture():
    rows = {
        "ĐB": ["80249"], "1": ["92492"], "2": ["75208", "72159"],
        "3": ["44099", "14653", "62907", "73559", "33333", "72240"],
        "4": ["6004", "5337", "3507", "0688"],
        "5": ["6136", "6654", "0300", "1926", "2039", "4282"],
        "6": ["407", "708", "813"], "7": ["44", "16", "94", "99"]
    }
    return "<table class='table-result'>" + "".join(
        f"<tr><td>{name}</td><td>{''.join(values)}</td></tr>"
        for name, values in rows.items()) + "</table>"


class MBParserTests(unittest.TestCase):
    def test_prize3_5_correct_position(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = Path.cwd()
            os.chdir(tmp)
            try:
                client = LotteryMB()
                client._http = FakeHttp(fixture())
                result = client.fetch(date(2026, 10, 14))
                self.assertIsNotNone(result)
                self.assertEqual(result.prize3_3, 62907)
                self.assertEqual(result.prize3_5, 33333)
            finally:
                os.chdir(old)

    def test_incomplete_mb_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = Path.cwd()
            os.chdir(tmp)
            try:
                client = LotteryMB()
                client._http = FakeHttp("<table class='table-result'><tr><td>ĐB</td><td>12345</td></tr></table>")
                result = client.fetch(date(2026, 10, 14))
                self.assertIsNone(result)
                self.assertNotIn(date(2026, 10, 14), client._data)
            finally:
                os.chdir(old)


if __name__ == "__main__":
    unittest.main()
