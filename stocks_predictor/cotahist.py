"""COTAHIST (B3) — parser posicional + gerador sintético determinístico (M1).

Layout do registro de cotação tipo 01 (245 bytes), posições do documento OFICIAL da B3
(HistoricalQuotations_B3.pdf / SeriesHistoricas_Layout.pdf), VERIFICADAS — não de
memória. Preços (11)V99 têm 2 decimais implícitos (÷100).

Truque do mock (DESIGN §M1): o parser consome uma ITERÁVEL de linhas; `synthetic_cotahist`
cospe linhas no formato posicional EXATO (volatilidade controlada, determinística).
Quando o arquivo real da B3 chegar, troca-se a fonte das linhas — o parser não vê
diferença. Destrava M1–M6 sem o arquivo físico.
"""
import logging
import random

logger = logging.getLogger(__name__)

RECORD_LEN = 245

# Fatias 0-indexed derivadas das posições 1-indexed do layout oficial.
F_TIPREG = slice(0, 2)      # 1-2    fixo "01"
F_DATA = slice(2, 10)       # 3-10   AAAAMMDD
F_CODBDI = slice(10, 12)    # 11-12
F_CODNEG = slice(12, 24)    # 13-24  código de negociação (ticker)
F_TPMERC = slice(24, 27)    # 25-27  tipo de mercado (010 = à vista)
F_PREABE = slice(56, 69)    # 57-69  abertura  (V99)
F_PREMAX = slice(69, 82)    # 70-82  máxima    (V99)
F_PREMIN = slice(82, 95)    # 83-95  mínima    (V99)
F_PREULT = slice(108, 121)  # 109-121 último/fechamento (V99)
F_QUATOT = slice(152, 170)  # 153-170 quantidade total
F_VOLTOT = slice(170, 188)  # 171-188 volume financeiro (V99)
F_FATCOT = slice(210, 217)  # 211-217 fator de cotação


def parse_line(line: str):
    """Parseia uma linha posicional → dict (colunas de prices_raw), ou None se não for
    registro de cotação tipo 01."""
    raw = line.rstrip("\r\n")
    if raw[F_TIPREG] != "01":
        return None
    raw = raw.ljust(RECORD_LEN)
    d = raw[F_DATA]
    # AAAAMMDD tem que ser 8 dígitos — sem essa checagem, um byte corrompido
    # (espaço/lixo em vez de dígito) virava um "date" tipo "2024- x-  " sem
    # levantar exceção nenhuma (os campos numéricos abaixo já quebram com
    # int(), mas data era interpolação de string crua). Uma data assim
    # corrompe silenciosamente a ordenação lexicográfica que TODA query
    # anti-lookahead (`date < ?`, `ORDER BY date DESC`) depende — achado de
    # varredura 2026-09-04. ValueError aqui é capturado e contado como
    # n_bad por parse_lines, mesmo tratamento dos outros campos.
    if not (len(d) == 8 and d.isdigit()):
        raise ValueError(f"data malformada no registro tipo 01: {d!r}")
    return {
        "date": f"{d[0:4]}-{d[4:6]}-{d[6:8]}",
        "ticker": raw[F_CODNEG].strip(),
        "bdi_code": raw[F_CODBDI].strip(),
        "market_type": raw[F_TPMERC].strip(),
        "open": int(raw[F_PREABE]) / 100.0,
        "high": int(raw[F_PREMAX]) / 100.0,
        "low": int(raw[F_PREMIN]) / 100.0,
        "close": int(raw[F_PREULT]) / 100.0,
        "qty": int(raw[F_QUATOT]),
        "volume_fin": int(raw[F_VOLTOT]) / 100.0,
        "quote_factor": int(raw[F_FATCOT]),
    }


def _pack(date, ticker, bdi, tpmerc, o, h, lo, c, qty, vol_fin, fatcot) -> str:
    """Monta uma linha de 245 bytes no formato posicional (para o gerador sintético)."""
    buf = [" "] * RECORD_LEN

    def put(start1, text):
        i = start1 - 1
        buf[i:i + len(text)] = list(text)

    def cents(v, w):
        return str(int(round(v * 100))).zfill(w)

    put(1, "01")
    put(3, str(date).replace("-", ""))
    put(11, str(bdi).rjust(2, "0"))
    put(13, ticker.ljust(12)[:12])
    put(25, str(tpmerc).rjust(3, "0"))
    put(57, cents(o, 13)); put(70, cents(h, 13)); put(83, cents(lo, 13))
    put(96, cents(c, 13))                 # PREMED (filler)
    put(109, cents(c, 13))
    put(148, "00100")                     # TOTNEG (filler)
    put(153, str(int(qty)).zfill(18))
    put(171, cents(vol_fin, 18))
    put(211, str(int(fatcot)).zfill(7))
    return "".join(buf)


