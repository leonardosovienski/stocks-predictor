"""Protocolo v2 — previsão (Prompt 3c): métricas probabilísticas, tarefas PIT, baselines, previsões externas com
proveniência, contaminação/poder, adaptador COTAHIST e execução sob o ledger."""

import copy
import hashlib
import json
import math
import zipfile
from pathlib import Path
from statistics import NormalDist

import pytest

from stocks_predictor.cotahist import _pack
from stocks_predictor.v2 import synthetic
from stocks_predictor.v2.costs import CostModel, LiquidityRule
from stocks_predictor.v2.cotahist_dataset import CotahistError, build_from_cotahist
from stocks_predictor.v2.dataset import PITDataset
from stocks_predictor.v2.engine import ProtocolConfig
from stocks_predictor.v2.execution import ExecutionConvention
from stocks_predictor.v2.forecast_eval import load_riskfree, load_spec, main, run_forecast_evaluation
from stocks_predictor.v2.forecast_metrics import coverage, crps_quantile, pinball, wql
from stocks_predictor.v2.forecasting import (EmpiricalRandomWalk, GaussianRandomWalk, build_tasks,
                                             contamination_status, evaluate_predictions, load_forecasts,
                                             tasks_sha256)
from stocks_predictor.v2.manifest import TrialLedger
from stocks_predictor.v2.policy import load_policy

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/engineering/2026-09-24-protocol-v2"
POLICY = load_policy(ROOT / "policy/stocks-evaluation-policy-v1.json")
DS = PITDataset(synthetic.build())
LEVELS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
CONFIG = ProtocolConfig(start="2020-01-02", end="2021-06-30", rebalance="monthly", execution=ExecutionConvention(),
                        costs=CostModel(0.0, 0.0, 3.0, 7.5, 7.5, 0.0, 0.5, 0.0),
                        liquidity=LiquidityRule(1e6, 63, 0.05), seed=7)
TASKS, STATS = build_tasks(DS, CONFIG, horizon=21, context_length=64, jump_threshold=0.30)
SPEC = load_spec(json.loads((DOCS / "synthetic-forecast-spec.json").read_text()))
GIT = {"commit": "0" * 40, "dirty": False}


# -- métricas conferidas à mão -----------------------------------------------------------------------
def test_quantile_metrics_hand_computed():
    assert pinball(0.0, -1.0, 0.1) == pytest.approx(0.1) and pinball(0.0, 1.0, 0.9) == pytest.approx(0.1)
    # CRPS: (2/3)·(0,1 + 0 + 0,1) = 0,13333
    assert crps_quantile([0.0], [[-1.0, 0.0, 1.0]], [0.1, 0.5, 0.9]) == pytest.approx(0.2 * 2 / 3)
    # WQL: 2·0,2/(3·2) = 0,066667
    assert wql([2.0], [[1.0, 2.0, 3.0]], [0.1, 0.5, 0.9]) == pytest.approx(0.4 / 6)
    assert coverage([0.0, 2.0], [-1.0, -1.0], [1.0, 1.0]) == 0.5
    with pytest.raises(ValueError, match="cruzados"):
        crps_quantile([0.0], [[1.0, 0.0, 2.0]], [0.1, 0.5, 0.9])
    with pytest.raises(ValueError, match="Σ"):
        wql([0.0], [[-1.0, 0.0, 1.0]], [0.1, 0.5, 0.9])


def test_quantile_crps_approximates_the_closed_form_gaussian_crps():
    """CRPS(N(0,1), y = 0) = 2φ(0) − 1/√π = 0,233695 (Gneiting & Raftery 2007, eq. 21)."""
    levels = [i / 100 for i in range(1, 100)]
    quantiles = [[NormalDist().inv_cdf(t) for t in levels]]
    exact = 2 * NormalDist().pdf(0) - 1 / math.sqrt(math.pi)
    assert crps_quantile([0.0], quantiles, levels) == pytest.approx(exact, rel=0.02)


# -- tarefas PIT ------------------------------------------------------------------------------------
def test_tasks_use_only_known_context_and_realized_targets():
    assert STATS["tasks"] == len(TASKS) > 100 and STATS["origins"] > 10
    cal = DS.calendar
    for task in TASKS[:: 17]:
        view = DS.view(cal[task.origin_index + 1])
        sessions, _o, closes, _v = view.history(task.security_id)
        assert list(task.context) == closes[-64:] and sessions[-1] == task.origin
        end = DS.realized_bar(task.security_id, cal[task.origin_index + 21])
        factor = math.prod(m for i in range(task.origin_index + 1, task.origin_index + 22)
                           for m in DS.realized_actions(task.security_id, cal[i]))
        assert task.target_log_return == pytest.approx(math.log(end.close * factor / task.context[-1]))
        assert DS.position(task.origin) + 1 + 21 <= DS.position(CONFIG.end)


