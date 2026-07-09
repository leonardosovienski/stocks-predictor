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

Adjudicação humana (export/import CSV): a IA infere a PROPORÇÃO redonda mas NUNCA grava
em `adjustments` sozinha (§9b/§11 — sem fix silencioso). `export_candidates_csv` lista os
candidatos plausíveis para revisão; `import_approved_adjustments` só grava as linhas que
o humano preencheu com `source` E `approved_by` — o resto fica em quarentena.
"""
import csv

_SPLIT_RATIOS = (2, 3, 4, 5, 6, 8, 10)
_CSV_FIELDS = ("ticker", "ex_date", "close_before", "close_after", "ratio",
               "tipo_inferido", "factor_sugerido", "source", "approved_by", "notes")


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
        # GROUP BY date: re-ingest sob outro source_file duplica (date,ticker) —
        # sem o dedup, o par duplicado viraria um "retorno" espúrio de ~0%.
        rows = conn.execute(
            "SELECT date, MAX(close) FROM prices_raw WHERE ticker=? "
            "GROUP BY date ORDER BY date", (t,)).fetchall()
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
    """(dates, adjusted_closes) de um ticker, aplicando a tabela `adjustments`.
    GROUP BY date dedupa re-ingest sob outro source_file."""
    rows = conn.execute(
        "SELECT date, MAX(close) FROM prices_raw WHERE ticker=? "
        "GROUP BY date ORDER BY date", (ticker,)).fetchall()
    dates = [r[0] for r in rows]
    closes = [r[1] for r in rows]
    adjustments = [(r[0], r[1]) for r in conn.execute(
        "SELECT ex_date, factor FROM adjustments WHERE ticker=? ORDER BY ex_date", (ticker,))]
    return dates, adjusted_closes(dates, closes, adjustments)


# --- adjudicação humana: quarentena -> candidatos com proporção redonda -----

def list_split_candidates(conn, tol=0.08):
    """Quarentena ABERTA cuja proporção de preço bate um split/grupamento redondo.
    Não resolve nada — só ordena o que É plausível de ser um evento corporativo real
    (para o humano confirmar com fonte) do que é ruído de ilíquida/erro."""
    by_ticker: dict[str, list[str]] = {}
    for tk, d in conn.execute(
            "SELECT ticker, date FROM quarantine "
            "WHERE resolved_at IS NULL ORDER BY ticker, date"):
        by_ticker.setdefault(tk, []).append(d)
    out = []
    for tk, qdates in by_ticker.items():
        # série do ticker UMA vez (não por linha de quarentena); GROUP BY date protege
        # contra duplicatas de re-ingest (UNIQUE inclui source_file).
        prices = conn.execute(
            "SELECT date, MAX(close) FROM prices_raw WHERE ticker=? "
            "GROUP BY date ORDER BY date", (tk,)).fetchall()
        idx = {r[0]: i for i, r in enumerate(prices)}
        for d in qdates:
            i = idx.get(d)
            if not i:                                     # ausente ou primeiro pregão
                continue
            cb, ca = prices[i - 1][1], prices[i][1]
            factor = infer_split_factor(cb, ca, tol)
            if factor is None:
                continue
            out.append({
                "ticker": tk, "ex_date": d,
                "close_before": round(cb, 4), "close_after": round(ca, 4),
                "ratio": round(cb / ca, 4) if ca else None,
                "tipo_inferido": "desdobramento" if factor < 1 else "grupamento",
                "factor_sugerido": factor,
                "source": "", "approved_by": "", "notes": "",
            })
    return out


def export_candidates_csv(conn, path, tol=0.08) -> int:
    """Grava os candidatos a split/grupamento em CSV para revisão humana. Colunas
    `source`/`approved_by` ficam em branco — preencha e rode `import_approved_adjustments`
    para gravar em `adjustments` só as linhas explicitamente aprovadas."""
    candidates = list_split_candidates(conn, tol)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
        w.writeheader()
        w.writerows(candidates)
    return len(candidates)


def import_approved_adjustments(conn, path) -> int:
    """Lê o CSV de revisão de volta; grava em `adjustments` SÓ as linhas com `source` E
    `approved_by` preenchidos (write-once via UNIQUE(ticker,ex_date,type) — não
    reescreve linha existente). A quarentena correspondente é RESOLVIDA junto — é a
    aprovação humana explícita (via CSV) que fecha o ciclo, nunca a IA sozinha (§9b/§11).
    Linhas sem aprovação ficam ignoradas (permanecem quarentenadas). Retorna nº de
    ajustes gravados."""
    n = 0
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            source = (row.get("source") or "").strip()
            approved_by = (row.get("approved_by") or "").strip()
            if not source or not approved_by:
                continue
            tipo = "split" if row["tipo_inferido"] == "desdobramento" else "grupamento"
            factor = float(row["factor_sugerido"])
            cur = conn.execute(
                "INSERT OR IGNORE INTO adjustments"
                "(ticker, ex_date, factor, type, source, notes, approved_by) "
                "VALUES (?,?,?,?,?,?,?)",
                (row["ticker"], row["ex_date"], factor, tipo,
                 source, row.get("notes") or None, approved_by))
            if cur.rowcount == 0:
                # write-once: já existe ajuste p/ (ticker, ex_date, type). Se o fator
                # DIVERGE do CSV, a correção NÃO entrou — não podemos resolver a
                # quarentena como se tivesse entrado (série continuaria descontínua
                # com o papel readmitido no universo). Avisar e pular.
                existing = conn.execute(
                    "SELECT factor FROM adjustments WHERE ticker=? AND ex_date=? AND type=?",
                    (row["ticker"], row["ex_date"], tipo)).fetchone()
                if existing is None or abs(existing[0] - factor) > 1e-9:
                    print(f"AVISO: {row['ticker']} {row['ex_date']}: ajuste já existe "
                          f"com fator {existing[0] if existing else '?'} != {factor} do CSV "
                          f"(write-once — linha IGNORADA, quarentena mantida)")
                    continue
                # fator idêntico => re-import idempotente; ok resolver.
            else:
                n += 1
            conn.execute(
                "UPDATE quarantine SET resolved_at=datetime('now'), "
                "resolution=COALESCE(resolution, ?) "
                "WHERE ticker=? AND date=? AND resolved_at IS NULL",
                (f"aprovado por {approved_by} ({source})", row["ticker"], row["ex_date"]))
    conn.commit()
    return n
