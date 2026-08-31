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


def parse_cotahist(zip_path: str, db_path: str | None = None) -> int:
    """Parse posicional do TXT dentro do ZIP → prices_raw. Encoding CP1252/latin-1."""
    conn = db.get_connection(db_path)
    try:
        with zipfile.ZipFile(zip_path) as z:
            name = next(n for n in z.namelist() if n.upper().endswith(".TXT"))
            with z.open(name) as f:
                lines = (b.decode("latin-1") for b in f)
                return cotahist.load_prices(conn, lines, source_file=Path(zip_path).name)
    finally:
        conn.close()
