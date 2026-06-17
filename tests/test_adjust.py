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
    conn.execute("INSERT INTO adjustments(ticker,ex_date,factor,type,source) "
                 "VALUES('VALE3','2024-01-02',0.5,'split','inferred')")
    conn.commit()
    assert adjust.scan_and_quarantine(conn, threshold=0.30) == 0   # salto explicado
    _, adj = adjust.adjusted_series(conn, "VALE3")
    assert adj == [10.0, 10.0]                                     # série ajustada contínua
    conn.close()


def _insert(conn, ticker, points):
    for d, c in points:
        conn.execute(
            "INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,low,close,"
            "volume_fin,qty,quote_factor,source_file) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (d, ticker, "02", "010", c, c, c, c, c * 1000, 1000, 1, "SYNTH"))
    conn.commit()
