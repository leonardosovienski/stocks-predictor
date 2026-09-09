"""Run only preregistered H21 valuations, preserving every attempt append-only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from stocks_predictor.etf_hold import selic_reference, simulate


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("inputs", "selic", "protocol", "output", "journal"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--expected-protocol-sha256", required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if digest(args.protocol) != args.expected_protocol_sha256:
        raise ValueError("Preregistered protocol hash mismatch")
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if protocol["protocol_id"] != "H21_BOVA11_BUY_HOLD_FEASIBILITY_V1":
        raise ValueError("Wrong protocol")
    inputs = json.loads(args.inputs.read_text(encoding="utf-8"))
    if [inputs["records"][i]["date"] for i in (0, -1)] != [
            protocol["window"]["entry_on_or_after"], protocol["window"]["exit_on_or_after"]]:
        raise ValueError("Quotes do not match frozen interval")
    files = [args.inputs, args.selic, args.protocol, ROOT / "stocks_predictor/etf_hold.py", Path(__file__)]
    hashes = {str(p.resolve()): digest(p) for p in files}
    args.journal.parent.mkdir(parents=True, exist_ok=True)

    def record(event, **extra):
        with args.journal.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"at_utc": datetime.now(timezone.utc).isoformat(), "event": event,
                                     "output": str(args.output), **extra}, ensure_ascii=False) + "\n")

    record("START", input_hashes=hashes, specifications=4, capital_valuations=8,
           evidence="EXPLORATORY_CONDITIONAL_SAME_HISTORY")
    try:
        reference = selic_reference(json.loads(args.selic.read_text(encoding="utf-8")),
                                    inputs["market_sessions"], inputs["records"][0]["date"],
                                    inputs["records"][-1]["date"])
        outcomes = [simulate(inputs["records"], inputs["market_sessions"], capital=capital,
                             rate=rate, mode=mode, entry_signal=protocol["window"]["entry_decision"],
                             exit_signal=protocol["window"]["exit_decision"])
                    for capital in protocol["capital_brl"] for mode in protocol["price_modes"]
                    for rate in protocol["one_way_cost_rates"]]
        if any(digest(p) != hashes[str(p.resolve())] for p in files):
            raise ValueError("Inputs changed during measurement")
        result = {"protocol_id": protocol["protocol_id"], "input_hashes": hashes,
                  "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                  "runtime": {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
                              "scope": "stdlib auxiliary research only; not production Python 3.13 contract validation"},
                  "n_quote_dates": len(inputs["records"]), "quote_sources": inputs["sources"],
                  "evidence_state": "INCONCLUSIVE_EXECUTABLE_PROFIT_CONDITIONAL_HISTORY_MEASURED",
                  "fully_net_executable_profit_brl": None, "expected_future_profit_brl": None,
                  "gross_selic_reference": reference, "outcomes": outcomes}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
        record("COMPLETE", result_sha256=digest(args.output), observed_specifications=4,
               capital_valuations=8, independent_histories=1)
        print(json.dumps({"output": str(args.output), "sha256": digest(args.output),
                          "selic": reference, "outcomes": [{k: v for k, v in r.items() if k in {
                              "capital_brl", "mode", "one_way_cost_rate", "units", "buy_reference_brl",
                              "sell_reference_brl", "buy_cost_brl", "sale_cost_brl", "tax_obligation_brl",
                              "conditional_profit_before_unknown_expenses_brl", "max_marked_drawdown",
                              "historical_annualized_conditional_return", "historical_expense_budget_per_year_brl",
                              "largest_marked_loss_from_initial_brl"}} for r in outcomes]}, indent=2))
    except Exception as exc:
        record("FAILED", error=f"{type(exc).__name__}: {exc}")
        raise


if __name__ == "__main__":
    main()
