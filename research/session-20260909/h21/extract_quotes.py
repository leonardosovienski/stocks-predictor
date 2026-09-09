"""Extract BOVA11 unchanged lines and market-session coverage, without returns."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from stocks_predictor.cotahist import parse_line


def extract(raw_dir, destination):
    if destination.exists():
        raise FileExistsError(destination)
    receipt = json.loads((raw_dir / "receipt.json").read_text(encoding="utf-8"))
    records, raw_lines, sessions, files = {}, [], set(), []
    for row in receipt["selected_files"]:
        path = raw_dir / Path(row["path"]).name
        with path.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != row["sha256"]:
                raise ValueError("Source changed")
        counts = {"records": 0, "selected": 0}
        with zipfile.ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n.upper().endswith(".TXT") and "COTAHIST" in n.upper()]
            if len(names) != 1:
                raise ValueError("Ambiguous COTAHIST source")
            with archive.open(names[0]) as stream:
                for line in stream:
                    if line[:2] != b"01":
                        continue
                    counts["records"] += 1
                    if line[24:27] != b"010" or not b"20180102" <= line[2:10] <= b"20260408":
                        continue
                    date_raw = line[2:10].decode("ascii")
                    sessions.add(f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}")
                    if line[12:24].strip() != b"BOVA11" or line[2:10] > b"20260401":
                        continue
                    raw = line.rstrip(b"\r\n")
                    if len(raw) != 245:
                        raise ValueError("Malformed selected quote width")
                    rec = parse_line(raw.decode("latin-1"))
                    rec["isin"] = raw[230:242].decode("ascii").strip()
                    rec["currency"] = raw[52:56].decode("ascii").strip()
                    if rec["date"] in records:
                        raise ValueError("Duplicate BOVA11 spot date")
                    if rec["quote_factor"] != 1 or rec["isin"] != "BRBOVACTF003" or rec["currency"] != "R$":
                        raise ValueError("Unexpected factor, identity or currency")
                    records[rec["date"]] = rec
                    raw_lines.append(raw + b"\r\n")
                    counts["selected"] += 1
        files.append({**row, **counts})
        print(path.name, counts, flush=True)
    selected_sessions = {d for d in sessions if d <= "2026-04-01"}
    missing = sorted(selected_sessions - records.keys())
    if missing:
        raise ValueError(f"BOVA11 missing market sessions: {missing}")
    if min(records) != "2018-01-02" or max(records) != "2026-04-01":
        raise ValueError("Scheduled endpoint unavailable")
    destination.mkdir(parents=True)
    payload = {"archive_sha256": receipt["archive_sha256"], "sources": files,
               "records": [records[d] for d in sorted(records)], "market_sessions": sorted(sessions),
               "missing_quote_sessions": missing, "events_certified": False,
               "coverage_note": "All spot-market sessions observed in the same annual COTAHIST files. Not an external completeness audit of B3's publication."}
    (destination / "quotes.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (destination / "BOVA11.original-lines.txt").write_bytes(b"".join(raw_lines))
    print("Coverage PASS:", len(records), "BOVA11 dates; no returns computed", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    extract(args.raw, args.destination)
