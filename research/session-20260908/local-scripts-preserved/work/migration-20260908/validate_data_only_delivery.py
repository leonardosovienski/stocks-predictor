"""Validate the separate migration using restored data and read-only source audit."""
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import zipfile

MAIN = Path(r"C:\Users\Superleo13\stocks-predictor-work")
CHAT = Path(r"C:\Users\Superleo13\Documents\Codex\2026-09-07\lei-2")
OUT = Path(r"E:\STOCKS_MIGRACAO_MAIN_20260908")
DEST = CHAT / "work/migration-20260908/data-only-restoration-test"
sys.path.insert(0, str(MAIN))
from tools import data_transfer
from stocks_predictor import source_closure

archive_path = OUT / "DADOS_STOCKS.zip"
receipt = data_transfer.verify(archive_path, DEST, "session/work/migration-20260908/validation-14")
print(json.dumps(receipt), flush=True)
baseline_prefix = "session/work/continuation-14/baseline-13/"
db_rows = []
with zipfile.ZipFile(archive_path) as archive:
    manifest, _ = data_transfer.read_manifest(archive)
    selected = [row for row in manifest["files"] if
                row["path"].startswith(baseline_prefix + "baseline/") or
                row["path"] in {baseline_prefix + "signals.json", baseline_prefix + "source-protocol.json"} or
                (row["path"].endswith(".db") and not row["path"].startswith("unpacked-archives/"))]
    for row in selected:
        target = DEST / data_transfer.validate_name(row["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open("objects/" + row["sha256"]) as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
        assert data_transfer.digest(target) == row["sha256"]
        if target.suffix == ".db":
            with sqlite3.connect(target.as_uri() + "?mode=ro&immutable=1", uri=True) as conn:
                result = [r[0] for r in conn.execute("PRAGMA quick_check")]
            assert result == ["ok"], (row["path"], result)
            assert data_transfer.digest(target) == row["sha256"]
            db_rows.append({"path": row["path"], "sha256": row["sha256"], "quick_check": "ok"})
base = DEST / baseline_prefix
inputs = DEST / "session/work/migration-20260908/validation-14/inputs"
audit = source_closure.audit(base / "baseline", inputs, base / "signals.json", base / "source-protocol.json")
payload = (json.dumps(audit, ensure_ascii=False, indent=2) + "\n").encode()
audit_sha = hashlib.sha256(payload).hexdigest()
assert audit_sha == "f27461eeef0c86d5df0727dae73b3d1c4b9ed817b2c8423f2d2649c88d6a67a8", audit_sha
assert audit["new_historical_return_evaluations"] == 0
(OUT / "AUDITORIA_FONTES_14_NA_MAIN.json").write_bytes(payload)
dep_rows = json.loads((OUT / "MANIFESTO_DEPENDENCIAS.json").read_text(encoding="utf-8"))
for row in dep_rows:
    assert data_transfer.digest(OUT / row["path"]) == row["sha256"], row["path"]
original = json.loads(Path(r"E:\EXPORTACAO_STOCKS_20260908\MANIFESTO.json").read_text(encoding="utf-8"))
local_names = {"dfp_2023_companies.txt", "dividend_exploration.txt", "ticker_of_2019.json",
               "ticker_of_proposto.json", "universo_2018_2026.txt", "universo_snapshots.txt"}
for row in original["files"]:
    if row["path"].removeprefix("project/") in local_names:
        assert data_transfer.digest(MAIN / row["path"].removeprefix("project/")) == row["sha256"]
code_head = subprocess.check_output(["git", "-C", str(MAIN), "rev-parse", "HEAD"], encoding="utf-8").strip()
result = {
    "code_tested_commit": code_head, "branch": "main", "pushed": False,
    "suite": {"passed": 777, "failures": 0, "warnings": 0, "seconds": 83.83,
              "runtime": "Python 3.13; Core 3.2.0 from copied dependencies; clean clone"},
    "ruff": "passed", "pyright": "0 errors, 0 warnings",
    "data_archive": json.loads(archive_path.with_suffix(".json").read_text(encoding="utf-8")),
    "verification": receipt, "sqlite_databases": db_rows,
    "additional_data_files_restored": len(selected),
    "dependencies_files_verified": len(dep_rows),
    "source_audit_14_sha256": audit_sha,
    "source_audit_status": audit["status"], "new_historical_return_evaluations": 0,
    "original_untracked_data_files_preserved": sorted(local_names),
    "full_backup_unchanged": r"E:\EXPORTACAO_STOCKS_20260908",
    "restoration_test_directory": str(DEST),
}
data_transfer.write_json(OUT / "RESULTADO.json", result)
shutil.copy2(CHAT / "work/migration-20260908/main-clean-tests.log", OUT / "TESTES_MAIN.log")
print(json.dumps({"databases": len(db_rows), "source_audit_sha256": audit_sha,
                  "dependency_files": len(dep_rows), "status": "VERIFIED"}), flush=True)
