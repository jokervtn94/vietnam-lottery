"""A province model failure must not save a partial draw for that date."""
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from src.lotterymn import LotteryMN

PRIZES = {"ĐB": [500923], "1": [3298], "2": [24740], "3": [92862, 69020],
          "4": [34860, 19906, 79917, 67049, 99939, 49442, 24769],
          "5": [3457], "6": [1008, 2070, 8280], "7": [944], "8": [13]}

def make_html():
    html = "<table class='table-result'><tr><th>Giải</th><th>Vĩnh Long</th><th>Cần Thơ</th></tr>"
    for label, values in PRIZES.items():
        rendered = " ".join(str(v) for v in values)
        html += f"<tr><td>{label}</td><td>{rendered}</td><td>{rendered}</td></tr>"
    return html + "</table>"

class FakeReply:
    status_code = 200
    text = make_html()

class FakeClient:
    def get(self, url): return FakeReply()

class AtomicProvinceTests(unittest.TestCase):
    def test_both_provinces_required(self):
        with tempfile.TemporaryDirectory() as temp:
            old = Path.cwd()
            try:
                os.chdir(temp)
                instance = LotteryMN()
                instance._http = FakeClient()
                original = instance._create_result_model
                def create(selected_date, province, prizes):
                    if province == "Cần Thơ":
                        raise ValueError("simulated failed province validation")
                    return original(selected_date, province, prizes)
                instance._create_result_model = create
                outcome = instance.fetch(date(2026, 10, 14))
                self.assertEqual(outcome, [])
                self.assertNotIn(date(2026, 10, 14), instance._data)
            finally:
                os.chdir(old)

if __name__ == "__main__":
    unittest.main()
