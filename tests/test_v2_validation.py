"""Protocolo v2 — validação estatística (Prompt 3b): CPCV com purge/embargo, IC/Rank IC, métricas em excesso da
taxa livre de risco, PSR/DSR, PBO por CSCV e política de decisão versionada."""

import copy
import itertools
import json
import math
import random
from pathlib import Path

import pytest
from predictor_core.measurement.stats import probabilistic_sharpe_ratio
from predictor_core.measurement.trials import DeflationNotEstimableError, expected_max_sharpe

from stocks_predictor.v2 import synthetic
from stocks_predictor.v2.baselines import EqualWeightUniverse, Momentum12_1, forward_return
from stocks_predictor.v2.costs import CostModel, LiquidityRule
from stocks_predictor.v2.cpcv import (assert_no_leakage, block_spans, cpcv_paths, cpcv_splits,
                                      derive_purge_embargo, label_samples, run_cpcv)
from stocks_predictor.v2.dataset import PITDataset
from stocks_predictor.v2.engine import ProtocolConfig, run_backtest
from stocks_predictor.v2.execution import ExecutionConvention
from stocks_predictor.v2.factor_metrics import average_ranks, cross_section, pearson, spearman
from stocks_predictor.v2.manifest import LedgerError, TrialLedger
from stocks_predictor.v2.metrics import (NetSeries, beta_alpha, dsr_sensitivity, n_trials_grid, psr_from_moments,
                                         strategy_report)
from stocks_predictor.v2.pbo import pbo_cscv
from stocks_predictor.v2.policy import PolicyError, decide, load_policy
from stocks_predictor.v2.preregistration import PREREG_FIELDS, preregister
from stocks_predictor.v2.riskfree import RiskFreeError, RiskFreeSeries, excess_returns
from stocks_predictor.v2.validation import load_spec, main, run_validation
from stocks_predictor.v2.walkforward import LeakageError

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "policy/stocks-evaluation-policy-v1.json"
DOCS = ROOT / "docs/engineering/2026-09-24-protocol-v2"
DS = PITDataset(synthetic.build())
RF = RiskFreeSeries(synthetic.riskfree())
CONFIG = ProtocolConfig(start="2020-01-02", end="2021-06-30", rebalance="monthly", execution=ExecutionConvention(),
                        costs=CostModel(0.0, 0.0, 3.0, 7.5, 7.5, 0.0, 0.5, 0.0),
                        liquidity=LiquidityRule(1e6, 63, 0.05), seed=7)


def rf_series(annual: float, sessions: list[str], series_id: str = "BCB-SGS-12") -> RiskFreeSeries:
    return RiskFreeSeries({"schema": "stocks-riskfree/1", "series_id": series_id, "unit": "percent_per_year_252",
                           "source": {"kind": "test"}, "rates": [{"session": s, "rate": annual} for s in sessions]})


def approved_policy(tmp_path, **changes):
    """Cópia da política real com status APPROVED (só limiares do arquivo; nada no código)."""
    raw = json.loads(POLICY.read_text())
    raw["status"] = "APPROVED"
    for section, values in changes.items():
        raw[section] = raw[section] | values
    path = tmp_path / "approved-policy.json"
    path.write_text(json.dumps(raw))
    return load_policy(path)


def permissive_policy(tmp_path, **changes):
    raw = json.loads(POLICY.read_text())
    raw["status"] = "APPROVED"
    raw["data"] = {"forbid_synthetic_dataset": False, "min_sessions": 100}
    raw["risk_free"]["allowed_series"].append("SYNTHETIC-RF")
    raw["pbo"]["n_splits"] = 4
    for section, values in changes.items():
        raw[section] = raw[section] | values
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(raw))
    return load_policy(path)


