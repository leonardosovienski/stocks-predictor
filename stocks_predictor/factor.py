"""M4 — Motor interpretável: momentum 12-1 (série AJUSTADA, point-in-time).

Sinal em `asof` = retorno acumulado de [asof-252, asof-21] (12 meses excluindo o último
— o clássico, evita a reversão de curtíssimo prazo). UM fator só; zoológico proibido até
a H1 ser julgada. Usa apenas preços <= asof.

H2 (pré-registro 2026-07-16, H1 já julgada): `realized_vol` — desvio-padrão dos
retornos diários dos últimos `lookback` pregões ≤ asof. Mesma disciplina
point-in-time; a carteira da H2 toma o quintil INFERIOR (baixa volatilidade).
"""
import datetime
import statistics

import db as db_mod
import universe as universe_mod


def _idx_le(dates, asof):
    """Índice do último pregão <= asof (dates asc), ou None."""
    res = None
    for i, d in enumerate(dates):
        if d <= asof:
            res = i
        else:
            break
    return res


def momentum_12_1(dates, closes, asof, lookback=252, skip=21):
    """Retorno de [asof-lookback] a [asof-skip] na série ajustada. None se histórico
    insuficiente. Point-in-time: nada após asof entra."""
    i = _idx_le(dates, asof)
    if i is None:
        return None
    i_end, i_start = i - skip, i - lookback
    # i_end<0 só ocorre se skip>lookback (config malformada — nenhuma
    # hipótese registrada usa isso hoje); sem esta guarda, `closes[i_end]`
    # indexava por trás (Python) e lia um preço fora da janela pretendida.
    if i_start < 0 or i_end < 0 or closes[i_start] <= 0 or closes[i_end] <= 0:
        return None   # preço <= 0 em qualquer ponta = retorno indefinido
    return closes[i_end] / closes[i_start] - 1.0


def signals(series_by_ticker, asof, lookback=252, skip=21):
    """{ticker: momentum} para os tickers com histórico suficiente em asof."""
    out = {}
    for t, (dates, closes) in series_by_ticker.items():
        m = momentum_12_1(dates, closes, asof, lookback, skip)
        if m is not None:
            out[t] = m
    return out


def realized_vol(dates, closes, asof, lookback=252):
    """Desvio-padrão dos retornos diários da janela [asof-lookback, asof] na série
    ajustada. None se histórico insuficiente ou preço <=0 na janela (sinal
    indefinido > sinal distorcido). Point-in-time: nada após asof entra."""
    i = _idx_le(dates, asof)
    if i is None or i - lookback < 0:
        return None
    window = closes[i - lookback:i + 1]
    if any(c <= 0 for c in window):
        return None
    rets = [window[j] / window[j - 1] - 1.0 for j in range(1, len(window))]
    return statistics.pstdev(rets)


def vol_signals(series_by_ticker, asof, lookback=252):
    """{ticker: vol realizada} para os tickers com histórico suficiente em asof."""
    out = {}
    for t, (dates, closes) in series_by_ticker.items():
        v = realized_vol(dates, closes, asof, lookback)
        if v is not None:
            out[t] = v
    return out


def _fundamental_signals(conn, tickers, asof, disclosure_embargo_days, column,
                         use_known_at=True):
    """Motor comum de sinal contábil point-in-time (H7 ROE, H9 alavancagem):
    {ticker: valor de `column` em `fundamentals`} usando a linha mais recente
    cujo embargo de divulgação já venceu em `asof`.

    `fundamentals.ref_date` é o fim do exercício, não a data de publicação real
    (a DFP só é PUBLICADA meses depois — ver `ingest_cvm.py`). Usar `ref_date`
    puro como `known_at` seria otimista/lookahead. `disclosure_embargo_days`
    soma um embargo fixo: só entra no sinal em `asof` a linha mais recente com
    `ref_date + embargo <= asof` (comparação lexicográfica de datas ISO, dias
    corridos). Ticker sem nenhuma linha elegível fica FORA (dado indisponível
    > dado inventado, mesma disciplina de `vol_signals`/`ownership`)."""
    if column not in ("roe", "leverage", "net_margin", "accruals",
                      "lucro_liquido", "patrimonio_liquido", "shares_outstanding"):
        raise ValueError(f"coluna de fundamentals não suportada: {column!r}")
    out = {}
    for t in tickers:
        rows = conn.execute(
            f"SELECT ref_date, {column}, known_at FROM fundamentals WHERE ticker = ?"
            f" AND {column} IS NOT NULL ORDER BY ref_date DESC", (t,)).fetchall()
        for ref_date, value, observed_at in rows:
            known_at = (observed_at if (use_known_at and observed_at) else (
                datetime.date.fromisoformat(ref_date)
                + datetime.timedelta(days=disclosure_embargo_days)).isoformat())
            if known_at <= asof:
                out[t] = value
                break
    return out


