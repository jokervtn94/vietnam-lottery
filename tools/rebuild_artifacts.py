"""Rebuild derived Parquet files from tracked CSV snapshots.

Only generated binary exports are written. Never changes CSV/JSON lottery values.
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd


def main():
    data = Path("data")
    output = []
    for region in ("mb", "mn", "mt"):
        for kind in ("", "-2-digits", "-sparse"):
            csv_path = data / f"xs{region}{kind}.csv"
            if not csv_path.is_file():
                raise FileNotFoundError(csv_path)
            frame = pd.read_csv(csv_path, dtype={"date": "string", "province": "string"})
            if frame.empty or "date" not in frame:
                raise ValueError(f"Missing or empty date values in {csv_path}")
            frame["date"] = pd.to_datetime(frame["date"], errors="raise")
            dest = csv_path.with_suffix(".parquet")
            frame.to_parquet(dest, index=False)
            output.append(str(dest))
    print("Rebuilt derived Parquet exports:", *output, sep="\n - ")


if __name__ == "__main__":
    main()