# -- obrigatório: purge/embargo ------------------------------------------------------------------
def test_overlapping_labels_leak_without_purge_and_never_with_it():
    samples = label_samples(list(range(200)), lag=1, horizon=21)  # rótulos de 22 pregões se sobrepõem
    naive_train = [i for i in range(200) if not 80 <= i < 120]
    assert any(samples[i].t0 <= samples[j].t1 and samples[i].t1 >= samples[j].t0
               for i in naive_train for j in range(80, 120))  # sem purge há vazamento
    splits = cpcv_splits(samples, 6, 2, embargo=5)
    assert len(splits) == math.comb(6, 2)
    for split in splits:
        parts = [set(split.train), set(split.test), set(split.purged), set(split.embargoed)]
        assert set().union(*parts) == set(range(200)) and sum(map(len, parts)) == 200
        for i in split.train:
            for j in split.test:
                assert not (samples[i].t0 <= samples[j].t1 and samples[i].t1 >= samples[j].t0)
        for _start, end in block_spans(samples, list(split.test)):
            assert not any(end < samples[i].t0 <= end + 5 for i in split.train)
        assert split.purged  # a sobreposição existia e foi removida


def test_leakage_guard_rejects_a_leaking_split():
    samples = label_samples(list(range(20)), lag=1, horizon=5)
    split = cpcv_splits(samples, 4, 1, embargo=2)[1]
    leaking = type(split)(split.index, split.test_groups, tuple(sorted(split.train + split.purged)), split.test,
                          (), split.embargoed)
    with pytest.raises(LeakageError, match="cruza"):
        assert_no_leakage(samples, leaking, 2)
    embargo_leak = type(split)(split.index, split.test_groups, tuple(sorted(split.train + split.embargoed)),
                               split.test, split.purged, ())
    with pytest.raises(LeakageError, match="embargo"):
        assert_no_leakage(samples, embargo_leak, 2)


def test_purge_and_embargo_sizes_are_derived_not_chosen():
    rng = random.Random(3)
    noise = [rng.gauss(0, 1) for _ in range(200)]
    persistent = [0.0]
    for _ in range(199):
        persistent.append(0.9 * persistent[-1] + rng.gauss(0, 1))
    white = derive_purge_embargo(21, 1, 21, noise)
    ar = derive_purge_embargo(21, 1, 21, persistent)
    assert white["purge_size"] == ar["purge_size"] == 22
    assert white["embargo_size"] == 0 and white["first_insignificant_lag"] == 1
    assert ar["embargo_size"] > 0 and ar["embargo_size"] % 21 == 0
    assert derive_purge_embargo(21, 1, 21, persistent, max_lag=2)["max_lag_exhausted"] is True


def test_cpcv_paths_cover_every_group_once():
    for n, k in ((6, 2), (5, 3), (4, 1)):
        paths = cpcv_paths(n, k)
        assert len(paths) == math.comb(n - 1, k - 1)
        splits = list(itertools.combinations(range(n), k))
        for path in paths:
            assert [g for g, _s in path] == list(range(n))
            assert all(g in splits[s] for g, s in path)


def test_run_cpcv_fits_only_on_train_and_assembles_full_paths():
    samples = label_samples(list(range(0, 120, 5)), lag=1, horizon=10)
    seen = []

    def fit_predict(train, test):
        assert not set(train) & set(test)
        seen.append(len(train))
        mean = sum(train) / len(train)
        return {i: i - mean for i in test}

    out = run_cpcv(samples, 6, 2, embargo=5, fit_predict=fit_predict, performance=lambda xs: float(len(xs)))
    assert out["n_splits"] == 15 and out["n_paths"] == 5
    assert all(p["n"] == len(samples) for p in out["paths"])
    assert all(s["purged"] > 0 for s in out["splits"])
    with pytest.raises(ValueError, match="exatamente"):
        run_cpcv(samples, 6, 2, embargo=5, fit_predict=lambda tr, te: {}, performance=len)


