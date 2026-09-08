"""Record the source-only V3 update; no market return computation."""
import hashlib
import json
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
out = root / "outputs"
repo = root / "work/stocks-predictor"
receipt = json.loads((out / "H19_DATAS_V3_REPRODUCAO.json").read_text(encoding="utf-8"))
audit = json.loads((out / "H19_CAIXA_EXECUCAO_V3.json").read_text(encoding="utf-8"))
assert audit["status"] == "BLOCKED_MISSING_EVIDENCE"
assert audit["profit"] is None and not audit["full_history_executed"]
assert receipt["summary"] == audit["original_queue_summary"]
assert receipt["rebuilt_registry_identical"]
for filename, expected in [
    (receipt["archive"], receipt["sha256"]),
    ("H19_CAIXA_EXECUCAO_V3.json", receipt["audit_sha256"]),
    ("H19_CAIXA_PAGAMENTOS_REVISADOS_V3.json", receipt["registry_sha256"]),
]:
    assert hashlib.sha256((out / filename).read_bytes()).hexdigest() == expected, filename

decision = {
    "scientific_state": "DISCOVERY_H19_NET_INCONCLUSIVE_DATA_QUALITY",
    "source_update": "H19_PAYMENT_DATES_V3",
    "runtime_commit": "5e71bc8642cc2b0759e8a1885cab446e315121fd",
    "runtime_unchanged": True,
    "prior_runtime_tests": 558,
    "runtime_tests_repeated": False,
    "full_history_executed": False,
    "net_profit": None,
    "new_return_evaluations": 0,
    "budget_minimum": {"configurations": 32, "historical_return_evaluations": 37},
    "capital_brl": [5000, 10000],
    "user_minimum_annual_profit": None,
    "user_monthly_maintenance_hours": None,
    "incremental_selected_rows_reviewed": 16,
    "queue_summary": receipt["summary"],
    "normalized_installment_rows": 2,
    "selected_candidate_only_rows_remaining": 8,
    "complete_cash_coverage_verified": False,
    "issue_counts": audit["issue_counts"],
    "reproduction": receipt,
    "promote": False,
    "next_work": [
        "Review remaining candidates and complete both cash inventories including JBS and successors",
        "Review net amounts, corporate deliveries, fractions and fiscal basis",
        "Implement continuous historical portfolio and dated fiscal schedule",
        "Evaluate reconstruction cost before expanding research; no new factor family or tuning",
    ],
}
target = repo / "docs/research/2026-09-07-h19-dates-v3-decision.json"
target.write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
shutil.copyfile(out / "H19_DATAS_V3_RESULTADO.md", repo / "docs/research/2026-09-07-h19-dates-v3-results.md")
print(json.dumps({"recorded": True, "hashes_checked": 3, "new_return_evaluations": 0}))
