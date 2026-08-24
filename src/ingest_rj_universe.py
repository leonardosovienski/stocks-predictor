"""Ingestão do universo RJ: snapshots datados da lista oficial da B3.

O problema que isto resolve (viés de sobrevivência do UNIVERSO, não só dos
preços): a lista pública de "emissores em recuperação judicial" da B3 é um
RETRATO DE HOJE — quem saiu (falência decretada, RJ encerrada, deslistagem)
desaparece dela. Construir o universo 2015-2026 a partir da lista atual
recriaria exatamente o viés que o protocolo §3 proíbe ("universo primeiro,
rally depois — incluindo as deslistadas").

Estratégia:
1. `fetch_b3_rj_list` baixa o retrato atual (URL configurável — a B3 muda o
   endpoint com alguma frequência; falha de rede NÃO é silenciada).
2. `save_snapshot` grava cada retrato com data em `rj_universe_snapshots`
   (append-only, migração 0005) — a série histórica de retratos É o dado.
3. `diff_snapshots` gera o changelog (entradas/saídas entre retratos) — as
   saídas são candidatas a encerramento/falência e entram na fila de revisão
   humana com `source`/`approved_by` (mesma disciplina de adjust.py: a IA
   propõe, o humano aprova, nada entra em `rj_universe` sem aprovação).
4. `propose_universe_rows` monta linhas candidatas para revisão.

Fontes complementares para o passado: snapshots da página no Wayback Machine
(`wayback_snapshots` baixa os retratos arquivados de uma URL) e changelogs
públicos de RJ — ambos alimentam a mesma fila de revisão, nunca a tabela
final diretamente.
"""
import hashlib
import json
import logging
import urllib.request
from html.parser import HTMLParser

logger = logging.getLogger(__name__)

# URL configurável: o endpoint da B3 para a lista de emissores em RJ muda;
# o default é a página pública de "empresas listadas em situação especial".
B3_RJ_LIST_URL = (
    "https://www.b3.com.br/pt_br/produtos-e-servicos/negociacao/renda-variavel/"
    "empresas-listadas.htm"
)

# O schema da tabela rj_universe_snapshots vive em db.MIGRATIONS (0005) —
# padrão append-only do projeto; este módulo só consome a tabela.


def fetch_url(url: str, timeout: int = 60) -> bytes:
    """Download fail-loud: qualquer erro de rede propaga como exceção —
    nunca devolve lista vazia fingindo que 'não há empresas em RJ hoje'."""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


class _TableTextParser(HTMLParser):
    """Extrai texto de células de tabelas HTML — tolerante a mudanças de
    layout da página (procura linhas que pareçam ticker + nome)."""
    def __init__(self):
        super().__init__()
        self._in_cell = False
        self._cell = ""
        self.rows: list[list[str]] = []
        self._row: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th"):
            self._in_cell, self._cell = True, ""

    def handle_data(self, data):
        if self._in_cell:
            self._cell += data

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._in_cell:
            self._in_cell = False
            self._row.append(" ".join(self._cell.split()))
        elif tag == "tr" and self._row:
            self.rows.append(self._row)


def parse_b3_rj_list_html(html: bytes | str) -> list[dict]:
    """Extrai [(ticker, company_name)] das tabelas do HTML da B3.

    Heurística deliberadamente simples e auditável: uma linha é candidata se
    contém um token que casa o padrão de ticker B3 (4 letras + dígito, ex.
    AMER3). Tudo que não casa é descartado — melhor perder uma linha do que
    fabricar ticker espúrio no universo (fail-closed)."""
    import re
    text = html.decode("utf-8", errors="replace") if isinstance(html, bytes) else html
    parser = _TableTextParser()
    parser.feed(text)
    ticker_re = re.compile(r"^[A-Z]{4}[0-9]{1,2}$")
    out = []
    for row in parser.rows:
        tickers = [c for c in row if ticker_re.match(c.strip())]
        names = [c for c in row if not ticker_re.match(c.strip()) and len(c) > 3]
        for tk in tickers:
            out.append({"ticker": tk.strip(),
                        "company_name": names[0].strip() if names else ""})
    # dedup preservando ordem
    seen, dedup = set(), []
    for r in out:
        if r["ticker"] not in seen:
            seen.add(r["ticker"])
            dedup.append(r)
    return dedup


