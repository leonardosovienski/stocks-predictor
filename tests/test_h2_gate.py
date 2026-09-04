"""H2 — fator de vol realizada, quintil inferior, trava de poder e Experiment Registry.

Valida a MAQUINARIA da H2 em sintético (o veredito real é da rodada única
pré-registrada): fator point-in-time, carteira bottom-quintile, controle
positivo do harness sobre o judge REAL, e a trava do registro (criar trial
nova sem atestado é erro; mudar params de trial existente é erro N+1).
"""
import datetime

import pytest

import backtest
import cotahist
import db
import factor
import portfolio
import trials_gate
from predictor_core.measurement import trials
from predictor_core.measurement.trials import PowerAttestationMissingError
from predictor_core.testing.harness import (PipelineHasNoPowerError,
                                            assert_pipeline_has_power)

# bootstrap enxuto: teste valida mecânica, não precisão do IC
_FAST_BOOT = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}


# ---------- fator: vol realizada (point-in-time) ----------

def test_realized_vol_known_value():
    dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
    closes = [100.0, 110.0, 99.0]
    # retornos: +10% e -10% -> pstdev = 0.10
    v = factor.realized_vol(dates, closes, "2024-01-03", lookback=2)
    assert v == pytest.approx(0.10)


def test_realized_vol_requires_full_window():
    dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
    closes = [100.0, 110.0, 99.0]
    assert factor.realized_vol(dates, closes, "2024-01-03", lookback=3) is None
    assert factor.realized_vol(dates, [100.0, 0.0, 99.0], "2024-01-03", lookback=2) is None
    assert factor.realized_vol(dates, closes, "2023-12-31", lookback=2) is None


def test_realized_vol_is_point_in_time():
    """Nada após asof pode tocar o sinal — mutação do futuro não muda a vol."""
    dates = [f"2024-01-{d:02d}" for d in range(1, 11)]
    closes = [100.0, 101.0, 99.5, 100.5, 102.0, 101.0, 103.0, 102.5, 104.0, 103.0]
    asof = "2024-01-06"
    before = factor.realized_vol(dates, closes, asof, lookback=5)
    mutated = closes[:6] + [1000.0, 0.5, 9999.0, 0.01]
    after = factor.realized_vol(dates, mutated, asof, lookback=5)
    assert before == after is not None


# ---------- carteira: quintil inferior ----------

def test_select_portfolio_bottom_takes_lowest_signals():
    sig = {"A": 0.05, "B": 0.01, "C": 0.03, "D": 0.02, "E": 0.04}
    port = portfolio.select_portfolio(sig, quantile=0.4, take="bottom")
    assert set(port) == {"B", "D"}
    assert all(w == pytest.approx(0.5) for w in port.values())


def test_select_portfolio_default_still_top():
    sig = {"A": 0.05, "B": 0.01, "C": 0.03, "D": 0.02, "E": 0.04}
    assert set(portfolio.select_portfolio(sig, quantile=0.4)) == {"A", "E"}
    with pytest.raises(ValueError):
        portfolio.select_portfolio(sig, take="middle")


# ---------- trava de poder: controle positivo sobre o judge REAL ----------

def _fast_cfg():
    return {"bootstrap": dict(_FAST_BOOT)}


def test_pipeline_has_power_with_real_judge():
    """O pedágio real detecta edge plantado E rejeita ruído (sens. + espec.)."""
    cfg = _fast_cfg()
    assert assert_pipeline_has_power(
        lambda pair: trials_gate._judge_verdict(pair, cfg),
        trials_gate.edge_pair, trials_gate.noise_pair,
        edge_verdict="COMPROVADA", null_verdict="não comprovada")


def test_blind_judge_fails_the_gate():
    """Um juiz cego (sempre NO-GO) tem que REPROVAR no controle positivo."""
    with pytest.raises(PipelineHasNoPowerError):
        assert_pipeline_has_power(
            lambda pair: {"verdict": "não comprovada"},
            trials_gate.edge_pair, trials_gate.noise_pair,
            edge_verdict="COMPROVADA", null_verdict="não comprovada")


def test_credulous_judge_fails_the_gate():
    """Um juiz crédulo (sempre GO) fabrica significância — reprova também."""
    with pytest.raises(PipelineHasNoPowerError):
        assert_pipeline_has_power(
            lambda pair: {"verdict": "COMPROVADA"},
            trials_gate.edge_pair, trials_gate.noise_pair,
            edge_verdict="COMPROVADA", null_verdict="não comprovada")


# ---------- Experiment Registry: criação gated + identidade N+1 ----------

def test_new_trial_requires_attestation(tmp_path):
    reg = trials.TrialRegistry(tmp_path / "trials.json")
    with pytest.raises(PowerAttestationMissingError):
        reg.register("h2-lowvol-252", params={"x": 1}, metric=trials_gate.METRIC)


