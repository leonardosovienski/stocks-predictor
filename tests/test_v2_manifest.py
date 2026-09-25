"""Protocolo v2 — RunManifest e TrialLedger: toda execução avaliativa registrada, inclusive falhas e crashes;
nada sobrescrito; cadeia de hashes verificada; linha ``trial-registry/2.0.0`` validada pelo core."""

import json
import re
from pathlib import Path

import pytest
from predictor_core.contracts.trial_v2 import require_trial_v2

from stocks_predictor.v2 import __main__ as cli
from stocks_predictor.v2 import manifest as manifest_module
from stocks_predictor.v2 import synthetic
from stocks_predictor.v2.baselines import EqualWeightUniverse, ForecastBaselines, RandomPortfolio
from stocks_predictor.v2.costs import CostModel, LiquidityRule
from stocks_predictor.v2.dataset import PITDataset
from stocks_predictor.v2.engine import ProtocolConfig, Strategy
from stocks_predictor.v2.execution import ExecutionConvention
from stocks_predictor.v2.manifest import (LedgerError, TrialLedger, build_manifest, git_state, host_id,
                                          ledger_index, run_evaluation)

DS = PITDataset(synthetic.build())
CONFIG = ProtocolConfig(start="2020-07-01", end="2020-12-30", rebalance="monthly", execution=ExecutionConvention(),
                        costs=CostModel(0.0, 0.0, 3.0, 7.5, 7.5, 0.0, 0.5, 0.0),
                        liquidity=LiquidityRule(1e6, 63, 0.05), seed=3)
GIT = {"commit": "0" * 40, "dirty": False}
REQUIRED = ("run_id", "git", "config", "config_hash", "dataset", "universe", "interval", "seed", "model", "costs",
            "execution", "validation", "policy_version", "engine_version")


class Boom(Strategy):
    name = "boom"

    def targets(self, ctx):
        raise RuntimeError("falha sintética da estratégia")


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_every_evaluative_run_writes_a_complete_manifest(tmp_path):
    ledger = TrialLedger(tmp_path / "ledger.jsonl")
    out = run_evaluation(ledger, DS, EqualWeightUniverse(), CONFIG, family="baselines", git=GIT,
                         validation={"scheme": "single_window", "horizon": 21})
    for key in REQUIRED:
        assert key in out
    assert out["trial_number"] == 1 and out["status"] == "COMPLETED"
    assert out["git"] == GIT and out["dataset"]["hash"] == DS.hash
    assert out["dataset"]["data_cutoff"] == DS.cutoff and out["universe"]["cutoff"] == DS.cutoff
    assert out["interval"] == {"start": "2020-07-01", "end": "2020-12-30", "rebalance": "monthly"}
    assert out["execution"]["lag_sessions"] == 1 and out["costs"]["exchange_fee_bps"] == 3.0
    assert out["metrics"]["net"]["total_return"] == out["metrics"]["net"]["total_return"]
    records = lines(tmp_path / "ledger.jsonl")
    assert [r["kind"] for r in records] == ["STARTED", "COMPLETED"]
    row = records[1]["payload"]["trial_v2"]
    assert require_trial_v2(row) == row
    assert row["dataset_hash"] == "sha256:" + DS.hash and row["code_version"] == "git:" + "0" * 40
    assert row["n_trials_family"] == 1 and row["n_trials_domain"] == "known_trials >= 72"
    assert records[1]["payload"]["result"]["result_digest"] == out["metrics"]["result_digest"]


def test_failed_runs_are_recorded_counted_and_reraised(tmp_path):
    ledger = TrialLedger(tmp_path / "ledger.jsonl")
    with pytest.raises(RuntimeError, match="falha sintética"):
        run_evaluation(ledger, DS, Boom(), CONFIG, family="baselines", git=GIT)
    out = run_evaluation(ledger, DS, EqualWeightUniverse(), CONFIG, family="baselines", git=GIT)
    records = lines(tmp_path / "ledger.jsonl")
    assert [r["kind"] for r in records] == ["STARTED", "FAILED", "STARTED", "COMPLETED"]
    assert records[1]["payload"]["error_type"] == "RuntimeError"
    assert require_trial_v2(records[1]["payload"]["trial_v2"])["status"] == "FAILED"
    assert out["trial_number"] == 2  # o trial que falhou conta


