"""M2 — Ajustes corporativos: detector de saltos + quarentena + série ajustada.

Splits/grupamentos (saltos GRANDES — o detector pega): a razão de preços ao redor do
evento sugere a proporção redonda (1:2, 1:4, 10:1...); o fator entra em `adjustments`.
Salto sem proporção plausível => QUARENTENA (nenhum retorno em quarentena alimenta o
fator).

Dividendos/JCP (pequenos — o detector NÃO pega): ROTA (b) do design §4 é a que
TODAS as hipóteses H1-H10 usam — primeira passada em retorno SÓ-PREÇO. Viés
conhecido e DECLARADO: omitir proventos subestima o retorno total e o viés NÃO é
neutro — papéis de momentum tendem a yield menor, então omitir FAVORECE a
estratégia contra o benchmark (viés a nosso favor = o pior tipo). Registrado no
HANDOFF.

ROTA (a) [retorno total, proventos reinvestidos] implementada 2026-09-04 —
`total_return_series` (fonte: CVM/FRE via `ingest_cvm.ingest_fre_dividends_year`,
tabela `dividends`). Opt-in: NÃO substitui `adjusted_series`/rota (b) usada por
H1-H10 já julgadas — usar exige hipótese NOVA, pré-registrada, ciente das
aproximações declaradas (ver docstring de `total_return_series`).

Adjudicação humana (export/import CSV): a IA infere a PROPORÇÃO redonda mas NUNCA grava
em `adjustments` sozinha (§9b/§11 — sem fix silencioso). `export_candidates_csv` lista os
candidatos plausíveis para revisão; `import_approved_adjustments` só grava as linhas que
o humano preencheu com `source` E `approved_by` — o resto fica em quarentena.
"""
import csv
import logging

from db import price_expr
from universe import SPOT_MARKET

logger = logging.getLogger(__name__)

# preço POR AÇÃO (close ÷ quote_factor) — correção na leitura, 2026-07-18
_CLOSE = price_expr("close")

