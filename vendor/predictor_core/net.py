"""predictor-core.net — download utilitário com suporte a proxy corporativo."""
import urllib.request
import urllib.error
import pathlib
import logging
import hashlib
import time

logger = logging.getLogger(__name__)


def download_file(url: str, dest: pathlib.Path, timeout: int = 120,
                  retries: int = 3, backoff: float = 5.0) -> pathlib.Path:
    """Baixa url para dest (cria diretórios necessários). Retorna dest."""
    dest = pathlib.Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    for attempt in range(1, retries + 1):
        try:
            logger.info("download attempt %d/%d: %s", attempt, retries, url)
            urllib.request.urlretrieve(url, tmp)
            tmp.replace(dest)
            logger.info("saved to %s", dest)
            return dest
        except urllib.error.URLError as exc:
            logger.warning("attempt %d failed: %s", attempt, exc)
            if attempt < retries:
                time.sleep(backoff * attempt)
            else:
                raise
    raise RuntimeError("unreachable")


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
