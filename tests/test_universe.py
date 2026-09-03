"""M3 — universo point-in-time. O teste-âncora: nenhum snapshot usa dado > asof."""
import datetime

import db
import universe


def _dates(n, start=(2023, 1, 2)):
    base = datetime.date(*start)
    return [(base + datetime.timedelta(days=i)).isoformat() for i in range(n)]


def _ins(conn, ticker, dates, vols):
    for d, v in zip(dates, vols):
        conn.execute(
            "INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,low,close,"
            "volume_fin,qty,quote_factor,source_file) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (d, ticker, "02", "010", 10.0, 10.0, 10.0, 10.0, v, 1000, 1, "SYNTH"))
    conn.commit()


def test_universe_is_point_in_time(tmp_path):
    """BBBB3 tem volume ínfimo ANTES do asof e um pico gigante DEPOIS. A seleção em
    asof deve ignorar o futuro — senão BBBB3 lideraria."""
    conn = db.get_connection(tmp_path / "s.db")
    d = _dates(20)
    asof = d[10]
    _ins(conn, "AAAA3", d, [1000.0] * 20)                       # estável
    _ins(conn, "BBBB3", d, [10.0] * 10 + [1_000_000_000.0] * 10)  # pico só no futuro
    ranked = dict(universe.rank_universe(conn, asof, lookback=5, min_history=8))
    assert ranked["BBBB3"] == 10.0, "vazou dado >= asof na mediana (lookahead!)"
    uni = universe.select_universe(conn, asof, top_n=2, lookback=5, min_history=8)
    assert uni[0] == "AAAA3"
    conn.close()


def test_excludes_quarantined(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    d = _dates(20)
    _ins(conn, "AAAA3", d, [1000.0] * 20)
    _ins(conn, "CCCC3", d, [5000.0] * 20)        # mais líquida, mas em quarentena
    conn.execute("INSERT INTO quarantine(ticker,date,reason) VALUES('CCCC3','2023-01-05','x')")
    conn.commit()
    uni = universe.select_universe(conn, d[10], top_n=5, lookback=5, min_history=8)
    assert "CCCC3" not in uni and "AAAA3" in uni
    conn.close()


def test_future_quarantine_does_not_exclude(tmp_path):
    """ANTI-LOOKAHEAD: um salto quarentenado DEPOIS do asof não pode tocar a seleção de
    hoje — senão informação do futuro entra no universo passado."""
    conn = db.get_connection(tmp_path / "s.db")
    d = _dates(20)
    asof = d[10]
    _ins(conn, "AAAA3", d, [1000.0] * 20)
    _ins(conn, "DDDD3", d, [5000.0] * 20)        # mais líquida
    conn.execute("INSERT INTO quarantine(ticker,date,reason) VALUES('DDDD3',?,'salto futuro')",
                 (d[15],))
    conn.commit()
    uni = universe.select_universe(conn, asof, top_n=5, lookback=5, min_history=8)
    assert "DDDD3" in uni, "quarentena futura vazou para a seleção passada (lookahead!)"
    conn.close()


def test_resolved_quarantine_does_not_exclude(tmp_path):
    """Quarentena RESOLVIDA pelo humano (ajuste registrado) não exclui mais o papel."""
    conn = db.get_connection(tmp_path / "s.db")
    d = _dates(20)
    _ins(conn, "AAAA3", d, [1000.0] * 20)
    _ins(conn, "FFFF3", d, [5000.0] * 20)
    conn.execute("INSERT INTO quarantine(ticker,date,reason,resolved_at) "
                 "VALUES('FFFF3','2023-01-05','split','2023-02-01')")
    conn.commit()
    uni = universe.select_universe(conn, d[10], top_n=5, lookback=5, min_history=8)
    assert "FFFF3" in uni, "quarentena já resolvida não deveria excluir"
    conn.close()


def test_dedup_on_pn_keeps_more_liquid(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    d = _dates(20)
    _ins(conn, "PETR3", d, [500.0] * 20)
    _ins(conn, "PETR4", d, [1000.0] * 20)         # mesma empresa, mais líquida
    uni = universe.select_universe(conn, d[10], top_n=5, lookback=5, min_history=8)
    assert uni == ["PETR4"]                        # só uma por empresa, a mais líquida
    conn.close()


def test_excludes_delisted_ticker_stale_before_window(tmp_path):
    """DDDD3 tem histórico LONGO mas seu último pregão foi ANTES da janela de liquidez
    (deslistado/incorporado) — não pode ser tratado como ativo só por ter linhas
    suficientes em algum ponto do passado (regressão do bug: vols[-lookback:] pegava
    os últimos N registros DO PRÓPRIO ticker, não os últimos N pregões do calendário)."""
    conn = db.get_connection(tmp_path / "s.db")
    d = _dates(40)
    _ins(conn, "AAAA3", d, [1000.0] * 40)           # ativa até o fim
    _ins(conn, "DDDD3", d[:20], [5000.0] * 20)      # deslistada em d[19] — nunca mais negociou
    asof = d[30]
    ranked = dict(universe.rank_universe(conn, asof, lookback=5, min_history=8))
    assert "DDDD3" not in ranked, "papel deslistado não pode ser elegível no universo"
    assert "AAAA3" in ranked
    conn.close()


def test_sporadic_trader_median_counts_no_trade_days_as_zero(tmp_path):
    """EEEE3 tem histórico longo mas negociou UMA vez dentro da janela de liquidez,
    com um bloco gigante. Sessão sem negócio conta como volume 0 — senão a 'mediana'
    de um único print (R$80M) colocaria um papel intragável acima dos líquidos."""
    conn = db.get_connection(tmp_path / "s.db")
    d = _dates(30)
    _ins(conn, "AAAA3", d, [1000.0] * 30)                 # negocia todo dia
    _ins(conn, "EEEE3", d[:20] + [d[27]], [50.0] * 20 + [80_000_000.0])
    asof = d[29]                                           # janela = últimos 5 pregões
    ranked = dict(universe.rank_universe(conn, asof, lookback=5, min_history=8))
    assert ranked["AAAA3"] == 1000.0
    assert ranked["EEEE3"] == 0.0, "mediana de 1 print não pode ranquear liquidez"
    conn.close()


def test_min_history_excludes_short(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    d = _dates(20)
    _ins(conn, "AAAA3", d, [1000.0] * 20)
    _ins(conn, "NEW3", d[:3], [9999.0] * 3)        # histórico curto demais
    uni = universe.select_universe(conn, d[10], top_n=5, lookback=5, min_history=8)
    assert "NEW3" not in uni
    conn.close()


def test_newly_listed_ticker_does_not_appear_before_its_ipo_date(tmp_path):
    """IPOX3 estreia (primeiro pregão) só na METADE do calendário sintético, com volume
    altíssimo desde o dia 1 de negociação — se apareceria em QUALQUER asof anterior à
    estreia, seria survivorship bias ao contrário (o universo "conheceria" uma empresa
    antes dela existir). RESEARCH_FREEZE.md §3/§13 (CLAIM-ST-PIT) registrava esse caso
    como coberto só indiretamente via min_history_excludes_short; este teste o nomeia
    explicitamente e cobre tanto `rank_universe` quanto `select_universe`, e confirma
    que o MESMO ticker aparece normalmente uma vez que tenha `min_history` dias de
    pregão acumulados após a estreia — não é uma exclusão permanente por nome."""
    conn = db.get_connection(tmp_path / "s.db")
    d = _dates(40)
    ipo_idx = 20
    _ins(conn, "AAAA3", d, [1000.0] * 40)                       # sempre listada, estável
    _ins(conn, "IPOX3", d[ipo_idx:], [9_000_000.0] * (40 - ipo_idx))  # estreia em d[20]

    asof_before_ipo = d[10]
    ranked_before = dict(universe.rank_universe(
        conn, asof_before_ipo, lookback=5, min_history=8))
    assert "IPOX3" not in ranked_before, (
        "ticker apareceu no ranking ANTES do seu próprio primeiro pregão (lookahead de "
        "listagem!) — universo não pode conhecer uma empresa antes dela existir"
    )
    uni_before = universe.select_universe(
        conn, asof_before_ipo, top_n=5, lookback=5, min_history=8)
    assert "IPOX3" not in uni_before

    asof_right_after_ipo = d[ipo_idx + 2]
    uni_too_soon = universe.select_universe(
        conn, asof_right_after_ipo, top_n=5, lookback=5, min_history=8)
    assert "IPOX3" not in uni_too_soon, (
        "min_history deveria continuar excluindo o recém-listado logo após a estreia"
    )

    asof_after_min_history = d[ipo_idx + 8]
    uni_after = universe.select_universe(
        conn, asof_after_min_history, top_n=5, lookback=5, min_history=8)
    assert "IPOX3" in uni_after, (
        "uma vez cumprido min_history após a estreia real, o ticker deve ficar elegível "
        "normalmente — a exclusão é sobre disponibilidade temporal, não uma blacklist"
    )
    conn.close()