# -- obrigatório: DSR mais conservador com N maior -------------------------------------------------
def test_dsr_is_more_conservative_with_more_trials():
    rng = random.Random(11)
    excess = [0.0006 + rng.gauss(0, 0.01) for _ in range(750)]
    trials = [rng.gauss(0.02, 0.02) for _ in range(20)]
    out = dsr_sensitivity(excess, trials, n_trials_grid(71, [1, 2, 5], 150))
    values = [row["dsr"] for row in out["rows"]]
    assert [row["n"] for row in out["rows"]] == [71, 142, 150, 355]
    assert all(b < a for a, b in zip(values, values[1:]))
    assert out["worst"]["n"] == 355
    with pytest.raises(DeflationNotEstimableError):
        dsr_sensitivity(excess, [0.1, None], [71])


# -- obrigatório: valores conferidos contra exemplo publicado ou cálculo à mão ------------------
def test_dsr_matches_the_published_numerical_example():
    """Bailey & López de Prado (2014), exemplo numérico: SR anual 2,5 em T = 1250 observações diárias (250/ano),
    N = 100 tentativas, V[SR] anual = 1/2, γ3 = −3, γ4 = 10 → E[max SR] ≈ 0,1132 (diário) e DSR ≈ 0,9004."""
    sr0 = expected_max_sharpe(100, 0.5 / 250)
    assert sr0 == pytest.approx(0.1132, abs=5e-5)
    dsr = psr_from_moments(2.5 / math.sqrt(250), 1250, -3.0, 10.0, benchmark=sr0)
    assert dsr == pytest.approx(0.9004, abs=1e-3)


def test_psr_from_moments_agrees_with_the_core_on_a_series():
    rng = random.Random(5)
    xs = [rng.gauss(0.001, 0.01) + (0.03 if rng.random() < 0.02 else 0.0) for _ in range(500)]
    n = len(xs)
    mean = sum(xs) / n
    m2 = sum((x - mean) ** 2 for x in xs) / n
    skew = sum((x - mean) ** 3 for x in xs) / n / m2 ** 1.5
    kurt = sum((x - mean) ** 4 for x in xs) / n / m2 ** 2
    local = psr_from_moments(mean / math.sqrt(m2), n, skew, kurt, benchmark=0.01)
    assert local == pytest.approx(probabilistic_sharpe_ratio(xs, 0.01), abs=1e-12)


def test_ic_and_rank_ic_hand_computed():
    # Spearman sem empates: d = (−1, 1, −1, 1, 0), Σd² = 4 → 1 − 6·4/(5·24) = 0,8
    assert spearman([1, 2, 3, 4, 5], [2, 1, 4, 3, 5]) == pytest.approx(0.8)
    # Pearson: x = (1, 2, 3), y = (1, 3, 2) → Sxy = 1, Sxx = Syy = 2 → 0,5
    assert pearson([1, 2, 3], [1, 3, 2]) == pytest.approx(0.5)
    # empates: postos de x = (1; 2,5; 2,5; 4) → Sxy = 4,5; Sxx = 4,5; Syy = 5 → 4,5/√22,5 = 0,948683
    assert average_ranks([1, 2, 2, 3]) == [1, 2.5, 2.5, 4]
    assert spearman([1, 2, 2, 3], [1, 2, 3, 4]) == pytest.approx(4.5 / math.sqrt(22.5))
    assert pearson([1, 1, 1], [1, 2, 3]) is None


def test_pbo_hand_computed_example():
    """T = 4, S = 4 blocos de 1 linha, desempenho = média. A = (3, −1, 2, −2), B = 0,6 constante.
    IS {0,1}: A → OOS A=0 < B: ω=1/3; {0,2}: A → OOS −1,5: 1/3; {0,3}: B (0,5 < 0,6) → OOS A=0,5: B no topo, 2/3;
    {1,2}: B → OOS A=0,5: 2/3; {1,3}: B → OOS A=2,5: 1/3; {2,3}: B → OOS A=1: 1/3. PBO = 4/6."""
    matrix = [[3, 0.6], [-1, 0.6], [2, 0.6], [-2, 0.6]]
    out = pbo_cscv(matrix, 4, performance=lambda xs: sum(xs) / len(xs))
    assert out["combinations"] == 6
    assert out["pbo"] == pytest.approx(4 / 6)
    assert sorted(round(x, 6) for x in out["logits"]) == [round(math.log(0.5), 6)] * 4 + [round(math.log(2), 6)] * 2


