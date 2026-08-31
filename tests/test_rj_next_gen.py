"""Testes das famílias next-gen, CoDa, outcomes auxiliares e robustez
estatística — tudo do pacote de melhorias 2026-08-24 que NÃO toca o
pré-registro das 8 famílias."""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "stocks_predictor"))

import rj_coda as coda
import rj_families as families
import rj_families_next as nextgen
import rj_judge_robust as robust
import rj_outcomes as outcomes


def _calendar(n=300, start="2020-01-06"):
    import datetime
    d = datetime.date.fromisoformat(start)
    out = []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += datetime.timedelta(days=1)
    return out


# --- next-gen families -----------------------------------------------------

def test_next_gen_registry_disjoint_from_preregistered():
    assert not (set(nextgen.NEXT_GEN_REGISTRY) & set(families.REGISTRY))
    assert set(nextgen.NEXT_GEN_DIRECTIONS) == set(nextgen.NEXT_GEN_REGISTRY)


def test_max_lottery_uses_only_past_and_picks_extremes():
    dates = _calendar(100)
    closes = [10.0]
    for i in range(1, 100):
        closes.append(closes[-1] * (1.20 if i in (80, 82) else 1.0))
    asof = dates[90]
    v = nextgen.max_lottery(dates, closes, asof, k=2, window=21)
    assert v == pytest.approx(0.20)      # os dois +20% estão na janela
    # truncar o futuro não pode mudar o valor (point-in-time)
    v_cut = nextgen.max_lottery(dates[:91], closes[:91], asof, k=2, window=21)
    assert v_cut == pytest.approx(v)


def test_equity_issuance_respects_known_at():
    events = [{"event_type": "aumento_capital", "event_date": "2020-05-10",
               "known_at": "2020-05-12"}]
    assert nextgen.equity_issuance(events, "2020-05-11") == 0   # não era público
    assert nextgen.equity_issuance(events, "2020-06-01") == 1
    assert nextgen.equity_issuance(events, "2022-01-01") == 0   # fora da janela


def test_retail_migration_delta():
    snaps = [{"ref_date": "2019-06-01", "pct_retail": 0.30},
             {"ref_date": "2020-06-01", "pct_retail": 0.85}]
    v = nextgen.retail_migration(snaps, "2020-09-01", "2020-01-15")
    assert v == pytest.approx(0.55)
    assert nextgen.retail_migration([], "2020-09-01", "2020-01-15") is None


def test_altman_z_and_chs_nimta():
    fin = {"working_capital": 100, "retained_earnings": 200, "ebit": 50,
           "equity_value": 500, "total_liabilities": 400,
           "sales": 800, "total_assets": 1000, "net_income": 30}
    z = nextgen.altman_z(fin)
    assert z is not None and z > 0
    assert nextgen.altman_z({"working_capital": 1}) is None   # fail-closed
    assert nextgen.chs_nimta(fin) == pytest.approx(30 / 900)
    assert nextgen.chs_nimta({"net_income": 1}) is None


# --- CoDa ------------------------------------------------------------------

def test_impute_zeros_auditable():
    m = [[10.0, 0.0], [20.0, 4.0], [None, 8.0]]
    r = coda.impute_zeros(m)
    assert r["data"][0][1] == pytest.approx(2.0)   # metade do mínimo (4.0)
    assert r["data"][2][0] == pytest.approx(5.0)   # metade do mínimo (10.0)
    assert set(r["mask"]) == {(0, 1), (2, 0)}      # toda imputação é auditável


def test_clr_invariant_and_fail_closed():
    v = coda.clr([1.0, 2.0, 4.0])
    assert sum(v) == pytest.approx(0.0)            # CLR soma zero
    assert coda.clr([1.0, 0.0]) is None            # nunca log de zero
    # escalar a composição por constante não muda o CLR (propriedade CoDa)
    assert coda.clr([2.0, 4.0, 8.0]) == pytest.approx(v)


# --- outcomes auxiliares ----------------------------------------------------

def test_market_adjusted_rally_isolates_idiosyncratic():
    dates = _calendar(120)
    # papel sobe 60% mas índice sobe 40%: excesso = ~14pp, NÃO é rally ajustado
    closes = [10.0 * (1.6 ** (i / 119)) for i in range(120)]
    idx = [1000.0 * (1.4 ** (i / 119)) for i in range(120)]
    r = outcomes.market_adjusted_rally(dates, closes, dates, idx, dates[50],
                                       threshold_pct=0.50,
                                       max_window_trading_days=60)
    assert r["outcome"] == "no_market_adjusted_rally"
    # papel +100% com índice plano: excesso >= 50% -> rally ajustado
    closes2 = list(closes)
    for i in range(51, 70):
        closes2[i] = closes[50] * 2.0
    r2 = outcomes.market_adjusted_rally(dates, closes2, dates, idx, dates[50],
                                        threshold_pct=0.50,
                                        max_window_trading_days=60)
    assert r2["outcome"] == "rally_market_adjusted"


def test_walk_forward_never_looks_back():
    for train, test in outcomes.walk_forward_splits(n_obs=30, min_train=10,
                                                    step=5):
        assert max(train) < min(test)              # teste sempre no futuro
        assert train.start == 0                    # expanding, não rolling


# --- robustez estatística ---------------------------------------------------

def test_romano_wolf_detects_strong_signal_and_ignores_noise():
    import random
    rng = random.Random(3)
    strong = [(f"T{i}", rng.gauss(1.5 if i < 15 else 0.0, 1.0),
               1 if i < 15 else 0) for i in range(30)]
    noise = [(f"T{i}", rng.gauss(0.0, 1.0), 1 if i < 15 else 0)
             for i in range(30)]
    units = {name: list(noise) for name in families.PREDICTIVE_FAMILIES
             if name not in families.CATEGORICAL_FAMILIES}
    units["drawdown"] = strong
    rw = robust.romano_wolf_stepdown(units, n_perm=300, seed=1)
    assert rw["drawdown"]["significant_romanowolf"]
    noise_only = {k: v for k, v in units.items() if k != "drawdown"}
    rw2 = robust.romano_wolf_stepdown(noise_only, n_perm=300, seed=1)
    assert sum(v["significant_romanowolf"] for v in rw2.values()) <= 1


def test_oos_haircut():
    assert robust.apply_oos_haircut(1.0) == pytest.approx(0.64)
    assert robust.apply_oos_haircut(-2.0) == pytest.approx(-1.28)
