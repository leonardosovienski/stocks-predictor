"""Ingestão dos dados abertos da CVM para o domínio RJ.

Resolve as duas lacunas de dados que travam a coleta real (todas as fontes
são o Portal de Dados Abertos da CVM — dados.cvm.gov.br):

1. IPE (Informações Periódicas e Eventuais): fatos relevantes com
   **data de entrega no sistema** — essa data é literalmente o `known_at`
   que o protocolo §8 exige (um fato datado de 10/05 mas entregue na noite
   de 11/05 só existe para decisão a partir de 11/05). Sem este campo, as
   famílias `info_trigger` e `ownership` não podem rodar sem lookahead
   informacional.

2. FRE (Formulário de Referência): distribuição do capital social e
   acionistas >=5% — alimenta `free_float` (família `liquidity`, hoje sem
   fonte) e a base para a futura família de migração de base acionária.

Os layouts da CVM usam cabeçalhos com nomes longos e acentuados que mudam de
ano para ano — por isso o parsing é por PALAVRA-CHAVE normalizada (sem
acento, minúsculo), não por nome exato de coluna: perder uma coluna por
renomeação silenciosa é o modo de falha que este módulo existe para evitar.

Fail-loud: arquivo sem as colunas mínimas levanta exceção — nunca grava
evento com known_at fabricado.
"""
import csv
import io
import logging
import unicodedata
import urllib.request
import zipfile

logger = logging.getLogger(__name__)

IPE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_{year}.zip"
FRE_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_{year}.zip"

