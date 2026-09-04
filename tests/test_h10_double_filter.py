"""H10 — filtro duplo ROE ∩ baixa alavancagem (pré-registro 2026-09-04).

Mesma maquinaria de universo/custos/pareamento/pedágio/embargo de H7/H9;
filtro duplo top ROE, depois menor alavancagem DENTRO desse subconjunto —
mesmo racional da H8 (momentum∩baixa-vol), agora sobre as duas variáveis
contábeis. O smoke valida o encadeamento; o veredito real é da rodada única
em dado real (mesma `fundamentals` já ingerida por H7/H9).
"""
import datetime

import backtest
import cotahist
import db
import portfolio
import trials_gate


def _dates(n, start=(2016, 7, 1)):
    base = datetime.date(*start)
    return [(base + datetime.timedelta(days=i)).strftime("%Y%m%d") for i in range(n)]


def _synthetic_conn(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    tickers = [f"T{c}{c}{c}3" for c in "ABCDEFGHIJKL"]
    cotahist.load_prices(conn, cotahist.synthetic_cotahist(tickers, _dates(900), seed=11),
                         "COTAHIST_SYNTH.TXT")
    for i, t in enumerate(tickers):
        roe = 0.05 + 0.01 * i
        lev = 0.20 + 0.02 * i
        conn.execute(
            "INSERT INTO fundamentals(ticker, ref_date, ativo_total, passivo_total,"
            " patrimonio_liquido, lucro_liquido, roe, leverage, source)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (t, "2016-12-31", 1000.0, 400.0 + 1000.0 * lev, 600.0 - 1000.0 * lev,
             600.0 * roe, roe, lev, "CVM DFP 2016 (sintético)"))
    conn.commit()
    return conn


def test_run_h10_smoke(tmp_path, capsys):
    from config import load_config
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 300, "block_length": 21, "confidence": 0.95, "seed": 42}

    conn = _synthetic_conn(tmp_path)
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)     # h1 + h2 no tmp
    v = backtest.run_h10(cfg, conn, trials_path=tp)
    conn.close()

    assert "H10:" in capsys.readouterr().out
    assert v["n"] > 60 and v.get("n_trials") == 3     # h1 + h2 + h10 neste registro tmp
    assert v.get("dsr") is not None and 0.0 <= v["dsr"] <= 1.0


def test_h10_frozen_config_hash_golden():
    """Mexeu num param [H10-FROZEN] -> quebra alto AQUI (pré-registro 2026-09-04)."""
    from config import h10_frozen_config_hash, load_config
    assert h10_frozen_config_hash(load_config()) == "150023ca75fd4324"


def test_h10_frozen_hash_ignores_operational_params():
    from config import h10_frozen_config_hash, load_config
    cfg = load_config()
    base = h10_frozen_config_hash(cfg)
    cfg["data"]["db_path"] = "outro.db"
    cfg["bootstrap"]["seed"] = 999
    assert h10_frozen_config_hash(cfg) == base
    cfg["h10_portfolio"]["roe_quantile"] = 0.1     # tocar num FROZEN muda o lacre
    assert h10_frozen_config_hash(cfg) != base


def test_roe_lowlev_double_filter_intersects_correctly():
    """Ponto central da H10: 2ª etapa filtra DENTRO do subconjunto da 1ª, não
    do universo inteiro — e só entram tickers com AMBOS os sinais."""
    roe = {"A": 0.20, "B": 0.15, "C": 0.05, "D": 0.18, "E": 0.02}
    # E teria a MENOR alavancagem do universo inteiro (0.01), mas não entra no
    # top-40% de ROE (0.02 é o pior) — 1ª etapa exclui antes da 2ª nem olhar.
    lev = {"A": 0.6, "B": 0.1, "C": 0.05, "D": 0.3, "E": 0.01}
    # top-40% de ROE (round(5*0.4)=2): {A, D}. Dentro desses, menor alavancagem
    # (round(2*0.5)=1): D (0.3) < A (0.6) -> só D sobra.
    chosen = portfolio.roe_lowlev_double_filter(roe, lev, roe_quantile=0.4, leverage_quantile=0.5)
    assert chosen == {"D": 1.0}
    assert "E" not in chosen    # excluído na 1ª etapa (ROE baixo), apesar da alavancagem baixa
    assert "B" not in chosen    # ROE de B (0.15) não entra no top-40%
