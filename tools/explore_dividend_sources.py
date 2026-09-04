"""Script AD-HOC (não faz parte do pacote) — explora datasets da CVM à
procura de proventos/dividendos POR EVENTO (data-ex, data pagamento, valor
por ação) — não totais agregados.

Baixa três zips candidatos (FRE, que já é usado pra free_float; FCA, usado
pra ticker_of; e um teste do padrão IPE) e lista TODOS os CSVs internos,
imprimindo o cabeçalho de qualquer um cujo nome contenha "provento",
"dividendo" ou "distribuicao". NÃO decide nada, NÃO ingere nada — só
imprime o que existe pra revisão humana antes de qualquer código de
parsing ser escrito.

Uso: python tools/explore_dividend_sources.py [ano]
"""
import io
import sys
import zipfile

sys.path.insert(0, "stocks_predictor")
import ingest_cvm  # noqa: E402


def _norm(s):
    return ingest_cvm._norm(s)


KEYWORDS = ("provento", "dividendo", "distribuicao", "jcp", "juros_sobre_capital")

CANDIDATES = {
    "FRE": ingest_cvm.FRE_URL,
    "FCA": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_{year}.zip",
}


def explore(label, url_template, year):
    url = url_template.format(year=year)
    print(f"\n=== {label} {year}: {url} ===")
    try:
        zbytes = ingest_cvm.download_zip(url)
    except Exception as e:
        print(f"  FALHOU download: {e!r}")
        return
    zf = zipfile.ZipFile(io.BytesIO(zbytes))
    names = zf.namelist()
    print(f"  {len(names)} arquivos no zip:")
    for n in sorted(names):
        flag = " <-- candidato" if any(kw in _norm(n) for kw in KEYWORDS) else ""
        print(f"    {n}{flag}")

    for n in sorted(names):
        if not any(kw in _norm(n) for kw in KEYWORDS) or not n.endswith(".csv"):
            continue
        print(f"\n  --- cabeçalho + 2 linhas de {n} ---")
        with zf.open(n) as f:
            text = io.TextIOWrapper(f, encoding="latin-1")
            for i, line in enumerate(text):
                print(f"    {line.rstrip()}")
                if i >= 2:
                    break


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2023
    for label, url_template in CANDIDATES.items():
        explore(label, url_template, year)


if __name__ == "__main__":
    main()
