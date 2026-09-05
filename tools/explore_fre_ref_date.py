"""Script AD-HOC (não faz parte do pacote) — SOMENTE LEITURA, não toca no banco.

Investiga o que a CVM entende por `Data_Referencia` no FRE, e se existe uma
DATA DE ENTREGA disponível.

Por que isso importa (achado de operação 2026-09-05): a `ref_date` gravada em
`fundamentals` muda de convenção no meio da amostra —

    BBAS3  2019-01-01 .. 2022-01-01     primeiro dia do ano
    BBAS3  2023-12-31 .. 2026-12-31     último dia do ano

O embargo de divulgação de H18/H19 soma 90 dias corridos sobre esse campo. Se
a semântica dele muda, o tamanho do lookahead muda junto — não é viés
constante, é viés que salta em 2023. Um embargo fixo não é defensável sobre um
campo assim.

A saída ideal desta investigação NÃO é escolher um embargo melhor: é descobrir
se o FRE publica a data de ENTREGA do documento, como o IPE publica
`Data_Entrega`. Se publicar, o `known_at` deixa de ser estimado e passa a ser
observado — que é o que o protocolo §8 pede, e o que `ingest_ipe_year` já faz
para os fatos relevantes.

Uso (rede limpa):
    py -3.13 tools\\explore_fre_ref_date.py                 # 2022 e 2023
    py -3.13 tools\\explore_fre_ref_date.py --anos 2019,2022,2023,2024
"""
import collections
import csv
import io
import sys
import zipfile

sys.path.insert(0, "stocks_predictor")
import ingest_cvm  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Pistas de coluna que indicariam data de ENTREGA/recebimento do documento.
# `receb` ABREVIADO, não `recebimento` (achado 2026-09-05): a coluna real da
# CVM é `DT_RECEB`, e a lista original — que exigia a palavra inteira — deu
# FALSO NEGATIVO, anunciando "o FRE não expõe data de entrega" três linhas
# acima de imprimir `DT_RECEB = 2022-05-31`. Mesmo erro de casamento por
# palavra-chave longa demais que a auditoria pegou em `_FRE_FLOAT_COLS`;
# aqui o custo foi uma conclusão errada em letra garrafal.
_PISTAS_ENTREGA = ("entrega", "receb", "protocolo", "envio", "divulgacao",
                   "dt_rec")


def _anos():
    for i, a in enumerate(sys.argv):
        if a == "--anos" and i + 1 < len(sys.argv):
            return [int(x) for x in sys.argv[i + 1].split(",")]
    return [2022, 2023]


def _rows(zf, name):
    with zf.open(name) as f:
        yield from csv.reader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";")


def investiga(year):
    print("=" * 72)
    print(f"FRE {year}")
    print("=" * 72)
    zbytes = ingest_cvm.download_zip(ingest_cvm.FRE_URL.format(year=year))
    zf = zipfile.ZipFile(io.BytesIO(zbytes))
    nomes = sorted(n for n in zf.namelist() if n.lower().endswith(".csv"))
    print(f"\n{len(nomes)} CSVs no zip:")
    for n in nomes:
        print(f"   {n}")

    # 1) Alguma coluna de ENTREGA em QUALQUER csv do zip?
    print("\n--- procurando coluna de data de ENTREGA em todos os CSVs ---")
    achou = False
    for n in nomes:
        try:
            header = next(_rows(zf, n))
        except (StopIteration, UnicodeDecodeError):
            continue
        hits = [c for c in header
                if any(p in ingest_cvm._norm(c) for p in _PISTAS_ENTREGA)]
        if hits:
            achou = True
            print(f"   {n}")
            for c in hits:
                print(f"       -> {c}")
    if not achou:
        print("   NENHUMA. O FRE não expõe data de entrega neste layout —")
        print("   o known_at teria de continuar estimado por embargo.")

    # 2) O arquivo PRINCIPAL do FRE (não o distribuicao_capital)
    principal = [n for n in nomes
                 if ingest_cvm._norm(n).endswith(f"fre_cia_aberta_{year}.csv")]
    if principal:
        print(f"\n--- cabeçalho do arquivo principal ({principal[0]}) ---")
        it = _rows(zf, principal[0])
        header = next(it)
        for i, c in enumerate(header):
            print(f"   [{i}] {c}")
        amostra = next(it, None)
        if amostra:
            print("\n   1ª linha:")
            for c, v in zip(header, amostra):
                print(f"       {c} = {v}")

    # 3) Data_Referencia + Versao no distribuicao_capital
    print("\n--- Data_Referencia no distribuicao_capital ---")
    it = ingest_cvm._open_fre_distribuicao_capital_main(zbytes)
    header = next(it)
    i_ref = ingest_cvm._find_col(header, ("data_referencia",))
    i_ver = ingest_cvm._find_col(header, ("versao",))
    i_ass = ingest_cvm._find_col(header, ("data_ultima_assembleia",))
    refs, assembleias = collections.Counter(), collections.Counter()
    versoes = collections.Counter()
    for row in it:
        if i_ref is not None and i_ref < len(row):
            refs[row[i_ref].strip()[:10]] += 1
        if i_ver is not None and i_ver < len(row):
            versoes[row[i_ver].strip()] += 1
        if i_ass is not None and i_ass < len(row):
            assembleias[row[i_ass].strip()[:7]] += 1
    print(f"   valores distintos de Data_Referencia: {len(refs)}")
    for v, n in refs.most_common(5):
        print(f"       {v!r:14s} {n} linhas")
    print(f"\n   Versao (top 5): {dict(versoes.most_common(5))}")
    if assembleias:
        print("\n   Data_Ultima_Assembleia por mês (top 8) — pista indireta de")
        print("   QUANDO o documento reflete a realidade:")
        for v, n in assembleias.most_common(8):
            print(f"       {v!r:10s} {n}")


def main():
    for year in _anos():
        try:
            investiga(year)
        except Exception as e:
            print(f"{year}: FALHOU ({e!r})")
        print()


if __name__ == "__main__":
    main()
