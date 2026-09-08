"""Register a bounded H20 historical comparison before joining signals to returns."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(r"C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907")
REPO = ROOT / "work/stocks-predictor"

def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

inputs = {
    "h20_signals": "work/h20-implementation-20260908/observation-02.json",
    "audited_marks": "work/profit-validation-ready-7b3722cd2bf1/results/VALIDACAO_LUCRO_STOCKS.json",
    "audited_package_manifest": "work/profit-validation-ready-7b3722cd2bf1/validation-manifest.json",
    "identity_observation": "work/profit-validation-ready-7b3722cd2bf1/baseline/observations/h18-h19-reorganization-observation.json",
    "execution_manifest": "work/stocks-final-review-bundle/inputs/SHA256.json",
    "h20_protocol": "work/stocks-predictor/docs/research/2026-09-08-h20-implementation-protocol.json",
}
protocol = {
    "protocol_id": "H20_FIXED_SELECTION_RETURN_DIAGNOSTIC_1",
    "registered_at_utc": datetime.now(timezone.utc).isoformat(),
    "request": "Testar o projeto e verificar se melhorou a projeção de lucro.",
    "runtime_before_comparison": "f84f7fa",
    "inputs": {k: {"path": v, "sha256": digest(ROOT / v)} for k, v in inputs.items()},
    "hypothesis": "The frozen H20 value/profitability selection and retention membership may improve historical marked outcomes relative to value alone. This does not presume improved executable net profit.",
    "arms": ["VALUE_COMMON_UNIVERSE", "VALUE_PROFITABILITY", "VALUE_PROFITABILITY_BUFFER"],
    "selection": "Reuse exact archived H20 memberships, rankings, dates and ISINs without reselection or parameter changes. BUFFER here is the previously intended membership sequence, not the actual continuous execution of retention and weight bands.",
    "schedule": "All 32 quarterly signals March 2018 to December 2025 remain in output. The pre-existing first date has insufficient feature coverage. Each eligible signal buys next-session open/close and marks at next quarter's execution endpoint. All 31 existing quarterly H19 mark periods are used if every needed identity is priced, ending 2026-04-01. Endpoints were inspected as metadata before registration, not selected by return.",
    "paired_universe": "The full eligible H20 ranking must be identical across arms. Join by signal, ticker, CNPJ and archived ISIN; check audit member against frozen original observation. Compare equally weighted selected names and equally weighted common universe at identical dates. Original frozen H19 selection is a contextual reference on the same dates, with its different universe disclosed.",
    "measurement": "Reuse previously independently audited per-share marks including source-reviewed splits, successor stock entitlements and compulsory cash at face value. These omit ordinary dividends/JCP and delivery/tax frictions and are NOT total returns, executable P&L or a forecast. Reference source marks are already historically exposed.",
    "missing_policy": "Missing identities, missing prices, failed_entry or nonfinite returns remain explicit null/block reasons. Never treat a failed entry as zero or silently shrink the common universe. A period requires all common names and selected names. Summaries are conditional if periods are blocked. Never compound across a missing interval; if the eligible range has a gap, cumulative/annualized results stay null.",
    "price_modes": ["open", "close", "worst"],
    "one_way_cost_rates": [0.0018, 0.0036],
    "cost_model": "For every arm and benchmark equally, cost-adjusted quarter mark = (1 + mark_return) * (1-c)/(1+c) - 1. This is hypothetical full rotation each quarter, NOT actual turnover or savings. No estimated retention cost benefit is inserted. C is the prior assumed one-side fee/slippage rate, not a newly verified current market tariff.",
    "capital_brl": [5000, 10000],
    "capital_interpretation": "Amounts are synthetic wealth equivalents of full reinvestment of marks, no cash lag, no integer/fractional fills, taxes, ordinary income or upkeep. Financial projection and executable_profit fields remain null. Do not present these amounts as profit or extrapolate to a future year.",
    "metrics": ["paired mean quarter returns and differences", "geometric annualized mark change", "synthetic wealth equivalents", "quarter-end-only drawdown", "positive paired quarters", "fixed first15/last16 quarters", "all calendar years", "source and execution evidence coverage"],
    "uncertainty": "Paired stationary block bootstrap of quarter differences, expected block length4, 10000 draws, fixed seed20260908. Descriptive 95% interval unadjusted for prior adaptive search; no Proof or independent holdout. Same resampling draws for every comparison. Report all three modes and both costs, not just a favorable one.",
    "comparisons": ["VALUE_PROFITABILITY minus VALUE_COMMON_UNIVERSE", "VALUE_PROFITABILITY_BUFFER minus VALUE_COMMON_UNIVERSE", "VALUE_PROFITABILITY_BUFFER minus VALUE_PROFITABILITY", "each arm minus common equal-weight universe", "each arm minus contextual original H19"],
    "decision_rule": "Net-profit improvement remains INCONCLUSIVE unless ordinary cash, taxes, corporate terms and continuous execution for the exact H20 holdings are certified. Describe direction of all measured proxy differences; do not convert proxy success to projected profit. No automatic promotion or new tuning; record negative or mixed results as observed.",
    "stop": "One frozen comparison and independent arithmetic reproduction, plus proportional existing/new measurement tests and current economic evidence gate. No parameter/window/sector search, new factors, bulk data reconstruction, protected runs, real orders or spending.",
    "budget": {"previous_registered_configurations_minimum": 35, "previous_return_evaluations_minimum": 37, "new_registered_diagnostic_scenarios": 18, "new_return_evaluations_if_all_observed": 18, "after_registered_minimum": 53, "after_return_evaluations_if_all_observed": 55, "note": "Conservatively count all 3 arms x3 price modes x2 costs as additional diagnostic specifications; capital scalings and benchmark/reference arithmetic are not independent candidates. Three strategy rules already existed. Shared observed history, no intact holdout."},
}
path = REPO / "docs/research/2026-09-08-h20-profit-test-protocol.json"
with path.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(protocol, stream, indent=2, ensure_ascii=False, allow_nan=False)
    stream.write("\n")
print(json.dumps({"protocol": str(path), "sha256": digest(path)}, indent=2))
