"""M2 — detector de saltos, inferência de split, série ajustada e quarentena."""
import adjust
import db


def test_detect_jumps():
    dates = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]
    closes = [20.0, 20.4, 10.1, 10.2]          # split ~1:2 entre 02 e 03
    jumps = adjust.detect_jumps(dates, closes, threshold=0.30)
    assert len(jumps) == 1 and jumps[0][0] == "2024-01-03"
    assert adjust.detect_jumps(dates, [20.0, 20.1, 20.2, 20.3], 0.30) == []


def test_infer_split_factor():
    assert adjust.infer_split_factor(20.0, 10.0) == 0.5      # split 1:2
    assert adjust.infer_split_factor(10.0, 20.0) == 2.0      # grupamento 2:1
    assert adjust.infer_split_factor(50.0, 10.0) == 0.2      # split 1:5
    assert adjust.infer_split_factor(20.0, 19.0) is None     # variação normal, não split


def test_adjusted_closes_continuous_after_split():
    dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
    closes = [20.0, 20.0, 10.0]                # split 1:2 em 03 (preço cai à metade)
    adj = adjust.adjusted_closes(dates, closes, [("2024-01-03", 0.5)])
    assert adj == [10.0, 10.0, 10.0]           # série contínua após o ajuste


def test_scan_quarantines_unexplained_jump(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    _insert(conn, "PETR4", [("2024-01-01", 20.0), ("2024-01-02", 10.0)])   # salto sem ajuste
    n = conn.execute("SELECT COUNT(*) FROM quarantine").fetchone()[0]
    assert n == 0
    flagged = adjust.scan_and_quarantine(conn, threshold=0.30)
    assert flagged == 1
    row = conn.execute("SELECT ticker, date FROM quarantine").fetchone()
    assert (row["ticker"], row["date"]) == ("PETR4", "2024-01-02")
    conn.close()


def test_explained_jump_is_not_quarantined(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    _insert(conn, "VALE3", [("2024-01-01", 20.0), ("2024-01-02", 10.0)])
    conn.execute("INSERT INTO adjustments(ticker,ex_date,factor,type,source,approved_by) "
                 "VALUES('VALE3','2024-01-02',0.5,'split','inferred','teste')")
    conn.commit()
    assert adjust.scan_and_quarantine(conn, threshold=0.30) == 0   # salto explicado
    _, adj = adjust.adjusted_series(conn, "VALE3")
    assert adj == [10.0, 10.0]                                     # série ajustada contínua
    conn.close()


def test_pending_adjustment_without_approval_does_not_explain_jump(tmp_path):
    """Achado de revisão de código 2026-08-28: um ajuste PENDENTE (approved_by
    NULL, §9b/§11 — nunca gravado pela IA sozinha) não pode contar como "salto
    explicado" nem entrar na série que alimenta o fator/backtest — senão o
    evento sumiria da fila de revisão humana E seria aplicado sem aprovação."""
    conn = db.get_connection(tmp_path / "s.db")
    _insert(conn, "VALE3", [("2024-01-01", 20.0), ("2024-01-02", 10.0)])
    conn.execute("INSERT INTO adjustments(ticker,ex_date,factor,type,source) "
                 "VALUES('VALE3','2024-01-02',0.5,'split','inferred')")  # approved_by NULL
    conn.commit()
    assert adjust.scan_and_quarantine(conn, threshold=0.30) == 1   # ainda vai pra fila
    _, adj = adjust.adjusted_series(conn, "VALE3")
    assert adj == [20.0, 10.0]                                     # fator PENDENTE não aplicado
    conn.close()


def test_require_scanned_passes_on_small_test_db(tmp_path):
    """Fixtures sintéticas de teste (poucas linhas) nunca disparam o guard —
    só bancos de escala de produção nunca escaneados."""
    conn = db.get_connection(tmp_path / "s.db")
    _insert(conn, "PETR4", [("2024-01-01", 20.0), ("2024-01-02", 19.5)])
    adjust.require_scanned(conn)   # não levanta
    conn.close()


def test_require_scanned_fails_loud_when_never_scanned(tmp_path):
    """Achado de revisão de código 2026-08-28: nada impedia rodar o backtest
    direto após o ingest, sem nunca rodar `adjust` — um split real ficaria
    sem excluir/ajustar e corromperia o Sharpe em silêncio. Banco de escala de
    produção (>= min_rows) com quarantine E adjustments vazios tem que falhar
    alto, não seguir em frente calado."""
    conn = db.get_connection(tmp_path / "s.db")
    dates = [f"2024-{m:02d}-{d:02d}" for m in range(1, 13) for d in (1, 15)]
    rows = [(dt, "PETR4", 20.0) for dt in dates] * 3000   # >= min_rows sintético
    for i, (dt, tk, c) in enumerate(rows):
        conn.execute(
            "INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,"
            "low,close,volume_fin,qty,quote_factor,source_file) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (dt, f"{tk}{i}", "02", "010", c, c, c, c, 1.0, 1, 1, "SYNTH"))
    conn.commit()
    import pytest
    with pytest.raises(RuntimeError, match="nunca rodou"):
        adjust.require_scanned(conn, min_rows=1000)
    conn.close()


def test_list_split_candidates_separates_round_ratio_from_noise(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    _insert(conn, "PETR4", [("2024-01-01", 20.0), ("2024-01-02", 10.0)])   # split 1:2 plausível
    _insert(conn, "XYZW3", [("2024-01-01", 20.0), ("2024-01-02", 8.6)])    # sem proporção redonda
    adjust.scan_and_quarantine(conn, threshold=0.30)
    cands = adjust.list_split_candidates(conn)
    tickers = {c["ticker"] for c in cands}
    assert tickers == {"PETR4"}                    # XYZW3 fica de fora (é ruído, não split)
    assert cands[0]["factor_sugerido"] == 0.5
    assert cands[0]["tipo_inferido"] == "desdobramento"
    assert cands[0]["source"] == "" and cands[0]["approved_by"] == ""   # em branco p/ humano
    conn.close()


def test_export_then_import_only_grava_linhas_aprovadas(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    _insert(conn, "PETR4", [("2024-01-01", 20.0), ("2024-01-02", 10.0)])
    _insert(conn, "VALE3", [("2024-01-01", 20.0), ("2024-01-02", 10.0)])
    adjust.scan_and_quarantine(conn, threshold=0.30)

    csv_path = tmp_path / "candidates.csv"
    n = adjust.export_candidates_csv(conn, csv_path)
    assert n == 2

    # simula revisão humana: aprova só PETR4 (source+approved_by preenchidos)
    import csv as _csv
    rows = list(_csv.DictReader(open(csv_path, encoding="utf-8")))
    for r in rows:
        if r["ticker"] == "PETR4":
            r["source"], r["approved_by"] = "b3_fato_relevante", "leonardo"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = _csv.DictWriter(f, fieldnames=adjust._CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)

    imported = adjust.import_approved_adjustments(conn, csv_path)
    assert imported == 1
    row = conn.execute(
        "SELECT ticker, factor, source, approved_by FROM adjustments").fetchone()
    assert (row["ticker"], row["factor"], row["source"], row["approved_by"]) == (
        "PETR4", 0.5, "b3_fato_relevante", "leonardo")
    # VALE3 NÃO aprovado -> permanece só em quarentena, nada gravado por ele
    assert conn.execute(
        "SELECT COUNT(*) FROM adjustments WHERE ticker='VALE3'").fetchone()[0] == 0

    # re-scan: PETR4 agora está explicado (some da quarentena aberta); VALE3 continua
    adjust.scan_and_quarantine(conn, threshold=0.30)
    open_tickers = {r[0] for r in conn.execute(
        "SELECT DISTINCT ticker FROM quarantine WHERE resolved_at IS NULL")}
    assert open_tickers == {"VALE3"}
    conn.close()


def test_import_fator_conflitante_nao_resolve_quarentena(tmp_path):
    """Write-once: se já existe ajuste com fator DIFERENTE do CSV, o INSERT é ignorado
    e a quarentena NÃO pode ser resolvida como se a correção tivesse entrado — senão o
    papel volta ao universo com a série ainda descontínua."""
    import csv as _csv
    conn = db.get_connection(tmp_path / "s.db")
    _insert(conn, "PETR4", [("2024-01-01", 20.0), ("2024-01-02", 10.0)])
    adjust.scan_and_quarantine(conn, threshold=0.30)
    # ajuste pré-existente com fator ERRADO (0.25 em vez de 0.5)
    conn.execute("INSERT INTO adjustments(ticker,ex_date,factor,type,source) "
                 "VALUES('PETR4','2024-01-02',0.25,'split','manual')")
    conn.commit()

    csv_path = tmp_path / "c.csv"
    adjust.export_candidates_csv(conn, csv_path)   # quarentena segue aberta → exporta
    rows = list(_csv.DictReader(open(csv_path, encoding="utf-8")))
    for r in rows:
        r["source"], r["approved_by"] = "fonte", "leonardo"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = _csv.DictWriter(f, fieldnames=adjust._CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)

    imported = adjust.import_approved_adjustments(conn, csv_path)
    assert imported == 0                                        # nada novo entrou
    assert conn.execute("SELECT factor FROM adjustments").fetchone()[0] == 0.25
    # quarentena PERMANECE aberta — a divergência precisa de decisão humana
    assert conn.execute("SELECT COUNT(*) FROM quarantine "
                        "WHERE resolved_at IS NULL").fetchone()[0] == 1
    conn.close()


def _insert(conn, ticker, points):
    for d, c in points:
        conn.execute(
            "INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,low,close,"
            "volume_fin,qty,quote_factor,source_file) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (d, ticker, "02", "010", c, c, c, c, c * 1000, 1000, 1, "SYNTH"))
    conn.commit()
