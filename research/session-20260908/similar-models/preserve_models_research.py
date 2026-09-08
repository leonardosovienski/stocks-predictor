"""One-shot acquisition record, not a fund/backtest reproducer; opens no databases."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

CHAT = Path(r"C:\Users\Superleo13\Documents\Codex\2026-09-07\lei-2")
ROOT = Path(r"C:\Users\Superleo13\stocks-predictor-work\.local-research\stocks-session-20260907")
REPO = ROOT / "work/stocks-predictor"
if (REPO / "research/session-20260908/similar-models/PESQUISA_MODELOS_FONTES.json").exists():
    raise SystemExit("Review already preserved; do not rerun or overwrite this source record.")
ARCHIVE = ROOT / "work/similar-models-20260908/sources"
ARCHIVE.mkdir(parents=True, exist_ok=True)
SOURCES = [
    ("AVUV", "Avantis U.S. Small Cap Value ETF — factsheet 2026-06-30", "https://res.avantisinvestors.com/docs/avantis-us-small-cap-value-avuv-etf-fact-sheet.pdf", "fund_report", "pdf"),
    ("DIMENSIONAL", "All Day, Every Day, Multifactor All the Way — 2022-09-21", "https://www.dimensional.com/dk-en/insights/all-day-every-day-multifactor-all-the-way", "manager_methodology_and_conditional_live_analysis", None),
    ("AQR_VALUE_MOMENTUM", "Value and Momentum Everywhere — 2013", "https://www.aqr.com/Insights/Research/Journal-Article/Value-and-Momentum-Everywhere?aqrPDF=1", "academic_historical", None),
    ("AQR_COSTS", "Trading Costs of Asset Pricing Anomalies — 2012", "https://www.aqr.com/Insights/Research/Working-Paper/Trading-Costs-of-Asset-Pricing-Anomalies", "live_trades_calibrating_simulated_costs", "html"),
    ("PEAD_ATTENTION", "Driven to Distraction — 2009", "https://bpb-us-e2.wpmucdn.com/sites.uci.edu/dist/c/362/files/2020/07/Driven-to-Distraction-Extraneous-Events-and-Underreaction-to-Earnings-News.pdf", "academic_historical", None),
    ("PEAD_COSTS", "Implications of Transaction Costs for the Post-Earnings Announcement Drift — 2008", "https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1475-679X.2008.00290.x", "publisher_abstract_reviewed_full_access_limited", None),
    ("PEAD_RECENT", "Warp speed price moves — version 2026-01-15", "https://arxiv.org/abs/2601.08962v2", "author_paper_abstract_reviewed", None),
    ("ML_PAPER", "Empirical Asset Pricing via Machine Learning — RFS 2020", "https://dachxiu.chicagobooth.edu/download/ML.pdf", "academic_historical_temporal_split", "pdf"),
    ("ML_NBER", "Empirical Asset Pricing via Machine Learning — NBER", "https://www.nber.org/papers/w25398", "academic_abstract_and_disclosures", None),
    ("SA_FEATURES", "Seeking Alpha Premium: List of Features", "https://help.seekingalpha.com/premium/seeking-alpha-premium-feature-list", "provider_features", None),
    ("SA_BACKTEST", "Have Seeking Alpha's Quant Ratings Been Backtested?", "https://help.seekingalpha.com/premium/have-seeking-alphas-quant-ratings-been-back-tested", "provider_backtest_disclosure", None),
    ("SA_SUBSCRIPTIONS", "Seeking Alpha Subscriptions - Cancellation and Refund Policy", "https://help.seekingalpha.com/basic/seeking-alpha-subscriptions-cancellation-and-refund-policy", "provider_business_model", None),
    ("DANELFIN_MODEL", "How Danelfin Works", "https://danelfin.com/how-it-works", "provider_model_and_backtest_disclosure", None),
    ("DANELFIN_PRICING", "Danelfin monthly pricing", "https://danelfin.com/pricing/monthly", "provider_price_snapshot", "html"),
    ("DANELFIN_AUDIT", "Does our AI Score Work? — 2026-04-14", "https://blog.danelfin.com/ai-score-audit", "provider_claim_not_independent_audit", None),
    ("NEFIN", "NEFIN methodology", "https://nefin.com.br/resources/NEFIN_methodology.pdf", "academic_brazil_methodology", "pdf"),
    ("SPIVA", "SPIVA Latin America Year-End 2025 — 2026-03-23", "https://www.spglobal.com/spdji/en/spiva/article/spiva-latin-america/", "index_provider_fund_comparison", None),
]

def snapshot(source):
    key, title, url, evidence, suffix = source
    entry = {"id": key, "title": title, "url": url, "evidence_type": evidence,
             "reviewed_via": "web tool: available excerpts and relevant sections; not independent replication",
             "access_date_utc": "2026-09-08", "access_date_brazil": "2026-09-07",
             "raw_snapshot": None}
    if suffix is None:
        return entry
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (public research source preservation)"})
        with urllib.request.urlopen(req, timeout=20) as response:
            raw = response.read(12_000_001)
            if len(raw) > 12_000_000:
                raise ValueError("source exceeds bounded download size")
            if suffix == "pdf" and not raw.startswith(b"%PDF"):
                raise ValueError("response is not a PDF")
            path = ARCHIVE / f"{key.lower()}.{suffix}"
            if path.exists():
                raise FileExistsError(f"refuse overwriting archived source: {path}")
            path.write_bytes(raw)
            entry["raw_snapshot"] = {"path": str(path), "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(), "final_url": response.url,
                "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                "note": "Independent HTTP preservation; not a second extraction or reproduction of provider results."}
    except Exception as exc:
        entry["raw_snapshot_error"] = f"{type(exc).__name__}: {exc}"
    return entry

with ThreadPoolExecutor(max_workers=5) as pool:
    entries = list(pool.map(snapshot, SOURCES))

report = CHAT / "outputs/PESQUISA_MODELOS_STOCKS.md"
raw_report = report.read_bytes()
assert b"INCONCLUSIVE_NET_PROFIT / OPERATIONAL_NO_GO" in raw_report
assert round(12.29 - 8.23, 2) == 4.06
assert round(39.00 - 43.01, 2) == -4.01
assert round(19.06 - 18.73, 2) == 0.33
assert 2 * 12 * 25 == 600
assert 5000 * .03 - 600 == -450
assert 10000 * .03 - 600 == -300

manifest = {
    "review_id": "STOCKS_SIMILAR_MODELS_SOURCE_REVIEW_20260908",
    "scope": "external source review only; equity selection and feasibility for BRL 5000-10000",
    "report_sha256": hashlib.sha256(raw_report).hexdigest(),
    "sources": entries,
    "exposure": {"new_internal_return_configurations": 0, "new_internal_return_evaluations": 0,
        "minimum_prior_configurations": 32, "minimum_prior_return_evaluations": 37,
        "external_performance_observed": ["AVUV reported overlapping horizons ending 2026-06-30",
            "SPIVA 2025 and decade comparison", "published factor, ML and PEAD findings",
            "provider marketing performance claims encountered, not treated as audited results"],
        "independent_holdout_created": False,
        "caveat": "External source selection was adaptive and informs research priorities; it is not proof or a preregistered return experiment."},
    "research_priority": ["cost and maintenance feasibility before marginal rank trades",
        "point-in-time availability of value plus profitability data", "conditional PEAD source feasibility", "ML deferred"],
    "h19_status": "INCONCLUSIVE_NET_PROFIT / OPERATIONAL_NO_GO",
    "validation": {"arithmetic_checked": True, "runtime_changed": False,
        "tests_run": False, "reason": "Source review and documentation only; no application behavior changed.",
        "databases_opened": False, "orders_or_spending": False},
    "access_limits": ["Seeking Alpha performance detail required JavaScript",
        "Danelfin audit dashboard not accessible via web reader; vendor announcement reviewed",
        "Wiley abstract initially accessible, subsequent reopen returned HTTP 403",
        "NEFIN old /data/risk_factors.html URL returned 404; methodology PDF available",
        "Search index AVUV snippet was older; report uses opened factsheet dated 2026-06-30",
        "No independent reconstruction of fund NAV, private model weights, provider profits, or subscriber account returns"],
}
out = CHAT / "outputs/PESQUISA_MODELOS_FONTES.json"
out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

dest = ROOT / "outputs/similar-models-20260908"
dest.mkdir(parents=True, exist_ok=True)
for original in (report, out):
    (dest / original.name).write_bytes(original.read_bytes())

repo_report = REPO / "docs/research/2026-09-08-similar-models.md"
repo_report.write_bytes(raw_report)
repo_evidence = REPO / "research/session-20260908/similar-models"
repo_evidence.mkdir(parents=True, exist_ok=True)
(repo_evidence / out.name).write_bytes(out.read_bytes())
(repo_evidence / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
print(json.dumps({"sources": len(entries), "archived": sum(x["raw_snapshot"] is not None for x in entries),
    "snapshot_errors": [{"id":x["id"],"error":x["raw_snapshot_error"]} for x in entries if "raw_snapshot_error" in x],
    "report_sha256": manifest["report_sha256"], "arithmetic": "passed", "runtime_changes": False}, ensure_ascii=False))