def test_crash_leaves_a_started_record_that_becomes_abandoned(tmp_path, monkeypatch):
    path = tmp_path / "ledger.jsonl"
    crashed = build_manifest(DS, EqualWeightUniverse(), CONFIG, validation={"scheme": "single_window"},
                             family="baselines", git=GIT)
    TrialLedger(path).start(crashed)  # processo "morre" aqui: sem desfecho
    monkeypatch.setattr(manifest_module, "_alive", lambda pid: False)
    ledger = TrialLedger(path)
    assert [r["run_id"] for r in ledger.open_runs()] == [crashed["run_id"]]
    out = run_evaluation(ledger, DS, RandomPortfolio(3), CONFIG, family="baselines", git=GIT)
    assert ledger.outcome(crashed["run_id"]) == "ABANDONED"
    assert out["trial_number"] == 2
    assert [r["kind"] for r in lines(path)] == ["STARTED", "ABANDONED", "STARTED", "COMPLETED"]


def test_live_concurrent_run_is_not_marked_abandoned(tmp_path):
    path = tmp_path / "ledger.jsonl"
    running = build_manifest(DS, EqualWeightUniverse(), CONFIG, validation={}, family="baselines", git=GIT)
    first = TrialLedger(path)
    first.start(running)  # este processo está vivo
    second = TrialLedger(path)
    assert second.recover_abandoned() == []
    run_evaluation(second, DS, RandomPortfolio(3), CONFIG, family="baselines", git=GIT)
    first.complete(running["run_id"], {"note": "terminou depois"}, {"status": "COMPLETED"})
    assert TrialLedger(path).outcome(running["run_id"]) == "COMPLETED"


def test_nothing_is_overwritten(tmp_path):
    ledger = TrialLedger(tmp_path / "ledger.jsonl")
    manifest = build_manifest(DS, EqualWeightUniverse(), CONFIG, validation={}, family="baselines", git=GIT)
    ledger.start(manifest)
    with pytest.raises(LedgerError, match="já registrado"):
        ledger.start(manifest)
    with pytest.raises(LedgerError, match="não está em andamento"):
        ledger.complete("inexistente", {}, {})


@pytest.mark.parametrize("damage", ["edit", "drop", "truncate", "reorder"])
def test_ledger_is_tamper_evident(tmp_path, damage):
    path = tmp_path / "ledger.jsonl"
    ledger = TrialLedger(path)
    for _ in range(2):
        run_evaluation(ledger, DS, EqualWeightUniverse(), CONFIG, family="baselines", git=GIT)
    text = path.read_text().splitlines(keepends=True)
    if damage == "edit":
        text[1] = text[1].replace('"COMPLETED"', '"FAILED"', 1)
    elif damage == "drop":
        del text[1]
    elif damage == "truncate":
        text[-1] = text[-1][:-5]
    else:
        text[0], text[1] = text[1], text[0]
    path.write_text("".join(text))
    with pytest.raises(LedgerError):
        TrialLedger(path)
    with pytest.raises(LedgerError):
        ledger.start(build_manifest(DS, EqualWeightUniverse(), CONFIG, validation={}, family="x", git=GIT))


def test_git_state_is_real_or_unknown(tmp_path):
    state = git_state()
    assert re.fullmatch(r"[0-9a-f]{40}", state["commit"]) and isinstance(state["dirty"], bool)
    assert git_state(tmp_path / "nao-existe") == {"commit": "UNKNOWN", "dirty": None}


def test_unknown_git_falls_back_to_package_identity(tmp_path):
    ledger = TrialLedger(tmp_path / "ledger.jsonl")
    run_evaluation(ledger, DS, EqualWeightUniverse(), CONFIG, family="baselines",
                   git={"commit": "UNKNOWN", "dirty": None})
    row = lines(tmp_path / "ledger.jsonl")[-1]["payload"]["trial_v2"]
    assert row["code_version"].startswith("package:stocks-predictor==")


DEMO_CONFIG = Path(__file__).resolve().parents[1] / "docs/engineering/2026-09-24-protocol-v2/synthetic-demo-config.json"