def test_pbo_properties():
    rng = random.Random(9)
    dominant = [[1.0 + rng.gauss(0, 0.1), rng.gauss(0, 0.1), rng.gauss(0, 0.1)] for _ in range(64)]
    assert pbo_cscv(dominant, 8)["pbo"] == 0.0
    # Ruído puro: o posto OOS do vencedor IS é uniforme → E[PBO] = 0,5. Uma matriz isolada varia muito (desvio
    # medido de 0,22 em 200 matrizes 80×10), então o teste usa a média de 30 matrizes independentes
    # (desvio ≈ 0,22/√30 ≈ 0,04): 0,5 ± 0,15 é mais de 3,5 desvios.
    values = []
    for seed in range(30):
        g = random.Random(seed)
        values.append(pbo_cscv([[g.gauss(0, 1) for _ in range(10)] for _ in range(80)], 8)["pbo"])
    assert 0.35 < sum(values) / len(values) < 0.65
    noise = [[rng.gauss(0, 1) for _ in range(4)] for _ in range(16)]
    with pytest.raises(ValueError):
        pbo_cscv(noise, 3)
    with pytest.raises(ValueError):
        pbo_cscv([[1.0], [2.0]], 2)


def test_beta_alpha_hand_computed():
    x = [0.01, -0.02, 0.015, 0.0, 0.005]
    out = beta_alpha([2 * v + 0.001 for v in x], x, 252)
    assert out["beta"] == pytest.approx(2) and out["alpha_per_period"] == pytest.approx(0.001)
    assert out["alpha_ann"] == pytest.approx(0.252) and out["r2"] == pytest.approx(1)


def test_cross_section_ic_is_one_for_an_oracle_scorer():
    """Escore = o próprio retorno realizado (só possível em teste): IC e Rank IC têm de ser 1. Um desalinhamento
    entre escore e rótulo (pregão, horizonte ou execução) quebraria esta igualdade."""
    config = CONFIG
    cal = DS.calendar

    def oracle(view, universe):
        start = DS.position(view.session) - 1 + config.execution.lag_sessions
        return {sid: r for sid in universe if (r := forward_return(DS, sid, start, 21, "open")) is not None}

    out = cross_section(DS, config, oracle, [21, 63])
    assert out["summary"][21]["ic"]["mean"] == pytest.approx(1)
    assert out["summary"][21]["rank_ic"]["mean"] == pytest.approx(1)
    q = out["quantile_mean_returns"]
    assert all(a < b for a, b in zip(q, q[1:]))
    assert out["long_short"]["mean"] > 0 and out["summary"][63]["rank_ic"]["n"] < out["summary"][21]["rank_ic"]["n"]
    assert all(p["signal_session"] < p["execution_session"] for p in out["periods"])
    assert all(DS.position(p["execution_session"]) + 21 <= DS.position(config.end) for p in out["periods"])
    assert cal[0] < out["periods"][0]["signal_session"]