def test_unannounced_jump_or_bad_revision_excludes_the_window():
    weekly = ProtocolConfig(**{**CONFIG.__dict__, "rebalance": "weekly", "start": "2020-01-02", "end": "2020-06-30"})
    tasks, stats = build_tasks(DS, weekly, horizon=5, context_length=20, jump_threshold=0.30)
    assert stats["excluded"].get("jump_context", 0) >= 1  # revisão errada do E01 (×1,5) visível em 2020-02-17
    assert not any(t.security_id == "E01" and t.origin == "2020-02-14" for t in tasks)


def test_baseline_forecasters_are_centered_and_ordered():
    context = TASKS[0].context
    for forecaster in (GaussianRandomWalk(), EmpiricalRandomWalk()):
        q = forecaster.predict(context, 21, LEVELS)
        assert q == sorted(q) and q[4] == pytest.approx(0.0, abs=1e-12)
    gaussian = GaussianRandomWalk().predict(context, 21, LEVELS)
    assert gaussian[0] == pytest.approx(-gaussian[-1])
    with pytest.raises(ValueError):
        EmpiricalRandomWalk().predict(context[:22], 21, LEVELS)


def test_evaluation_scores_a_perfect_forecast_as_zero_crps_and_full_ic():
    perfect = {t.key: [t.target_log_return] * len(LEVELS) for t in TASKS}
    ranking = {t.key: [t.target_exec_return] * len(LEVELS) for t in TASKS}
    base = {t.key: GaussianRandomWalk().predict(t.context, 21, LEVELS) for t in TASKS}
    design = {"alpha": 0.05, "power": 0.8, "min_detectable_relative_improvement": 0.05}
    out = evaluate_predictions(TASKS, perfect, LEVELS, baseline=base, design=design)
    assert out["crps"] == pytest.approx(0.0) and out["wql_price"] == pytest.approx(0.0)
    assert out["vs_baseline"]["mean_diff"] < 0 and out["vs_baseline"]["relative_improvement"] == pytest.approx(1.0)
    assert out["vs_baseline"]["n_required"] >= 1
    assert evaluate_predictions(TASKS, ranking, LEVELS)["rank_ic"]["mean"] == pytest.approx(1.0)


# -- previsões externas: proveniência obrigatória e sem lacunas --------------------------------------
MODEL = {"id": "amazon/chronos-bolt-small", "revision": "772f3d25d38aec6d914c8949dab4462e2d46f5d8",
         "weights_sha256": "06a6a19bbe74bc10a9cd193bd4bf2bf638ae07f7e0d51653ae7ab8ea968a21dd",
         "license": "apache-2.0", "license_verified_at": "2026-09-24", "weights_committed_at": "2024-11-13T13:28:57Z",
         "published_at": "2024-11-25T08:18:08Z", "source": "https://huggingface.co/amazon/chronos-bolt-small",
         "library": "chronos-forecasting", "library_version": "2.3.2"}


def external(model=MODEL, tasks=TASKS, value=lambda t: [t.target_exec_return + d for d in (-0.02, -0.01, -0.005,
                                                                                          -0.001, 0, 0.001, 0.005,
                                                                                          0.01, 0.02)]):
    return {"schema": "stocks-forecasts/1", "model": model, "horizon": 21, "levels": LEVELS,
            "tasks_sha256": tasks_sha256(TASKS),
            "entries": [{"security_id": t.security_id, "origin_session": t.origin, "quantiles": value(t)}
                        for t in tasks]}


