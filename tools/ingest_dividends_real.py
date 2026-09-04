"""Script AD-HOC (não faz parte do pacote) — ingestão real de proventos p/
retorno total.

Para cada ano 2018-2026: monta o ticker_of DAQUELE ano (mesma lógica de
tools/build_h7_ticker_of.py/ingest_h7_real.py) e chama
ingest_cvm.ingest_fre_dividends_year contra o stocks.db REAL. Grava em
`dividends` — não altera prices_raw/adjustments; `adjust.total_return_series`
é quem combina os dois na hora de ler.

Uso:
    python tools/ingest_dividends_real.py                  # 2018-2026, grava no banco
    python tools/ingest_dividends_real.py --dry-run         # só mostra o que faria
"""
import sys

sys.path.insert(0, "stocks_predictor")
import db  # noqa: E402
import ingest_cvm  # noqa: E402

from build_h7_ticker_of import cnpj_to_company, cnpj_to_tickers, load_universe, _norm  # noqa: E402


def pairs_for_year(year, universe):
    cnpj_company = cnpj_to_company(year)
    cnpj_tickers = cnpj_to_tickers(year)
    out = {}
    for cnpj, company in cnpj_company.items():
        hit = sorted(cnpj_tickers.get(cnpj, set()) & universe)
        if hit:
            out[_norm(company)] = hit[0]
    return out


def main():
    dry_run = "--dry-run" in sys.argv
    universe = load_universe()
    print(f"universo alvo: {len(universe)} tickers | dry_run={dry_run}", file=sys.stderr)

    conn = None if dry_run else db.get_connection()
    total = 0
    for year in range(2018, 2027):
        try:
            ticker_of = pairs_for_year(year, universe)
        except Exception as e:
            print(f"{year}: FALHOU montando ticker_of ({e!r}) — pulado", file=sys.stderr)
            continue
        if not ticker_of:
            print(f"{year}: 0 tickers do universo casados, pulado", file=sys.stderr)
            continue
        print(f"{year}: {len(ticker_of)} empresas mapeadas", file=sys.stderr)
        if dry_run:
            continue
        try:
            n = ingest_cvm.ingest_fre_dividends_year(conn, year, ticker_of=ticker_of)
        except Exception as e:
            print(f"{year}: ingest_fre_dividends_year FALHOU ({e!r}) — pulado", file=sys.stderr)
            continue
        print(f"{year}: {n} linhas gravadas em dividends", file=sys.stderr)
        total += n

    if conn is not None:
        conn.close()
    print(f"\nTOTAL: {total} linhas gravadas em dividends (2018-2026)", file=sys.stderr)


if __name__ == "__main__":
    main()
