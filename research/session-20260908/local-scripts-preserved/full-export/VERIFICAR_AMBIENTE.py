"""Reproduce the source audit, optionally testing the restored code, without installs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    if sys.version_info[:2] != (3, 13):
        raise RuntimeError("Use Python global 3.13")
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Restored root, e.g. C:\\Stocks")
    parser.add_argument("--testes", action="store_true", help="Also run the existing code tests")
    args = parser.parse_args()
    root = args.root.resolve()
    work = root / "project/.local-research/stocks-session-20260907/work"
    repo = work / "stocks-predictor"
    for path in (root / "RECIBO_RESTAURACAO.json", repo / "AGENTS.md", work / "runtime/predictor_core"):
        if not path.exists():
            raise FileNotFoundError(path)
    output = Path(tempfile.mkdtemp(prefix="migration-validation-", dir=root))
    supplement = root / "session/work/continuation-14/deliverable"
    baseline = root / "session/work/continuation-14/baseline-13"
    audit = subprocess.run([sys.executable, "-B", "-I", "-S", str(supplement / "VALIDAR_REVISAO_14.py"),
                            "--baseline13", str(baseline), "--workspace", str(output / "audit-14")],
                           capture_output=True, encoding="utf-8", timeout=600)
    (output / "audit.log").write_text(audit.stdout + audit.stderr, encoding="utf-8")
    if audit.returncode:
        raise RuntimeError(f"Audit failed; see {output / 'audit.log'}")
    audit_path = output / "audit-14/auditoria-fontes-14.json"
    sha = hashlib.sha256(audit_path.read_bytes()).hexdigest()
    if sha != "f27461eeef0c86d5df0727dae73b3d1c4b9ed817b2c8423f2d2649c88d6a67a8":
        raise RuntimeError("Relocated source audit does not reproduce the original bytes")
    result = {"source_audit": "IDENTICAL", "sha256": sha, "output": str(output),
              "python": sys.version, "new_historical_return_evaluations": 0,
              "economic_status": "BLOCKED_MISSING_EVIDENCE", "tests_run": False}
    print(json.dumps(result), flush=True)
    if args.testes:
        deps = [work / "runtime", work / "checks", work / "lint", root / "python313-packages"]
        env = os.environ | {"PYTHONPATH": os.pathsep.join(str(p) for p in deps),
                            "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1",
                            "PYTHONNOUSERSITE": "1", "GIT_OPTIONAL_LOCKS": "0"}
        # -S excludes this computer's installed packages; dependencies come from the export.
        probe = subprocess.run([sys.executable, "-B", "-S", "-c",
                                "import predictor_core, yaml, pytest; print(predictor_core.__file__); print(yaml.__file__); print(pytest.__file__)"],
                               cwd=repo, env=env, capture_output=True, encoding="utf-8", check=True)
        (output / "dependencies.log").write_text(probe.stdout, encoding="utf-8")
        if str(work / "runtime") not in probe.stdout or str(root / "python313-packages") not in probe.stdout:
            raise RuntimeError("Dependencies did not load from restored copies")
        tests = subprocess.run([sys.executable, "-B", "-S", "-m", "pytest", "tests",
                                "research/session-20260908/chat-review/test_h20_evidence_integrity.py",
                                "research/session-20260908/h20-profit-test/test_h20_profit_comparison.py",
                                "-q", "-p", "no:cacheprovider"],
                               cwd=repo, env=env, capture_output=True, encoding="utf-8", timeout=1200)
        (output / "tests.log").write_text(tests.stdout + tests.stderr, encoding="utf-8")
        result.update({"tests_run": True, "test_exit_code": tests.returncode,
                       "test_summary": tests.stdout.splitlines()[-3:]})
        if tests.returncode:
            raise RuntimeError(f"Restored tests failed; see {output / 'tests.log'}")
    (output / "VALIDACAO_AMBIENTE.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
