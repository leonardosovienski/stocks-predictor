"""Ingestão dos dados abertos da CVM para os domínios RJ e ações.

Resolve as lacunas de dados que travam a coleta real (todas as fontes são o
Portal de Dados Abertos da CVM — dados.cvm.gov.br):

1. IPE (Informações Periódicas e Eventuais): fatos relevantes com
   **data de entrega no sistema** — essa data é literalmente o `known_at`
   que o protocolo §8 exige (um fato datado de 10/05 mas entregue na noite
   de 11/05 só existe para decisão a partir de 11/05). Sem este campo, as
   famílias `info_trigger` e `ownership` não podem rodar sem lookahead
   informacional.

2. FRE (Formulário de Referência): distribuição do capital social e
   acionistas >=5% — alimenta `free_float` (família `liquidity`, hoje sem
   fonte) e a base para a futura família de migração de base acionária.

3. DFP (Demonstrações Financeiras Padronizadas): balanço patrimonial e DRE
   anuais consolidados — insumo da futura H7 (fator de qualidade: ROE/
   alavancagem, ver HANDOFF 2026-08-27). `ref_date` (DT_REFER, fim do
   exercício) é o `known_at` conservador (o dado só é PUBLICADO bem depois
   do fechamento — usar `ref_date` sem embargo adicional é otimista; a H7,
   quando pré-registrada, decide se soma um embargo de divulgação).

Os layouts da CVM usam cabeçalhos com nomes longos e acentuados que mudam de
ano para ano — por isso o parsing é por PALAVRA-CHAVE normalizada (sem
acento, minúsculo), não por nome exato de coluna: perder uma coluna por
renomeação silenciosa é o modo de falha que este módulo existe para evitar.

Fail-loud: arquivo sem as colunas mínimas levanta exceção — nunca grava
evento com known_at fabricado, nunca grava fundamento com conta ambígua.
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
DFP_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{year}.zip"

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
    # ORDEM IMPORTA (achado 2026-09-05, contra o FRE 2023 real): o keyword
    # genérico "circulacao" casava a PRIMEIRA coluna que o contém, que no
    # arquivo real é `Quantidade_Acoes_Ordinarias_Circulacao` — o free float
    # só das ORDINÁRIAS, não o total ON+PN. A coluna total vem primeiro na
    # lista e o catch-all "circulacao" foi REMOVIDO: casar qualquer coluna
    # com "circulacao" no nome é como o erro acontecia.
    "free_float": ("quantidade_total_acoes_circulacao",
                   "quantidade_acoes_circulacao", "acoes_em_circulacao"),
    # Percentual do capital em circulação — a chave para DERIVAR as ações
    # totais (ver `parse_fre_float_rows`). Formato EN neste dataset
    # ("49.596000"), diferente das quantidades: parse próprio, nunca o BR.
    "float_pct": ("percentual_total_acoes_circulacao",),
    # ID do documento — chave de junção com o arquivo PRINCIPAL do FRE, que
    # é onde vive a data de recebimento (`DT_RECEB`). Por documento, logo
    # por VERSÃO: uma retificação tem ID próprio e data própria.
    "doc_id": ("id_documento",),
}
_DFP_COLS = {
    "cnpj": ("cnpj_cia",),
    "company": ("denom_cia",),
    "ref_date": ("dt_refer",),
    "order": ("ordem_exerc",),
    "account_code": ("cd_conta",),
    "account_desc": ("ds_conta",),
    "value": ("vl_conta",),
}
# CD_CONTA padrão do plano de contas CVM (BPA/BPP consolidados) — estável
# entre anos para companhias NÃO financeiras. Cruzado com DS_CONTA
# (palavra-chave) como checagem de sanidade: código bate mas descrição não
# contém a palavra esperada = suspeito, linha descartada com aviso (nunca
# um número fabricado). Companhias financeiras (bancos/seguradoras) usam
# plano de contas diferente e podem não casar — ficam de fora silenciosamente
# nesta 1ª versão (registrado, não escondido: ver `ingest_dfp_year`).
_ASSET_TOTAL_CODE = "1"
_ASSET_TOTAL_KEYWORDS = ("ativo_total",)
_LIABILITY_TOTAL_CODE = "2"
_LIABILITY_TOTAL_KEYWORDS = ("passivo_total",)
_EQUITY_CODE = "2.03"
_EQUITY_KEYWORDS = ("patrimonio_liquido_consolidado", "patrimonio_liquido")
# DRE: código do lucro/prejuízo do período varia mais entre companhias
# (financeiras vs. não financeiras usam DRE distintas) — casado só por
# DESCRIÇÃO (mais estável que código aqui), exigindo "lucro"/"prejuizo" E
# "periodo" na mesma linha para não pegar subtotal intermediário.
_NET_INCOME_KEYWORDS_ALL = ("periodo",)
_NET_INCOME_KEYWORDS_ANY = ("lucro", "prejuizo")
# Receita líquida (DRE) — insumo da H12 (margem)/H13 (crescimento YoY),
# pré-registradas 2026-09-04. Código 3.01 do plano de contas CVM
# ("Receita de Venda de Bens e/ou Serviços"), cruzado com "receita" na
# descrição (mesma checagem de sanidade dos outros campos).
_REVENUE_CODE = "3.01"
_REVENUE_KEYWORDS = ("receita",)
# DFC-MI (Demonstração de Fluxo de Caixa, método indireto, consolidada) —
# insumo da H17 (accruals), pré-registrada 2026-09-04. Código 6.01 do plano
# de contas CVM ("Caixa Líquido Atividades Operacionais"), cruzado com
# "caixa" E "operacional" na descrição (mesma checagem de sanidade dos
# outros campos: código sozinho já mudou de significado entre layouts em
# outros datasets da CVM, descrição sozinha casa subtotal).
#
# Por que esta é a PRIMEIRA demonstração nova desde o M2: BPA (ativo), BPP
# (passivo/PL) e DRE (resultado) são todas de COMPETÊNCIA — o mesmo regime
# contábil, com os mesmos graus de liberdade de reconhecimento. A DFC é de
# CAIXA. Nenhuma combinação de BPA/BPP/DRE reconstrói o fluxo de caixa
# operacional; é dado genuinamente novo, não recombinação (ver
# RESEARCH_FREEZE §11, que nomeia "fluxo de caixa" como fonte materialmente
# nova admissível).
_CASHFLOW_OPS_CODE = "6.01"
_CASHFLOW_OPS_KEYWORDS_ALL = ("caixa", "operaciona")


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


def _open_fre_distribuicao_capital_main(zbytes: bytes):
    """Abre o CSV `distribuicao_capital` PRINCIPAL de um zip FRE (não o
    `_classe_acao`). `_open_zip_csv` recusa o nome puro por ambiguidade —
    "distribuicao_capital" bate tanto no arquivo principal quanto no
    "_classe_acao" (substring) — então filtra à mão excluindo
    "classe_acao" do nome. Único ponto de verdade para essa seleção;
    reutilizado por `load_free_float` e `ingest_fre_dividends_year`."""
    zf = zipfile.ZipFile(io.BytesIO(zbytes))
    candidates = [n for n in zf.namelist()
                 if "distribuicao_capital" in _norm(n) and "classe_acao" not in _norm(n)
                 and n.endswith(".csv")]
    if len(candidates) != 1:
        raise ValueError(
            f"esperava 1 CSV 'distribuicao_capital' (sem classe_acao), achei "
            f"{len(candidates)}: {candidates}")
    with zf.open(candidates[0]) as f:
        text = io.TextIOWrapper(f, encoding="latin-1")
        reader = csv.reader(text, delimiter=";")
        yield from reader


def parse_fre_float_rows(rows) -> list[dict]:
    """Linhas FRE de distribuição de capital -> {company, ref_date,
    shares_outstanding, free_float}. Sem coluna de circulação: fail-loud,
    porque free_float fabricado contaminaria a família liquidity inteira.

    COLISÃO DE COLUNA (achado de auditoria 2026-09-04 — era BUG SILENCIOSO):
    `_find_col` casa por SUBSTRING, e as duas chaves de quantidade colidem
    no cabeçalho real da CVM. O arquivo
    `fre_cia_aberta_distribuicao_capital_{ano}.csv` publica
    `Quantidade_Total_Acoes_Circulacao` — que CONTÉM a substring
    `quantidade_total_acoes` procurada por `shares_outstanding` E a
    substring `circulacao` procurada por `free_float`. As duas chaves
    resolviam para a MESMA coluna, e `shares_outstanding` recebia
    silenciosamente o FREE FLOAT: a capitalização de mercado de H18/H19
    ficava subestimada pelo percentual de ações em circulação, e o
    ranking de "valor" virava um ranking de concentração acionária.

    Defesa: se `shares_outstanding` resolver para a MESMA coluna que
    `free_float`, o cabeçalho NÃO distingue as duas quantidades — então
    `shares_outstanding` é `None` (desconhecido), nunca o valor da outra
    coluna. `free_float` continua intacto (a coluna de circulação É o que
    a família liquidity quer), então nenhum caminho que já funcionava
    muda de comportamento. Quem precisa de ações totais descobre a
    ausência no fail-loud de `ingest_fre_shares_year`, não num número
    plausível e errado.
    """
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
            if idx["shares_outstanding"] == idx["free_float"]:
                # O cabeçalho real da CVM cai SEMPRE aqui: só existe a coluna
                # de circulação. Dois desfechos MUITO diferentes, e o nível de
                # log distingue os dois (achado de operação 2026-09-05: a
                # mensagem anterior anunciava "shares_outstanding=None" e
                # calava que a derivação acontecia em seguida — assustava sem
                # informar, que é o pior tipo de aviso).
                idx["shares_outstanding"] = None
                if idx.get("float_pct") is not None:
                    logging.info(
                        "FRE: sem coluna de ações totais (%r é circulação) — "
                        "total DERIVADO de circulação ÷ percentual",
                        header[idx["free_float"]])
                else:
                    logging.warning(
                        "FRE: sem coluna de ações totais (%r é circulação) e "
                        "sem coluna de percentual — não há como derivar; "
                        "shares_outstanding fica None. cabecalho=%s",
                        header[idx["free_float"]], header)
            continue
        if len(row) < len(header):
            continue
        def num(col):
            if idx[col] is None or not row[idx[col]].strip():
                return None
            return float(row[idx[col]].replace(".", "").replace(",", "."))
        float_shares = num("free_float")
        shares = num("shares_outstanding")
        if shares is None:
            shares = _derive_total_shares(float_shares, _pct(row, idx))
        i_doc = idx.get("doc_id")
        out.append({
            "company": row[idx["company"]].strip() if idx["company"] is not None else "",
            "ref_date": row[idx["ref_date"]].strip()[:10] if idx["ref_date"] is not None else "",
            "shares_outstanding": shares,
            "free_float": float_shares,
            "doc_id": row[i_doc].strip() if i_doc is not None and i_doc < len(row) else "",
        })
    return out


_FRE_MAIN_COLS = {
    "doc_id": ("id_doc",),
    "received_at": ("dt_receb",),
}


def parse_fre_received_dates(zbytes: bytes) -> dict[str, str]:
    """{ID_DOC: DT_RECEB} do arquivo PRINCIPAL do FRE.

    `DT_RECEB` é a data em que a CVM RECEBEU o documento — o instante a
    partir do qual ele é público. É o `known_at` OBSERVADO, análogo exato do
    `Data_Entrega` que `ingest_ipe_year` já usa para fatos relevantes.

    Por que isso importa mais que um embargo (achado 2026-09-05): a
    `DT_REFER` do FRE é rótulo de exercício, não data do dado. No FRE 2023 a
    referência (2023-12-31) é POSTERIOR ao recebimento (2023-05-30) — somar
    dias a esse campo não produz nada interpretável, e o erro de fazê-lo
    troca de SINAL entre as convenções pré e pós-2023.

    Ausência do arquivo principal ou das colunas devolve `{}` — o chamador
    grava `known_at` NULL e o consumidor cai no embargo, sem inventar data.
    """
    zf = zipfile.ZipFile(io.BytesIO(zbytes))
    alvo = [n for n in zf.namelist()
            if n.endswith(".csv") and _norm(n).split("/")[-1].startswith("fre_cia_aberta_")
            and _norm(n).split("/")[-1].count("_") == 3]
    if len(alvo) != 1:
        logging.warning("FRE: arquivo principal não identificado (%d candidatos) — "
                        "known_at ficará NULL", len(alvo))
        return {}
    with zf.open(alvo[0]) as f:
        rows = csv.reader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";")
        header = next(rows, None)
        if header is None:
            return {}
        idx = {k: _find_col(header, kw) for k, kw in _FRE_MAIN_COLS.items()}
        if idx["doc_id"] is None or idx["received_at"] is None:
            logging.warning("FRE: arquivo principal sem ID_DOC/DT_RECEB "
                            "(cabecalho=%s) — known_at ficará NULL", header)
            return {}
        out = {}
        for row in rows:
            if max(idx["doc_id"], idx["received_at"]) >= len(row):
                continue
            doc, receb = row[idx["doc_id"]].strip(), row[idx["received_at"]].strip()[:10]
            if doc and receb:
                out[doc] = receb
        return out


def _pct(row, idx) -> float | None:
    """Percentual do capital em circulação. Formato EN neste dataset da CVM
    ("49.596000" = 49,596%), ao contrário das QUANTIDADES no mesmo arquivo
    (inteiros sem separador). Parsear este campo com a convenção BR
    (remover ".") multiplicaria o valor por 10^6 em silêncio — o mesmo modo
    de falha que `_to_float` já documenta para `Montante`."""
    i = idx.get("float_pct")
    if i is None or i >= len(row) or not row[i].strip():
        return None
    try:
        return float(row[i].strip())
    except ValueError:
        return None


def _derive_total_shares(float_shares: float | None,
                         pct: float | None) -> float | None:
    """Ações TOTAIS emitidas = ações em circulação ÷ (percentual ÷ 100).

    Por que derivar (achado 2026-09-05, confirmado contra o FRE 2023 real):
    `fre_cia_aberta_distribuicao_capital` **não publica** a quantidade total
    de ações emitidas. Publica, por classe e no total, apenas a quantidade
    EM CIRCULAÇÃO e o PERCENTUAL que ela representa do capital — e a razão
    entre os dois recupera o total exatamente.

    Verificado contra o arquivo real: para as três primeiras companhias de
    2023, o total derivado da linha TOTAL bate com a soma dos totais
    derivados das pernas ON e PN a menos de 1e-4 relativo (só arredondamento
    dos 6 decimais do percentual). BCO BRASIL: 2.842.247.534 / 0,49596 =
    5.730.799.931 ações — a contagem real da companhia.

    `None` (nunca um número fabricado) se faltar qualquer perna, se o
    percentual estiver fora de (0, 100], ou se o total derivado ficar MENOR
    que as ações em circulação — que é contábilmente impossível e denuncia
    percentual ou quantidade corrompidos."""
    if float_shares is None or pct is None:
        return None
    if not (0.0 < pct <= 100.0):
        return None
    total = float_shares / (pct / 100.0)
    if total < float_shares:
        return None
    return total


def parse_dfp_statement_rows(rows, statement: str) -> list[dict]:
    """Linhas de UM demonstrativo DFP (BPA_con/BPP_con/DRE_con) ->
    [{company, cnpj, ref_date, account_code, account_desc, value}].

    Filtra ORDEM_EXERC='ÚLTIMO': o CVM inclui, na MESMA tabela, uma coluna de
    comparação do exercício ANTERIOR ('PENÚLTIMO') — incluir as duas
    duplicaria patrimônio/lucro de um ano que já tem seu próprio arquivo
    DFP (o do ano anterior). Fail-loud: sem VL_CONTA/CD_CONTA/DS_CONTA/
    ORDEM_EXERC no cabeçalho, ou zero linhas 'ÚLTIMO' válidas, exceção —
    nunca um demonstrativo vazio silencioso."""
    header = None
    idx = {}
    out = []
    for row in rows:
        if header is None:
            header = row
            idx = {k: _find_col(header, kw) for k, kw in _DFP_COLS.items()}
            missing = [k for k in ("ref_date", "order", "account_desc", "value")
                      if idx[k] is None]
            if missing:
                raise ValueError(
                    f"DFP {statement} sem coluna(s) {missing}; cabeçalho={header}")
            continue
        if len(row) < len(header):
            continue
        if _norm(row[idx["order"]]) != "ultimo":
            continue    # descarta a coluna de comparação do exercício anterior
        val = row[idx["value"]].strip()
        if not val:
            continue
        out.append({
            "company": row[idx["company"]].strip() if idx["company"] is not None else "",
            "cnpj": row[idx["cnpj"]].strip() if idx["cnpj"] is not None else "",
            "ref_date": row[idx["ref_date"]].strip()[:10],
            "account_code": row[idx["account_code"]].strip() if idx["account_code"] is not None else "",
            "account_desc": row[idx["account_desc"]].strip(),
            "value": float(val.replace(".", "").replace(",", ".")),
        })
    if not out:
        raise ValueError(
            f"DFP {statement}: 0 linhas válidas (ORDEM_EXERC='ÚLTIMO') — "
            "arquivo vazio ou layout quebrado; NADA foi ingerido")
    return out


def _pick_account(rows: list[dict], code: str | None,
                  keywords_all: tuple[str, ...],
                  keywords_any: tuple[str, ...] = ()) -> dict[tuple[str, str], float]:
    """{(company_normalizado, ref_date): valor} da conta que bate `code`
    (quando informado) E contém todas as palavras de `keywords_all` E ao
    menos uma de `keywords_any` (quando informado) na descrição normalizada.
    Múltiplas linhas casando a MESMA (company, ref_date) é ambiguidade —
    marcada com None e removida no chamador (fail-closed, nunca 'a última
    lida')."""
    found: dict[tuple[str, str], float | None] = {}
    for r in rows:
        if code is not None and r["account_code"] != code:
            continue
        desc = _norm(r["account_desc"])
        if not all(kw in desc for kw in keywords_all):
            continue
        if keywords_any and not any(kw in desc for kw in keywords_any):
            continue
        key = (_norm(r["company"]), r["ref_date"])
        if key in found:
            found[key] = None      # ambíguo: mais de uma conta bateu
        else:
            found[key] = r["value"]
    return {k: v for k, v in found.items() if v is not None}


def compute_fundamentals(bpa_rows: list[dict], bpp_rows: list[dict],
                         dre_rows: list[dict],
                         dfc_rows: list[dict] | None = None) -> list[dict]:
    """BPA+BPP+DRE(+DFC) já parseados -> [{company, ref_date, ativo_total,
    passivo_total, patrimonio_liquido, lucro_liquido, roe, leverage,
    receita_liquida, net_margin, fluxo_caixa_operacional, accruals}].

    `dfc_rows` (H17, pré-registro 2026-09-04) é OPCIONAL e default `None` —
    chamador que não passa DFC recebe as mesmas linhas de antes com
    `fluxo_caixa_operacional`/`accruals` em `None`. H7-H16 e seus testes
    não mudam de comportamento.

    `accruals = (lucro_liquido - fluxo_caixa_operacional) / ativo_total`
    (Sloan 1996): a parte do lucro que NÃO virou caixa, escalada pelo ativo.
    Grupo de elegibilidade PRÓPRIO (lucro + fco + ativo resolvidos sem
    ambiguidade), independente dos outros dois — mesma disciplina que
    `receita_liquida`/`net_margin` já seguem. `ativo_total <= 0` -> `None`
    (denominador inválido, sem ratio fabricado).

    `receita_liquida`/`net_margin` (H12/H13, pré-registro 2026-09-04) usam
    seu PRÓPRIO critério de elegibilidade (`lucro` + `receita` resolvidos
    sem ambiguidade), independente de `roe`/`leverage` — uma companhia com
    receita e lucro mas sem PL resolvido ainda ganha `net_margin` (roe/
    leverage ficam `None` para ela). A linha só existe se PELO MENOS UM dos
    dois grupos (roe/leverage OU receita/net_margin) resolver; cada valor
    individual é `None` quando seu próprio grupo de contas não resolveu —
    nunca um ratio fabricado misturando contas de linhas diferentes.
    `net_margin` fica `None` se `receita_liquida` <= 0.

    ARMADILHA do plano de contas padronizado CVM (registrada aqui para não
    repetir o erro): `CD_CONTA "2" - Passivo Total` no BPP JÁ INCLUI o
    Patrimônio Líquido (2.01 Circulante + 2.02 Não Circulante + 2.03 PL) —
    por identidade contábil, `passivo_total` (CD 2) SEMPRE bate com
    `ativo_total` (CD 1). Um `leverage = passivo_total / ativo_total`
    ingênuo daria sempre ~1.0 (índice inútil). `passivo_total` gravado é
    o valor CRU do CD_CONTA "2" (útil como checagem de integridade contra
    `ativo_total`); `leverage` é calculado como dívida EXCLUINDO patrimônio:
    `(passivo_total - patrimonio_liquido) / ativo_total`.

    Só entra (company, ref_date) com AS QUATRO contas resolvidas sem
    ambiguidade — ratio calculado com conta faltante seria pior que não
    calcular (fail-closed). roe/leverage ficam None se o denominador for
    <=0 (patrimônio negativo/zero é dado real de empresa em dificuldade,
    mas ROE sobre PL negativo inverte o sinal do índice e não é comparável
    — melhor None e registrado do que um número que engana)."""
    ativo = _pick_account(bpa_rows, _ASSET_TOTAL_CODE, _ASSET_TOTAL_KEYWORDS)
    passivo = _pick_account(bpp_rows, _LIABILITY_TOTAL_CODE, _LIABILITY_TOTAL_KEYWORDS)
    pl = _pick_account(bpp_rows, _EQUITY_CODE, _EQUITY_KEYWORDS)
    lucro = _pick_account(dre_rows, None, _NET_INCOME_KEYWORDS_ALL, _NET_INCOME_KEYWORDS_ANY)
    receita = _pick_account(dre_rows, _REVENUE_CODE, _REVENUE_KEYWORDS)
    fco = _pick_account(dfc_rows or [], _CASHFLOW_OPS_CODE, _CASHFLOW_OPS_KEYWORDS_ALL)
    roe_leverage_keys = set(ativo) & set(passivo) & set(pl) & set(lucro)
    margin_keys = set(lucro) & set(receita)
    accrual_keys = set(lucro) & set(fco) & set(ativo)
    keys = roe_leverage_keys | margin_keys | accrual_keys
    out = []
    for company, ref_date in sorted(keys):
        key = (company, ref_date)
        row = {"company": company, "ref_date": ref_date,
              "ativo_total": None, "passivo_total": None,
              "patrimonio_liquido": None, "lucro_liquido": None,
              "roe": None, "leverage": None,
              "receita_liquida": None, "net_margin": None,
              "fluxo_caixa_operacional": None, "accruals": None}
        if key in roe_leverage_keys:
            a, p, e, l = ativo[key], passivo[key], pl[key], lucro[key]
            row.update({
                "ativo_total": a, "passivo_total": p,
                "patrimonio_liquido": e, "lucro_liquido": l,
                "roe": (l / e) if e > 0 else None,
                "leverage": ((p - e) / a) if a > 0 else None,
            })
        if key in margin_keys:
            l, r = lucro[key], receita[key]
            row["lucro_liquido"] = l    # mesmo valor em ambos os grupos
            row["receita_liquida"] = r
            row["net_margin"] = (l / r) if r > 0 else None
        if key in accrual_keys:
            l, c, a = lucro[key], fco[key], ativo[key]
            row["lucro_liquido"] = l    # mesmo valor dos outros grupos
            row["ativo_total"] = a      # idem
            row["fluxo_caixa_operacional"] = c
            row["accruals"] = ((l - c) / a) if a > 0 else None
        out.append(row)
    return out


def ingest_dfp_year(conn, year: int, companies: set[str] | None = None,
                    ticker_of: dict | None = None, zbytes: bytes | None = None) -> int:
    """Baixa o DFP consolidado de `year`, calcula ROE/alavancagem por
    companhia e grava em `fundamentals`. `ticker_of`: mesmo mapa
    nome_companhia_normalizado -> ticker de `ingest_ipe_year` (ligação
    CVM->B3 revisável por humano). Companhias sem as 4 contas resolvidas
    (comum em financeiras, plano de contas diferente — ver módulo) ficam
    de fora, contadas no aviso, nunca com ratio fabricado.

    `zbytes`: bytes do zip já baixado, opcional — evita rebaixar o mesmo
    ano quando o chamador precisa gravar o mesmo balanço sob tickers
    diferentes (ex.: ON+PN da mesma empresa, ver `tools/ingest_h7_real.py`).
    None (padrão) baixa como sempre."""
    if zbytes is None:
        zbytes = download_zip(DFP_URL.format(year=year))
    bpa = parse_dfp_statement_rows(_open_zip_csv(zbytes, "bpa_con"), "BPA_con")
    bpp = parse_dfp_statement_rows(_open_zip_csv(zbytes, "bpp_con"), "BPP_con")
    dre = parse_dfp_statement_rows(_open_zip_csv(zbytes, "dre_con"), "DRE_con")
    # DFC-MI (H17, pré-registro 2026-09-04). Ausência do CSV é TOLERADA com
    # aviso, não fail-loud: o método indireto é o usual mas a companhia pode
    # publicar DFC-MD (método direto), e anos antigos do dataset podem não
    # trazer o arquivo. Nesse caso `accruals` fica None para o ano inteiro e
    # os tickers simplesmente ficam fora do sinal da H17 (dado indisponível >
    # dado inventado) — o resto da ingestão (H7/H9/H12/H13) segue intacto.
    try:
        dfc = parse_dfp_statement_rows(_open_zip_csv(zbytes, "dfc_mi_con"), "DFC_MI_con")
    except ValueError as exc:
        logger.warning("DFP %d: DFC-MI indisponível (%s) — accruals ficam NULL neste ano",
                       year, exc)
        dfc = None
    fundamentals = compute_fundamentals(bpa, bpp, dre, dfc)
    n = 0
    for f in fundamentals:
        if companies and f["company"] not in companies:
            continue
        ticker = (ticker_of or {}).get(f["company"])
        if ticker is None:
            continue    # companhia sem ticker mapeado: revisão humana antes
        conn.execute(
            "INSERT INTO fundamentals"
            "(ticker, ref_date, ativo_total, passivo_total, patrimonio_liquido,"
            " lucro_liquido, roe, leverage, receita_liquida, net_margin,"
            " fluxo_caixa_operacional, accruals, source)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(ticker, ref_date, source) DO UPDATE SET"
            # backfill APENAS quando a linha existente ainda não tem
            # receita/margem (rodadas de ingest anteriores à migração
            # 0010_fundamentals_revenue, H12/H13 2026-09-04) — nunca
            # sobrescreve um valor já preenchido, e não conta como
            # "mudança" num re-run comum (mesmo dado, WHERE não bate),
            # preservando a idempotência já testada (re-executar o mesmo
            # ano não duplica NEM recontabiliza).
            # Backfill de colunas acrescentadas DEPOIS de rodadas de ingest
            # anteriores (receita/margem na 0010; fluxo de caixa/accruals na
            # 0011, H17 2026-09-04). COALESCE garante a regra que já valia:
            # só preenche o que está NULL, NUNCA sobrescreve valor existente.
            # O WHERE em OR dispara quando QUALQUER um dos dois grupos tem
            # buraco a preencher — com ambos já preenchidos o WHERE é falso e
            # o re-run não conta como mudança, preservando a idempotência já
            # testada (re-executar o mesmo ano não duplica NEM recontabiliza).
            " receita_liquida = COALESCE(fundamentals.receita_liquida,"
            " excluded.receita_liquida),"
            " net_margin = COALESCE(fundamentals.net_margin, excluded.net_margin),"
            " fluxo_caixa_operacional = COALESCE(fundamentals.fluxo_caixa_operacional,"
            " excluded.fluxo_caixa_operacional),"
            " accruals = COALESCE(fundamentals.accruals, excluded.accruals)"
            " WHERE (fundamentals.receita_liquida IS NULL"
            " AND excluded.receita_liquida IS NOT NULL)"
            " OR (fundamentals.fluxo_caixa_operacional IS NULL"
            " AND excluded.fluxo_caixa_operacional IS NOT NULL)",
            (ticker, f["ref_date"], f["ativo_total"], f["passivo_total"],
             f["patrimonio_liquido"], f["lucro_liquido"], f["roe"], f["leverage"],
             f["receita_liquida"], f["net_margin"],
             f["fluxo_caixa_operacional"], f["accruals"], f"CVM DFP {year}"))
        n += conn.execute("SELECT changes()").fetchone()[0]
    conn.commit()
    return n


_DIVIDEND_COLS = {
    "cnpj": ("cnpj_companhia",),
    "company": ("nome_companhia",),
    "pay_date": ("data_pagamento_dividendo",),
    "amount": ("montante",),
}
_CAPITAL_TOTAL_COLS = {
    "cnpj": ("cnpj_companhia",),
    "total_shares": ("quantidade_total_acoes_circulacao",),
}


def _to_float(raw: str, fmt: str) -> float | None:
    """Converte string numérica da CVM para float. CVM mistura formato entre
    datasets (DFP/FRE-float usam vírgula decimal BR com ponto de milhar;
    FRE-dividendos `Montante` observado usa ponto decimal puro, sem milhar).
    Adivinhar o formato olhando só a string é ambíguo — "450.000" é 450 em
    inglês e 450000 em BR — então `fmt` é OBRIGATÓRIO e escolhido pelo
    chamador de acordo com o dataset/coluna, nunca inferido em silêncio:

    - `fmt="en"`: ponto decimal, sem separador de milhar (`float(raw)` puro).
    - `fmt="br"`: vírgula decimal, ponto de milhar (mesma convenção de
      `parse_fre_float_rows`/DFP).

    Nunca adivinha um valor que não faz parse no formato pedido (`None`)."""
    if fmt not in ("en", "br"):
        raise ValueError(f"_to_float: fmt inválido {fmt!r}, esperado 'en' ou 'br'")
    raw = raw.strip()
    if not raw:
        return None
    try:
        if fmt == "en":
            return float(raw)
        return float(raw.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def parse_fre_dividend_rows(rows) -> list[dict]:
    """Linhas de `fre_cia_aberta_distribuicao_dividendos_classe_acao` ->
    [{cnpj, company, pay_date, amount}]. Uma linha por CATEGORIA de
    distribuição (ex.: "Dividendo Obrigatório", "Outros") — o chamador soma
    por (cnpj, pay_date). Linha sem data de pagamento (ainda não paga, ou
    campo vazio) é DESCARTADA — sem isso um provento aprovado mas não pago
    entraria como ex_date fabricado."""
    header = None
    idx = {}
    out = []
    for row in rows:
        if header is None:
            header = row
            idx = {k: _find_col(header, kw) for k, kw in _DIVIDEND_COLS.items()}
            missing = [k for k in ("cnpj", "company", "pay_date", "amount") if idx[k] is None]
            if missing:
                raise ValueError(
                    f"FRE dividendos sem coluna(s) {missing}; cabeçalho={header}")
            continue
        if len(row) < len(header):
            continue
        pay_date = row[idx["pay_date"]].strip()[:10]
        if not pay_date:
            continue
        amount = _to_float(row[idx["amount"]], fmt="en")
        if amount is None:
            continue
        out.append({
            "cnpj": row[idx["cnpj"]].strip(),
            "company": row[idx["company"]].strip(),
            "pay_date": pay_date,
            "amount": amount,
        })
    return out


def parse_fre_capital_total_rows(rows) -> dict[str, float]:
    """Linhas de `fre_cia_aberta_distribuicao_capital` (arquivo PRINCIPAL,
    não `_classe_acao`) -> {cnpj: total de ações em circulação}. Múltiplas
    linhas por CNPJ (uma por versão/retificação do FRE): fica a de MAIOR
    Data_Referencia, mesma disciplina de `load_free_float`."""
    header = None
    idx = {}
    ref_col = None
    best: dict[str, tuple[str, float]] = {}
    for row in rows:
        if header is None:
            header = row
            idx = {k: _find_col(header, kw) for k, kw in _CAPITAL_TOTAL_COLS.items()}
            ref_col = _find_col(header, ("data_referencia",))
            missing = [k for k in ("cnpj", "total_shares") if idx[k] is None]
            if missing or ref_col is None:
                raise ValueError(
                    f"FRE capital total sem coluna(s) {missing or ['data_referencia']}; "
                    f"cabeçalho={header}")
            continue
        if len(row) < len(header):
            continue
        total = _to_float(row[idx["total_shares"]], fmt="br")
        if total is None or total <= 0:
            continue
        cnpj = row[idx["cnpj"]].strip()
        ref_date = row[ref_col].strip()[:10]
        prev = best.get(cnpj)
        if prev is None or ref_date > prev[0]:
            best[cnpj] = (ref_date, total)
    return {cnpj: total for cnpj, (_, total) in best.items()}


def ingest_fre_dividends_year(conn, year: int, companies: set[str] | None = None,
                              ticker_of: dict | None = None) -> int:
    """Baixa o FRE de `year`, aproxima valor por ação dos proventos
    (`Montante` somado por categoria ÷ total de ações em circulação) e grava
    em `dividends`. Duas aproximações DECLARADAS (não escondidas — ver
    HANDOFF 2026-09-04, migração `0009_dividends`):

    1. `Montante` é o total distribuído na categoria/período pela companhia
       inteira, não por classe de ação isolada — dividido pelo total de
       ações em circulação (ON+PN), não pela classe específica que recebeu
       aquele valor. Companhias com ON e PN de proventos MUITO diferentes
       (comum: PN paga mais) ficam com um valor por ação médio, não exato
       por classe.
    2. `Data_Pagamento_Dividendo` é usada como proxy de `ex_date` — a data-ex
       real (a que de fato move o preço) tipicamente vem semanas/meses
       antes; este dataset da CVM não expõe a data-ex. Conservador na
       direção errada é possível (adiar o ajuste pode deixar dividendo
       "vazar" um pedaço de retorno já capturado no preço real antes da
       data escolhida) — limitação registrada, não escondida.

    `companies`/`ticker_of`: mesmo contrato de `ingest_dfp_year`."""
    zbytes = download_zip(FRE_URL.format(year=year))
    div_rows = parse_fre_dividend_rows(
        _open_zip_csv(zbytes, "distribuicao_dividendos_classe_acao"))
    total_shares_by_cnpj = parse_fre_capital_total_rows(
        _open_fre_distribuicao_capital_main(zbytes))

    # soma Montante por (cnpj, pay_date) — várias categorias de distribuição
    # (ex.: "Dividendo Obrigatório" + "Outros") no mesmo pagamento.
    summed: dict[tuple[str, str], float] = {}
    company_by_cnpj: dict[str, str] = {}
    for r in div_rows:
        key = (r["cnpj"], r["pay_date"])
        summed[key] = summed.get(key, 0.0) + r["amount"]
        company_by_cnpj[r["cnpj"]] = r["company"]

    n = 0
    for (cnpj, pay_date), amount in summed.items():
        total_shares = total_shares_by_cnpj.get(cnpj)
        if not total_shares:
            continue    # sem total de ações confiável: sem dado inventado
        company = _norm(company_by_cnpj[cnpj])
        if companies and company not in companies:
            continue
        ticker = (ticker_of or {}).get(company)
        if ticker is None:
            continue    # companhia sem ticker mapeado: revisão humana antes
        value_per_share = amount / total_shares
        if value_per_share <= 0:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO dividends(ticker, ex_date, value_per_share, source)"
            " VALUES (?,?,?,?)",
            (ticker, pay_date, value_per_share, f"CVM FRE {year}"))
        n += conn.execute("SELECT changes()").fetchone()[0]
    conn.commit()
    return n


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
        _open_fre_distribuicao_capital_main(download_zip(FRE_URL.format(year=year))))
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


