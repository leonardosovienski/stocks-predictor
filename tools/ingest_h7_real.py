"""Script AD-HOC (não faz parte do pacote) — ingestão real da DFP p/ H7.

Para cada ano 2018-2026: monta o ticker_of DAQUELE ano (DFP+FCA do mesmo
ano — mesma lógica de tools/build_h7_ticker_of.py, empresa que trocou de
ticker no meio da janela pega o código certo por ano) e chama
ingest_dfp_year contra o stocks.db REAL. Ao contrário de
build_h7_ticker_of.py (que só IMPRIME pra revisão), este ESCREVE na tabela
fundamentals — rodar só depois de já ter revisado a amostra (2019/2023) e
confiado no método.

Diferença deliberada do build_h7_ticker_of.py: quando um CNPJ bate com MAIS
DE UM ticker do universo no mesmo ano (ex.: ON+PN da mesma empresa), aqui
os DOIS entram — não só o primeiro alfabético. Como `ticker_of` é
`company_norm -> UM ticker` (não suporta duas chaves iguais), isso exige
uma 2ª chamada a `ingest_dfp_year` no mesmo ano, restrita via `companies=`
às empresas ambíguas, remapeadas pro ticker que sobrou de fora da 1ª
passada — o ROE gravado é o MESMO balanço, só a linha em `fundamentals` é
por ticker (ON e PN não compartilham linha na tabela).

Uso:
    python tools/ingest_h7_real.py                  # 2018-2026, grava no banco
    python tools/ingest_h7_real.py --dry-run         # só mostra o que faria
"""
import sys

sys.path.insert(0, "stocks_predictor")
import db  # noqa: E402
import ingest_cvm  # noqa: E402

from build_h7_ticker_of import cnpj_to_company, cnpj_to_tickers, load_universe, _norm  # noqa: E402


def pairs_for_year(year, universe):
    """{company_norm: [tickers do universo]} — pode ter mais de um ticker
    por empresa (ON+PN do mesmo CNPJ)."""
    cnpj_company = cnpj_to_company(year)
    cnpj_tickers = cnpj_to_tickers(year)
    out = {}
    for cnpj, company in cnpj_company.items():
        hit = sorted(cnpj_tickers.get(cnpj, set()) & universe)
        if hit:
            out[_norm(company)] = hit
    return out


def main():
    dry_run = "--dry-run" in sys.argv
    universe = load_universe()
    print(f"universo alvo: {len(universe)} tickers | dry_run={dry_run}", file=sys.stderr)

    conn = None if dry_run else db.get_connection()
    total = 0
    for year in range(2018, 2027):
        try:
            by_company = pairs_for_year(year, universe)
        except Exception as e:
            print(f"{year}: FALHOU montando ticker_of ({e!r}) — pulado", file=sys.stderr)
            continue
        if not by_company:
            print(f"{year}: 0 tickers do universo casados, pulado", file=sys.stderr)
            continue

        primary = {c: tks[0] for c, tks in by_company.items()}
        extra_by_company = {c: tks[1:] for c, tks in by_company.items() if len(tks) > 1}
        n_extra_tickers = sum(len(v) for v in extra_by_company.values())
        print(f"{year}: {len(primary)} empresas (1ª ticker), "
              f"{n_extra_tickers} ticker(s) extra de {len(extra_by_company)} "
              f"empresa(s) ambígua(s) (ON+PN)", file=sys.stderr)
        if dry_run:
            continue

        try:
            n = ingest_cvm.ingest_dfp_year(conn, year, ticker_of=primary)
        except Exception as e:
            print(f"{year}: ingest_dfp_year (primária) FALHOU ({e!r}) — pulado", file=sys.stderr)
            continue
        total += n

        # 2ª classe (ON+PN): uma chamada por ticker extra, restrita via
        # `companies=` à empresa ambígua específica — não reintroduz as
        # demais empresas do ano (já gravadas na passada primária).
        for company, extras in extra_by_company.items():
            for tk in extras:
                try:
                    n2 = ingest_cvm.ingest_dfp_year(
                        conn, year, companies={company}, ticker_of={company: tk})
                except Exception as e:
                    print(f"{year}: 2ª classe {company}->{tk} FALHOU ({e!r})",
                          file=sys.stderr)
                    continue
                total += n2

        print(f"{year}: {n} linhas (primária) gravadas em fundamentals", file=sys.stderr)

    if conn is not None:
        conn.close()
    print(f"\nTOTAL: {total} linhas gravadas em fundamentals (2018-2026)", file=sys.stderr)


if __name__ == "__main__":
    main()