# -- obrigatório: Sharpe usa a taxa livre de risco configurada --------------------------------------
def test_sharpe_uses_the_configured_risk_free_rate():
    result = NetSeries.from_result(run_backtest(DS, EqualWeightUniverse(), CONFIG))
    high, zero = rf_series(12.0, DS.calendar), rf_series(0.0, DS.calendar)
    with_rf, without = strategy_report(result, high), strategy_report(result, zero)
    daily = 1.12 ** (1 / 252) - 1
    excess = [r - daily for r in result.returns]
    mean = sum(excess) / len(excess)
    sd = math.sqrt(sum((x - mean) ** 2 for x in excess) / (len(excess) - 1))
    assert with_rf["sharpe_excess_ann"] == pytest.approx(mean / sd * math.sqrt(252))
    assert with_rf["sharpe_excess_ann"] < without["sharpe_excess_ann"] - 0.5
    assert with_rf["risk_free"]["series_id"] == "BCB-SGS-12"


def test_risk_free_series_fails_closed():
    assert RiskFreeSeries({"schema": "stocks-riskfree/1", "series_id": "X", "unit": "percent_per_day",
                           "source": {"k": 1}, "rates": [{"session": "2020-01-02", "rate": 0.04}]}
                          ).daily("2020-01-02") == pytest.approx(0.0004)
    with pytest.raises(RiskFreeError, match="sem taxa"):
        excess_returns(["2020-01-03"], [0.01], rf_series(10.0, ["2020-01-02"]))
    raw = synthetic.riskfree()
    bad = copy.deepcopy(raw)
    bad["rates"][3], bad["rates"][4] = bad["rates"][4], bad["rates"][3]
    with pytest.raises(RiskFreeError, match="ordenadas"):
        RiskFreeSeries(bad)
    with pytest.raises(RiskFreeError):
        RiskFreeSeries(raw | {"unit": "percent_per_month"})
    with pytest.raises(RiskFreeError):
        RiskFreeSeries(raw | {"source": {}})


# -- obrigatório: sem baseline → NO_DECISION --------------------------------------------------------
def evidence(**overrides):
    base = {"dataset_version": "real-v1", "risk_free_series_id": "BCB-SGS-12", "sessions": 800,
            "strategy": {"sharpe_excess_ann": 1.2, "psr_vs_zero": 0.99},
            "baselines": {"ew_universe": {"sharpe_excess_ann": 0.5}, "index_buy_and_hold": {"sharpe_excess_ann": 0.4}},
            "dsr": {"worst": {"n": 355, "dsr": 0.97}}, "pbo": {"pbo": 0.1}, "t_stat": 3.5}
    return base | overrides


def test_no_baseline_means_no_decision():
    policy = load_policy(POLICY)
    out = decide(evidence(baselines={}), policy)
    assert out["decision"] == "NO_DECISION"
    assert any("sem comparação com baseline" in r for r in out["no_decision_reasons"])
    partial = decide(evidence(baselines={"ew_universe": {"sharpe_excess_ann": 0.5}}), policy)
    assert partial["decision"] == "NO_DECISION"


def test_unapproved_policy_never_decides_but_records_what_it_would_decide():
    proposed = load_policy(POLICY)
    out = decide(evidence(), proposed)
    assert proposed.status == "PROPOSED_PENDING_OWNER_APPROVAL"
    assert out["decision"] == "NO_DECISION" and out["decision_if_approved"] == "PASS"
    assert any("não aprovados pelo dono" in r for r in out["no_decision_reasons"])
    assert out["checks"] and out["policy_path"] == "policy/stocks-evaluation-policy-v1.json"
    assert decide(evidence(pbo={"pbo": 0.5}), proposed)["decision_if_approved"] == "REJECT"


