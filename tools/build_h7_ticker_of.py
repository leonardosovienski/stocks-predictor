"""Script AD-HOC (não faz parte do pacote) — monta o `ticker_of` da H7 por CNPJ.

Cruza dois datasets abertos da CVM pelo CNPJ (não pelo nome — evita risco de
acento/mojibake): o DFP (que ingest_dfp_year já usa, tem `cnpj` cru por linha)
e o FCA `valor_mobiliario` (tem `Codigo_Negociacao`, o ticker B3 por CNPJ).
Filtra só os tickers do universo real 2018-2026 (`universo_2018_2026.txt`,
gerado nesta sessão). NÃO escreve no banco — só imprime o `ticker_of`
proposto (chaves já em `_norm()`, ASCII, sem acento) para revisão humana
antes de colar em qualquer chamada de `ingest_dfp_year`.
"""
import csv
import io
import json
import re
import sys
import zipfile

sys.path.insert(0, "stocks_predictor")
import ingest_cvm  # noqa: E402


def _norm(s):
    return ingest_cvm._norm(s)


def _digits(s):
    return re.sub(r"\D", "", s or "")


def load_universe(path="universo_2018_2026.txt"):
    # Windows PowerShell (não pwsh) grava `>` em UTF-16LE por padrão (BOM
    # FF FE) — detecta pelo BOM em vez de assumir UTF-8, que quebrava aqui.
    with open(path, "rb") as f:
        raw = f.read()
    encoding = "utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    lines = [l.strip() for l in raw.decode(encoding).splitlines() if l.strip()]
    # 1ª linha é a contagem (print(len(seen)) do script anterior)
    return set(lines[1:]) if lines and lines[0].isdigit() else set(lines)


def cnpj_to_company(dfp_year=2023):
    zbytes = ingest_cvm.download_zip(ingest_cvm.DFP_URL.format(year=dfp_year))
    bpa = ingest_cvm.parse_dfp_statement_rows(
        ingest_cvm._open_zip_csv(zbytes, "bpa_con"), "BPA_con")
    out = {}
    for r in bpa:
        cnpj = _digits(r["cnpj"])
        if cnpj:
            out[cnpj] = r["company"].strip()
    return out


FCA_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_{year}.zip"


def cnpj_to_tickers(fca_year=2023):
    zbytes = ingest_cvm.download_zip(FCA_URL.format(year=fca_year))
    zf = zipfile.ZipFile(io.BytesIO(zbytes))
    names = [n for n in zf.namelist() if "valor_mobiliario" in _norm(n) and n.endswith(".csv")]
    if not names:
        raise ValueError(f"nenhum CSV valor_mobiliario em {zf.namelist()}")
    out = {}
    for name in names:
        with zf.open(name) as f:
            text = io.TextIOWrapper(f, encoding="latin-1")
            reader = csv.reader(text, delimiter=";")
            header = next(reader)
            idx = {_norm(h): i for i, h in enumerate(header)}
            cnpj_i = next(i for k, i in idx.items() if "cnpj" in k)
            cod_i = next((i for k, i in idx.items() if "codigo_negociacao" in k), None)
            if cod_i is None:
                continue
            for row in reader:
                if len(row) <= max(cnpj_i, cod_i):
                    continue
                cod = row[cod_i].strip().upper()
                if not cod:
                    continue
                cnpj = _digits(row[cnpj_i])
                out.setdefault(cnpj, set()).add(cod)
    return out


def build_ticker_of(year, universe):
    """Ticker_of do ANO ESPECÍFICO (DFP + FCA do mesmo ano) — não um dict
    global. Empresa que trocou de ticker no meio de 2018-2026 (fusão,
    rebatismo — ex.: Arezzo/Grupo Soma viraram Azzas 2154 em 2024, negociada
    como AZZA3, não mais ARZZ3) precisa do ticker VÁLIDO NAQUELE ANO, não
    um fixo pra toda a janela. Retorna (ticker_of, ambiguous) — `ambiguous`
    lista CNPJs cujo FCA do ano bate com MAIS DE UM ticker do universo (ex.:
    ON e PN da mesma empresa, ambas no top-60 em algum momento): a chave
    ganha só um (ordem alfabética, determinístico) — revisão humana decide
    se os dois devem entrar."""
    cnpj_company = cnpj_to_company(year)
    cnpj_tickers = cnpj_to_tickers(year)
    print(f"DFP {year}: {len(cnpj_company)} CNPJs | FCA {year}: "
          f"{len(cnpj_tickers)} CNPJs com valor mobiliário", file=sys.stderr)

    ticker_of, matched_tickers, ambiguous = {}, set(), []
    for cnpj, company in cnpj_company.items():
        hit = sorted(cnpj_tickers.get(cnpj, set()) & universe)
        if not hit:
            continue
        if len(hit) > 1:
            ambiguous.append((company, hit))
        ticker_of[_norm(company)] = hit[0]
        matched_tickers.add(hit[0])
    return ticker_of, matched_tickers, ambiguous


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2023
    universe = load_universe()
    print(f"universo alvo: {len(universe)} tickers | ano de referência: {year}",
          file=sys.stderr)

    ticker_of, matched_tickers, ambiguous = build_ticker_of(year, universe)
    missing = sorted(universe - matched_tickers)

    print(f"\nticker_of proposto ({year}): {len(ticker_of)} entradas cobrindo "
          f"{len(matched_tickers)}/{len(universe)} tickers do universo\n", file=sys.stderr)
    print(json.dumps(ticker_of, ensure_ascii=True, indent=2, sort_keys=True))

    if ambiguous:
        print(f"\n# AMBÍGUOS ({len(ambiguous)}) — mesmo CNPJ bateu com MAIS DE UM "
              f"ticker do universo (ex.: ON+PN); só o primeiro alfabético entrou "
              f"no ticker_of acima, revisar se os dois precisam de linha própria:",
              file=sys.stderr)
        for company, tks in ambiguous:
            print(f"#   {company} -> {tks}", file=sys.stderr)

    print(f"\n# NÃO casaram em {year} (revisar manualmente — nome mudou, fusão, "
          f"delistagem, ou CNPJ divergente entre datasets; rode com outro ano "
          f"como argumento, ex. `python tools/build_h7_ticker_of.py 2019`, "
          f"pra empresas que trocaram de ticker no meio da janela):",
          file=sys.stderr)
    for tk in missing:
        print(f"#   {tk}", file=sys.stderr)


if __name__ == "__main__":
    main()
