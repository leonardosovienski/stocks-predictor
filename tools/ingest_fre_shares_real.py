"""Script AD-HOC (não faz parte do pacote) — ingestão real do FRE p/ H18/H19.

Grava `fundamentals.shares_outstanding` a partir do
`fre_cia_aberta_distribuicao_capital_{ano}.csv`. Espelha a estrutura de
`ingest_h7_real.py` (mesmo loop por ano, mesmo `--dry-run`, mesma
disciplina de ticker_of), mas com UMA diferença deliberada no mapeamento:

`ingest_h7_real.py` monta o `ticker_of` a partir dos nomes da DFP. Aqui o
mapa é montado a partir dos nomes do PRÓPRIO FRE, ligados ao ticker pelo
CNPJ via FCA. Nome de companhia é chave frágil e DFP e FRE não são
obrigados a grafar igual; casar por CNPJ dentro do arquivo que está sendo
ingerido elimina esse acoplamento silencioso.

O que este script NÃO faz, deliberadamente: não calcula sinal, não roda
backtest, não toca em `trials.json`, não olha retorno. Coverage é assunto
do `cobertura_h18.py`.

Uso (rede limpa, Python 3.13 global, sem venv):
    python tools/ingest_fre_shares_real.py --dry-run    # não escreve nada
    python tools/ingest_fre_shares_real.py              # grava no stocks.db
    python tools/ingest_fre_shares_real.py --anos 2018-2024
"""
import sys
import zipfile

sys.path.insert(0, "stocks_predictor")
sys.path.insert(0, "tools")
import db  # noqa: E402
import ingest_cvm  # noqa: E402

import universe as universe_mod  # noqa: E402
from config import load_config  # noqa: E402
from returns import month_end_dates  # noqa: E402

from build_h7_ticker_of import _norm, cnpj_to_tickers, load_universe  # noqa: E402


def universo_alvo(conn):
    """Tickers que o FRE precisa cobrir.

    Preferência pelo `universo_2018_2026.txt` que o `ingest_h7_real.py` já
    usou — mesma lista, mesma ingestão comparável. O arquivo é artefato
    LOCAL do operador (não versionado), então quando ele não existe o
    universo é derivado do PRÓPRIO banco: a união dos universos
    point-in-time de todas as datas de rebalance. É a mesma definição, só
    recalculada — nenhuma lista escrita à mão."""
    try:
        uni = load_universe()
        if uni:
            print(f"universo: {len(uni)} tickers de universo_2018_2026.txt",
                  file=sys.stderr)
            return uni
    except OSError:
        pass
    cfg = load_config().get("universe", {})
    all_dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM prices_raw WHERE market_type = ? ORDER BY date",
        (universe_mod.SPOT_MARKET,))]
    uni = set()
    for asof in month_end_dates(all_dates):
        uni.update(universe_mod.select_universe(
            conn, asof, top_n=cfg.get("top_n", 60),
            lookback=cfg.get("lookback_trading_days", 126),
            min_history=cfg.get("min_history_days", 252)))
    print(f"universo: {len(uni)} tickers derivados do banco "
          f"(universo_2018_2026.txt ausente)", file=sys.stderr)
    return uni


def _digits(s):
    return "".join(c for c in s if c.isdigit())


def fre_company_by_cnpj(zbytes):
    """{cnpj_só_dígitos: nome_companhia} lido do FRE do próprio ano.

    Ler o nome DAQUI (e não da DFP) é o que garante que a chave usada no
    `ticker_of` seja exatamente a que `ingest_fre_shares_year` vai
    normalizar ao gravar. Um nome que diverge entre formulários faria a
    companhia ser pulada em silêncio por 'ticker não mapeado'."""
    rows = ingest_cvm._open_fre_distribuicao_capital_main(zbytes)
    header = next(rows)
    i_cnpj = ingest_cvm._find_col(header, ("cnpj_companhia", "cnpj"))
    i_nome = ingest_cvm._find_col(header, ("nome_companhia", "companhia"))
    if i_cnpj is None or i_nome is None:
        raise ValueError(f"FRE sem CNPJ/nome; cabeçalho={header}")
    out = {}
    for row in rows:
        if len(row) <= max(i_cnpj, i_nome):
            continue
        cnpj = _digits(row[i_cnpj])
        nome = row[i_nome].strip()
        if cnpj and nome:
            out.setdefault(cnpj, nome)
    return out


