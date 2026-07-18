"""quote_factor aplicado na LEITURA (decisão do operador, 2026-07-18).

COTAHIST cota papéis em lote (FATCOT 10/100/1000/1000000): o preço cru fica na
escala do lote. `prices_raw` permanece o espelho intocável do arquivo; a divisão
por quote_factor acontece nas queries de leitura (adjust/paper). Estes testes
cobrem: preço por ação na série, mudança de fator NÃO é salto econômico, e
execução do paper na escala certa.
"""
import cotahist
import db
import paper
from adjust import adjusted_series, scan_and_quarantine


def _line(date, ticker, raw_price, fatcot, mkt="010", bdi="02"):
    return cotahist._pack(date, ticker, bdi, mkt, raw_price, raw_price,
                          raw_price, raw_price, 1000, raw_price * 1000, fatcot)


def test_adjusted_series_divides_by_quote_factor(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    # preço econômico constante R$ 20: 2 dias cotados por ação, 2 por lote de mil
    lines = [_line("2024-01-02", "QFAT3", 20.0, 1),
             _line("2024-01-03", "QFAT3", 20.0, 1),
             _line("2024-01-04", "QFAT3", 20000.0, 1000),
             _line("2024-01-05", "QFAT3", 20000.0, 1000)]
    cotahist.load_prices(conn, lines, "QF.TXT")
    dates, closes = adjusted_series(conn, "QFAT3")
    assert closes == [20.0, 20.0, 20.0, 20.0]

    # sem a divisão, a troca de lote viraria um "salto" de 999x -> quarentena falsa
    assert scan_and_quarantine(conn, threshold=0.30) == 0
    conn.close()


def test_paper_settles_at_per_share_price(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    cotahist.load_prices(conn, [_line("2024-01-02", "QFAT3", 20000.0, 1000),
                                _line("2024-01-03", "QFAT3", 21000.0, 1000)], "QF.TXT")
    conn.execute(
        "INSERT INTO decisions(run_id,asof,ticker,signal_value,rank,"
        "conviction_band,frozen_mode) VALUES('r1','2024-01-02','QFAT3',0.1,1,"
        "'quintil_superior',1)")
    conn.commit()
    assert paper.settle_executions(conn, {}) == 1
    row = conn.execute("SELECT exec_date, exec_price FROM decisions").fetchone()
    assert row["exec_date"] == "2024-01-03"
    assert row["exec_price"] == 21.0          # por AÇÃO, não por lote de mil
    conn.close()
