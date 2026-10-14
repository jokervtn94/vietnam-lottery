"""Descriptive historical analysis, not a lottery prediction model.

Statistics are computed from observed prize suffixes only. A frequent or
long-absent number does not have a known higher future winning probability.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REGION_FILES = {"MB": "xsmb-2-digits.csv", "MN": "xsmn-2-digits.csv", "MT": "xsmt-2-digits.csv"}


def load_two_digit_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"date": "string", "province": "string"})
    if "date" not in df.columns or df.empty:
        raise ValueError(f"Empty data or missing date: {path}")
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    number_columns = [c for c in df if c not in {"date", "province"}]
    if not number_columns:
        raise ValueError("No prize fields")
    for col in number_columns:
        df[col] = pd.to_numeric(df[col], errors="raise")
        if df[col].isna().any() or df[col].mod(1).ne(0).any() or not df[col].between(0, 99).all():
            raise ValueError(f"Invalid 2-digit column {col}")
    return df


def frequency_counts(df: pd.DataFrame) -> pd.Series:
    cols = [c for c in df if c not in ("date", "province")]
    values = pd.concat([df[c] for c in cols], ignore_index=True).astype(int)
    counts = values.value_counts().reindex(range(100), fill_value=0).sort_values(ascending=False)
    counts.index = counts.index.map(lambda n: f"{n:02d}")
    return counts


def draw_frequency(df: pd.DataFrame) -> pd.Series:
    """Number of province-draw rows containing a given pair at least once."""
    cols = [c for c in df if c not in ("date", "province")]
    result = pd.Series({f"{num:02d}": int(df[cols].eq(num).any(axis=1).sum()) for num in range(100)})
    return result.sort_values(ascending=False)


def days_since_last_seen(df: pd.DataFrame, as_of: date) -> dict[str, int | None]:
    last = df[df["date"].dt.date <= as_of]
    cols = [c for c in last if c not in ("date", "province")]
    out = {}
    for number in range(100):
        hit_dates = last.loc[last[cols].eq(number).any(axis=1), "date"]
        out[f"{number:02d}"] = (as_of - hit_dates.max().date()).days if not hit_dates.empty else None
    return out


def plot_ranking(series: pd.Series, title: str, file: Path, *, top: int = 10, xlabel: str = "Số lần xuất hiện") -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    values = series.head(top).sort_values(ascending=True)
    ax.barh(values.index.tolist(), values.values.tolist())
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    fig.tight_layout()
    fig.savefig(file, dpi=140)
    plt.close(fig)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Descriptive frequencies of observed 2-digit prize suffixes")
    p.add_argument("--data-dir", default="data")
    p.add_argument("--output-dir", default="data")
    p.add_argument("--region", choices=list(REGION_FILES))
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--as-of", type=date.fromisoformat, help="YYYY-MM-DD; default = latest observed date")
    args = p.parse_args(argv)
    if args.top <= 0:
        p.error("--top must be > 0")
    data_dir, output_dir = Path(args.data_dir), Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    reports = {}
    for region in ([args.region] if args.region else REGION_FILES):
        path = data_dir / REGION_FILES[region]
        if not path.exists():
            print(f"Missing {path}; skipping {region}")
            continue
        df = load_two_digit_data(path)
        as_of = args.as_of or df["date"].max().date()
        df = df[df["date"].dt.date <= as_of]
        if df.empty:
            print(f"No records before {as_of} for {region}")
            continue
        count = frequency_counts(df)
        presence = draw_frequency(df)
        last_seen = days_since_last_seen(df, as_of)
        overdue = pd.Series({k: v for k, v in last_seen.items() if v is not None}).sort_values(ascending=False)
        reports[region] = {"as_of": as_of.isoformat(), "draw_rows": len(df),
                           "date_min": df["date"].min().date().isoformat(),
                           "date_max": df["date"].max().date().isoformat(),
                           "top_occurrences": count.head(args.top).to_dict(),
                           "top_draws_present": presence.head(args.top).to_dict(),
                           "longest_absent": overdue.head(args.top).to_dict(),
                           "never_observed": [k for k, v in last_seen.items() if v is None],
                           "notes": "Descriptive only; historical frequency does not imply forecast advantage"}
        plot_ranking(count, f"{region}: most frequent 2-digit suffixes", output_dir / f"{region.lower()}-most-frequent.png", top=args.top)
        if not overdue.empty:
            plot_ranking(overdue, f"{region}: calendar days since last observed", output_dir / f"{region.lower()}-least-recent.png", top=args.top, xlabel="Số ngày lịch từ lần xuất hiện cuối")
    if not reports:
        print("No usable data")
        return 1
    (output_dir / "analysis-summary.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Analyzed: {', '.join(reports)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
