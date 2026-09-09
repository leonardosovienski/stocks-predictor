"""Reproduce an existing economic outcome without registering a new observation."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from stocks_predictor.etf_hold import simulate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Existing local h21 artifact directory")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result_path = args.root / "result-01.json"
    if hashlib.sha256(result_path.read_bytes()).hexdigest() != "39a940514b5fdcbb577c496f996ddd324c8107436852ab67da352401bb8870d2":
        raise ValueError("Original result seal changed")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    local_inputs = args.root / "inputs/quotes.json"
    local_selic = args.root / "public/selic-11.json"
    for path in (local_inputs, local_selic):
        expected = next(h for original, h in result["input_hashes"].items()
                        if original.replace("\\", "/").rsplit("/", 1)[-1] == path.name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Input hash changed")
    inputs = json.loads(local_inputs.read_text(encoding="utf-8"))
    copies = [simulate(inputs["records"], inputs["market_sessions"], capital=row["capital_brl"],
                       rate=row["one_way_cost_rate"], mode=row["mode"], entry_signal="2017-12-29",
                       exit_signal="2026-03-31") for row in result["outcomes"]]
    if copies != result["outcomes"]:
        raise AssertionError("Current engine changed the recorded economic outcomes")
    # Separate logarithmic composition, not the engine's Decimal product loop.
    rates = json.loads(local_selic.read_text(encoding="utf-8"))
    factor = math.exp(math.fsum(math.log1p(float(row["valor"]) / 100) for row in rates))
    if not math.isclose(factor, result["gross_selic_reference"]["gross_factor"], rel_tol=1e-14):
        raise AssertionError("Selic composition discrepancy")
    receipt = json.loads((args.root / "raw/receipt.json").read_text(encoding="utf-8"))
    for row in receipt["selected_files"]:
        with (args.root / "raw" / Path(row["path"]).name).open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != row["sha256"]:
                raise ValueError("Recovered original quote ZIP changed")
    answer = {"status": "PASS", "economic_outcomes_identical": 8,
              "daily_points_identical": sum(len(r["equity_curve"]) for r in copies),
              "original_quote_objects_rehashed": 9, "selic_independent_log_compounding_factor": factor,
              "new_hypotheses": 0, "new_independent_evidence": 0,
              "original_result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest()}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(answer, stream, indent=2)
        stream.write("\n")
    print(json.dumps(answer, indent=2))


if __name__ == "__main__":
    main()
