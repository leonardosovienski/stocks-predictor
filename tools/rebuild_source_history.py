"""Rebuild issuer history in an exclusive NEW database copy, offline.

All four CVM derivations are audit observations, isolated from factor inputs.
The current archives do not promise every superseded filing version. No name
or current ticker is projected backward, and no performance is calculated.
"""

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stocks_predictor"))
import cvm_pit  # noqa: E402
import db  # noqa: E402
import source_history  # noqa: E402


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stage_records(conn, kind, year, rows):
    count = 0
    for row in rows:
        payload = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        identity = hashlib.sha256((kind + "\n" + payload).encode("utf-8")).hexdigest()
        n = conn.execute(
            "INSERT OR IGNORE INTO research_source_documents"
            "(record_id,kind,archive_year,cnpj,document_id,available_at,source_sha256,payload_json)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (
                identity,
                kind,
                year,
                row.get("cnpj"),
                row.get("document_id"),
                row.get("available_at"),
                row["source_sha256"],
                payload,
            ),
        ).rowcount
        count += n
    return count


def rebuild(source_db, output_db, source_dir, years, export_dir):
    source_db, output_db = Path(source_db).resolve(), Path(output_db).resolve()
    source_dir, export_dir = Path(source_dir), Path(export_dir)
    if not source_db.is_file() or output_db.exists() or output_db == source_db:
        raise ValueError("require an existing source and an exclusive NEW output database")
    if not years:
        raise ValueError("nonempty years required")
    inputs = [
        source_dir / f"{kind}_cia_aberta_{year}.zip" for year in years for kind in ("dfp", "fre", "fca")
    ]
    if not all(p.is_file() for p in inputs):
        raise ValueError("all raw CVM inputs must already exist")
    before = sha256(source_db)
    output_db.parent.mkdir(parents=True, exist_ok=True)
    with output_db.open("xb"):
        pass
    with closing(sqlite3.connect(source_db.as_uri() + "?mode=ro", uri=True)) as src:
        src.execute("PRAGMA query_only=ON")
        with closing(sqlite3.connect(output_db)) as dst:
            src.backup(dst)
    export_dir.mkdir(parents=True, exist_ok=True)
    conn = db.get_connection(output_db)
    results = []
    try:
        conn.execute("BEGIN")
        for year in years:
            issues = []
            dfp = (source_dir / f"dfp_cia_aberta_{year}.zip").read_bytes()
            fre = (source_dir / f"fre_cia_aberta_{year}.zip").read_bytes()
            fca = (source_dir / f"fca_cia_aberta_{year}.zip").read_bytes()
            metadata = source_history.document_metadata(fre, "fre", year)
            shares = cvm_pit.derive_fre_shares(fre, year, issues=issues)
            for row in shares:
                row["cnpj"] = metadata[row["document_id"]]["cnpj"]
                row["count_method"] = "free_float_percentage_estimate"
                row["eligible_for_valuation"] = False
            groups = {
                "DFP": cvm_pit.derive_dfp(dfp, year, issues=issues),
                "FRE_FLOAT_ESTIMATE": shares,
                "FCA_SECURITY": source_history.derive_fca_securities(fca, year, issues=issues),
                "FRE_ISSUED_CAPITAL": source_history.derive_reported_capital(fre, year, issues=issues),
            }
            counts = {}
            for kind, rows in groups.items():
                counts[kind] = stage_records(conn, kind, year, rows)
                path = export_dir / f"{kind.lower()}_{year}.jsonl"
                path.write_text(
                    "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows),
                    encoding="utf-8",
                )
            result = {"year": year, "counts": counts, "issues": issues}
            results.append(result)
            print(json.dumps({"year": year, "counts": counts, "issues": len(issues)}), flush=True)
        conn.commit()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError(f"SQLite integrity failure: {integrity}")
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    if sha256(source_db) != before:
        raise ValueError("source changed during rebuild; validation invalid")
    return {
        "source_sha256": before,
        "source_unchanged": True,
        "output_sha256": sha256(output_db),
        "integrity_check": integrity,
        "years": results,
        "inputs": [{"file": p.name, "sha256": sha256(p)} for p in inputs],
        "signal_tables_populated": False,
        "performance_observed": False,
        "all_superseded_versions_recovered": False,
        "share_bases_certified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source-db", "output-db", "source-dir", "export-dir", "report"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--first-year", type=int, default=2016)
    parser.add_argument("--last-year", type=int, default=2026)
    args = parser.parse_args()
    result = rebuild(
        args.source_db,
        args.output_db,
        args.source_dir,
        range(args.first_year, args.last_year + 1),
        args.export_dir,
    )
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
