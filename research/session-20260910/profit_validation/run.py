"""Execute exactly the R5 registered matrix, preserving every attempt."""
import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from stocks_predictor.monthly_etf import Costs, simulate
from verify import verify


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    work = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    if not work.is_relative_to(Path("C:/STOCKS").resolve()) or not output.is_relative_to(work):
        raise ValueError("Output outside declared work root")
    if output.exists():
        raise FileExistsError(output)
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).strip():
        raise ValueError("Commit code before observing new outcomes")
    path = ROOT / "docs/research/2026-09-10-profit-validation-r5-protocol.json"
    registered = subprocess.check_output(["git", "show", "1d2b625:" + path.relative_to(ROOT).as_posix()], cwd=ROOT)
    if registered != path.read_bytes():
        raise ValueError("Protocol bytes changed since registration")
    protocol = json.loads(registered)
    receipt = json.loads((ROOT / "docs/research/2026-09-10-r5/inputs-receipt.json").read_text(encoding="utf-8"))
    if sha(work / "inputs.json") != receipt["input_sha256"]:
        raise ValueError("Prepared input identity mismatch")
    inputs = json.loads((work / "inputs.json").read_text(encoding="utf-8"))
    identity = {"started_at": datetime.now(timezone.utc).isoformat(), "protocol_sha256": sha(path),
                "inputs_sha256": sha(work / "inputs.json"), "python": platform.python_version(),
                "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}
    # x mode creates the attempt record before the first economic calculation.
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps({"kind": "START", **identity}) + "\n")
        stream.flush()
        windows = [protocol["windows"]["full"], *protocol["windows"]["fixed_temporal_diagnostics"]]
        for start, end in windows:
            for spec in protocol["specifications"]:
                costs = Costs(Decimal(str(spec["one_way_variable_cost"])),
                              Decimal(str(spec["fixed_cost_per_order_brl"])),
                              Decimal(str(spec["monthly_expense_brl"])), spec["price_mode"])
                for capital in protocol["capital_brl_scenarios"]:
                    for arm in ["trend", "hold"]:
                        row = {"kind": "VALUATION", "start": start, "end": end,
                               "specification": spec["id"], "capital": capital, "arm": arm}
                        try:
                            result = simulate(inputs["records"], inputs["calendar"], start=start,
                                              end=end, capital=capital, costs=costs, arm=arm)
                            row["result"] = result
                            row["verification"] = verify(result, inputs, spec)
                        except Exception as exc:
                            row["error"] = f"{type(exc).__name__}: {exc}"
                        stream.write(json.dumps(row) + "\n")
                        stream.flush()
                        print(json.dumps({**{k: v for k, v in row.items() if k != "result"},
                            "summary": {k: v for k, v in row.get("result", {}).items()
                                        if k not in {"curve", "ledger", "tax_ledger", "year_profit"}}}), flush=True)
        stream.write(json.dumps({"kind": "END", "ended_at": datetime.now(timezone.utc).isoformat()}) + "\n")


if __name__ == "__main__":
    main()
