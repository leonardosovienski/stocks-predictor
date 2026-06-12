"""M1 — Ingestão COTAHIST: download (separado) e parse posicional → prices_raw."""
# Implementado em M1. Esqueleto presente para satisfazer imports do M0.

def download_cotahist(year: int, dest_dir: str) -> None:
    """Baixar COTAHIST_AXXXX.ZIP da B3. Rodar em rede limpa."""
    raise NotImplementedError("M1")


def parse_cotahist(zip_path: str, db_path: str | None = None) -> int:
    """Parse posicional do arquivo TXT dentro do ZIP → prices_raw. Retorna linhas inseridas."""
    raise NotImplementedError("M1")