def test_external_forecasts_require_provenance_and_exact_coverage():
    predictions, meta = load_forecasts(external(), TASKS, horizon=21, levels=LEVELS)
    assert len(predictions) == len(TASKS) and len(meta["forecasts_sha256"]) == 64
    with pytest.raises(ValueError, match="proveniência"):
        load_forecasts(external(model={**MODEL, "license": ""}), TASKS, horizon=21, levels=LEVELS)
    with pytest.raises(ValueError, match="faltam 1"):
        load_forecasts(external(tasks=TASKS[1:]), TASKS, horizon=21, levels=LEVELS)
    with pytest.raises(ValueError, match="outras tarefas"):
        load_forecasts(external() | {"tasks_sha256": "0" * 64}, TASKS, horizon=21, levels=LEVELS)
    with pytest.raises(ValueError, match="níveis"):
        load_forecasts(external() | {"levels": [0.5]}, TASKS, horizon=21, levels=LEVELS)
    raw = external()
    raw["entries"].append(copy.deepcopy(raw["entries"][0]))
    with pytest.raises(ValueError, match="duplicada"):
        load_forecasts(raw, TASKS, horizon=21, levels=LEVELS)


def test_contamination_status_uses_the_latest_of_weights_and_publication():
    assert contamination_status(None, TASKS, 10)["status"] == "NOT_APPLICABLE"
    late = {**MODEL, "published_at": "2030-01-01T00:00:00Z"}
    assert contamination_status(late, TASKS, 10)["status"] == "POTENTIALLY_CONTAMINATED"
    early = {**MODEL, "weights_committed_at": "2019-06-01T00:00:00Z", "published_at": "2019-06-02T00:00:00Z"}
    assert contamination_status(early, TASKS, 10)["status"] == "CLEAN_POST_CUTOFF"
    assert contamination_status(early, TASKS, 10 ** 6)["status"] == "INSUFFICIENT_SAMPLE"
    middle = {**MODEL, "weights_committed_at": "2020-09-01T00:00:00Z", "published_at": "2020-08-01T00:00:00Z"}
    status = contamination_status(middle, TASKS, 1)
    assert status["cutoff"] == "2020-09-01" and 0 < status["tasks_post_cutoff"] < len(TASKS)


# -- adaptador COTAHIST ------------------------------------------------------------------------------
def cotahist_zip(tmp_path, rows):
    lines = []
    for day, ticker, bdi, isin, close in rows:
        line = _pack(day, ticker, bdi, "010", close, close, close, close, 1000, close * 1000, 1)
        lines.append(line[:230] + isin.ljust(12) + line[242:])
    path = tmp_path / "COTAHIST_TEST.ZIP"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("COTAHIST_TEST.TXT", "00HEADER\n" + "\n".join(lines) + "\n99TRAILER\n")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_cotahist_adapter_builds_a_valid_pit_dataset_and_declares_limits(tmp_path):
    rows = [("2026-01-05", "AAAA3", "02", "BRAAAAACNOR1", 10.0), ("2026-01-05", "BOVA11", "14", "BRBOVACTF003", 100.0),
            ("2026-01-05", "OPCX1", "78", "BROPCXXXXX01", 1.0),
            ("2026-01-06", "AAAA3", "02", "BRAAAAACNOR1", 10.5), ("2026-01-06", "BOVA11", "14", "BRBOVACTF003", 101.0),
            ("2026-01-06", "NEWW3", "02", "BRNEWWACNOR2", 5.0),
            ("2026-01-07", "AAAB3", "02", "BRAAAAACNOR1", 10.4), ("2026-01-07", "BOVA11", "14", "BRBOVACTF003", 102.0),
            ("2026-01-08", "AAAB3", "02", "BRAAAAACNOR1", 10.6)]
    path, digest = cotahist_zip(tmp_path, rows)
    raw, meta = build_from_cotahist(path, expected_sha256=digest)
    ds = PITDataset(raw)
    assert ds.calendar == ["2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08"]
    assert meta["index_isin"] == "BRBOVACTF003" and meta["securities"] == 3 and meta["limitations"]
    assert ds.securities["BRBOVACTF003"]["kind"] == "index_fund"
    assert "BROPCXXXXX01" not in ds.securities  # opção (BDI 78) fora
    assert not ds.view("2026-01-06").listed("BRNEWWACNOR2") and ds.view("2026-01-07").listed("BRNEWWACNOR2")
    assert ds.view("2026-01-07").ticker("BRAAAAACNOR1") == "AAAA3"  # o novo ticker só se sabe à noite
    assert ds.view("2026-01-08").ticker("BRAAAAACNOR1") == "AAAB3"  # troca de ticker, mesmo ISIN
    with pytest.raises(CotahistError, match="sha256"):
        build_from_cotahist(path, expected_sha256="0" * 64)


