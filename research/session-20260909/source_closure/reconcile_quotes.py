"""Reconcile the new 2026 B3 source, without any economic valuation."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import zipfile

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from stocks_predictor.cotahist import parse_line

def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def run(raw, previous, calendar_path, destination):
    if destination.exists():
        raise FileExistsError(destination)
    receipt = json.loads(raw.with_name(raw.name + ".source.json").read_text(encoding="utf-8"))
    if digest(raw) != receipt["sha256"]:
        raise ValueError("Source hash differs from captured bytes")
    if digest(previous / "quotes.json") != "445a24c3098deb3da6f3bdd7b3d92ca48e24e6b4f9fdc38fb52b7705c2467d94":
        raise ValueError("Original H21 quotes changed")
    if digest(previous / "BOVA11.original-lines.txt") != "95a0f8c69954911c7c8e332af846b830989ccbe3d2f7e6ed1bdff014213e6eb3":
        raise ValueError("Original H21 lines changed")
    calendar = json.loads(calendar_path.read_text(encoding="utf-8"))
    if digest(Path(calendar["source_path"])) != calendar["source_sha256"]:
        raise ValueError("Calendar source changed")
    first, last = dt.date(2026, 1, 2), dt.date(2026, 9, 8)
    expected = set()
    day = first
    while day <= last:
        if day.weekday() < 5 and day.isoformat() not in calendar["closed_equity_dates"]:
            expected.add(day.isoformat())
        day += dt.timedelta(days=1)
    records, original_lines, sessions = {}, {}, set()
    scanned = 0
    with zipfile.ZipFile(raw) as archive:
        names = [n for n in archive.namelist() if n.upper().endswith(".TXT") and "COTAHIST" in n.upper()]
        if len(names) != 1:
            raise ValueError("Ambiguous archive")
        with archive.open(names[0]) as stream:
            for line in stream:
                if line[:2] != b"01":
                    continue
                scanned += 1
                if line[24:27] != b"010" or not b"20260102" <= line[2:10] <= b"20260908":
                    continue
                day = dt.datetime.strptime(line[2:10].decode("ascii"), "%Y%m%d").date().isoformat()
                sessions.add(day)
                if line[12:24].strip() != b"BOVA11":
                    continue
                rawline = line.rstrip(b"\r\n")
                if len(rawline) != 245:
                    raise ValueError("Selected quote width")
                rec = parse_line(rawline.decode("latin-1"))
                rec["isin"] = rawline[230:242].decode("ascii").strip()
                rec["currency"] = rawline[52:56].decode("ascii").strip()
                if rec["date"] in records:
                    raise ValueError("Duplicate BOVA11 date")
                if (rec["isin"], rec["currency"], rec["quote_factor"]) != ("BRBOVACTF003", "R$", 1):
                    raise ValueError("Identity/currency/factor")
                if not 0 < rec["low"] <= min(rec["open"], rec["close"]) <= max(rec["open"], rec["close"]) <= rec["high"]:
                    raise ValueError("OHLC ordering")
                if rec["qty"] <= 0 or rec["volume_fin"] <= 0:
                    raise ValueError("Nonpositive trading volume")
                records[day], original_lines[day] = rec, rawline + b"\r\n"
        # Reading the complete member checks its CRC in ZipExtFile.
        member_crc = archive.getinfo(names[0]).CRC
    prior = json.loads((previous / "quotes.json").read_text(encoding="utf-8"))["records"]
    old = {r["date"]: r for r in prior}
    oldlines = {f"{line[2:6].decode()}-{line[6:8].decode()}-{line[8:10].decode()}": line.rstrip(b"\r\n") + b"\r\n"
                for line in (previous / "BOVA11.original-lines.txt").read_bytes().splitlines(keepends=True)}
    overlap = sorted(records.keys() & old.keys())
    revised = [d for d in overlap if records[d] != old[d]]
    revised_lines = [d for d in overlap if original_lines[d] != oldlines[d]]
    missing, unexpected = sorted(expected - records.keys()), sorted(records.keys() - expected)
    if not records or missing or unexpected or set(records) != sessions:
        raise ValueError(f"Calendar coverage mismatch: {missing=}, {unexpected=}")
    if len(overlap) != len([d for d in old if d >= first.isoformat()]):
        raise ValueError("Incomplete old overlap")
    destination.mkdir(parents=True)
    payload = {
        "kind": "SOURCE_VALIDATION_NO_RETURNS",
        "cutoff": last.isoformat(), "source_sha256": receipt["sha256"],
        "calendar_sha256": digest(calendar_path),
        "calendar_validation_scope": [first.isoformat(), last.isoformat()],
        "acquired_after_cutoff": True,
        "known_at_policy": "Source acquired 2026-09-09; never a point-in-time trading signal",
        "records": [records[d] for d in sorted(records)],
        "events_certified": False,
    }
    (destination / "quotes-2026.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (destination / "BOVA11-2026.original-lines.txt").write_bytes(b"".join(original_lines[d] for d in sorted(original_lines)))
    merged = {**old, **records}
    # The newer source is isolated even if revised; the frozen book is never changed.
    combined = dict(payload, records=[merged[d] for d in sorted(merged)],
                    source_policy="Original preserved H21 quotes before 2026; new B3 capture in 2026",
                    original_quotes_sha256=digest(previous / "quotes.json"),
                    original_lines_sha256=digest(previous / "BOVA11.original-lines.txt"),
                    earlier_calendar_revalidated=False)
    (destination / "quotes-2018-20260908.json").write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")
    result = {
        "source_records_scanned": scanned, "zip_member_crc": member_crc,
        "zip_member_crc_checked_by_full_read": True,
        "selected_2026": len(records), "first": min(records), "last": max(records),
        "combined_count": len(merged), "added_since_original": len(records.keys() - old.keys()),
        "overlap_count": len(overlap), "revised_parsed_dates": revised,
        "revised_original_line_dates": revised_lines,
        "missing_calendar_dates": missing, "unexpected_calendar_dates": unexpected,
        "market_sessions_match": set(records) == sessions,
        "calendar_scope": "Official published 2026 calendar plus source-observed trading days",
        "economic_valuations": 0, "original_book_changed": False, "events_certified": False,
        "files": {p.name: {"bytes": p.stat().st_size, "sha256": digest(p)} for p in destination.iterdir()},
    }
    (destination / "reconciliation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result), flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("raw", "previous", "calendar", "destination"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    run(args.raw, args.previous, args.calendar, args.destination)