def roe_signals(conn, tickers, asof, disclosure_embargo_days=90):
    """H7 (pré-registro 2026-09-03) — {ticker: roe} point-in-time."""
    # JULGADA: embargo estimado, explicitamente. Ver `_fundamental_signals`.
    return _fundamental_signals(conn, tickers, asof, disclosure_embargo_days,
                                "roe", use_known_at=False)


def leverage_signals(conn, tickers, asof, disclosure_embargo_days=90):
    """H9 (pré-registro 2026-09-04) — {ticker: leverage} point-in-time.
    `leverage = (passivo_total - patrimonio_liquido) / ativo_total`
    (ver `ingest_cvm.compute_fundamentals` — exclui o PL do passivo, senão
    o índice daria sempre ~1.0 por identidade contábil)."""
    # JULGADA: embargo estimado, explicitamente. Ver `_fundamental_signals`.
    return _fundamental_signals(conn, tickers, asof, disclosure_embargo_days,
                                "leverage", use_known_at=False)


def net_margin_signals(conn, tickers, asof, disclosure_embargo_days=90):
    """H12 (pré-registro 2026-09-04) — {ticker: net_margin} point-in-time.
    `net_margin = lucro_liquido / receita_liquida` (ver
    `ingest_cvm.compute_fundamentals`). Mesma fonte/embargo de H7/H9
    (DFP/CVM), motor comum `_fundamental_signals`."""
    # JULGADA: embargo estimado, explicitamente. Ver `_fundamental_signals`.
    return _fundamental_signals(conn, tickers, asof, disclosure_embargo_days,
                                "net_margin", use_known_at=False)


def revenue_growth_signals(conn, tickers, asof, disclosure_embargo_days=90):
    """H13 (pré-registro 2026-09-04) — {ticker: crescimento YoY de receita
    líquida} point-in-time. Primeira hipótese de CRESCIMENTO testada neste
    domínio (H1-H12 são todas nível/valor).

    Diferente de `_fundamental_signals` (que lê 1 linha): precisa das DUAS
    linhas mais RECENTES e ELEGÍVEIS (embargo já vencido em `asof`) de
    `receita_liquida` do ticker — a mais nova é o numerador, a anterior o
    denominador. `growth = (mais_recente - anterior) / anterior`. Como a
    DFP é anual (`ingest_dfp_year`, não ITR trimestral), as duas linhas mais
    recentes elegíveis são tipicamente ~12 meses de distância — mas isso não
    é verificado aqui (dependeria do calendário real de cada empresa); um
    gap maior por dado faltante num ano específico entra do mesmo jeito,
    limitação herdada da granularidade anual da fonte, não escondida.
    Ticker com menos de 2 linhas elegíveis, ou com receita anterior <= 0,
    fica FORA (sem crescimento fabricado sobre denominador inválido)."""
    out = {}
    for t in tickers:
        rows = conn.execute(
            "SELECT ref_date, receita_liquida FROM fundamentals WHERE ticker = ?"
            " AND receita_liquida IS NOT NULL ORDER BY ref_date DESC", (t,)).fetchall()
        eligible = []
        for ref_date, receita in rows:
            # JULGADA: embargo estimado, sem known_at. Ver `_fundamental_signals`.
            known_at = (datetime.date.fromisoformat(ref_date)
                       + datetime.timedelta(days=disclosure_embargo_days)).isoformat()
            if known_at <= asof:
                eligible.append((ref_date, receita))
            if len(eligible) == 2:
                break
        if len(eligible) < 2:
            continue
        (_, latest), (_, previous) = eligible
        if previous is None or previous <= 0:
            continue
        out[t] = (latest - previous) / previous
    return out


