"""Incremental XSMB/XSMN/XSMT collection with safe re-fetch support.

Run from repository root: python -m src.fetch [--region MB|MN|MT].
Original JSON remains the source of truth for known days. --force re-fetches
only explicitly selected dates and restores old values on fetch failure.
"""
from __future__ import annotations

import argparse
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .lotterymb import LotteryMB
from .lotterymn import LotteryMN
from .lotterymt import LotteryMT

logger = logging.getLogger("vietnam-lottery")
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
REGION_CLASSES = {"MB": LotteryMB, "MN": LotteryMN, "MT": LotteryMT}


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Date must be YYYY-MM-DD") from exc


def choose_dates(existing_dates, today: date, start: date | None, end: date | None,
                 repair_gaps: bool = False) -> list[date]:
    """Plan independently for each region, never based on another region's CSV."""
    end = end or today
    known = set(existing_dates)
    if start is None:
        if repair_gaps:
            raise ValueError("--repair-gaps requires explicit --start")
        start = (max(known) + timedelta(days=1)) if known else end - timedelta(days=6)
    if start > end:
        return []
    requested = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    return [d for d in requested if d not in known] if repair_gaps else requested


def fetch_region(region: str, *, start: date | None, end: date | None,
                 force: bool, repair_gaps: bool) -> tuple[int, int, int]:
    lottery = REGION_CLASSES[region]()
    lottery.load()
    now_vn = datetime.now(VN_TZ).date()
    requested = choose_dates(lottery._data.keys(), now_vn, start, end, repair_gaps)
    new_records, skipped, failed = 0, 0, 0
    logger.info("%s: checking %d days", region, len(requested))

    for day in requested:
        was_known = day in lottery._data
        if was_known and not force:
            skipped += 1
            continue
        old_result = lottery._data.pop(day, None) if force and was_known else None
        try:
            outcome = lottery.fetch(day)
            if not outcome:
                raise ValueError("empty result")
            new_records += 1
        except Exception as exc:
            if old_result is not None:
                lottery._data[day] = old_result
            failed += 1
            logger.warning("%s %s: no valid draw data (%s)", region, day, exc)

    if new_records:
        lottery.generate_dataframes()
        lottery.dump()
        lottery.generate_and_dump_sparse_json()
    logger.info("%s: updated=%d unchanged=%d failed=%d", region, new_records, skipped, failed)
    return new_records, skipped, failed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Fetch Vietnam Lottery historical results")
    parser.add_argument("--start", type=parse_date, help="inclusive YYYY-MM-DD")
    parser.add_argument("--end", type=parse_date, help="inclusive YYYY-MM-DD")
    parser.add_argument("--region", choices=REGION_CLASSES)
    parser.add_argument("--force", action="store_true", help="replace existing results on successful re-fetch")
    parser.add_argument("--repair-gaps", action="store_true", help="only fetch dates absent from stored data; requires --start")
    parser.add_argument("--allow-empty", action="store_true", help="for known no-draw holidays; logs unresolved dates")
    args = parser.parse_args(argv)
    if args.start and args.end and args.start > args.end:
        parser.error("--start cannot be after --end")
    if args.repair_gaps and not args.start:
        parser.error("--repair-gaps requires --start")
    if args.force and (not args.start or not args.end):
        parser.error("--force requires explicit --start and --end to bound re-fetch dates")
    if args.force and args.repair_gaps:
        parser.error("--force and --repair-gaps cannot be combined")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    regions = [args.region] if args.region else list(REGION_CLASSES)
    failures = 0
    for region in regions:
        try:
            _, _, failed = fetch_region(region, start=args.start, end=args.end,
                                        force=args.force, repair_gaps=args.repair_gaps)
            failures += failed
        except Exception:
            logger.exception("Fatal error while fetching %s", region)
            failures += 1
    if failures:
        logger.warning("Unresolved draw dates: %d", failures)
    return 0 if args.allow_empty or failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