# palavras-chave (normalizadas) para localizar colunas tolerando renomeações
_IPE_COLS = {
    "company": ("nome_companhia", "nomecompanhia", "companhia"),
    "cnpj": ("cnpj",),
    "delivered_at": ("data_entrega", "dataentrega"),
    "event_ref_date": ("data_referencia", "datareferencia", "data_evento"),
    "category": ("categoria",),
    "type": ("tipo",),
    "subject": ("assunto",),
    "link": ("link_download", "link"),
}
_FRE_FLOAT_COLS = {
    "company": ("nome_companhia", "companhia"),
    "ref_date": ("data_referencia", "datareferencia"),
    "shares_outstanding": ("quantidade_total_acoes", "qtd_acoes_total"),
    "free_float": ("quantidade_acoes_circulacao", "acoes_em_circulacao",
                   "circulacao"),
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return s.lower().replace(" ", "_").strip()


def _find_col(header: list[str], keywords: tuple[str, ...]) -> int | None:
    normed = [_norm(h) for h in header]
    for kw in keywords:
        for i, h in enumerate(normed):
            if kw in h:
                return i
    return None


def download_zip(url: str, timeout: int = 300) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _open_zip_csv(zbytes: bytes, name_contains: str):
    zf = zipfile.ZipFile(io.BytesIO(zbytes))
    names = [n for n in zf.namelist() if name_contains in _norm(n) and n.endswith(".csv")]
    if not names:
        raise ValueError(f"nenhum CSV contendo '{name_contains}' em {zf.namelist()}")
    if len(names) > 1:
        # ambíguo = layout mudou; escolher names[0] na sorte poderia misturar
        # anos/versões sem aviso — fail-loud.
        raise ValueError(
            f"{len(names)} CSVs contendo '{name_contains}' em {zf.namelist()} "
            "— padrão ambíguo, revisar o layout do zip")
    with zf.open(names[0]) as f:
        text = io.TextIOWrapper(f, encoding="latin-1")
        reader = csv.reader(text, delimiter=";")
        yield from reader


def parse_ipe_rows(rows, companies: set[str] | None = None) -> list[dict]:
    """Linhas IPE -> eventos {company, event_date, known_at, category, subject}.

    `known_at` = data de ENTREGA à CVM (nunca a data de referência do fato).
    Linhas sem data de entrega são DESCARTADAS com contagem logada — um
    evento sem known_at confiável não pode alimentar família nenhuma
    (fail-closed informacional). `companies` (nomes normalizados) filtra o
    universo de interesse; None = tudo.

    Fail-loud (regra 4): parse que produz ZERO linhas válidas (antes do
    filtro de companhias) levanta exceção — CSV vazio/truncado ou layout
    quebrado não é "sem fatos no ano". Se o FILTRO de companhias esvaziar
    tudo, também é exceção: provável erro no mapeamento de nomes CVM->B3,
    que deve ser revisado, não engolido. Datas são validadas com
    date.fromisoformat — lote com data malformada levanta exceção com a
    contagem (nunca `[:10]` cego, que aceitaria "11/01/2023" -> "11/01/2023"
    como se fosse ISO)."""
    from datetime import date
    header = None
    idx = {}
    out, dropped, malformed = [], 0, 0
    n_lines = n_valid = 0
    for row in rows:
        if header is None:
            header = row
            idx = {k: _find_col(header, kw) for k, kw in _IPE_COLS.items()}
            if idx["delivered_at"] is None:
                raise ValueError(
                    f"IPE sem coluna de data de entrega; cabeçalho={header}")
            continue
        if len(row) < len(header):
            continue
        n_lines += 1
        company = row[idx["company"]].strip() if idx["company"] is not None else ""
        known_at = row[idx["delivered_at"]].strip()[:10]
        if not known_at:
            dropped += 1
            continue
        ref = row[idx["event_ref_date"]].strip()[:10] if idx["event_ref_date"] is not None else ""
        try:
            date.fromisoformat(known_at)
            if ref:
                date.fromisoformat(ref)
        except ValueError:
            malformed += 1
            continue
        n_valid += 1
        if companies and _norm(company) not in companies:
            continue
        out.append({
            "company": company,
            "cnpj": row[idx["cnpj"]].strip() if idx["cnpj"] is not None else "",
            "event_date": ref or known_at,
            "known_at": known_at,
            "category": row[idx["category"]].strip() if idx["category"] is not None else "",
            "subject": row[idx["subject"]].strip() if idx["subject"] is not None else "",
        })
    if dropped:
        logger.warning("IPE: %d linhas descartadas por falta de data de entrega", dropped)
    if malformed:
        raise ValueError(
            f"IPE: {malformed} linha(s) com data malformada (fora de ISO "
            "YYYY-MM-DD) — lote rejeitado, revisar a fonte antes de ingerir")
    if n_lines == 0 or n_valid == 0:
        raise ValueError(
            "IPE: 0 linhas válidas no parse (antes do filtro de companhias) "
            "— CSV vazio ou layout quebrado; NADA foi ingerido")
    if companies and not out:
        raise ValueError(
            "IPE: filtro de companhias esvaziou TODAS as linhas válidas — "
            "provável erro no mapeamento de nomes CVM->B3; revisar antes "
            "de aceitar 'zero eventos'")
    return out


def parse_fre_float_rows(rows) -> list[dict]:
    """Linhas FRE de distribuição de capital -> {company, ref_date,
    shares_outstanding, free_float}. Sem coluna de circulação: fail-loud,
    porque free_float fabricado contaminaria a família liquidity inteira."""
    header = None
    idx = {}
    out = []
    for row in rows:
        if header is None:
            header = row
            idx = {k: _find_col(header, kw) for k, kw in _FRE_FLOAT_COLS.items()}
            if idx["free_float"] is None:
                raise ValueError(
                    f"FRE sem coluna de ações em circulação; cabeçalho={header}")
            continue
        if len(row) < len(header):
            continue
        def num(col):
            if idx[col] is None or not row[idx[col]].strip():
                return None
            return float(row[idx[col]].replace(".", "").replace(",", "."))
        out.append({
            "company": row[idx["company"]].strip() if idx["company"] is not None else "",
            "ref_date": row[idx["ref_date"]].strip()[:10] if idx["ref_date"] is not None else "",
            "shares_outstanding": num("shares_outstanding"),
            "free_float": num("free_float"),
        })
    return out


def ingest_ipe_year(conn, year: int, companies: set[str] | None = None,
                    ticker_of: dict | None = None) -> int:
    """Baixa o IPE de `year`, filtra as companhias do universo e grava em
    `rj_events` os fatos relevantes com known_at = data de entrega.
    `ticker_of`: mapa nome_companhia_normalizado -> ticker (a ligação
    CVM->B3 é por nome/CNPJ, revisável por humano como tudo o mais)."""
    events = parse_ipe_rows(_open_zip_csv(download_zip(IPE_URL.format(year=year)),
                                          "ipe_cia_aberta"), companies)
    n = 0
    for e in events:
        ticker = (ticker_of or {}).get(_norm(e["company"]))
        if ticker is None:
            continue    # companhia sem ticker mapeado: revisão humana antes
        etype = ("fato_relevante" if "fato" in _norm(e["category"])
                 else "ipe_outro")
        # idempotência por SELECT-before-INSERT (sem UNIQUE novo no schema —
        # migrações já aplicadas não são tocadas): re-executar o ingest do
        # mesmo ano não duplica eventos.
        dup = conn.execute(
            "SELECT 1 FROM rj_events WHERE ticker=? AND event_date=?"
            " AND known_at=? AND event_type=? AND source=?",
            (ticker, e["event_date"], e["known_at"], etype,
             f"CVM IPE {year}")).fetchone()
        if dup:
            continue
        conn.execute(
            "INSERT INTO rj_events(ticker, event_date, known_at, event_type,"
            " source, notes) VALUES(?,?,?,?,?,?)",
            (ticker, e["event_date"], e["known_at"], etype,
             f"CVM IPE {year}", e["subject"][:200]))
        n += 1
    conn.commit()
    return n


def build_ticker_map(cvm_names: list[str],
                     known: dict[str, str] | None = None) -> dict:
    """Mapa nome_companhia_normalizado -> ticker, para revisão humana.

    A ligação CVM->B3 é por nome/CNPJ, e nomes mudam (ex.: "Lojas Americanas"
    -> "Americanas"; "Via Varejo" -> "GPA" tem casos ambíguos). Este mapa é
    gerado como PROPOSTA (`known` recebe os pares já confirmados); qualquer
    pareamento automático novo deve passar pela mesma aprovação humana de
    `source`+`approved_by` que rege ajustes e eventos — um ticker errado aqui
    contamina todos os eventos da empresa."""
    out = dict(known or {})
    for name in cvm_names:
        key = _norm(name)
        if key not in out:
            out[key] = None   # pendente de mapeamento/revisão
    return out


def load_free_float(year: int, companies: set[str] | None = None) -> dict:
    """FRE -> {nome_companhia_normalizado: free_float} do ano (insumo da
    família liquidity via --free-float-csv no rj_pipeline).

    Múltiplas linhas por companhia no mesmo FRE: vale a de MAIOR ref_date
    (determinístico — nunca "a última lida", que dependeria da ordem do
    arquivo)."""
    rows = parse_fre_float_rows(
        _open_zip_csv(download_zip(FRE_URL.format(year=year)),
                      "distribuicao_capital"))
    best: dict[str, tuple[str, float]] = {}
    for r in rows:
        if r["free_float"] is None:
            continue
        key = _norm(r["company"])
        if companies and key not in companies:
            continue
        ref = r["ref_date"] or ""
        if key not in best or ref >= best[key][0]:
            best[key] = (ref, r["free_float"])
    return {k: v for k, (_, v) in best.items()}
