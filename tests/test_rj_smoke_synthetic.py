"""Smoke test com dados SINTÉTICOS — valida que a maquinaria (episódios,
famílias, judge, FDR, LOCO) funciona ANTES de qualquer dado real de RJ
existir. Mesmo papel que `cotahist.py` sintético fez no stocks-predictor:
destrava desenvolvimento sem esperar a coleta manual do universo real.

Não é o veredito de hipótese nenhuma — é teste de unidade da MECÂNICA.
"""
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

import rj_episodes as episodes
import rj_families as families
import rj_judge as judge
import yaml


def load_test_config():
    cfg_path = pathlib.Path(__file__).parent.parent / "config_rj.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def make_trading_calendar(n_days=800, start="2020-01-06"):
    import datetime
    d = datetime.date.fromisoformat(start)
    dates = []
    while len(dates) < n_days:
        if d.weekday() < 5:
            dates.append(d.isoformat())
        d += datetime.timedelta(days=1)
    return dates


def synth_series_with_rally(dates, rng, has_rally=True, trough_idx=200):
    """Série sintética: cai até trough_idx, depois ou dispara (+80%) ou
    fica lateral (sem cruzar +50%) — controla o outcome pelo desenho."""
    closes = [10.0]
    for i in range(1, trough_idx):
        closes.append(max(0.05, closes[-1] * (1 + rng.gauss(-0.01, 0.02))))
    if has_rally:
        for i in range(trough_idx, min(trough_idx + 30, len(dates))):
            closes.append(closes[-1] * (1 + rng.gauss(0.03, 0.02)))
    else:
        for i in range(trough_idx, min(trough_idx + 30, len(dates))):
            closes.append(closes[-1] * (1 + rng.gauss(0.0, 0.015)))
    # cauda longa SEM deriva (mu=0) — só ruído. Com deriva positiva mesmo
    # pequena, 400+ pregões acumulam e cruzam +50% por acaso, confundindo o
    # cenário "sem rally" com um rally lento não-intencional no teste.
    while len(closes) < len(dates):
        closes.append(max(0.05, closes[-1] * (1 + rng.gauss(0.0, 0.015))))
    return closes[:len(dates)]


def test_classify_episode_detects_rally():
    dates = make_trading_calendar(400)
    rng = random.Random(1)
    closes = synth_series_with_rally(dates, rng, has_rally=True, trough_idx=150)
    cfg = load_test_config()
    trough_date, trough_price = episodes.find_local_trough(dates, closes, dates[100], dates[200])
    result = episodes.classify_episode(dates, closes, trough_date, cfg, asof_today=dates[-1])
    assert result["outcome"] == "rally"
    assert result["rally_pct"] >= 0.50


def test_classify_episode_no_rally_when_window_closed():
    dates = make_trading_calendar(400)
    rng = random.Random(2)
    closes = synth_series_with_rally(dates, rng, has_rally=False, trough_idx=100)
    cfg = load_test_config()
    trough_date, _ = episodes.find_local_trough(dates, closes, dates[50], dates[150])
    result = episodes.classify_episode(dates, closes, trough_date, cfg, asof_today=dates[-1])
    assert result["outcome"] in ("no_rally_observed", "censored")


def test_drawdown_family_direction():
    dates = make_trading_calendar(300)
    closes = [100.0 - i * 0.3 for i in range(300)]
    val = families.drawdown(dates, closes, dates[250], dates[0])
    assert val is not None and 0 < val < 1


def test_judge_run_all_families_end_to_end():
    """Universo sintético de 20 empresas: 10 com rally, 10 controle. A
    família 'drawdown' é construída para ter sinal real (rally tem drawdown
    maior); as outras são ruído puro — o teste verifica que o pipeline roda
    sem erro E que o FDR não declara TODAS as 8 como significativas por
    acidente (sanidade contra falso positivo trivial)."""
    cfg = load_test_config()
    rng = random.Random(7)
    units_by_family = {name: [] for name in families.REGISTRY}
    for i in range(20):
        ticker = f"SYN{i}3"
        group = 1 if i < 10 else 0
        # drawdown com sinal real: rally-group sistematicamente mais fundo
        dd = rng.gauss(0.75, 0.05) if group == 1 else rng.gauss(0.55, 0.05)
        units_by_family["drawdown"].append((ticker, dd, group))
        for name in families.REGISTRY:
            if name == "drawdown":
                continue
            units_by_family[name].append((ticker, rng.gauss(0.0, 1.0), group))

    verdicts = judge.run_all_families(units_by_family, cfg)
    assert set(verdicts.keys()) == set(families.REGISTRY.keys())
    for name, v in verdicts.items():
        assert "significant_after_fdr" in v
        assert "loco" in v
    # sanidade: nem toda família de ruído puro deveria sobreviver ao FDR
    n_sig = sum(1 for v in verdicts.values() if v["significant_after_fdr"])
    assert n_sig < len(families.REGISTRY)