def near_52w_high(dates, closes, asof, lookback=252):
    """H14 (pré-registro 2026-09-04) — `close(asof) / max(close nos últimos
    `lookback` pregões incluindo asof)`. Fator de preço distinto de
    momentum (George & Hwang 2004, "52-week high" — proximidade da máxima
    tem poder preditivo próprio, não é redutível ao retorno acumulado que
    momentum mede). Mesma disciplina point-in-time de `momentum_12_1`
    (`_idx_le`, nada após `asof` entra). `None` se histórico insuficiente,
    a máxima da janela for <=0, ou `close(asof)` <=0."""
    i = _idx_le(dates, asof)
    if i is None or i - lookback < 0:
        return None
    window = closes[i - lookback:i + 1]
    high = max(window)
    if high <= 0 or closes[i] <= 0:
        return None
    return closes[i] / high


def near_52w_high_signals(series_by_ticker, asof, lookback=252):
    """{ticker: proximidade da máxima de 52 semanas} para tickers com
    histórico suficiente em asof."""
    out = {}
    for t, (dates, closes) in series_by_ticker.items():
        v = near_52w_high(dates, closes, asof, lookback)
        if v is not None:
            out[t] = v
    return out


def volume_surge_signals(conn, tickers, asof, short_lookback=21, long_lookback=252):
    """H15 (pré-registro 2026-09-04) — {ticker: volume médio recente /
    volume médio de longo prazo − 1} point-in-time. `volume_fin` já vive em
    `prices_raw` desde o M1 (usado só pra ranquear liquidez do universo,
    nunca como SINAL de seleção) — zero ingestão nova.

    Consulta direta em `prices_raw` (não `series_by_ticker`, que só carrega
    preço) — mesmo padrão de `_fundamental_signals` (lê `conn` direto).
    Só os `long_lookback` pregões mais recentes `< asof` (estritamente
    anterior — o volume do próprio dia `asof` não é conhecido antes do
    fechamento, mesma disciplina anti-lookahead do resto do domínio).
    `None` se o ticker tiver menos de `long_lookback` pregões disponíveis
    ou volume médio de longo prazo <=0 (denominador inválido, sem sinal
    fabricado)."""
    out = {}
    for t in tickers:
        rows = conn.execute(
            "SELECT volume_fin FROM prices_raw WHERE ticker=? AND market_type=?"
            " AND date < ? ORDER BY date DESC LIMIT ?",
            (t, universe_mod.SPOT_MARKET, asof, long_lookback)).fetchall()
        if len(rows) < long_lookback:
            continue
        vols = [r[0] for r in rows]    # mais recente primeiro
        long_avg = sum(vols) / len(vols)
        if long_avg <= 0:
            continue
        short_avg = sum(vols[:short_lookback]) / short_lookback
        out[t] = short_avg / long_avg - 1.0
    return out


def accruals_signals(conn, tickers, asof, disclosure_embargo_days=90):
    """H17 (pré-registro 2026-09-04) — {ticker: accruals} point-in-time.

    `accruals = (lucro_liquido − fluxo_caixa_operacional) / ativo_total`
    (Sloan 1996), gravado na ingestão (`ingest_cvm.compute_fundamentals`).
    Mede a fração do lucro que NÃO virou caixa: accrual alto = lucro
    sustentado por reconhecimento contábil, não por caixa.

    Direção pré-registrada: quintil INFERIOR (`take="bottom"`), ou seja
    lucro LASTREADO EM CAIXA. Isso é o que a literatura prevê (accruals
    altos anteciparam retorno FUTURO BAIXO) e está fixado ANTES da rodada —
    testar as duas pontas e ficar com a que der é exatamente o p-hacking
    que o pedágio IC95%+DSR existe para barrar.

    Mesma fonte (DFP/CVM) e mesmo motor `_fundamental_signals` de
    H7/H9/H12/H13 — o que é NOVO é a demonstração de origem (DFC-MI, regime
    de caixa), não a maquinaria.

    RE-PRÉ-REGISTRO 2026-09-06: usa `known_at` OBSERVADO (`DT_RECEB` da DFP)
    quando disponível, com o embargo só como fallback. Legítimo porque a H17
    NUNCA rodou. As julgadas ficam no embargo estimado, explicitamente."""
    return _fundamental_signals(conn, tickers, asof, disclosure_embargo_days,
                                "accruals", use_known_at=True)


