"""M1 — Ingestão COTAHIST: download (rede limpa, separado) e parse posicional → prices_raw.

A lógica de formato (parser, gerador sintético, carga) vive em `cotahist.py`. Aqui só a
orquestração: baixar (separado) e processar (offline), como manda o DESIGN.
"""
import zipfile
from pathlib import Path

import cotahist
import db


def download_cotahist(year: int, dest_dir: str):
    """Baixa COTAHIST_AXXXX.ZIP da B3 via o net unificado do predictor_core. Rede limpa."""
    from predictor_core.net import download_file
    url = f"https://bvmf.bmfbovespa.com.br/InstDados/SerHist/COTAHIST_A{year}.ZIP"
    return download_file(url, Path(dest_dir) / f"COTAHIST_A{year}.ZIP")


def _pick_cotahist_txt(names: list[str]) -> str:
    """Escolhe o .TXT de cotação dentro do zip — nunca o primeiro que bater
    por sorte (achado de varredura 2026-09-04: `next(... .TXT)` pegava
    qualquer .TXT, inclusive um README/layout companheiro se algum dia
    existir no zip). Prefere nome contendo "COTAHIST"; sem nenhum
    "COTAHIST" e com exatamente 1 .TXT, aceita (zip real de hoje só tem
    um); com mais de 1 e nenhum "COTAHIST", falha alto — ambíguo, não
    adivinha."""
    txts = [n for n in names if n.upper().endswith(".TXT")]
    if not txts:
        raise ValueError(f"nenhum .TXT no zip — conteúdo: {names}")
    cota = [n for n in txts if "COTAHIST" in n.upper()]
    if len(cota) == 1:
        return cota[0]
    if len(cota) > 1:
        raise ValueError(f"{len(cota)} .TXT com 'COTAHIST' no nome — ambíguo: {cota}")
    if len(txts) == 1:
        return txts[0]
    raise ValueError(
        f"{len(txts)} .TXT no zip, nenhum com 'COTAHIST' no nome — "
        f"ambíguo, revisar antes de escolher: {txts}")


def parse_cotahist(zip_path: str, db_path: str | None = None) -> int:
    """Parse posicional do TXT dentro do ZIP → prices_raw. Encoding CP1252/latin-1."""
    conn = db.get_connection(db_path)
    try:
        with zipfile.ZipFile(zip_path) as z:
            name = _pick_cotahist_txt(z.namelist())
            with z.open(name) as f:
                lines = (b.decode("latin-1") for b in f)
                return cotahist.load_prices(conn, lines, source_file=Path(zip_path).name)
    finally:
        conn.close()