def test_policy_decisions_carry_version_and_hash_and_use_file_thresholds(tmp_path):
    policy = approved_policy(tmp_path)
    ok = decide(evidence(), policy)
    assert ok["decision"] == "PASS" and ok["policy_version"] == "1.0.0" and ok["no_decision_reasons"] == []
    assert len(ok["policy_sha256"]) == 64 and ok["policy_status"] == "APPROVED"
    assert decide(evidence(pbo={"pbo": 0.5}), policy)["decision"] == "REJECT"
    assert decide(evidence(dsr={"worst": {"n": 355, "dsr": 0.5}}), policy)["failed"] == ["dsr_worst_case"]
    assert decide(evidence(strategy={"sharpe_excess_ann": 0.45, "psr_vs_zero": 0.99}), policy)["failed"] == \
        ["beats:ew_universe"]
    for reason, change in (("sintético", {"dataset_version": "synthetic-x"}),
                           ("não admitida", {"risk_free_series_id": "SYNTHETIC-RF"}),
                           ("pregões", {"sessions": 100}), ("DSR", {"dsr": None}), ("PBO", {"pbo": None})):
        out = decide(evidence(**change), policy)
        assert out["decision"] == "NO_DECISION" and any(reason in r for r in out["no_decision_reasons"])
    stricter = permissive_policy(tmp_path, pbo={"max": 0.05})
    assert decide(evidence(), stricter)["decision"] == "REJECT"  # limiar vem do arquivo, não do código
    assert stricter.sha256 != policy.sha256
    gate = permissive_policy(tmp_path, t_stat={"role": "gate"})
    assert decide(evidence(t_stat=2.0), gate)["decision"] == "REJECT"
    assert decide(evidence(t_stat=2.0), policy)["decision"] == "PASS"  # diagnóstico não bloqueia


def test_retired_policy_never_decides(tmp_path):
    raw = json.loads(POLICY.read_text()) | {"status": "RETIRED"}
    path = tmp_path / "retired-policy.json"
    path.write_text(json.dumps(raw))
    out = decide(evidence(), load_policy(path))
    assert out["decision"] == "NO_DECISION" and out["decision_if_approved"] == "PASS"
    assert any("aposentada" in r for r in out["no_decision_reasons"])


def test_policy_file_is_validated(tmp_path):
    raw = json.loads(POLICY.read_text())
    for broken in ({**raw, "extra": 1}, {**raw, "status": "MAYBE"}, {**raw, "psr": {**raw["psr"], "min_probability": 2}},
                   {**raw, "t_stat": {**raw["t_stat"], "role": "maybe"}},
                   {**raw, "dsr": {**raw["dsr"], "aggregation": "best_case"}}):
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(broken))
        with pytest.raises(PolicyError):
            load_policy(path)


def test_trial_grid_matches_the_audit():
    assert n_trials_grid(71, [1, 2, 5], 150) == [71, 142, 150, 355]


# -- ponta a ponta sob o ledger ---------------------------------------------------------------------
SPEC = json.loads((DOCS / "synthetic-validation-spec.json").read_text())


def test_validation_on_synthetic_data_is_ledgered_and_refuses_to_decide(tmp_path):
    ledger = TrialLedger(tmp_path / "ledger.jsonl")
    report = run_validation(DS, CONFIG, RF, load_policy(POLICY), ledger, load_spec(SPEC),
                            git={"commit": "0" * 40, "dirty": False})
    assert report["decision"]["decision"] == "NO_DECISION"
    assert any("sintético" in r for r in report["decision"]["no_decision_reasons"])
    records = ledger.records
    kinds = [r["kind"] for r in records]
    assert kinds.count("STARTED") == kinds.count("COMPLETED") == 8 and kinds[-1] == "DECISION"
    started = [r for r in records if r["kind"] == "STARTED"]
    assert all(r["payload"]["manifest"]["decision_policy"]["policy_sha256"] == report["policy"]["policy_sha256"]
               for r in started)
    assert all(r["payload"]["manifest"]["validation"]["risk_free"]["hash"] == RF.hash for r in started)
    assert records[-1]["payload"]["evaluated_run_ids"] == report["run_ids"]
    assert report["n_trials"]["grid"][0] == 71 + 8
    assert report["purge_embargo"]["purge_size"] == 22 and report["cpcv"]["n_paths"] == 5
    assert report["candidate_report"]["vs_benchmark"]["benchmark"] == "index_buy_and_hold"


