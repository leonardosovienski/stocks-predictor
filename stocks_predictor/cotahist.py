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
from datetime import date

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
    if len(raw) != RECORD_LEN:
        raise ValueError(f"registro tipo 01 deve ter {RECORD_LEN} caracteres: {len(raw)}")
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
    day = date.fromisoformat(f"{d[0:4]}-{d[4:6]}-{d[6:8]}").isoformat()
    quote_factor = int(raw[F_FATCOT])
    if quote_factor <= 0:
        raise ValueError("fator de cotação deve ser positivo")
    return {
        "date": day,
        "ticker": raw[F_CODNEG].strip(),
        "bdi_code": raw[F_CODBDI].strip(),
        "market_type": raw[F_TPMERC].strip(),
        "open": int(raw[F_PREABE]) / 100.0,
        "high": int(raw[F_PREMAX]) / 100.0,
        "low": int(raw[F_PREMIN]) / 100.0,
        "close": int(raw[F_PREULT]) / 100.0,
        "qty": int(raw[F_QUATOT]),
        "volume_fin": int(raw[F_VOLTOT]) / 100.0,
        "quote_factor": quote_factor,
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


def _iter_parsed_records(lines, stats):
    """Stream valid records; the terminal checks require consuming the iterator."""
    for line in lines:
        if line[F_TIPREG] != "01":
            continue
        stats['quotes'] += 1
        try:
            rec = parse_line(line)
        except (ValueError, IndexError):
            stats['malformed'] += 1
            continue
        if rec is not None:
            yield rec
    if not stats['quotes']:
        raise ValueError("0 linhas de registro tipo 01 na fonte — arquivo errado, vazio ou layout mudou")
    if stats['malformed'] == stats['quotes']:
        raise ValueError(f"{stats['malformed']} linhas malformadas em {stats['quotes']} "
                         "linhas de cotação — arquivo inteiro ilegível, revisar layout/fonte")


def parse_lines(lines):
    """Parseia linhas posicionais tolerando falhas INDIVIDUAIS: uma linha
    malformada (campos numéricos quebrados etc.) é PULADA e contada — não
    derruba o arquivo inteiro (comportamento anterior: um ValueError solto
    matava a carga de um COTAHIST de anos). Linhas que não são registro tipo
    01 não contam como malformadas (são cabeçalho/trailler/outros tipos).

    Retorna (records, n_malformed). Se TODAS as linhas de cotação forem
    malformadas, levanta ValueError — aí o problema é o arquivo/layout, não
    uma linha podre, e aceitar "zero registros" seria silêncio."""
    stats = {'quotes': 0, 'malformed': 0}
    recs = list(_iter_parsed_records(lines, stats))
    return recs, stats['malformed']


_PRICE_COLUMNS = ('date', 'ticker', 'bdi_code', 'market_type', 'open', 'high',
                  'low', 'close', 'volume_fin', 'qty', 'quote_factor', 'source_file')
_LOAD_BATCH_SIZE = 1000


def _insert_price_batch(conn, rows):
    """Insert new identities; identical replays are harmless, changed ones fail."""
    unique = {}
    for row in rows:
        key = (row[0], row[1], row[-1])
        if key in unique and unique[key] != row:
            raise ValueError(f"source content conflict for {key!r}")
        unique[key] = row
    columns = ','.join(_PRICE_COLUMNS)
    cursor = conn.executemany(
        f"INSERT INTO prices_raw({columns}) VALUES (?,?,?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(date,ticker,source_file) DO NOTHING", unique.values())
    if cursor.rowcount != len(unique):
        # Only replayed batches need comparison; bounded groups also work with
        # SQLite's historical 999-variable limit. No per-row query on new data.
        keys = list(unique)
        for start in range(0, len(keys), 250):
            group = keys[start:start + 250]
            placeholders = ','.join('(?,?,?)' for _ in group)
            params = [value for key in group for value in key]
            for stored in conn.execute(
                    f"SELECT {columns} FROM prices_raw WHERE "
                    f"(date,ticker,source_file) IN ({placeholders})", params):
                row = tuple(stored)
                key = (row[0], row[1], row[-1])
                if row != unique[key]:
                    raise ValueError(f"source content conflict for {key!r}")
    return cursor.rowcount


def load_prices(conn, lines, source_file: str, avista_only: bool = True) -> int:
    """Stream at most one batch, returning the number of genuinely new rows.

    A same-identity content conflict, database error or truncated input rolls back
    the entire load. A caller-owned transaction is never committed. Malformed
    individual records retain the documented skip/count policy of parse_lines.
    """
    if not isinstance(source_file, str) or not source_file.strip():
        raise ValueError("source_file must identify the source")
    stats = {'quotes': 0, 'malformed': 0}
    rows, inserted = [], 0
    conn.execute("SAVEPOINT stocks_price_load")
    try:
        for rec in _iter_parsed_records(lines, stats):
            if avista_only and not is_avista(rec):
                continue
            rows.append(tuple(rec[key] for key in _PRICE_COLUMNS[:-1]) + (source_file,))
            if len(rows) >= _LOAD_BATCH_SIZE:
                inserted += _insert_price_batch(conn, rows)
                rows.clear()
        if rows:
            inserted += _insert_price_batch(conn, rows)
    except BaseException:
        conn.execute("ROLLBACK TO stocks_price_load")
        conn.execute("RELEASE stocks_price_load")
        raise
    conn.execute("RELEASE stocks_price_load")
    if stats['malformed']:
        logger.warning("%s: %d linhas malformadas puladas no parse", source_file, stats['malformed'])
    return inserted