def _price_at(conn, ticker, asof):
    """Preço POR AÇÃO do último pregão <= `asof` (fechamento CRU, corrigido
    só pelo fator de cotação da B3), ou None.

    Por que CRU e não a série ajustada: o múltiplo de valor é
    `preço × ações ÷ fundamento`, e as três pernas têm que estar na MESMA
    escala da época. A série ajustada é retro-ajustada por proventos/
    desdobramentos — multiplicá-la pela quantidade de ações VIGENTE naquela
    data daria uma capitalização de mercado que nunca existiu, e o erro
    cresce quanto mais para trás se olha. Para RETORNO a série ajustada é a
    correta (e continua sendo, em todas as hipóteses); para NÍVEL DE PREÇO
    num múltiplo, é o preço cru. Ver `db.price_expr` para o fator de
    cotação (FATCOT)."""
    row = conn.execute(
        f"SELECT MAX({db_mod.price_expr('close')}) FROM prices_raw"
        " WHERE ticker=? AND market_type=? AND date<=?"
        " GROUP BY date ORDER BY date DESC LIMIT 1",
        (ticker, universe_mod.SPOT_MARKET, asof)).fetchone()
    if row is None or row[0] is None or row[0] <= 0:
        return None
    return row[0]


def _value_signals(conn, tickers, asof, disclosure_embargo_days, column):
    """Motor comum dos fatores de VALOR (H18 E/P, H19 B/M):
    {ticker: fundamento / capitalização de mercado} point-in-time.

    `market_cap = preço_cru(asof) × shares_outstanding`, com CADA insumo
    resolvido pelo seu PRÓPRIO caminho point-in-time:

    - `column` (`lucro_liquido` ou `patrimonio_liquido`) vem da linha DFP
      mais recente cujo embargo de divulgação já venceu em `asof`;
    - `shares_outstanding` vem da linha FRE mais recente já PÚBLICA em `asof`
      (por `known_at` observado quando existe, senão pelo embargo —
      formulário DIFERENTE, com data própria; ver
      `ingest_cvm.ingest_fre_shares_year`, que deliberadamente NÃO casa as
      duas datas à força), e é convertida para a base de desdobramento
      vigente em `asof` por `_shares_on_price_base`;
    - o preço é o do último pregão <= `asof`.

    Nada aqui olha para frente: as duas pernas contábeis passam pelo mesmo
    embargo de H7/H9/H12/H13 e o preço é o do próprio dia de rebalance, já
    conhecido no fechamento.

    Ticker fica FORA se faltar qualquer perna, se as ações forem <= 0, ou se
    o fundamento for <= 0. Fundamento negativo (prejuízo, ou patrimônio
    líquido negativo) é dado REAL de empresa em dificuldade, mas o múltiplo
    inverte de sinal e deixa de ser comparável — uma empresa com prejuízo
    enorme apareceria como "baríssima" no ranking. Mesma disciplina do
    `roe` sobre PL negativo em `compute_fundamentals`: None e registrado,
    melhor que um número que engana."""
    fundamento = _fundamental_signals(conn, tickers, asof,
                                      disclosure_embargo_days, column)
    shares = _shares_with_ref_date(conn, tickers, asof, disclosure_embargo_days)
    out = {}
    for t in tickers:
        f = fundamento.get(t)
        par = shares.get(t)
        if f is None or par is None or f <= 0:
            continue
        s = _shares_on_price_base(conn, t, par[0], par[1], asof)
        if s is None or s <= 0:
            continue
        price = _price_at(conn, t, asof)
        if price is None:
            continue
        out[t] = f / (price * s)
    return out


def _shares_with_ref_date(conn, tickers, asof, disclosure_embargo_days):
    """{ticker: (shares_outstanding, ref_date)} point-in-time.

    Igual a `_fundamental_signals` para `shares_outstanding`, mas devolve
    TAMBÉM a `ref_date` da linha escolhida — necessária para saber em que
    base de desdobramento aquela contagem de ações está."""
    out = {}
    for t in tickers:
        rows = conn.execute(
            "SELECT ref_date, shares_outstanding, known_at FROM fundamentals"
            " WHERE ticker = ? AND shares_outstanding IS NOT NULL"
            " ORDER BY ref_date DESC", (t,)).fetchall()
        for ref_date, value, observed_at in rows:
            known_at = observed_at or (
                datetime.date.fromisoformat(ref_date)
                + datetime.timedelta(days=disclosure_embargo_days)).isoformat()
            if known_at <= asof:
                out[t] = (value, ref_date)
                break
    return out