def test_validation_with_a_permissive_policy_reaches_a_decision(tmp_path):
    policy = permissive_policy(tmp_path)
    ledger = TrialLedger(tmp_path / "ledger.jsonl")
    report = run_validation(DS, CONFIG, RF, policy, ledger, load_spec(SPEC), git={"commit": "0" * 40, "dirty": False})
    assert report["decision"]["decision"] in ("PASS", "REJECT")
    assert {c["gate"] for c in report["decision"]["checks"]} == {"beats:ew_universe", "beats:index_buy_and_hold",
                                                                "psr", "dsr_worst_case", "pbo"}
    assert report["pbo"]["n_splits"] == 4


def test_decision_records_require_completed_runs(tmp_path):
    ledger = TrialLedger(tmp_path / "ledger.jsonl")
    with pytest.raises(LedgerError, match="sem execução concluída"):
        ledger.record_decision({"decision": "NO_DECISION", "policy_sha256": "x"}, ["nope"])
    with pytest.raises(LedgerError, match="política"):
        ledger.record_decision({"decision": "NO_DECISION"}, [])


def test_validation_cli_never_overwrites(tmp_path, capsys):
    output = tmp_path / "out.json"
    argv = ["--config", str(DOCS / "synthetic-demo-config.json"), "--validation",
            str(DOCS / "synthetic-validation-spec.json"), "--dataset", "synthetic", "--riskfree", "synthetic",
            "--policy", str(POLICY), "--ledger", str(tmp_path / "ledger.jsonl"), "--output", str(output)]
    assert main(argv) == 0
    assert json.loads(output.read_text())["decision"]["decision"] == "NO_DECISION"
    capsys.readouterr()
    with pytest.raises(SystemExit):
        main(argv)


def test_validation_spec_is_exact_and_candidate_is_predeclared():
    with pytest.raises(ValueError, match="campos exatos"):
        load_spec(SPEC | {"extra": 1})
    with pytest.raises(ValueError, match="pré-declarado"):
        load_spec(SPEC | {"candidate": {"lookback": 100, "skip": 10}})
    assert Momentum12_1().name == "momentum_12_1" and Momentum12_1(189, 21).name == "momentum_189_21"


def preregistered(ledger, max_variants):
    record = {k: f"valor de {k}" for k in PREREG_FIELDS}
    record |= {"hypothesis_id": "stocks:NEW-001", "policy": {"version": "1.0.0", "sha256": "0" * 64},
               "max_variants": max_variants, "seeds": [7], "secondary_metrics": ["ic"],
               "criteria": {"GO": "a", "NO_GO": "b", "NO_DECISION": "c"}}
    return preregister(ledger, record)


def test_validation_cli_ties_the_family_to_a_preregistered_hypothesis(tmp_path):
    """Cada configuração da família é uma variante: sem pré-registro nada da família roda; além de max_variants, para."""
    ledger = tmp_path / "ledger.jsonl"
    argv = ["--config", str(DOCS / "synthetic-demo-config.json"), "--validation",
            str(DOCS / "synthetic-validation-spec.json"), "--dataset", "synthetic", "--riskfree", "synthetic",
            "--policy", str(POLICY), "--ledger", str(ledger), "--hypothesis-id", "stocks:NEW-001"]
    with pytest.raises(LedgerError, match="sem pré-registro"):
        main(argv)
    assert all(not r["payload"]["manifest"].get("preregistration") for r in TrialLedger(ledger).started())
    preregistered(TrialLedger(ledger), max_variants=2)
    with pytest.raises(LedgerError, match="limite pré-registrado de 2"):
        main(argv)
    tied = [r["payload"]["manifest"]["preregistration"] for r in TrialLedger(ledger).started()
            if r["payload"]["manifest"].get("preregistration")]
    assert len(tied) == 2 and {t["hypothesis_id"] for t in tied} == {"stocks:NEW-001"}
    assert len({t["model_sha256"] for t in tied}) == 2