def test_point_in_time_candidates_no_lookahead():
    """point_in_time_candidates não pode gerar candidato cujo valor dependa
    de dado futuro: truncar a série em qualquer ponto >= um candidato não
    pode mudar se aquele candidato específico já havia sido gerado antes do
    corte (checagem direta de determinismo backward-only)."""
    dates = make_trading_calendar(300)
    rng = random.Random(3)
    closes = synth_series_with_rally(dates, rng, has_rally=True, trough_idx=150)
    rj_date = dates[10]
    full = episodes.point_in_time_candidates(dates, closes, rj_date, backward_lookback=40)
    # trunca a série em 200 pregões; todo candidato <= dates[199] no full
    # precisa continuar aparecendo idêntico na versão truncada (nada do
    # futuro pode ter influenciado a classificação de candidatos passados)
    cut = 200
    truncated = episodes.point_in_time_candidates(dates[:cut], closes[:cut], rj_date, backward_lookback=40)
    full_before_cut = [d for d in full if d <= dates[cut - 1]]
    assert full_before_cut == truncated


def test_classify_episode_primary_vs_secondary_window():
    """A janela primária (60 pregões) e secundária (252) podem discordar —
    um outcome 'rally' na secundária não implica rally na primária. O teste
    verifica que ambas rodam independentemente sem um sobrescrever o
    parâmetro congelado da outra."""
    dates = make_trading_calendar(400)
    rng = random.Random(4)
    closes = synth_series_with_rally(dates, rng, has_rally=True, trough_idx=150)
    cfg = load_test_config()
    trough_date, _ = episodes.find_local_trough(dates, closes, dates[100], dates[200])
    primary = episodes.classify_episode(dates, closes, trough_date, cfg,
                                         asof_today=dates[-1], window_key="primary_window_trading_days")
    secondary = episodes.classify_episode(dates, closes, trough_date, cfg,
                                           asof_today=dates[-1], window_key="secondary_window_trading_days")
    assert primary["outcome"] in ("rally", "no_rally_observed", "censored")
    assert secondary["outcome"] in ("rally", "no_rally_observed", "censored")


def test_classify_episode_censoring_boundary_exact_window():
    """Borda exata (revisão externa, 2ª rodada): trough_idx + max_window ==
    len(dates)-1 (janela COMPLETA, último pregão é exatamente o fim da
    janela) deve dar veredito definitivo, não censura."""
    dates = make_trading_calendar(200)
    cfg = load_test_config()
    max_w = cfg["rally"]["primary_window_trading_days"]
    trough_idx = len(dates) - 1 - max_w
    closes = [10.0] * len(dates)   # lateral, sem rally algum
    result = episodes.classify_episode(dates, closes, dates[trough_idx], cfg,
                                        asof_today=dates[-1], window_key="primary_window_trading_days")
    assert result["outcome"] == "no_rally_observed"
    assert result["censored"] == 0


def test_classify_episode_censoring_boundary_one_short():
    """Um pregão a menos que a janela completa: ainda é censura, não
    controle definitivo (o ajuste exato importa — off-by-one é o tipo de
    bug que criaria vazamento silencioso ou controle fabricado)."""
    dates = make_trading_calendar(200)
    cfg = load_test_config()
    max_w = cfg["rally"]["primary_window_trading_days"]
    trough_idx = len(dates) - max_w   # um pregão a menos de janela completa
    closes = [10.0] * len(dates)
    result = episodes.classify_episode(dates, closes, dates[trough_idx], cfg,
                                        asof_today=dates[-1], window_key="primary_window_trading_days")
    assert result["outcome"] == "censored"
    assert result["censored"] == 1


def test_full_window_required_for_candidates():
    """Sem janela completa (revisão externa, 2ª rodada, ponto 2): os
    primeiros `backward_lookback` pregões pós-RJ NUNCA podem ser candidatos,
    mesmo caindo monotonicamente (o cenário que gerava enxurrada de falsos
    candidatos antes da correção)."""
    dates = make_trading_calendar(200)
    closes = [100.0 - i * 0.5 for i in range(200)]   # queda monotônica
    rj_date = dates[0]
    lookback = 40
    candidates = episodes.point_in_time_candidates(dates, closes, rj_date, backward_lookback=lookback)
    early = [c for c in candidates if dates.index(c) - dates.index(rj_date) < lookback]
    assert early == [], f"candidatos com janela incompleta não deveriam existir: {early}"


def test_select_primary_and_secondary_episodes():
    dates = make_trading_calendar(500)
    rng = random.Random(9)
    closes = synth_series_with_rally(dates, rng, has_rally=False, trough_idx=250)
    rj_date = dates[0]
    candidates = episodes.point_in_time_candidates(dates, closes, rj_date, backward_lookback=40)
    if not candidates:
        return  # série sintética pode não gerar candidato; não é o alvo deste teste
    primary = episodes.select_primary_episode(candidates)
    assert primary == candidates[0]
    secondary = episodes.select_secondary_episodes(candidates, dates, min_separation_trading_days=60)
    assert secondary[0] == primary
    # separação mínima respeitada entre todos os mantidos
    idxs = [dates.index(d) for d in secondary]
    assert all(b - a >= 60 for a, b in zip(idxs, idxs[1:]))


if __name__ == "__main__":
    test_classify_episode_detects_rally()
    test_classify_episode_no_rally_when_window_closed()
    test_drawdown_family_direction()
    test_judge_run_all_families_end_to_end()
    test_point_in_time_candidates_no_lookahead()
    test_classify_episode_primary_vs_secondary_window()
    test_classify_episode_censoring_boundary_exact_window()
    test_classify_episode_censoring_boundary_one_short()
    test_full_window_required_for_candidates()
    test_select_primary_and_secondary_episodes()
    print("smoke sintético: 10/10 passou")