def ingest_fre_shares_year(conn, year: int, ticker_of: dict | None = None,
                           zbytes: bytes | None = None) -> int:
    """FRE de `year` -> `fundamentals.shares_outstanding`. Insumo de H18
    (E/P) e H19 (B/P), pré-registradas 2026-09-04.

    O parser (`parse_fre_float_rows`) já existia desde a família `liquidity`
    — o que faltava era PERSISTIR `shares_outstanding`: sem quantidade de
    ações não há capitalização de mercado, logo não há múltiplo. Esta função
    só grava o que já era lido e jogado fora.

    DECISÃO DE MODELAGEM (deliberada, não conveniência): a linha é gravada
    com `source = "CVM FRE {year}"` e a `ref_date` DO PRÓPRIO FRE, NUNCA
    casada à força com a `ref_date` da DFP. FRE e DFP são formulários
    distintos, com datas de referência e de entrega distintas; alinhar os
    dois por ano-calendário produziria uma capitalização de mercado com data
    errada — lookahead sutil e silencioso, exatamente o que o domínio
    proíbe. O sinal de valor (`factor._value_signals`) resolve cada
    fonte com seu PRÓPRIO embargo e junta só no momento do sinal.

    Idempotente por `ON CONFLICT(ticker, ref_date, source)`: re-executar o
    mesmo ano não duplica; `COALESCE` preserva valor já gravado."""
    if zbytes is None:
        zbytes = download_zip(FRE_URL.format(year=year))
    rows = parse_fre_float_rows(_open_fre_distribuicao_capital_main(zbytes))
    # Uma companhia aparece várias vezes no FRE (uma linha por classe de
    # acionista). `shares_outstanding` é o MESMO total repetido — dedupa por
    # (company, ref_date) ficando com o maior valor não-nulo. Divergência
    # entre linhas da mesma chave seria layout quebrado, não dado: o max é
    # determinístico e registrado aqui, não "a última lida".
    recebido_em = parse_fre_received_dates(zbytes)
    best: dict[tuple[str, str], float] = {}
    known: dict[tuple[str, str], str] = {}
    for r in rows:
        shares = r["shares_outstanding"]
        if shares is None or shares <= 0:
            continue
        key = (_norm(r["company"]), r["ref_date"][:10])
        if not key[1]:
            continue    # sem data de referência não há point-in-time possível
        best[key] = max(best.get(key, 0.0), shares)
        # known_at OBSERVADO por documento. Entre versões da mesma
        # (company, ref_date) fica a MAIS ANTIGA: é quando aquela informação
        # ficou pública pela primeira vez. Pegar a mais recente (uma
        # retificação de meses depois) atrasaria o sinal sem motivo; pegar
        # "a última lida" seria não-determinístico.
        receb = recebido_em.get(r.get("doc_id", ""))
        if receb and (key not in known or receb < known[key]):
            known[key] = receb
    if not best:
        # Nenhuma linha trouxe ações totais. Antes isto retornava 0 em
        # silêncio e H18/H19 rodavam com universo vazio ou (pior, antes da
        # correção de colisão em `parse_fre_float_rows`) com o free float
        # no lugar das ações totais. Fail-loud: sem quantidade de ações não
        # existe capitalização de mercado, logo não existe múltiplo.
        raise ValueError(
            f"FRE {year}: nenhuma linha com quantidade TOTAL de ações. O "
            "cabeçalho deste arquivo pode não distinguir ações totais de "
            "ações em circulação (ver `parse_fre_float_rows`) — H18/H19 "
            "precisam de ações totais e NÃO podem rodar com free float. "
            "Nada foi gravado.")
    n = 0
    for (company, ref_date), shares in sorted(best.items()):
        ticker = (ticker_of or {}).get(company)
        if ticker is None:
            continue    # companhia sem ticker mapeado: revisão humana antes
        conn.execute(
            "INSERT INTO fundamentals(ticker, ref_date, shares_outstanding,"
            " known_at, source) VALUES (?,?,?,?,?)"
            " ON CONFLICT(ticker, ref_date, source) DO UPDATE SET"
            " shares_outstanding = COALESCE(fundamentals.shares_outstanding,"
            " excluded.shares_outstanding),"
            # backfill de `known_at` em bancos ingeridos antes da migração
            " known_at = COALESCE(fundamentals.known_at, excluded.known_at)"
            # O update só dispara quando há buraco A PREENCHER e valor novo
            # PARA preencher. Sem a segunda metade de cada cláusula, um
            # re-run com known_at indisponível (zip sem arquivo principal)
            # contaria mudança toda vez e quebraria a idempotência — pego
            # pelo teste de re-execução ao implementar.
            " WHERE (fundamentals.shares_outstanding IS NULL"
            "        AND excluded.shares_outstanding IS NOT NULL)"
            "    OR (fundamentals.known_at IS NULL"
            "        AND excluded.known_at IS NOT NULL)",
            (ticker, ref_date, shares, known.get((company, ref_date)),
             f"CVM FRE {year}"))
        n += conn.execute("SELECT changes()").fetchone()[0]
    conn.commit()
    return n