def snapshot_hash(rows: list[dict]) -> str:
    payload = json.dumps(rows, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def save_snapshot(conn, rows: list[dict], snapshot_date: str,
                  source: str = "b3_live") -> int:
    """Grava o retrato (append-only: INSERT OR IGNORE — re-baixar o mesmo
    retrato no mesmo dia é idempotente, nunca reescrita)."""
    h = snapshot_hash(rows)
    for r in rows:
        conn.execute(
            "INSERT OR IGNORE INTO rj_universe_snapshots"
            "(snapshot_date, source, ticker, company_name, payload_hash,"
            " raw_payload) VALUES(?,?,?,?,?,?)",
            (snapshot_date, source, r["ticker"], r["company_name"], h,
             json.dumps(r, ensure_ascii=False)))
    conn.commit()
    return len(rows)


def diff_snapshots(conn, source: str = "b3_live") -> dict:
    """Changelog da lista: {'entries': [...], 'exits': [...]} entre retratos
    consecutivos. Saídas são as candidatas críticas (encerramento/falência/
    deslistagem) — sem elas o universo histórico perde justamente os casos
    extremos."""
    snaps = conn.execute(
        "SELECT DISTINCT snapshot_date FROM rj_universe_snapshots "
        "WHERE source=? ORDER BY snapshot_date", (source,)).fetchall()
    changes = {"entries": [], "exits": []}
    prev: set[str] = set()
    for (d,) in snaps:
        cur = {r[0] for r in conn.execute(
            "SELECT ticker FROM rj_universe_snapshots "
            "WHERE snapshot_date=? AND source=?", (d, source))}
        if prev:
            changes["entries"] += [{"date": d, "ticker": t}
                                   for t in sorted(cur - prev)]
            changes["exits"] += [{"date": d, "ticker": t}
                                 for t in sorted(prev - cur)]
        prev = cur
    return changes


def propose_universe_rows(conn) -> list[dict]:
    """Linhas CANDIDATAS de rj_universe a partir dos retratos acumulados:
    primeira aparição de cada ticker vira `rj_request_date` CANDIDATA (a data
    real do pedido sai do processo/fato relevante — revisão humana). Nada é
    gravado em `rj_universe` aqui; retorna a fila para aprovação com
    source+approved_by, mesma disciplina dos ajustes corporativos."""
    rows = conn.execute(
        "SELECT ticker, MIN(snapshot_date) AS first_seen, MAX(company_name)"
        " FROM rj_universe_snapshots GROUP BY ticker ORDER BY first_seen"
    ).fetchall()
    existing = {r[0] for r in conn.execute("SELECT ticker FROM rj_universe")}
    return [{"ticker": t, "company_name": n,
             "rj_request_date_candidate": d,
             "status": "ja_no_universo" if t in existing else "pendente_revisao"}
            for t, d, n in rows]


def ingest_b3_snapshot(conn, snapshot_date: str, url: str = B3_RJ_LIST_URL) -> int:
    """Fluxo completo: baixa -> parse -> grava retrato. Falha de rede ou
    parse vazio levantam exceção (fail-loud) — um retrato vazio NUNCA é
    gravado como se fosse 'lista vazia oficial'."""
    html = fetch_url(url)
    rows = parse_b3_rj_list_html(html)
    if not rows:
        raise ValueError(
            f"parse da lista B3 em {snapshot_date} retornou 0 tickers — "
            "layout da página mudou ou URL errada; NADA foi gravado")
    return save_snapshot(conn, rows, snapshot_date, source="b3_live")
