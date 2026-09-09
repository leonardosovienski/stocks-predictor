"""Separate integer-cent accounting from unchanged COTAHIST lines, no engine import."""
import argparse
import hashlib
import json
from pathlib import Path


def verify(result_file, lines_file):
    result = json.loads(result_file.read_text(encoding="utf-8"))
    lines = {line[2:10].decode("ascii"): line for line in lines_file.read_bytes().splitlines()}
    checks = []
    for row in result["outcomes"]:
        first = lines[row["entry"].replace("-", "")]
        last = lines[row["exit"].replace("-", "")]
        # Independent parsing in integer quote cents, not the reusable parser.
        buy, sell = int(first[56:69]), int(last[56:69])
        if row["mode"] == "worst_open_close":
            buy = max(buy, int(first[108:121]))
            sell = min(sell, int(last[108:121]))
        capital = round(row["capital_brl"] * 100)
        bps = round(row["one_way_cost_rate"] * 10000)

        def fee(n):
            return (n * bps + 5000) // 10000

        qty = 0
        while (qty + 10) * buy + fee((qty + 10) * buy) <= capital:
            qty += 10
        basis = qty * buy + fee(qty * buy)
        proceeds = qty * sell - fee(qty * sell)
        taxable = proceeds - basis
        tax = (max(0, taxable) * 15 + 50) // 100
        profit = taxable - tax
        expected = {"units": qty, "tax_basis_brl": basis / 100,
                    "residual_cash_brl": (capital - basis) / 100,
                    "sale_receivable_brl": proceeds / 100, "tax_obligation_brl": tax / 100,
                    "conditional_profit_before_unknown_expenses_brl": profit / 100,
                    "end_equity_after_tax_reserve_brl": (capital + profit) / 100}
        for key, value in expected.items():
            if row[key] != value:
                raise AssertionError((key, row[key], value))
        peak = capital
        worst = 0
        previous = capital
        yearly = {}
        for point in row["equity_curve"]:
            raw = lines[point["date"].replace("-", "")]
            equity = capital + profit if point["date"] == row["exit"] else capital - basis + qty * int(raw[108:121])
            if abs(equity / 100 - point["equity_brl"]) > 0.0000001:
                raise AssertionError("Daily wealth discrepancy")
            peak = max(peak, equity)
            worst = max(worst, (peak - equity) / peak)
            year = point["date"][:4]
            yearly[year] = yearly.get(year, 0) + equity - previous
            previous = equity
        if abs(worst - row["max_marked_drawdown"]) > 1e-12:
            raise AssertionError("Drawdown discrepancy")
        if {year: amount / 100 for year, amount in yearly.items()} != row["calendar_year_pnl_brl"]:
            raise AssertionError("Annual attribution discrepancy")
        if sum(yearly.values()) != profit:
            raise AssertionError("P&L reconciliation")
        checks.append({"capital": row["capital_brl"], "mode": row["mode"], "bps": bps,
                       "profit_brl": profit / 100, "daily_points_verified": len(row["equity_curve"])})
    return {"status": "PASS", "method": "Independent integer-cent implementation by the same agent, not external review",
            "result_sha256": hashlib.sha256(result_file.read_bytes()).hexdigest(),
            "original_lines_sha256": hashlib.sha256(lines_file.read_bytes()).hexdigest(), "checks": checks}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("original_lines", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    answer = verify(args.result, args.original_lines)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(answer, stream, indent=2)
        stream.write("\n")
    print(json.dumps(answer, indent=2))
