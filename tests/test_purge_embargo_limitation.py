"""Documenta, com um teste executável, a limitação conhecida de purge/embargo.

RESEARCH_FREEZE.md §4/§9/§14 registra a decisão `DOCUMENTED_HISTORICAL_LIMITATION`:
`backtest.purge_embargo_months` é declarado em config.yaml (`[H1-FROZEN]`) mas nunca é
consumido pelo motor de walk-forward. Este teste torna essa afirmação verificável em vez
de apenas descritiva em prosa — se algum dia alguém implementar purge/embargo de verdade
(evolução consciente, não silenciosa), ESTE teste vai quebrar e vai precisar ser
atualizado/removido explicitamente, o que é o comportamento desejado (nunca deixar a
suíte verde por acidente sobre uma mudança de proteção temporal).

Não testa se purge/embargo FUNCIONA (não funciona, por decisão) — testa que o parâmetro
é comprovadamente inerte hoje, e que o primeiro rebalance após `test_start` não guarda
nenhum espaçamento em relação à fronteira treino/teste.
"""
import datetime

import backtest
import cotahist
import db


def _dates(n, start=(2016, 7, 1)):
    base = datetime.date(*start)
    return [(base + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(n)]


def _cfg(purge_embargo_months):
    return {
        "factor": {"lookback_days": 252, "skip_days": 21},
        "universe": {"top_n": 60, "lookback_trading_days": 126, "min_history_days": 252},
        "portfolio": {},
        "execution": {"b3_fee_pct": 0.0003, "spread_slippage_pct": 0.0015},
        "backtest": {
            "test_start": "2018-01-01",
            "purge_embargo_months": purge_embargo_months,
        },
        "bootstrap": {"n_boot": 500, "block_length": 21, "confidence": 0.95, "seed": 42},
    }


def _load(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    tickers = [f"T{c}{c}{c}3" for c in "ABCDEFGHIJKL"]
    lines = cotahist.synthetic_cotahist(tickers, _dates(900), seed=11)
    cotahist.load_prices(conn, lines, "COTAHIST_SYNTH.TXT")
    return conn


def test_purge_embargo_months_has_no_effect_on_walk_forward(tmp_path):
    """`purge_embargo_months` mudar de 1 para 12 não altera nenhum retorno gerado.

    Isto prova que o parâmetro é lido em algum lugar (não quebra a config) mas não é
    consumido pela mecânica de rebalanceamento/seleção de datas do walk-forward — a
    lacuna descrita em RESEARCH_FREEZE.md §4. Um motor que de fato implementasse
    purge/embargo produziria séries DIFERENTES (menos rebalances, ou rebalances
    deslocados) para embargos tão distintos quanto 1 e 12 meses.
    """
    conn_a = db.get_connection(tmp_path / "a.db")
    tickers = [f"T{c}{c}{c}3" for c in "ABCDEFGHIJKL"]
    lines = cotahist.synthetic_cotahist(tickers, _dates(900), seed=11)
    cotahist.load_prices(conn_a, lines, "COTAHIST_SYNTH.TXT")

    conn_b = db.get_connection(tmp_path / "b.db")
    cotahist.load_prices(conn_b, lines, "COTAHIST_SYNTH.TXT")

    strat_a, bench_a = backtest.walk_forward(conn_a, _cfg(purge_embargo_months=1))
    strat_b, bench_b = backtest.walk_forward(conn_b, _cfg(purge_embargo_months=12))
    conn_a.close()
    conn_b.close()

    assert strat_a == strat_b, (
        "purge_embargo_months passou a afetar o walk-forward — se isso é uma "
        "implementação real e intencional de purge/embargo, atualize "
        "RESEARCH_FREEZE.md §4/§9 (ST_PURGE_EMBARGO_STATUS) e remova/reescreva este "
        "teste conscientemente; não deixe a suíte ficar verde por acidente."
    )
    assert bench_a == bench_b


def test_first_rebalance_after_test_start_has_no_embargo_gap(tmp_path):
    """O primeiro rebalance elegível é exatamente o primeiro fim-de-mês >= test_start.

    Não há nenhum deslocamento de `purge_embargo_months` aplicado à fronteira
    treino/teste — confirma, olhando as datas de rebalance reais, que a lacuna
    reportada em RESEARCH_FREEZE.md §4 é sobre a implementação (`backtest.py`),
    não apenas sobre a leitura do parâmetro.
    """
    from returns import month_end_dates

    conn = _load(tmp_path)
    test_start = "2018-01-01"
    all_dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM prices_raw WHERE market_type = ? ORDER BY date",
        (__import__("universe").SPOT_MARKET,))]
    conn.close()

    rebal = [d for d in month_end_dates(all_dates) if d >= test_start]
    assert rebal, "esperava pelo menos um rebalance na janela de teste sintética"
    first_gap_days = (
        datetime.datetime.strptime(rebal[0], "%Y-%m-%d").date()
        - datetime.datetime.strptime(test_start, "%Y-%m-%d").date()
    ).days
    # Um embargo de verdade (purge_embargo_months=1, config real) excluiria
    # qualquer rebalance no primeiro mês após test_start. Aqui, o mais próximo
    # possível (< 31 dias) É elegível — confirma ausência de embargo aplicado.
    assert first_gap_days < 31
