"""M2 — Ajustes corporativos: detector de saltos + quarentena + série ajustada.

Splits/grupamentos (saltos GRANDES — o detector pega): a razão de preços ao redor do
evento sugere a proporção redonda (1:2, 1:4, 10:1...); o fator entra em `adjustments`.
Salto sem proporção plausível => QUARENTENA (nenhum retorno em quarentena alimenta o
fator).

Dividendos/JCP (pequenos — o detector NÃO pega): ROTA (b) do design §4 — primeira
passada em retorno SÓ-PREÇO. Viés conhecido e DECLARADO: omitir proventos subestima o
retorno total e o viés NÃO é neutro — papéis de momentum tendem a yield menor, então
omitir FAVORECE a estratégia contra o benchmark (viés a nosso favor = o pior tipo).
Registrado no HANDOFF. Rota (a) [proventos de fonte nomeada] fica para quando houver fonte.
"""

_SPLIT_RATIOS = (2, 3, 4, 5, 6, 8, 10)


def overnight_returns(dates, closes):
    """Retornos close-a-close consecutivos: [(date, ret)] a partir do 2º ponto."""
    out = []
    for i in range(1, len(closes)):
        if closes[i - 1] > 0:
            out.append((dates[i], closes[i] / closes[i - 1] - 1.0))
    return out


def detect_jumps(dates, closes, threshold):
    """Datas onde |retorno overnight| > threshold (candidatas a split ou erro)."""
    return [(d, r) for d, r in overnight_returns(dates, closes) if abs(r) > threshold]


def infer_split_factor(close_before, close_after, tol=0.08):
    """Fator a MULTIPLICAR os preços ANTES do evento para a série ficar contínua.
    Split 1:r (preço cai ~r×) => 1/r. Grupamento r:1 (preço sobe ~r×) => r. None se não
    há proporção redonda plausível (=> quarentena)."""
    if close_before <= 0 or close_after <= 0:
        return None
    ratio = close_before / close_after
    for r in _SPLIT_RATIOS:
        if abs(ratio - r) / r < tol:                 # split: preço caiu ~r×
            return round(1.0 / r, 6)
        if abs(ratio - 1.0 / r) / (1.0 / r) < tol:   # grupamento: preço subiu ~r×
            return float(r)
    return None


def adjusted_closes(dates, closes, adjustments):
    """adjustments: [(ex_date, factor)]. Multiplica os closes ANTES de cada ex_date pelo
    fator (cumulativo via aplicação sequencial) — torna a série contínua."""
    out = list(closes)
    for ex_date, factor in adjustments:
        out = [c * factor if d < ex_date else c for d, c in zip(dates, out)]
    return out


# --- integração com o banco (prices_raw -> quarantine / série ajustada) -----

def scan_and_quarantine(conn, threshold) -> int:
    """Por ticker, detecta saltos; salto SEM ajuste registrado em `adjustments` =>
    quarentena. Retorna nº de saltos quarentenados. Não 'conserta' nada na mão — só
    registra a trilha (regra inviolável: nada de fix silencioso)."""
    tickers = [r[0] for r in conn.execute("SELECT DISTINCT ticker FROM prices_raw")]
    n = 0
    for t in tickers:
        rows = conn.execute(
            "SELECT date, close FROM prices_raw WHERE ticker=? ORDER BY date", (t,)).fetchall()
        dates = [r[0] for r in rows]
        closes = [r[1] for r in rows]
        explained = {r[0] for r in conn.execute(
            "SELECT ex_date FROM adjustments WHERE ticker=?", (t,))}
        for d, ret in detect_jumps(dates, closes, threshold):
            if d in explained:
                continue
            conn.execute(
                "INSERT OR IGNORE INTO quarantine(ticker,date,reason,raw_return) "
                "VALUES(?,?,?,?)", (t, d, "salto overnight sem ajuste registrado", round(ret, 4)))
            n += 1
    conn.commit()
    return n


def adjusted_series(conn, ticker):
    """(dates, adjusted_closes) de um ticker, aplicando a tabela `adjustments`."""
    rows = conn.execute(
        "SELECT date, close FROM prices_raw WHERE ticker=? ORDER BY date", (ticker,)).fetchall()
    dates = [r[0] for r in rows]
    closes = [r[1] for r in rows]
    adjustments = [(r[0], r[1]) for r in conn.execute(
        "SELECT ex_date, factor FROM adjustments WHERE ticker=? ORDER BY ex_date", (ticker,))]
    return dates, adjusted_closes(dates, closes, adjustments)


def adjusted_series_oc(conn, ticker):
    """(dates, adjusted_opens, adjusted_closes) — os MESMOS fatores multiplicativos
    valem para qualquer preço do papel (split reescala o livro inteiro). Necessário
    para a execução na abertura de D+1 (execution.price = next_open [H1-FROZEN])."""
    rows = conn.execute(
        "SELECT date, open, close FROM prices_raw WHERE ticker=? ORDER BY date",
        (ticker,)).fetchall()
    dates = [r[0] for r in rows]
    opens = [r[1] for r in rows]
    closes = [r[2] for r in rows]
    adjustments = [(r[0], r[1]) for r in conn.execute(
        "SELECT ex_date, factor FROM adjustments WHERE ticker=? ORDER BY ex_date", (ticker,))]
    return (dates,
            adjusted_closes(dates, opens, adjustments),
            adjusted_closes(dates, closes, adjustments))
