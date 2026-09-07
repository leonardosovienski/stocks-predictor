"""Read-only DFP provenance/unit checks; never evaluates a stock hypothesis.

The current ingestion path is compared with document-version dates and the
explicit currency scale in the CVM export. Passing these checks is NOT proof
readiness: prices, share classes, corporate actions and execution need separate
validation. The CLI opens only the supplied ZIP and writes JSON to stdout.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from stocks_predictor import ingest_cvm  # noqa: E402


def monetary_reais(value: str, scale: str, currency: str) -> Decimal:
    """CVM numeric export uses a decimal point, plus a separate scale column."""
    if currency.strip().upper() != "REAL":
        raise ValueError(f"unverified currency: {currency!r}")
    multiplier = {"MIL": Decimal(1000), "UNIDADE": Decimal(1)}.get(scale.strip().upper())
    if multiplier is None:
        raise ValueError(f"unverified monetary scale: {scale!r}")
    try:
        number = Decimal(value.strip())
    except InvalidOperation as exc:
        raise ValueError(f"invalid CVM decimal: {value!r}") from exc
    if not number.is_finite():
        raise ValueError("non-finite CVM monetary value")
    return number * multiplier


def _rows(archive: zipfile.ZipFile, name: str) -> list[list[str]]:
    with archive.open(name) as source:
        return list(csv.reader(io.TextIOWrapper(source, encoding="latin-1"), delimiter=";"))


def _digits(value: str) -> str:
    return "".join(c for c in value if c.isdigit())


def audit_dfp_zip(payload: bytes, year: int) -> dict:
    report = {
        "schema_version": 1,
        "mode": "DATA_FEASIBILITY_NO_PERFORMANCE",
        "input_sha256": hashlib.sha256(payload).hexdigest(),
        "year": year,
        "status": "AUDIT_CHECKS_PASS",
        "proof_authorized": False,
        "scope": "DFP monetary units and linkage to the received date of each version",
        "issues": [],
        "statements": {},
    }
    issues = report["issues"]
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = {Path(n).name: n for n in archive.namelist()}
        if len(names) != len(archive.namelist()):
            raise ValueError("ambiguous duplicate ZIP basenames")
        main_name = f"dfp_cia_aberta_{year}.csv"
        if main_name not in names:
            raise ValueError("DFP main document index missing")
        raw_main = _rows(archive, names[main_name])
        if not raw_main:
            raise ValueError("DFP main document index empty")
        required = {"CNPJ_CIA", "DT_REFER", "VERSAO", "DT_RECEB"}
        if not required.issubset(raw_main[0]):
            raise ValueError(f"DFP main missing columns: {sorted(required - set(raw_main[0]))}")
        version_dates = defaultdict(set)
        for values in raw_main[1:]:
            r = dict(zip(raw_main[0], values))
            if required.issubset(r) and r["DT_RECEB"]:
                date.fromisoformat(r["DT_REFER"])
                date.fromisoformat(r["DT_RECEB"][:10])
                version_dates[(_digits(r["CNPJ_CIA"]), r["DT_REFER"], r["VERSAO"])].add(r["DT_RECEB"][:10])
        assigned_dates = ingest_cvm.parse_dfp_received_dates(payload, year)
        version_mismatches = set()
        unit_count = 0
        for statement in ("BPA_con", "BPP_con", "DRE_con", "DFC_MI_con"):
            name = f"dfp_cia_aberta_{statement}_{year}.csv"
            if name not in names:
                issues.append({"code": "STATEMENT_NOT_AUDITED", "statement": statement})
                continue
            raw = _rows(archive, names[name])
            required_statement = {"CNPJ_CIA", "DT_REFER", "VERSAO", "MOEDA", "ESCALA_MOEDA", "ORDEM_EXERC", "VL_CONTA"}
            if not raw or not required_statement.issubset(raw[0]):
                raise ValueError(f"{statement}: version/unit metadata missing")
            rows = [dict(zip(raw[0], r)) for r in raw[1:] if len(r) == len(raw[0])]
            rows = [r for r in rows if ingest_cvm._norm(r["ORDEM_EXERC"]) == "ultimo" and r["VL_CONTA"].strip()]
            parsed = ingest_cvm.parse_dfp_statement_rows(raw, statement)
            if len(rows) != len(parsed):
                raise ValueError(f"{statement}: cannot align source and parsed observations")
            detail = {"rows": len(rows), "scales": dict(Counter(r["ESCALA_MOEDA"] for r in rows)),
                      "unit_mismatches": 0, "date_mismatches": 0, "unresolved_versions": 0,
                      "unit_examples": [], "date_examples": []}
            for r, actual in zip(rows, parsed):
                expected = monetary_reais(r["VL_CONTA"], r["ESCALA_MOEDA"], r["MOEDA"])
                observed = Decimal(str(actual["value"]))
                tolerance = max(Decimal("0.000001"), abs(expected) * Decimal("1e-12"))
                if abs(observed - expected) > tolerance:
                    detail["unit_mismatches"] += 1
                    unit_count += 1
                    if len(detail["unit_examples"]) < 3:
                        detail["unit_examples"].append({"company": r.get("DENOM_CIA"), "account": r.get("CD_CONTA"),
                            "raw_value": r["VL_CONTA"], "scale": r["ESCALA_MOEDA"],
                            "expected_reais": str(expected), "parsed_value": str(observed)})
                key = (_digits(r["CNPJ_CIA"]), r["DT_REFER"], r["VERSAO"])
                dates = version_dates.get(key, set())
                if len(dates) != 1:
                    detail["unresolved_versions"] += 1
                    continue
                matching_date = next(iter(dates))
                assigned = assigned_dates.get(key[:2])
                if assigned != matching_date:
                    detail["date_mismatches"] += 1
                    version_mismatches.add(key[:2])
                    if len(detail["date_examples"]) < 3:
                        detail["date_examples"].append({"company": r.get("DENOM_CIA"), "cnpj": key[0],
                            "reference": key[1], "version": key[2], "assigned_known_at": assigned,
                            "version_received_at": matching_date})
            report["statements"][statement] = detail
            if detail["unresolved_versions"]:
                issues.append({"code": "UNRESOLVED_VERSION", "statement": statement,
                               "rows": detail["unresolved_versions"]})
        if unit_count:
            issues.append({"code": "MONETARY_UNIT_MISMATCH", "rows": unit_count})
        if version_mismatches:
            issues.append({"code": "VERSION_DATE_MISMATCH", "company_periods": len(version_mismatches)})
        if not report["statements"]:
            issues.append({"code": "NO_STATEMENT_EVIDENCE"})
    if issues:
        report["status"] = "NOT_READY"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    try:
        report = audit_dfp_zip(args.zip.read_bytes(), args.year)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        report = {"status": "AUDIT_ERROR", "proof_authorized": False, "error": str(exc)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "AUDIT_CHECKS_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