# -- execução sob o ledger ---------------------------------------------------------------------------
def test_forecast_run_is_ledgered_with_contamination_and_rank_portfolio(tmp_path):
    ledger = TrialLedger(tmp_path / "ledger.jsonl")
    early = {**MODEL, "weights_committed_at": "2019-06-01T00:00:00Z", "published_at": "2019-06-02T00:00:00Z"}
    report = run_forecast_evaluation(DS, CONFIG, SPEC, POLICY, ledger, git=GIT,
                                     dataset_meta={"index_isin": "IDX11", "limitations": []},
                                     external=[external(model=early)])
    names = [row["candidate"] for row in report["table"]]
    model = "amazon/chronos-bolt-small@772f3d25d38a"
    assert names == ["gaussian_random_walk", "empirical_random_walk", model, "ew_universe", "index_buy_and_hold",
                     f"rank:{model}"]
    assert report["forecasts"][model]["contamination"]["status"] in ("CLEAN_POST_CUTOFF", "INSUFFICIENT_SAMPLE")
    assert report["forecasts"]["gaussian_random_walk"]["contamination"]["status"] == "NOT_APPLICABLE"
    kinds = [r["kind"] for r in ledger.records]
    assert kinds.count("STARTED") == kinds.count("COMPLETED") == 6 and kinds.count("DECISION") == 3
    assert all(row["decision"].startswith("NO_DECISION") for row in report["table"])
    assert report["portfolios"][f"rank:{model}"]["net"]["trades_filled"] > 0
    assert all(r["payload"]["manifest"]["validation"]["spec_sha256"] == report["spec_sha256"]
               for r in ledger.records if r["kind"] == "STARTED")


def test_forecast_cli_never_overwrites_and_spec_is_exact(tmp_path, capsys):
    output = tmp_path / "out.json"
    argv = ["--spec", str(DOCS / "synthetic-forecast-spec.json"), "--config", str(DOCS / "synthetic-demo-config.json"),
            "--dataset", "synthetic", "--policy", str(ROOT / "policy/stocks-evaluation-policy-v1.json"),
            "--ledger", str(tmp_path / "ledger.jsonl"), "--output", str(output)]
    assert main(argv) == 0 and json.loads(output.read_text())["tasks"]["tasks"] == STATS["tasks"]
    capsys.readouterr()
    with pytest.raises(SystemExit):
        main(argv)
    with pytest.raises(ValueError):
        load_spec(SPEC | {"extra": 1})
    with pytest.raises(ValueError, match="mediana"):
        load_spec(SPEC | {"levels": [0.1, 0.9]})


def test_real_spec_is_declared_and_pinned():
    real = load_spec(json.loads((DOCS / "prompt3c-real-forecast-spec.json").read_text()))
    assert real["source_sha256"].startswith("34b77468") and real["period_rule"] == "full_context_to_end"
    assert real["jump_threshold"] == 0.30 and real["baseline"] == "gaussian_random_walk"


def test_task_export_is_bound_to_the_exact_tasks(tmp_path, capsys):
    path = tmp_path / "tasks.json"
    argv = ["--spec", str(DOCS / "synthetic-forecast-spec.json"), "--config", str(DOCS / "synthetic-demo-config.json"),
            "--dataset", "synthetic", "--export-tasks", str(path)]
    assert main(argv) == 0
    payload = json.loads(path.read_text())
    assert payload["schema"] == "stocks-forecast-tasks/1" and payload["tasks_sha256"] == tasks_sha256(TASKS)
    assert len(payload["tasks"]) == len(TASKS) and payload["dataset_hash"] == DS.hash
    capsys.readouterr()
    with pytest.raises(FileExistsError):
        main(argv)
    with pytest.raises(SystemExit):  # avaliar exige política e ledger
        main(argv[:6])


def test_riskfree_from_the_raw_sgs_response_is_checked_against_its_receipt(tmp_path):
    rows = [{"data": "02/01/2020", "valor": "0.017089"}, {"data": "03/01/2020", "valor": "0.017089"}]
    raw = tmp_path / "sgs12.json"
    raw.write_text(json.dumps(rows))
    receipt = {"url": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json",
               "sha256": hashlib.sha256(raw.read_bytes()).hexdigest()}
    Path(str(raw) + ".receipt.json").write_text(json.dumps(receipt))
    rf = load_riskfree(f"bcb-sgs-12:{raw}")
    assert rf.series_id == "BCB-SGS-12" and rf.daily("2020-01-03") == pytest.approx(0.00017089)
    raw.write_text(json.dumps(rows[:1]))
    with pytest.raises(ValueError, match="recibo"):
        load_riskfree(f"bcb-sgs-12:{raw}")
