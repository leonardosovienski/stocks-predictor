"""Reproduce the H20 package with preserved sources, Python 3.13 and local dev tools."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--research-root", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if sys.version_info[:2] != (3, 13):
    raise SystemExit("Use the existing global Python 3.13; no runtime installation is performed.")
base = Path(__file__).resolve().parent
manifest = json.loads((base / "MANIFEST.json").read_text(encoding="utf-8"))
for name, expected in manifest["files"].items():
    file = (base / name).resolve()
    if not file.is_relative_to(base) or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
        raise SystemExit("Package integrity failure: " + name)
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=False)
installed = output / "wheel"
wheel = base / manifest["wheel"]
with zipfile.ZipFile(wheel) as archive:
    if any(not (installed / n).resolve().is_relative_to(installed) for n in archive.namelist()):
        raise SystemExit("Invalid wheel path")
    archive.extractall(installed)
tests = output / "tests"
tests.mkdir()
for source in (base / "tests").glob("*.py"):
    (tests / source.name).write_bytes(source.read_bytes())
root = args.research_root.resolve()
env = dict(os.environ)
env["PYTHONPATH"] = os.pathsep.join(map(str, [installed, installed / "stocks_predictor",
                                            root / "work/runtime", root / "work/checks"]))
test = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"], cwd=output,
                      env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
(output / "tests.log").write_text(test.stdout + test.stderr, encoding="utf-8")
if test.returncode:
    raise SystemExit("Packaged tests failed; see output/tests.log")
result = output / "observation.json"
command = [sys.executable, "-m", "stocks_predictor.h20_research",
           "--features", str(root / "work/value-prepared-features.json"),
           "--accounting", str(root / "work/value-capital-source/accounting-v2.json"),
           "--source-dir", str(root / "work/source-acquisition"),
           "--execution-inputs", str(root / "work/stocks-final-review-bundle/inputs"),
           "--protocol", str(base / "protocols/2026-09-08-h20-implementation-protocol.json"),
           "--entry-unit-review", str(base / "entry-unit-review/review.json"),
           "--output", str(result)]
run = subprocess.run(command, cwd=output, env=env, capture_output=True,
                     text=True, encoding="utf-8", errors="replace")
(output / "diagnostic.log").write_text(run.stdout + run.stderr, encoding="utf-8")
if run.returncode:
    raise SystemExit("H20 diagnostic failed; see output/diagnostic.log")
expected = base / "results/observation-02.json"
if result.read_bytes() != expected.read_bytes():
    raise SystemExit("Observation differs from the preserved Windows result")
print(json.dumps({"status": "REPRODUCED", "packaged_tests_passed": True,
                  "observation_byte_identical": True,
                  "sha256": hashlib.sha256(result.read_bytes()).hexdigest(),
                  "profit": None, "output": str(output)}))
