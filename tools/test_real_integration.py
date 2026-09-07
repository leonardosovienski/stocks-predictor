"""Offline real-source controls; separate from the protected H17-H19 runners.

Run from a checkout with Core on PYTHONPATH. All three paths are explicit.
The destination must be new; the source is opened read-only and hash checked.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stocks_predictor import cash_events, db, document_panel, simulation, source_history, stock_events


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_rows(conn, kind):
    return [json.loads(r[0]) for r in conn.execute(
        "SELECT payload_json FROM research_source_documents WHERE kind=? ORDER BY record_id", (kind,)
    )]


def check_close(actual, expected, label):
    if not math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-7):
        raise AssertionError(f"{label}: actual={actual}, expected={expected}")


def run_control(conn, case, capital, cost, mode):
    ticker = case["ticker"]
    dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM prices_raw WHERE market_type='010' AND date BETWEEN ? AND ? ORDER BY date",
        (case["start"], case["end"]),
    )]
    bars = simulation.load_bars(conn, ticker, end=case["end"])
    if not all(d in bars for d in dates):
        raise ValueError(f"missing quote in fixed control {ticker}")
    splits = simulation.split_events(conn, ticker, case["end"])
    bonuses = stock_events.bonus_events(conn, ticker, case["end"])
    events = []
    if case["cash"]:
        cash_events.require_coverage(conn, ticker, case["start"], case["end"])
        events = [tuple(r) for r in conn.execute(
            "SELECT ex_date,payment_date,value_per_share FROM cash_events WHERE ticker=? ORDER BY ex_date,payment_date",
            (ticker,),
        )]
    result = simulation.simulate_portfolio(
        dates, {ticker: bars}, {case["start"]: {ticker: 1.0}, case["exit_signal"]: {}},
        initial_cash=capital, cost_per_side=cost, price_mode=mode,
        quantity_step=case["quantity_step"], splits={ticker: splits},
        stock_events={ticker: bonuses}, cash_events={ticker: events},
    )
    trades = result["executions"]
    assert len(trades) == 2 and trades[0]["quantity"] > 0 and trades[1]["quantity"] < 0
    assert all(e["exec_date"] > e["signal_date"] and e["cash_after"] >= 0 for e in trades)
    first, last = trades
    assert first["exec_date"] == dates[1] and last["exec_date"] == dates[-1]
    for trade in trades:
        opening, closing = bars[trade["exec_date"]]
        expected_price = closing if mode == "next_close" else opening
        if mode == "worst":
            expected_price = max(opening, closing) if trade["quantity"] > 0 else min(opening, closing)
        check_close(trade["price"], expected_price, "execution price")
    quantity = first["quantity"]
    cash_expected = capital - quantity * first["price"] * (1 + cost)
    paid, unpaid = 0.0, 0.0
    for ex in sorted({d for d in splits} | {r[0] for r in bonuses} | {r[0] for r in events}):
        if not first["exec_date"] < ex <= last["exec_date"]:
            continue
        quantity /= splits.get(ex, 1)
        # Cash entitlement on the original pre-bonus share count; these fixed
        # controls have cash and bonus on different dates, verified in source.
        for event_ex, pay, amount in events:
            if event_ex == ex:
                if pay <= dates[-1]:
                    paid += quantity * amount
                else:
                    unpaid += quantity * amount
        for event_ex, credit, ratio in bonuses:
            if event_ex == ex:
                assert credit <= last["exec_date"]
                quantity *= 1 + ratio
    check_close(-last["quantity"], quantity, "sale quantity")
    cash_expected += quantity * last["price"] * (1 - cost) + paid
    check_close(result["cash"], cash_expected, "settled cash")
    check_close(sum(r[1] for r in result["receivables"]), unpaid, "future receivables")
    check_close(result["nav"][-1], cash_expected + unpaid, "final NAV")
    assert not result["holdings"] and not result["stock_receivables"] and not result["pending_orders"]
    if case["id"] == "ENGI_BONUS_AND_CASH":
        assert result["stock_entitlements"][0][:3] == ("2025-11-28", ticker, "2025-12-02")
        assert result["stock_deliveries"][0][:2] == ("2025-12-02", ticker)
        check_close(quantity, first["quantity"] * 1.1, "bonus quantity")
    if case["quantity_step"]:
        assert all(abs(e["quantity"] / case["quantity_step"] - round(e["quantity"] / case["quantity_step"])) < 1e-9 for e in trades)
    return {
        "case": case["id"], "capital_brl": capital, "cost_per_side": cost, "price_mode": mode,
        "sessions": len(dates), "quantity_step": case["quantity_step"], "checks": "PASS",
        "executions": trades, "stock_entitlements": result["stock_entitlements"],
        "stock_deliveries": result["stock_deliveries"], "settled_cash_brl": result["cash"],
        "future_receivables_brl": unpaid, "accounting_nav_brl": result["nav"][-1],
        "accounting_residual_brl": result["nav"][-1] - cash_expected - unpaid,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-db", required=True, type=Path)
    parser.add_argument("--output-db", required=True, type=Path)
    parser.add_argument("--sources", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    for path in (args.source_db, args.sources):
        if not path.exists():
            parser.error(f"missing input: {path}")
    if args.output_db.exists() or args.report.exists():
        parser.error("output database and report must be new paths")
    protocol_path = ROOT / "docs/research/2026-09-07-real-integration-protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    before = sha(args.source_db)
    if before != protocol["source_copy_sha256"]:
        parser.error("source database differs from the registered control")
    args.output_db.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(args.source_db.resolve().as_uri() + "?mode=ro", uri=True)
    target = sqlite3.connect(args.output_db)
    source.backup(target)
    source.close()
    target.close()
    conn = db.get_connection(args.output_db)
    fixtures = ROOT / "tests/fixtures/real_integration"
    payload = (fixtures / "bonus-events.json").read_bytes()
    assert stock_events.import_bonus_events(conn, payload) == 3
    assert stock_events.import_bonus_events(conn, payload) == 0
    financials, securities = read_rows(conn, "DFP"), read_rows(conn, "FCA_SECURITY")
    metadata = []
    for year in range(2016, 2027):
        archive = (args.sources / f"fca_cia_aberta_{year}.zip").read_bytes()
        metadata.extend({"document_id": doc, **r} for doc, r in source_history.document_metadata(archive, "fca", year).items())
    dates = [r[0] for r in conn.execute("SELECT DISTINCT date FROM prices_raw WHERE market_type='010' ORDER BY date")]
    months = {}
    for day in dates:
        if day >= "2018-01-01":
            months[day[:7]] = day
    coverage = []
    for day in months.values():
        panel = document_panel.fundamentals_asof(financials, securities, day, security_metadata=metadata)
        quoted = {r[0] for r in conn.execute("SELECT DISTINCT ticker FROM prices_raw WHERE market_type='010' AND date=?", (day,))}
        usable = {t: r for t, r in panel.items() if t in quoted and r.get("accruals") is not None}
        coverage.append({"date": day, "tickers_with_accruals_and_quote": len(usable),
                         "independent_issuers": len({r["cnpj"] for r in usable.values()})})
    dfp_metadata = source_history.document_metadata((args.sources / "dfp_cia_aberta_2023.zip").read_bytes(), "dfp", 2023)
    capital_rows = []
    for doc in ("134335", "133944", "134790"):
        provenance = json.loads((fixtures / "provenance.json").read_text(encoding="utf-8"))[f"capital-{doc}.html"]
        page = (fixtures / f"capital-{doc}.html").read_bytes()
        assert hashlib.sha256(page).hexdigest() == provenance["sha256"]
        capital_rows.append(document_panel.capital_from_viewer(
            page, {"document_id": doc, **dfp_metadata[doc]}, provenance["viewer_url"]
        ))
    # Fixed matrix is registered before any NAV is calculated. No factor-ranked
    # portfolio or H17-H19 runner is called anywhere in this tool.
    controls = [run_control(conn, case, capital, cost, mode)
                for case in protocol["cases"] for capital in protocol["capitals_brl"]
                for cost in protocol["cost_per_side"] for mode in protocol["execution_modes"]]
    assert len(controls) == protocol["expected_runs"]
    conn.commit()
    assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    report = {
        "run_id": protocol["id"], "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "protocol_sha256": sha(protocol_path), "source_db_sha256": before,
        "engine_version": simulation.ENGINE_VERSION, "mechanical_status": "PASS",
        "real_scenarios_passed": len(controls), "controls": controls,
        "capital_source_observations": capital_rows, "monthly_PIT_coverage": coverage,
        "cash_coverage_tickers": [r[0] for r in conn.execute("SELECT DISTINCT ticker FROM cash_event_coverage ORDER BY ticker")],
        "trial_status": "H17_H18_H19_NOT_EXECUTED",
        "research_verdict": "INCONCLUSIVE_DATA_QUALITY",
        "open_gaps": ["Complete historical universe and lifecycle coverage", "Complete cash and noncash events outside the reconciled subset", "Intervening issuance, share-class prices and valuation bases", "Earlier statement versions absent from current bulk files", "Real execution, taxes and bonus fractional-auction proceeds"],
        "limitations": protocol["limitations"],
    }
    conn.close()
    assert sha(args.source_db) == before
    report["source_unchanged"] = True
    report["output_db_sha256"] = sha(args.output_db)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"mechanical_status": "PASS", "real_scenarios_passed": len(controls), "trial_status": report["trial_status"], "source_unchanged": True}))


if __name__ == "__main__":
    main()