def synthetic_cotahist(tickers, dates, seed=42, start=20.0, vol=0.02):
    """Linhas COTAHIST sintéticas (random walk, volatilidade controlada) no formato
    posicional EXATO. Determinístico por seed."""
    rng = random.Random(seed)
    price = {t: start * (1 + 0.05 * i) for i, t in enumerate(tickers)}
    out = []
    for d in dates:
        for t in tickers:
            o = price[t]
            c = max(0.01, o * (1 + rng.gauss(0, vol)))
            h = max(o, c) * (1 + abs(rng.gauss(0, vol / 2)))
            lo = min(o, c) * (1 - abs(rng.gauss(0, vol / 2)))
            qty = rng.randint(1_000, 1_000_000)
            out.append(_pack(d, t, "02", "010", o, h, lo, c, qty, c * qty, 1))
            price[t] = c
    return out


# À-vista lote-padrão: mercado à vista (TPMERC 010) + BDI lote-padrão (02). O COTAHIST
# traz TUDO (opções 070/080 são ~98% do arquivo, termo, fracionário, leilão); a H1
# negocia SÓ ação à-vista lote-padrão — filtrar aqui mantém prices_raw enxuto e o
# "top-N por liquidez" livre de contratos de opção. Append-only-seguro: derivativos
# podem ser acrescentados depois sem reescrever nada.
AVISTA_MARKET = "010"
AVISTA_BDI = "02"


def is_avista(rec) -> bool:
    return rec["market_type"] == AVISTA_MARKET and rec["bdi_code"] == AVISTA_BDI


def parse_lines(lines):
    """Parseia linhas posicionais tolerando falhas INDIVIDUAIS: uma linha
    malformada (campos numéricos quebrados etc.) é PULADA e contada — não
    derruba o arquivo inteiro (comportamento anterior: um ValueError solto
    matava a carga de um COTAHIST de anos). Linhas que não são registro tipo
    01 não contam como malformadas (são cabeçalho/trailler/outros tipos).

    Retorna (records, n_malformed). Se TODAS as linhas de cotação forem
    malformadas, levanta ValueError — aí o problema é o arquivo/layout, não
    uma linha podre, e aceitar "zero registros" seria silêncio."""
    recs, n_bad, n_quote = [], 0, 0
    for line in lines:
        raw = line.rstrip("\r\n")
        if raw[F_TIPREG] != "01":
            continue
        n_quote += 1
        try:
            rec = parse_line(line)
        except (ValueError, IndexError):
            n_bad += 1
            continue
        if rec is not None:
            recs.append(rec)
    if n_quote and n_bad == n_quote:
        raise ValueError(
            f"{n_bad} linhas malformadas em {n_quote} linhas de cotação — "
            "arquivo inteiro ilegível, revisar layout/fonte")
    if n_quote == 0:
        # ZERO registros tipo 01 em toda a fonte — fonte errada (ex.: .TXT
        # não-COTAHIST dentro do zip, layout mudou, arquivo vazio) NUNCA é
        # "sem cotações para carregar": load_prices/parse_cotahist
        # retornariam 0 silenciosamente, sem log e sem exceção (achado de
        # varredura 2026-09-04). Fail-loud aqui é o único lugar que sabe a
        # diferença entre "0 linhas boas" e "0 linhas, ponto".
        raise ValueError(
            "0 linhas de registro tipo 01 na fonte — arquivo errado, vazio "
            "ou layout mudou, revisar antes de aceitar 'zero cotações'")
    return recs, n_bad


def load_prices(conn, lines, source_file: str, avista_only: bool = True) -> int:
    """Parseia linhas (de arquivo ou sintéticas) e carrega em prices_raw. Idempotente
    via UNIQUE(date,ticker,source_file). Por padrão filtra à-vista lote-padrão (a H1 só
    negocia ação à-vista). Retorna nº de registros carregados.

    Linhas malformadas são puladas, contadas e logadas com o nome do arquivo
    (ver `parse_lines`) — nunca derrubam a carga nem passam em silêncio."""
    recs, n_bad = parse_lines(lines)
    if n_bad:
        logger.warning("%s: %d linhas malformadas puladas no parse",
                       source_file, n_bad)
    rows = []
    for rec in recs:
        if avista_only and not is_avista(rec):
            continue
        rows.append((rec["date"], rec["ticker"], rec["bdi_code"], rec["market_type"],
                     rec["open"], rec["high"], rec["low"], rec["close"],
                     rec["volume_fin"], rec["qty"], rec["quote_factor"], source_file))
    conn.executemany(
        "INSERT OR IGNORE INTO prices_raw(date,ticker,bdi_code,market_type,open,high,"
        "low,close,volume_fin,qty,quote_factor,source_file) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    return len(rows)
