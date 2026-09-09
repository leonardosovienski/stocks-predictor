"""Reproduce the recovered source audits; never calculate historical returns."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from stocks_predictor.source_closure import audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recovery", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    root = args.recovery.resolve()
    if args.output.resolve().is_relative_to(root):
        raise ValueError("Audit output must be outside preserved recovery data")
    source13 = root / "bundles/source13"
    source14 = root / "source14-inputs"
    manifest_shas = {source13 / "inputs/SHA256.json":
                     "7c24e093f7a148c3f375fff9fbd23db62f049ba8012e49e6ba7b4413e27a372b",
                     source14 / "SHA256.json":
                     "3b36e2416e44f2b0a30e88d4306e00cdc74a7302c6e9b0e33950a893ea169bda"}
    for path, expected in manifest_shas.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Source manifest changed: " + str(path))
    results = {}
    for version, inputs in ((13, source13 / "inputs"), (14, source14)):
        result = audit(source13 / "baseline", inputs, source13 / "signals.json",
                       source13 / "source-protocol.json")
        if version == 13 and result != json.loads((source13 / "expected-audit.json").read_text(encoding="utf-8")):
            raise ValueError("Recovered revision13 differs from its original audit")
        if result["new_historical_return_evaluations"] != 0:
            raise ValueError("Source audit unexpectedly contains an economic evaluation")
        results[str(version)] = result
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump({"python": sys.version, "audit_kind": "SOURCE_COMPLETENESS_ONLY",
                   "production_environment_certificate": False, "audits": results},
                  stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({v: {k: r[k] for k in ("status", "missing_payment_dates", "missing_net_values")}
                      for v, r in results.items()}))


if __name__ == "__main__":
    main()
