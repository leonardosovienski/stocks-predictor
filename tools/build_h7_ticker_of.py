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
    with open(path, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
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


FCA_URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_valor_mobiliario_{year}.zip"


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


def main():
    universe = load_universe()
    print(f"universo alvo: {len(universe)} tickers", file=sys.stderr)

    cnpj_company = cnpj_to_company(2023)
    print(f"DFP 2023: {len(cnpj_company)} CNPJs", file=sys.stderr)

    cnpj_tickers = cnpj_to_tickers(2023)
    print(f"FCA 2023: {len(cnpj_tickers)} CNPJs com valor mobiliário", file=sys.stderr)

    ticker_of = {}
    matched_tickers = set()
    for cnpj, company in cnpj_company.items():
        tickers = cnpj_tickers.get(cnpj, set())
        hit = tickers & universe
        for tk in hit:
            ticker_of[_norm(company)] = tk
            matched_tickers.add(tk)

    missing = sorted(universe - matched_tickers)
    print(f"\nticker_of proposto: {len(ticker_of)} entradas cobrindo "
          f"{len(matched_tickers)}/{len(universe)} tickers do universo\n", file=sys.stderr)
    print(json.dumps(ticker_of, ensure_ascii=True, indent=2, sort_keys=True))
    print(f"\n# NÃO casaram (revisar manualmente — nome mudou, fusão, "
          f"delistagem no meio da janela, ou CNPJ divergente entre datasets):",
          file=sys.stderr)
    for tk in missing:
        print(f"#   {tk}", file=sys.stderr)


if __name__ == "__main__":
    main()
