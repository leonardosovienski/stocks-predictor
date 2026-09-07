"""Offline repair into a NEW SQLite copy; never updates the operational database.

Plan: {"years":[{"year":2023,"dfp_zip":"...","dfp_map":"...",
                 "fre_zip":"...","fre_map":"...","fre_basis":"optional.json"}]}
Mappings are explicit normalized-company -> ticker JSON files for that year.
No symbol inference, external downloads, signals, backtests or ledger writes.
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


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rebuild(source_db, output_db, plan):
    source_db, output_db = Path(source_db).resolve(), Path(output_db).resolve()
    if source_db == output_db or output_db.exists():
        raise ValueError("output must be a new file, distinct from the source database")
    if not source_db.is_file() or not plan.get("years"):
        raise ValueError("source database and a nonempty year plan are required")
    prepared, inputs = [], []
    for item in plan["years"]:
        year = int(item["year"])
        for kind in ("dfp", "fre"):
            if kind + "_zip" not in item:
                continue
            path, map_path = Path(item[kind + "_zip"]), Path(item[kind + "_map"])
            payload = path.read_bytes()
            mapping = json.loads(map_path.read_text(encoding="utf-8"))
            basis_path = Path(item["fre_basis"]) if kind == "fre" and item.get("fre_basis") else None
            basis = json.loads(basis_path.read_text(encoding="utf-8")) if basis_path else None
            if not isinstance(mapping, dict) or any(
                not isinstance(v, str) or not v for v in mapping.values()
            ):
                raise ValueError("each mapping must contain normalized company names and explicit tickers")
            rows = (
                cvm_pit.derive_dfp(payload, year)
                if kind == "dfp"
                else cvm_pit.derive_fre_shares(payload, year, basis)
            )
            matched = sum(r["company"] in mapping for r in rows)
            if not matched:
                raise ValueError(f"{kind}/{year}: no mapping matches; nothing is rebuilt")
            prepared.append((kind, year, payload, mapping, basis))
            inputs.append(
                {
                    "kind": kind,
                    "year": year,
                    "zip_sha256": sha256(path),
                    "mapping_sha256": sha256(map_path),
                    "derived_documents": len(rows),
                    "mapped_documents": matched,
                    "basis_sha256": sha256(basis_path) if basis_path else None,
                }
            )
    if not prepared:
        raise ValueError("plan has no CVM inputs")
    before = sha256(source_db)
    output_db.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive reservation prevents even an accidental overwrite between checks.
    with output_db.open("xb"):
        pass
    with closing(sqlite3.connect(source_db.as_uri() + "?mode=ro", uri=True)) as src:
        src.execute("PRAGMA query_only=ON")
        with closing(sqlite3.connect(output_db)) as dst:
            src.backup(dst)
    conn = db.get_connection(output_db)
    results = []
    try:
        conn.execute("BEGIN")
        for kind, year, payload, mapping, basis in prepared:
            fn = cvm_pit.ingest_dfp if kind == "dfp" else cvm_pit.ingest_fre_shares
            options = {"basis_by_document": basis} if kind == "fre" else {}
            n = fn(conn, year, ticker_of=mapping, zbytes=payload, **options)
            results.append({"kind": kind, "year": year, "inserted": n})
        conn.commit()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError(f"copy failed SQLite integrity_check: {integrity}")
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    after = sha256(source_db)
    if before != after:
        raise ValueError("source database changed during rebuild; discard this validation")
    return {
        "source_database_sha256": before,
        "source_unchanged": True,
        "output_database": str(output_db),
        "output_database_sha256": sha256(output_db),
        "inputs": inputs,
        "results": results,
        "integrity_check": integrity,
        "historical_tables_updated": False,
        "performance_observed": False,
        "proof_authorized": False,
        "limitations": [
            "Only supplied years and explicit mappings were rebuilt.",
            "FRE observations lack a verified effective share/price basis.",
            "Verified security-specific cash-event history must be supplied separately.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-db", type=Path, required=True)
    parser.add_argument("--output-db", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    result = rebuild(args.source_db, args.output_db, json.loads(args.plan.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