def test_trials_path_from_honors_env_var(tmp_path, monkeypatch):
    """Achado de varredura de infraestrutura (2026-09-04): sem
    `PREDICTOR_TRIALS_PATH`, qualquer chamador que não passe `trials_path`
    explícito (ex.: `main.py backtest-h <N>` via subprocess, que não tem
    como injetar o argumento direto) escrevia no `trials.json` REAL do
    repo — mesmo padrão de `db.DB_PATH_ENV`/`report.REPORTS_ENV`, faltando
    só aqui. Precedência: override explícito > env var > config > default."""
    from config import load_config
    cfg = load_config()
    env_path = tmp_path / "via_env.json"
    monkeypatch.setenv(trials_gate.TRIALS_PATH_ENV, str(env_path))
    assert trials_gate.trials_path_from(cfg) == env_path
    # override explícito ainda vence a env var
    explicit_path = tmp_path / "via_override.json"
    assert trials_gate.trials_path_from(cfg, explicit_path) == explicit_path


def test_register_hypothesis_preserves_realized_sharpe(tmp_path):
    """Regressão do bug de clobber (2026-07-18): re-registrar baseline com
    sharpe=None NÃO pode apagar o sharpe realizado de uma rodada única."""
    from config import H2_FROZEN_KEYS, load_config
    cfg = load_config()
    tp = tmp_path / "trials.json"
    trials_gate.attest(_fast_cfg(), trials_path=tp)
    trials_gate.register_hypothesis(cfg, "h2-lowvol-252", H2_FROZEN_KEYS,
                                    "pré-registro", trials_path=tp)
    trials_gate.register_hypothesis(cfg, "h2-lowvol-252", H2_FROZEN_KEYS,
                                    "rodada única", sharpe=0.0123, trials_path=tp)
    reg = trials_gate.register_hypothesis(cfg, "h2-lowvol-252", H2_FROZEN_KEYS,
                                          "pré-registro de novo", trials_path=tp)
    h2 = [t for t in reg.load() if t["name"] == "h2-lowvol-252"][0]
    assert h2["sharpe"] == 0.0123 and h2["notes"] == "rodada única"


def test_attest_then_register_and_identity_lock(tmp_path):
    cfg = _fast_cfg()
    tp = tmp_path / "trials.json"
    rec = trials_gate.attest(cfg, trials_path=tp)
    assert rec["metric"] == trials_gate.METRIC
    assert trials.attestation_path_for(tp).exists()

    reg = trials.TrialRegistry(tp)
    fp = rec["pipeline_fingerprint"]
    reg.register("h2-lowvol-252", params={"x": 1}, metric=trials_gate.METRIC,
                 pipeline_fingerprint=fp)
    # re-registro idempotente (mesmos params) OK; params diferentes = N+1, erro
    reg.register("h2-lowvol-252", params={"x": 1}, sharpe=0.01,
                 metric=trials_gate.METRIC, pipeline_fingerprint=fp)
    with pytest.raises(ValueError):
        reg.register("h2-lowvol-252", params={"x": 2}, metric=trials_gate.METRIC,
                     pipeline_fingerprint=fp)
    assert reg.validate() == []


# ---------- run_h2 end-to-end em sintético ----------

def _dates(n, start=(2016, 7, 1)):
    base = datetime.date(*start)
    return [(base + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(n)]


def test_run_h2_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = dict(_FAST_BOOT)

    conn = db.get_connection(tmp_path / "s.db")
    tickers = [f"T{c}{c}{c}3" for c in "ABCDEFGHIJKL"]
    cotahist.load_prices(conn, cotahist.synthetic_cotahist(tickers, _dates(900), seed=11),
                         "COTAHIST_SYNTH.TXT")

    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)
    v = backtest.run_h2(cfg, conn, trials_path=tp)
    conn.close()

    assert "H2:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 2
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0
    reg = trials.TrialRegistry(tp)
    h2 = [t for t in reg.load() if t["name"] == "h2-lowvol-252"][0]
    assert h2["sharpe"] is not None and reg.validate() == []


# ---------- lacre por máquina da H2 ----------

def test_h2_frozen_config_hash_golden():
    """Mexeu num param [H2-FROZEN] -> quebra alto AQUI (pré-registro 2026-07-16)."""
    from config import h2_frozen_config_hash, load_config
    assert h2_frozen_config_hash(load_config()) == "da5a063cedf2cd3a"


def test_h2_frozen_hash_ignores_operational_params():
    from config import h2_frozen_config_hash, load_config
    cfg = load_config()
    base = h2_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    cfg["h2_criteria"]["trials_path"] = "outro/trials.json"
    assert h2_frozen_config_hash(cfg) == base
    cfg["h2_factor"]["lookback_days"] = 63
    assert h2_frozen_config_hash(cfg) != base
