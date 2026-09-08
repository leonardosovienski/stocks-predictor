"""Local checks only; no installation, database writes, network or orders."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(r"C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907")
REPO = ROOT / "work/stocks-predictor"
OUT = ROOT / "work/h20-remediation-20260908"
ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8", "PYTHONPATH": os.pathsep.join(str(p) for p in
       [REPO, ROOT/"work/runtime", ROOT/"work/checks", ROOT/"work/lint"])}
sys.path[:0] = ENV["PYTHONPATH"].split(os.pathsep)
results = {}


def run(name, args, *, expected=0, cwd=REPO, env=ENV):
    p = subprocess.run([sys.executable, *args], cwd=cwd, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    (OUT / (name+".log")).write_text(p.stdout+p.stderr, encoding="utf-8")
    results[name] = {"exit_code": p.returncode, "expected": expected}
    print(name, p.returncode, flush=True)
    if p.returncode != expected:
        raise RuntimeError(name + " failed: " + (p.stdout+p.stderr)[-4000:])


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


run("ruff", ["-m", "ruff", "check", "stocks_predictor", "tests", "main.py"])
run("pyright", ["-m", "pyright"])
run("h19-replay", ["-m", "stocks_predictor.continuous_research", "--inputs",
    str(ROOT/"work/stocks-final-review-bundle/inputs"), "--output", str(OUT/"h19-replay.json")], expected=2)
assert sha(OUT/"h19-replay.json") == "585c72395fc2fefc2e0bbd90b6756c516e58d0f1e29ada3d6de196f46ea49c27"
run("h20-checked", ["-m", "stocks_predictor.h20_checked", "--root", str(ROOT), "--gate",
    str(ROOT/"work/h20-profit-test-20260908/h19-gate-replay.json"), "--output", str(OUT/"h20-checked.json")])
assert sha(OUT/"h20-checked.json") == "aa184580bf5ba69b515a20cc40115453396bdefa470ac0f5408c0d3ced15e1a3"
run("h20-readiness", ["-m", "stocks_predictor.h20_continuous", "--root", str(ROOT),
    "--output", str(OUT/"readiness-02.json")], expected=2)
assert (OUT/"readiness-01.json").read_bytes() == (OUT/"readiness-02.json").read_bytes()

# Compare full books to the pre-repair code, not merely to a second invocation
# of the same implementation. This is regression arithmetic, not independence.
old_path = OUT / "continuous_cash_before.py"
old_path.write_bytes(subprocess.check_output(["git", "show", "c1bfa15:stocks_predictor/continuous_cash.py"], cwd=REPO))
spec = importlib.util.spec_from_file_location("continuous_cash_before", old_path)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
from stocks_predictor.continuous_cash import run_continuous
from tests.test_continuous_cash import tape, dividend
from tests.test_h20_continuous import fixture, reorder, price
from stocks_predictor.h20_continuous import run_h20_book
from stocks_predictor.value_profitability import ARMS
cases = [tape(), tape(), tape(), tape()]
cases[1]["cash_events"] = [dividend()]
cases[2]["cash_events"] = [dividend("2020-04-30", "2020-05-04")]
cases[3]["cost_rate"] = ".0036"
for data in cases:
    assert old.run_continuous(**deepcopy(data)) == run_continuous(**deepcopy(data))
results["h19_original_code_regression"] = {"exact_synthetic_books": len(cases), "base_commit": "c1bfa15"}

data, ranks = fixture(5000, "bdr")
price(data, lambda d, t: d >= "2020-01-31", "10")
price(data, lambda d, t: d >= "2020-01-31" and t < "A04", "20")
reorder(ranks, [f"A{i:02}" for i in [*range(4, 20), *range(4)]])
data["cash_events"] = [{**dividend(), "ticker": "A00", "isin": "ID00"}]
result = run_h20_book(data, ranks, ARMS[2])
synthetic = {"evidence_kind": "SYNTHETIC_ENGINE_TEST_NOT_HISTORICAL_OR_FUTURE_PROFIT",
             "explanation": "5000 initial; 10000 sale; 750 tax; 9250 new buys; 62.50 dividend paid after exit; terminal 9312.50.",
             "result": result}
(OUT/"synthetic-accounting.json").write_text(json.dumps(synthetic, indent=2, default=str)+"\n", encoding="utf-8")

run("build-wheel", ["-m", "build", "--wheel", "--no-isolation", "--outdir", str(OUT/"dist")])
wheel, = (OUT/"dist").glob("*.whl")
outside = OUT / "outside-wheel"
outside.mkdir()
with zipfile.ZipFile(wheel) as archive:
    archive.extractall(outside/"site")
(outside/"tests").mkdir()
focused = ["__init__.py", "test_h20_continuous.py", "test_h20_checked.py", "test_h20_implementation.py",
           "test_continuous_cash.py", "test_corporate_auction_tax.py", "test_continuous_research.py"]
for name in focused:
    shutil.copyfile(REPO/"tests"/name, outside/"tests"/name)
outside_env = {**ENV, "PYTHONPATH": os.pathsep.join(str(p) for p in
               [outside/"site", ROOT/"work/runtime", ROOT/"work/checks"])}
run("wheel-import", ["-c", "import stocks_predictor.h20_continuous as m; print(m.__file__); assert 'outside-wheel' in m.__file__"],
    cwd=outside, env=outside_env)
run("wheel-tests", ["-m", "pytest", "tests", "-q"], cwd=outside, env=outside_env)
run("wheel-readiness", ["-m", "stocks_predictor.h20_continuous", "--root", str(ROOT),
    "--output", str(OUT/"readiness-wheel.json")], expected=2, cwd=outside, env=outside_env)
assert (OUT/"readiness-wheel.json").read_bytes() == (OUT/"readiness-02.json").read_bytes()
results["wheel"] = {"file": wheel.name, "sha256": sha(wheel), "installed": False}
results["byte_identical"] = {p: sha(OUT/p) for p in ["h19-replay.json", "h20-checked.json", "readiness-02.json", "readiness-wheel.json"]}
results["new_historical_return_evaluations"] = 0
(OUT/"verification.json").write_text(json.dumps(results, indent=2)+"\n", encoding="utf-8")
print(json.dumps(results, indent=2), flush=True)
