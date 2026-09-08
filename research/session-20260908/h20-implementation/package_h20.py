"""Archive the completed H20 implementation; preserve old inputs and observations."""
from pathlib import Path
import hashlib
import json
import zipfile

CHAT = Path(r"C:\Users\Superleo13\Documents\Codex\2026-09-07\lei-2")
ROOT = Path(r"C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907")
REPO = ROOT / "work/stocks-predictor"
WORK = ROOT / "work/h20-implementation-20260908"
OUT = CHAT / "outputs"
PACKAGE = WORK / "package"
PACKAGE.mkdir(exist_ok=False)

observation = json.loads((WORK / "observation-02.json").read_text(encoding="utf-8"))
assert observation["quarterly_signal_dates"] == 32
assert sum(r["status"] == "SIMULATED_ENTRY_ONLY" for r in observation["entry_cases"]) == 372
assert (96 - 70) / 96 * 100 == 27.083333333333332
validation = {"runtime_commit": "9ecf5eb", "full_suite_passed": 639, "full_suite_seconds": 131.70,
    "packaged_tests_passed": 92, "new_focused_tests": 26,
    "ruff": "PASS", "pyright_new_modules": "PASS, four modules",
    "h20_wheel_byte_identical": True,
    "h20_observation_sha256": hashlib.sha256((WORK / "observation-02.json").read_bytes()).hexdigest(),
    "h19_regression": json.loads((WORK / "h19-regression.json").read_text(encoding="utf-8")),
    "initial_external_harness_failures": ["legacy direct imports required the installed package directory", "imports between tests required a tests package"],
    "financial_status": "INCONCLUSIVE_NET_PROFIT / OPERATIONAL_NO_GO", "new_return_evaluations": 0,
    "registered_configurations_minimum": 35, "historical_return_evaluations_minimum": 37,
    "database_operations": "No database opened by implementation, diagnostics or packaging; tests use temporary data.",
    "runtime_dependencies_installed": [], "real_orders": False,
    "input_archives_verified": 11, "execution_input_files_verified": 31, "execution_quote_records_validated": 365198}
(OUT / "H20_VALIDACAO.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
(OUT / "H20_RESULTADOS.json").write_bytes((WORK / "observation-02.json").read_bytes())

def copy(source, relative):
    destination = PACKAGE / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())

copy(OUT / "H20_IMPLEMENTACAO.md", "README.md")
copy(OUT / "H20_VALIDACAO.json", "results/H20_VALIDACAO.json")
for name in ["observation-01.json", "observation-02.json", "h19-regression.json"]:
    copy(WORK / name, "results/" + name)
for name in ["2026-09-08-h20-implementation-protocol.json", "2026-09-08-h20-entry-source-addendum.json"]:
    copy(REPO / "docs/research" / name, "protocols/" + name)
for name in ["review.json", "cvm-corporate-0166.pdf"]:
    copy(ROOT / "work/continuation-20260908/entry-unit-review" / name, "entry-unit-review/" + name)
for name in ["value_profitability.py", "buffered_rebalance.py", "h20_research.py", "entry_feasibility.py"]:
    copy(REPO / "stocks_predictor" / name, "code/" + name)
for source in (WORK / "tests").glob("*.py"):
    copy(source, "tests/" + source.name)
for name in ["REPRODUZIR_H20.py", "EXECUTAR_H20.ps1"]:
    copy(CHAT / "work" / name, name)
wheel = next((WORK / "dist").glob("*.whl"))
copy(wheel, "dist/" + wheel.name)
for name in ["full-tests.log", "external-tests.log", "external-tests-final.log", "external-tests-complete.log"]:
    copy(WORK / name, "validation/" + name)

files = {p.relative_to(PACKAGE).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted(PACKAGE.rglob("*")) if p.is_file()}
manifest = {"files": files, "wheel": "dist/" + wheel.name, "runtime_commit": "9ecf5eb",
            "external_research_root": str(ROOT), "profit": None}
(PACKAGE / "MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
archive = OUT / "H20_IMPLEMENTACAO.zip"
with zipfile.ZipFile(archive,"x",compression=zipfile.ZIP_DEFLATED) as bundle:
    for file in sorted(PACKAGE.rglob("*")):
        if file.is_file():bundle.write(file,file.relative_to(PACKAGE).as_posix())
with zipfile.ZipFile(archive) as bundle:
    for name,digest in files.items():assert hashlib.sha256(bundle.read(name)).hexdigest()==digest
receipt = {"archive": archive.name, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
           "payloads_verified": len(files), "bytes": archive.stat().st_size,
           "runtime_commit": "9ecf5eb", "requires_preserved_sources": True}
(OUT / "H20_PACOTE.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")

durable = ROOT / "outputs/h20-implementation-20260908"
durable.mkdir(exist_ok=True)
for file in OUT.glob("H20_*"):(durable / file.name).write_bytes(file.read_bytes())
repo_artifacts = REPO / "research/session-20260908/h20-implementation"
repo_artifacts.mkdir(exist_ok=True)
for name in ["H20_IMPLEMENTACAO.md", "H20_VALIDACAO.json", "H20_PACOTE.json"]:
    (repo_artifacts / name).write_bytes((OUT / name).read_bytes())
for name in ["observation-01.json", "observation-02.json", "h19-regression.json", "full-tests.log",
             "external-tests.log", "external-tests-final.log", "external-tests-complete.log"]:
    (repo_artifacts / name).write_bytes((WORK / name).read_bytes())
for name in ["REPRODUZIR_H20.py", "EXECUTAR_H20.ps1", "package_h20.py"]:
    (repo_artifacts / name).write_bytes((CHAT / "work" / name).read_bytes())
(REPO / "docs/research/2026-09-08-h20-results.md").write_bytes((OUT / "H20_IMPLEMENTACAO.md").read_bytes())
print(json.dumps(receipt))