def test_cli_runs_every_baseline_as_a_ledgered_evaluation(tmp_path, capsys):
    ledger, output = tmp_path / "ledger.jsonl", tmp_path / "summary.json"
    argv = ["--config", str(DEMO_CONFIG), "--dataset", "synthetic", "--ledger", str(ledger), "--output", str(output)]
    assert cli.main(argv) == 0
    summary = json.loads(output.read_text())
    assert set(summary["results"]) == {"ew_universe", "index_buy_and_hold", "momentum_12_1", "random_5",
                                       "forecast_baselines_h21"}
    assert [r["trial_number"] for r in summary["results"].values()] == [1, 2, 3, 4, 5]
    assert summary["dataset"]["hash"] == DS.hash and summary["ledger"]["records"] == 10
    for name, row in summary["results"].items():
        if "net" in row:
            assert row["net"]["total_return"] <= row["gross_total_return"], name
    records = lines(ledger)
    assert [r["kind"] for r in records] == ["STARTED", "COMPLETED"] * 5
    for record in records[1::2]:
        require_trial_v2(record["payload"]["trial_v2"])
    capsys.readouterr()
    with pytest.raises(SystemExit):  # saída existente nunca é sobrescrita
        cli.main(argv)
    assert len(lines(ledger)) == 10


def test_cli_config_must_be_explicit_and_exact():
    raw = json.loads(DEMO_CONFIG.read_text())
    cli.load_config(raw)
    with pytest.raises(ValueError, match="campos exatos"):
        cli.load_config(raw | {"surprise": 1})
    del raw["costs"]["spread_bps"]
    with pytest.raises(ValueError):
        cli.load_config(raw)


def test_forecast_runner_rejects_portfolio_strategies():
    with pytest.raises(TypeError):
        ForecastBaselines.runner(DS, EqualWeightUniverse(), CONFIG)
    with pytest.raises(NotImplementedError):
        ForecastBaselines(21).targets(None)


def test_dirty_checkout_is_recorded(tmp_path):
    ledger = TrialLedger(tmp_path / "ledger.jsonl")
    out = run_evaluation(ledger, DS, EqualWeightUniverse(), CONFIG, family="baselines",
                         git={"commit": "1" * 40, "dirty": True})
    row = lines(tmp_path / "ledger.jsonl")[-1]["payload"]["trial_v2"]
    assert out["git"]["dirty"] is True and row["code_version"].endswith(";dirty")


def test_ledger_never_writes_the_host_name(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger = TrialLedger(path, host="MAQUINA-PESSOAL-XYZ")
    run_evaluation(ledger, DS, EqualWeightUniverse(), CONFIG, family="baselines", git=GIT)
    text = path.read_text()
    assert "MAQUINA-PESSOAL-XYZ" not in text and host_id("MAQUINA-PESSOAL-XYZ") in text


def test_legacy_records_with_host_name_are_still_recognized(tmp_path, monkeypatch):
    path = tmp_path / "ledger.jsonl"
    legacy = TrialLedger(path, host="antigo")
    manifest = build_manifest(DS, EqualWeightUniverse(), CONFIG, validation={}, family="baselines", git=GIT)
    legacy._append("STARTED", manifest["run_id"], {"trial_number": 1, "manifest": manifest,
                                                   "process": {"host": "antigo", "pid": 999999}})
    monkeypatch.setattr(manifest_module, "_alive", lambda pid: False)
    assert TrialLedger(path, host="outro").recover_abandoned() == []  # outro host: não é crash deste
    assert TrialLedger(path, host="antigo").recover_abandoned() == [manifest["run_id"]]


def test_ledger_index_is_verifiable_and_free_of_process_data(tmp_path):
    ledger = TrialLedger(tmp_path / "ledger.jsonl")
    run_evaluation(ledger, DS, EqualWeightUniverse(), CONFIG, family="baselines", git=GIT)
    index = ledger_index(ledger)
    assert index["records"] == 2 and index["head"] == ledger.records[-1]["hash"]
    assert [r["hash"] for r in index["rows"]] == [r["hash"] for r in ledger.records]
    assert index["counts"] == {"STARTED": 1, "COMPLETED": 1} and index["trials_started"] == 1
    assert "process" not in json.dumps(index) and index["rows"][0]["model"] == "ew_universe"
    out = tmp_path / "index.json"
    assert manifest_module.main(["index", "--ledger", str(tmp_path / "ledger.jsonl"), "--output", str(out)]) == 0
    with pytest.raises(FileExistsError):
        manifest_module.main(["index", "--ledger", str(tmp_path / "ledger.jsonl"), "--output", str(out)])