def _shares_on_price_base(conn, ticker, shares, shares_ref_date, asof):
    """Traz `shares` da base do FRE para a base de preço vigente em `asof`.

    O múltiplo é `fundamento / (preço_cru(asof) × ações)`. O preço vem de
    `asof`; as ações vêm da `ref_date` do FRE. Se houve desdobramento ou
    grupamento entre as duas datas, as pernas ficam em BASES DIFERENTES e o
    market cap erra pelo fator do evento — enviesando o ranking justamente
    nos papéis que desdobraram.

    Isto não é hipotético: BBAS3 vai de 2.865.417.024 ações (FRE 2022) para
    5.730.799.931 (FRE 2023), exatamente 2x, no papel mais líquido da bolsa
    (achado da ingestão real 2026-09-05, ver HANDOFF).

    `adjustments.factor` multiplica os PREÇOS anteriores à `ex_date` (ver
    `adjust.adjusted_closes`), então a contagem de ações anterior se converte
    pelo INVERSO: num split 1:2 o preço cai à metade (factor 0,5) e as ações
    dobram. Só eventos de `type` split/grupamento entram — provento não muda
    a quantidade de ações — e só os APROVADOS por humano, mesma disciplina de
    `adjust._load`.

    `ex_date` estritamente MAIOR que `shares_ref_date`: um evento na própria
    data de referência já está refletido na contagem que o FRE publicou.
    """
    if shares is None or not shares_ref_date:
        return shares
    fatores = [r[0] for r in conn.execute(
        "SELECT factor FROM adjustments WHERE ticker = ? AND approved_by IS NOT NULL"
        " AND type IN ('split', 'grupamento')"
        " AND ex_date > ? AND ex_date <= ?",
        (ticker, shares_ref_date, asof))]
    for f in fatores:
        if not f > 0:
            return None     # fator inválido: sem contagem fabricada
        shares = shares / f
    return shares


def earnings_yield_signals(conn, tickers, asof, disclosure_embargo_days=90):
    """H18 (pré-registro 2026-09-04) — {ticker: E/P} point-in-time.
    `E/P = lucro_liquido / (preço × ações)` — o inverso do P/L.

    Usa-se E/P e não P/L de propósito: P/L explode quando o lucro tende a
    zero e é indefinido com prejuízo, o que faria o RANKING depender de um
    polo instável. E/P é monotônico e finito no domínio admitido
    (lucro > 0), então o quintil superior é bem definido.

    Direção pré-registrada: quintil SUPERIOR (`take="top"`) = maior lucro
    por real de preço = mais BARATO. É a direção clássica do fator valor
    (Basu 1977; Fama & French 1992), fixada antes da rodada."""
    return _value_signals(conn, tickers, asof, disclosure_embargo_days,
                          "lucro_liquido")


def book_to_market_signals(conn, tickers, asof, disclosure_embargo_days=90):
    """H19 (pré-registro 2026-09-04) — {ticker: B/M} point-in-time.
    `B/M = patrimonio_liquido / (preço × ações)` — o inverso do P/VPA.

    Fator de valor DISTINTO de E/P (H18), não uma variação da mesma coisa:
    E/P ancora no FLUXO de um exercício (lucro, volátil, afetado por itens
    não recorrentes); B/M ancora no ESTOQUE acumulado (patrimônio líquido,
    estável). É por isso que Fama & French escolheram B/M, e não E/P, para
    o HML — e por isso as duas são hipóteses SEPARADAS aqui, cada uma
    julgada uma vez, com N do DSR próprio. Testar as duas e reportar a
    melhor seria p-hacking.

    Direção pré-registrada: quintil SUPERIOR (`take="top"`) = maior
    patrimônio por real de preço = mais barato."""
    return _value_signals(conn, tickers, asof, disclosure_embargo_days,
                          "patrimonio_liquido")