def pairs_for_year(zbytes, year, universe):
    """{company_norm: [tickers do universo]} — ON e PN do mesmo CNPJ entram
    os dois (mesma regra de `ingest_h7_real.py`)."""
    cnpj_tickers = cnpj_to_tickers(year)
    out = {}
    for cnpj, company in fre_company_by_cnpj(zbytes).items():
        hit = sorted(cnpj_tickers.get(cnpj, set()) & universe)
        if hit:
            out[_norm(company)] = hit
    return out


def parse_anos(argv, default=(2018, 2027)):
    for i, a in enumerate(argv):
        if a == "--anos" and i + 1 < len(argv):
            ini, _, fim = argv[i + 1].partition("-")
            return int(ini), int(fim or ini) + 1
    return default


def main():
    dry_run = "--dry-run" in sys.argv
    ini, fim = parse_anos(sys.argv)
    # o banco é aberto mesmo em dry-run: derivar o universo é LEITURA.
    conn = db.get_connection()
    universe = universo_alvo(conn)
    print(f"anos {ini}-{fim - 1} | dry_run={dry_run}", file=sys.stderr)
    if not universe:
        print("!! universo vazio — banco sem prices_raw? nada a fazer",
              file=sys.stderr)
        conn.close()
        return
    if dry_run:
        conn.close()
        conn = None
    total = 0
    for year in range(ini, fim):
        try:
            zbytes = ingest_cvm.download_zip(ingest_cvm.FRE_URL.format(year=year))
        except Exception as e:
            print(f"{year}: download do FRE FALHOU ({e!r}) — pulado", file=sys.stderr)
            continue
        try:
            by_company = pairs_for_year(zbytes, year, universe)
        except (ValueError, KeyError, zipfile.BadZipFile) as e:
            print(f"{year}: FALHOU montando ticker_of ({e!r}) — pulado", file=sys.stderr)
            continue
        if not by_company:
            print(f"{year}: 0 tickers do universo casados, pulado", file=sys.stderr)
            continue

        primary = {c: tks[0] for c, tks in by_company.items()}
        extra = {c: tks[1:] for c, tks in by_company.items() if len(tks) > 1}
        n_extra = sum(len(v) for v in extra.values())
        print(f"{year}: {len(primary)} empresas (1ª ticker), {n_extra} ticker(s) "
              f"extra de {len(extra)} empresa(s) ON+PN", file=sys.stderr)
        if dry_run:
            continue

        try:
            n = ingest_cvm.ingest_fre_shares_year(conn, year, ticker_of=primary,
                                                  zbytes=zbytes)
        except Exception as e:
            # fail-loud do parser (ex.: ações totais não deriváveis) é
            # informação, não ruído: nomeia o ano e segue para o próximo.
            print(f"{year}: ingest_fre_shares_year FALHOU ({e!r}) — pulado",
                  file=sys.stderr)
            continue
        total += n

        # ON+PN: mesma quantidade de ações, uma linha por ticker.
        for company, tickers in extra.items():
            for tk in tickers:
                try:
                    total += ingest_cvm.ingest_fre_shares_year(
                        conn, year, ticker_of={company: tk}, zbytes=zbytes)
                except Exception as e:
                    print(f"{year}: 2ª classe {company}->{tk} FALHOU ({e!r})",
                          file=sys.stderr)
        print(f"{year}: {n} linhas (primária) em fundamentals", file=sys.stderr)

    if conn is not None:
        conn.close()
    if dry_run:
        print("\nDRY-RUN: nada foi gravado.", file=sys.stderr)
    else:
        print(f"\nTOTAL: {total} linhas de shares_outstanding gravadas",
              file=sys.stderr)


if __name__ == "__main__":
    main()