_SPLIT_RATIOS = (2, 3, 4, 5, 6, 8, 10)
_FACTOR_MIN, _FACTOR_MAX = 0.05, 20.0  # faixa de sanidade p/ fator de ajuste
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
    fator (cumulativo via aplicação sequencial) — torna a série contínua.

    Fator <= 0 é dado inválido e levanta ValueError (não entra em silêncio); fator fora
    da faixa de sanidade [_FACTOR_MIN, _FACTOR_MAX] é aplicado mas logado como suspeito."""
    out = list(closes)
    for ex_date, factor in adjustments:
        if not factor > 0:
            raise ValueError(f"fator de ajuste inválido em {ex_date}: {factor!r} (deve ser > 0)")
        if not (_FACTOR_MIN <= factor <= _FACTOR_MAX):
            logger.warning("fator de ajuste suspeito em %s: %.4f (fora de [%.2f, %.0f])",
                           ex_date, factor, _FACTOR_MIN, _FACTOR_MAX)
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
            f"SELECT date, MAX({_CLOSE}) FROM prices_raw WHERE ticker=? AND market_type=? "
            "GROUP BY date ORDER BY date", (t, SPOT_MARKET)).fetchall()
        dates = [r[0] for r in rows]
        closes = [r[1] for r in rows]
        # approved_by IS NOT NULL: um ajuste PENDENTE (ainda não aprovado por humano,
        # §9b/§11) não pode contar como "salto já explicado" — senão o evento nunca
        # entraria em quarentena e sumiria da fila de revisão (achado de revisão de
        # código 2026-08-28, mesma defesa que adjusted_series ganhou abaixo).
        explained = {r[0] for r in conn.execute(
            "SELECT ex_date FROM adjustments WHERE ticker=? AND approved_by IS NOT NULL",
            (t,))}
        for d, ret in detect_jumps(dates, closes, threshold):
            if d in explained:
                continue
            cur = conn.execute(
                "INSERT OR IGNORE INTO quarantine(ticker,date,reason,raw_return) "
                "VALUES(?,?,?,?)", (t, d, "salto overnight sem ajuste registrado", round(ret, 4)))
            n += cur.rowcount   # conta só quarentenas NOVAS (re-execução = 0)
    conn.commit()
    return n


def require_scanned(conn, min_rows=50_000):
    """Fail loud (achado de revisão de código 2026-08-28) se `prices_raw` parece ter
    dado real de bulk (muitas linhas) mas `quarantine`/`adjustments` estão os DOIS
    vazios — sinal forte de que `main.py adjust` nunca rodou neste banco. Sem o
    scan, um split/grupamento real no meio da janela de teste não seria excluído
    nem ajustado: `adjusted_series` devolveria a série CRUA e o momentum/turnover/
    Sharpe seriam corrompidos por um salto overnight falso, sem erro nem aviso.

    `min_rows` é deliberadamente bem acima do maior fixture sintético dos testes
    (poucos milhares de linhas) e bem abaixo de uma carga real de B3 (~1M+) — não
    dispara em dado de teste, dispara em dado de produção nunca escaneado."""
    n_prices = conn.execute("SELECT COUNT(*) FROM prices_raw").fetchone()[0]
    if n_prices < min_rows:
        return
    n_q = conn.execute("SELECT COUNT(*) FROM quarantine").fetchone()[0]
    n_adj = conn.execute("SELECT COUNT(*) FROM adjustments").fetchone()[0]
    if n_q == 0 and n_adj == 0:
        raise RuntimeError(
            f"prices_raw tem {n_prices} linhas mas quarantine/adjustments estão "
            "AMBOS vazios — parece que `main.py adjust` nunca rodou neste banco. "
            "Rode `python main.py adjust` antes do backtest (M2, portão crítico do "
            "design): sem isso, splits/grupamentos reais não seriam excluídos nem "
            "ajustados, corrompendo o Sharpe silenciosamente.")


def adjusted_series(conn, ticker):
    """(dates, adjusted_closes) de um ticker, aplicando a tabela `adjustments`.
    GROUP BY date dedupa re-ingest sob outro source_file. Ajuste com ex_date fora do
    range de preços é IGNORADO com warning (provável erro de fonte/dados incompletos)."""
    rows = conn.execute(
        f"SELECT date, MAX({_CLOSE}) FROM prices_raw WHERE ticker=? AND market_type=? "
        "GROUP BY date ORDER BY date", (ticker, SPOT_MARKET)).fetchall()
    dates = [r[0] for r in rows]
    closes = [r[1] for r in rows]
    adjustments = []
    # approved_by IS NOT NULL: defesa em profundidade (achado de revisão de código
    # 2026-08-28) — hoje o único writer (import_approved_adjustments) já exige
    # approved_by preenchido antes de inserir, mas esta query não pode depender
    # disso silenciosamente; um ajuste PENDENTE nunca deve entrar na série que
    # alimenta o fator/backtest.
    for ex_date, factor in conn.execute(
            "SELECT ex_date, factor FROM adjustments WHERE ticker=? "
            "AND approved_by IS NOT NULL ORDER BY ex_date",
            (ticker,)):
        if dates and (ex_date < dates[0] or ex_date > dates[-1]):
            logger.warning("ajuste de %s em %s fora do range de preços [%s, %s] — ignorado",
                           ticker, ex_date, dates[0], dates[-1])
            continue
        adjustments.append((ex_date, factor))
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
            f"SELECT date, MAX({_CLOSE}) FROM prices_raw WHERE ticker=? AND market_type=? "
            "GROUP BY date ORDER BY date", (tk, SPOT_MARKET)).fetchall()
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


# --- retorno TOTAL (rota (a), 2026-09-04) — opt-in, NÃO substitui rota (b) --

def dividend_factor(close_at_ex: float, value_per_share: float) -> float | None:
    """Fator de ajuste de UM provento — mesma direção de `adjusted_closes`
    (multiplica preços ANTES da ex_date): `close_at_ex / (close_at_ex +
    value_per_share)`. None se `close_at_ex<=0` ou `value_per_share<=0`
    (dado indefinido não vira fator fabricado)."""
    if close_at_ex is None or close_at_ex <= 0 or value_per_share is None or value_per_share <= 0:
        return None
    return close_at_ex / (close_at_ex + value_per_share)


def total_return_series(conn, ticker):
    """(dates, closes) do `ticker` com proventos REINVESTIDOS, em cima da
    série já ajustada por splits (`adjusted_series`) — retorno TOTAL, não
    só-preço. ROTA (a) do design §4, implementada 2026-09-04 (fonte: CVM/FRE,
    `dividends`, ver `ingest_cvm.ingest_fre_dividends_year` para as duas
    aproximações declaradas — `ex_date` é proxy de data de pagamento, valor
    por ação é médio ON+PN).

    Opt-in: NÃO substitui `adjusted_series` (rota (b), só-preço) usada por
    TODAS as hipóteses H1-H10 já julgadas — usar isto exige hipótese NOVA,
    pré-registrada, ciente da rota (a) e suas aproximações (mesma disciplina
    de qualquer mudança de metodologia após rodada julgada)."""
    dates, closes = adjusted_series(conn, ticker)
    if not dates:
        return dates, closes
    divs = conn.execute(
        "SELECT ex_date, value_per_share FROM dividends WHERE ticker=? ORDER BY ex_date",
        (ticker,)).fetchall()
    date_idx = {d: i for i, d in enumerate(dates)}
    adjustments = []
    for ex_date, value_per_share in divs:
        if ex_date < dates[0] or ex_date > dates[-1]:
            logger.warning("provento de %s em %s fora do range de preços [%s, %s] — ignorado",
                           ticker, ex_date, dates[0], dates[-1])
            continue
        # preço de referência: o pregão da própria ex_date, ou o próximo
        # pregão disponível se ex_date cair fora do calendário de negócios
        # (feriado/fim de semana) — nunca um pregão ANTERIOR, que reduziria
        # o fator sem uma base de preço realmente pós-evento.
        i = date_idx.get(ex_date)
        if i is None:
            later = [d for d in dates if d >= ex_date]
            if not later:
                continue
            i = date_idx[later[0]]
        factor = dividend_factor(closes[i], value_per_share)
        if factor is None:
            continue
        adjustments.append((dates[i], factor))
    return dates, adjusted_closes(dates, closes, adjustments)
