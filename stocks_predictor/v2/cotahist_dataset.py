"""Dataset ``stocks-pit-dataset/2`` a partir de um COTAHIST local e versionado da B3.

Usa só o que o arquivo contém. Layout oficial do registro tipo 01, mesmas posições de ``stocks_predictor.cotahist``,
mais CODISI 231–242 (ISIN), conferido no ``COTAHIST_A2026``:

    barras        à vista (BDI 02, mercado 010) e o fundo de índice declarado (seu BDI, mercado 010); preço ÷ fator
                  de cotação; volume financeiro
    identidade    ISIN como ``security_id``; ticker (CODNEG) por vigência; emissor = código de 4 letras do ISIN
    calendário    pregões presentes no arquivo
    disponível    barra do pregão às 23:00 UTC (depois do fechamento; conservador)

Limitações declaradas em ``LIMITATIONS`` e registradas em toda execução que usa este dataset:
listagem = primeiro pregão no arquivo; deslistagem desconhecida; sem eventos societários, proventos nem
fundamentos (preços **não ajustados**).
"""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

from . import SCHEMA

BAR_TIME = "T23:00:00Z"
LIMITATIONS = (
    "listagem = primeiro pregão no arquivo (quem já era listado aparece como listado a partir dele)",
    "deslistagem desconhecida: o arquivo não informa saídas; o universo não perde ninguém por deslistagem",
    "sem eventos societários nem proventos: preços não ajustados; saltos são tratados pela regra de exclusão da "
    "avaliação",
    "sem fundamentos",
)


class CotahistError(ValueError):
    """Arquivo diferente do declarado ou conteúdo fora do layout."""


def _records(path: Path, index_ticker: str):
    with zipfile.ZipFile(path) as archive:
        members = [n for n in archive.namelist() if n.upper().endswith(".TXT")]
        if len(members) != 1:
            raise CotahistError("o ZIP deve conter exatamente um COTAHIST .TXT")
        with archive.open(members[0]) as handle:
            for raw in handle:
                line = raw.decode("latin-1").rstrip("\r\n")
                if line[:2] != "01":
                    continue
                if len(line) != 245:
                    raise CotahistError("registro tipo 01 fora do layout de 245 posições")
                ticker, bdi, market = line[12:24].strip(), line[10:12].strip(), line[24:27]
                if market != "010" or not (bdi == "02" or ticker == index_ticker):
                    continue
                factor = int(line[210:217])
                if factor <= 0:
                    raise CotahistError("fator de cotação não positivo")
                day = f"{line[2:6]}-{line[6:8]}-{line[8:10]}"
                yield {"session": day, "ticker": ticker, "isin": line[230:242].strip(),
                       "open": int(line[56:69]) / 100 / factor, "close": int(line[108:121]) / 100 / factor,
                       "volume_fin": int(line[170:188]) / 100}


def build_from_cotahist(path: Path | str, *, expected_sha256: str, index_ticker: str = "BOVA11") -> tuple[dict, dict]:
    """(dataset bruto, metadados). Recusa arquivo cujo sha256 difere do declarado."""
    path = Path(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected_sha256:
        raise CotahistError(f"sha256 do COTAHIST difere do declarado ({digest[:12]}…)")
    bars, first_seen, tickers, kinds = [], {}, {}, {}
    for rec in _records(path, index_ticker):
        isin = rec["isin"]
        if not isin:
            raise CotahistError("registro sem ISIN")
        kind = "index_fund" if rec["ticker"] == index_ticker else "equity"
        if kinds.setdefault(isin, kind) != kind:
            raise CotahistError(f"{isin} aparece como ação e como fundo de índice")
        first_seen.setdefault(isin, rec["session"])
        history = tickers.setdefault(isin, [])
        if not history or history[-1][1] != rec["ticker"]:
            history.append((rec["session"], rec["ticker"]))
        if rec["open"] <= 0 or rec["close"] <= 0:
            continue  # sem negócio com preço válido: não é barra
        bars.append({"security_id": isin, "session": rec["session"], "open": rec["open"], "close": rec["close"],
                     "volume_fin": rec["volume_fin"], "available_at": rec["session"] + BAR_TIME})
    calendar = sorted({b["session"] for b in bars})
    if not calendar:
        raise CotahistError("nenhuma barra à vista no arquivo")
    first = calendar[0]
    securities, identities = [], []
    for isin in sorted(first_seen):
        listed = first_seen[isin]
        known = first + "T00:00:00Z" if listed == first else listed + BAR_TIME
        securities.append({"security_id": isin, "kind": kinds[isin], "listed_on": listed, "listing_available_at": known,
                           "delisted_on": None, "delisting_available_at": None, "delisting_value": None})
        for number, (session, ticker) in enumerate(tickers[isin]):
            identities.append({"security_id": isin, "ticker": ticker, "issuer_id": isin[2:6],
                               "effective_on": session,
                               "available_at": known if number == 0 else session + BAR_TIME})
    raw = {"schema": SCHEMA, "dataset_version": f"cotahist-{path.name}-{digest[:16]}",
           "data_cutoff": calendar[-1] + "T23:59:59Z", "calendar": calendar, "securities": securities,
           "identity_events": identities, "bars": bars, "corporate_actions": [], "cash_events": [], "fundamentals": []}
    meta = {"source_file": path.name, "source_sha256": digest, "index_ticker": index_ticker,
            "index_isin": next((i for i, k in kinds.items() if k == "index_fund"), None),
            "sessions": len(calendar), "first_session": first, "last_session": calendar[-1],
            "securities": len(securities), "bars": len(bars), "limitations": list(LIMITATIONS)}
    return raw, meta


__all__ = ["BAR_TIME", "CotahistError", "LIMITATIONS", "build_from_cotahist"]
