"""Reconcile every target quote to original ZIP bytes; no economic outputs."""
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from stocks_predictor.cotahist import parse_line
from stocks_predictor.monthly_etf import validate_prices


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    work = Path(sys.argv[1]).resolve()
    if not work.is_relative_to(Path("C:/STOCKS").resolve()):
        raise ValueError("Output outside project root")
    output = work / "inputs.json"
    if output.exists():
        raise FileExistsError(output)
    quotes_path = Path("C:/STOCKS/work/h21-source-closure-20260909/normalized-v2/quotes-2018-20260908.json")
    previous = json.loads(quotes_path.read_text(encoding="utf-8"))["records"]
    records = {}
    calendar = set()
    sources = []
    for year in range(2017, 2027):
        path = (work / "raw/COTAHIST_A2017.ZIP" if year == 2017 else
                Path("C:/STOCKS/work/h21-source-closure-20260909/raw/COTAHIST_A2026.complete.ZIP")
                if year == 2026 else Path(f"C:/STOCKS/work/h21/raw/COTAHIST_A{year}.ZIP"))
        sessions = set()
        found = 0
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if len(names) != 1:
                raise ValueError("Unexpected archive members")
            with archive.open(names[0]) as stream:
                for line in stream:
                    if line[:2] != b"01" or line[24:27] != b"010":
                        continue
                    raw_day = line[2:10].decode("ascii")
                    day = date.fromisoformat(f"{raw_day[:4]}-{raw_day[4:6]}-{raw_day[6:]}").isoformat()
                    if not day.startswith(str(year)):
                        raise ValueError("Archive year mismatch")
                    if day > "2026-09-08":
                        continue
                    sessions.add(day)
                    if line[12:24].strip() != b"BOVA11":
                        continue
                    r = parse_line(line.decode("latin-1"))
                    r["isin"] = line[230:242].decode("ascii").strip()
                    r["currency"] = line[52:56].decode("ascii").strip()
                    if day in records:
                        raise ValueError("Duplicate target quote")
                    records[day] = r
                    found += 1
        calendar.update(sessions)
        source = {"year": year, "path": str(path), "sha256": digest(path),
                  "spot_sessions": len(sessions), "bova_records": found,
                  "url": f"https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{year}.ZIP"}
        sources.append(source)
        print(json.dumps(source), flush=True)
    actual = [records[d] for d in sorted(records) if d >= "2018-01-01"]
    if actual != previous:
        raise ValueError("Previously normalized quotes differ from raw archives")
    cal_path = Path("C:/STOCKS/work/h21-source-closure-20260909/calendar-2026.json")
    closures = set(json.loads(cal_path.read_text(encoding="utf-8"))["closed_equity_dates"])
    d = date(2026, 1, 1)
    expected = set()
    while d.year == 2026:
        if d.weekday() < 5 and d.isoformat() not in closures:
            expected.add(d.isoformat())
        d += timedelta(days=1)
    if {d for d in calendar if d.startswith("2026")} != {d for d in expected if d <= "2026-09-08"}:
        raise ValueError("2026 official calendar discrepancy")
    calendar.update(expected)
    ordered = [records[d] for d in sorted(records)]
    validate_prices(ordered, sorted(calendar))
    output.write_text(json.dumps({"records": ordered, "calendar": sorted(calendar), "sources": sources,
        "prior_quotes_sha256": digest(quotes_path), "calendar_2026_sha256": digest(cal_path),
        "coverage": "2017-2025 all spot dates observed in original annual archives; 2026 official calendar checked. Earlier full closure calendars not independently recovered.",
        "events_certified": False, "costs_certified": False}, indent=2), encoding="utf-8")
    print(json.dumps({"input_sha256": digest(output), "records": len(ordered), "calendar": len(calendar)}))


if __name__ == "__main__":
    main()
