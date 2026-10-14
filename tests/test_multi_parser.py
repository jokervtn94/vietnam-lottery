"""Offline regression fixtures for regional province-draw parser."""
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from src.lotterymn import LotteryMN


class FakeResponse:
    status_code = 200
    def __init__(self, html): self.text = html


class FakeHttp:
    def __init__(self, html): self.html = html
    def get(self, url): return FakeResponse(self.html)


def fixture(missing=None):
    prizes = {"ĐB": ["500923"], "1": ["03298"], "2": ["24740"],
              "3": ["92862", "69020"],
              "4": ["34860", "19906", "79917", "67049", "99939", "49442", "24769"],
              "5": ["03457"], "6": ["01008", "02070", "08280"],
              "7": ["0944"], "8": ["13"]}
    html = "<table class='table-result'><tr><th>Giải</th><th>Vĩnh Long</th></tr>"
    for prize, numbers in prizes.items():
        if prize == missing:
            continue
        cell = "<br/>".join(f"<span>{value}</span>" for value in numbers)
        html += f"<tr><td>{prize}</td><td>{cell}</td></tr>"
    return html + "</table>"


class MultiParserTests(unittest.TestCase):
    def _run(self, html):
        with tempfile.TemporaryDirectory() as tmp:
            old = Path.cwd()
            os.chdir(tmp)
            try:
                subject = LotteryMN()
                subject._http = FakeHttp(html)
                results = subject.fetch(date(2026, 10, 14))
                return results, dict(subject._data)
            finally:
                os.chdir(old)

    def test_complete(self):
        rows, data = self._run(fixture())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].special, 500923)
        self.assertEqual(rows[0].prize8, 13)
        self.assertEqual(len(data[date(2026, 10, 14)]), 1)

    def test_missing_prize_rejected(self):
        rows, data = self._run(fixture(missing="8"))
        self.assertFalse(rows)
        self.assertEqual(data, {})

    def test_placeholder_rejected(self):
        rows, data = self._run(fixture().replace("500923", "..."))
        self.assertFalse(rows)
        self.assertEqual(data, {})


if __name__ == "__main__":
    unittest.main()
