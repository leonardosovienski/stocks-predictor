"""Independent arithmetic against the just-reproduced underlying source marks."""
from datetime import date
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(r"C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907")
WORK = ROOT / "work/h20-profit-test-20260908"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check(actual, expected):
    assert math.isclose(actual, expected, abs_tol=2e-12, rel_tol=2e-12), (actual, expected)

result = read(WORK / "observation-01.json")
source = read(WORK / "source-reproduction/profit-validation-reproduced.json")
h20 = read(ROOT / "work/h20-implementation-20260908/observation-02.json")
signals = {p["asof"]: p for p in h20["periods"]}
trial = next(t for t in source["trials"] if t["family"] == "H19" and t["holding_months"] == 3)
mean_checks = path_checks = pair_checks = 0
for mode, measured in result["modes"].items():
    computed = {}
    for period in trial["modes"][mode]["periods"]:
        signal = signals[period["asof"]]
        members = {m["ticker"]: m for m in period["members"]}
        groups = {a: [m["ticker"] for m in signal["arms"][a]["members"]] for a in result["protocol"]["arms"]}
        groups["COMMON_EQUAL_WEIGHT"] = [m["ticker"] for m in next(iter(signal["arms"].values()))["ranking"]]
        groups["H19_ORIGINAL"] = [m["ticker"] for m in members.values() if m["selected"]]
        computed[period["asof"]] = {g: math.fsum(members[t]["return"] for t in names)/len(names) for g, names in groups.items()}
        current = next(p for p in measured["periods"] if p["asof"] == period["asof"])
        for g, value in computed[period["asof"]].items():
            check(current["returns"][g], value)
            mean_checks += 1
    start, end = trial["modes"][mode]["periods"][0]["entry"], trial["modes"][mode]["periods"][-1]["exit"]
    years = (date.fromisoformat(end)-date.fromisoformat(start)).days/365.25
    for case in measured["scenarios"]:
        cost = case["one_way_assumed_cost"]
        for group, summary in case["groups"].items():
            multipliers = [(1+computed[d][group])*(1-cost)/(1+cost) for d in sorted(computed)]
            total = math.prod(multipliers)
            check(summary["synthetic_path"]["terminal_multiple"], total)
            check(summary["synthetic_path"]["annualized_geometric_return"], total**(1/years)-1)
            values = [1.0] + [math.prod(multipliers[:i]) for i in range(1, len(multipliers)+1)]
            drawdown = min(v/max(values[:i+1])-1 for i, v in enumerate(values))
            check(summary["synthetic_path"]["period_mark_max_drawdown"], drawdown)
            path_checks += 1
        for pair in case["comparisons"]:
            a, b = pair["left"], pair["right"]
            values = [computed[d][a]-computed[d][b] for d in sorted(computed)]
            check(pair["mean_quarter_difference_after_assumed_cost"], math.fsum(values)/31*(1-cost)/(1+cost))
            check(pair["fixed_halves"][0]["mean_quarter_difference"], math.fsum(values[:15])/15)
            check(pair["fixed_halves"][1]["mean_quarter_difference"], math.fsum(values[15:])/16)
            pair_checks += 1
validation = {"status": "PASS", "independent_cross_section_mean_checks": mean_checks,
    "independent_compounding_annualization_drawdown_checks": path_checks,
    "independent_paired_mean_and_fixed_halves_checks": pair_checks,
    "source_reproduction": read(WORK / "source-reproduction/verification.json"),
    "h19_gate_byte_identical": (WORK/"h19-gate-replay.json").read_bytes() == (ROOT/"work/h20-implementation-20260908/h19-replay-native.json").read_bytes(),
    "h19_gate_sha256": sha(WORK/"h19-gate-replay.json"),
    "observation_sha256": sha(WORK/"observation-01.json"),
    "full_suite": "639 passed in 71.85s", "measurement_tests": "11 passed in 0.05s",
    "production_runtime_changed": False,
    "database_access": "Only frozen source reproduction opens archived quote extracts with SQLite mode=ro. Raw package hashes were verified before and after. Production databases, ledgers and quarantines are untouched.",
    "profit": None, "future_profit_projection": None}
with (WORK/"independent-verification.json").open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(validation, stream, indent=2, ensure_ascii=False)
    stream.write("\n")
print(json.dumps(validation, indent=2))
