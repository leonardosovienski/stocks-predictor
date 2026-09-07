"""Read-only research panel with independent issuer and filing availability.

This API exposes source observations for diagnostics. It does not certify the
universe, corporate actions, or share-class equivalence for a trading trial.
"""

from collections import defaultdict
from html import unescape
from html.parser import HTMLParser
import hashlib
import re

if __package__:
    from .cvm_pit import iso_date
    from .source_history import security_links_asof
else:
    from cvm_pit import iso_date
    from source_history import security_links_asof


def fundamentals_asof(financials, securities, asof, *, security_metadata=None):
    """Join two already-public documents; never backfill a ticker from the future."""
    iso_date(asof)
    by_issuer = defaultdict(list)
    securities_by_issuer, metadata_by_issuer = defaultdict(list), defaultdict(list)
    for row in securities:
        securities_by_issuer[row["cnpj"]].append(row)
    for row in security_metadata or []:
        metadata_by_issuer[row["cnpj"]].append(row)
    for row in financials:
        if row["available_at"] <= asof and row["ref_date"] <= asof:
            by_issuer[row["cnpj"]].append(row)
    result = {}
    for cnpj, rows in by_issuer.items():
        key = max((r["ref_date"], r["document_version"]) for r in rows)
        latest = [r for r in rows if (r["ref_date"], r["document_version"]) == key]
        # Duplicate source copies must agree on every economic field.
        content = [{k: v for k, v in r.items() if k not in {"source", "source_sha256"}} for r in latest]
        if any(r != content[0] for r in content[1:]):
            raise ValueError(f"conflicting issuer filings: {cnpj}")
        issuer_securities = securities_by_issuer[cnpj]
        if security_metadata is not None:
            eligible = [r for r in metadata_by_issuer[cnpj] if r["available_at"] <= asof]
            if not eligible:
                continue
            newest = max((r["ref_date"], r["version"], r["available_at"]) for r in eligible)
            docs = {r["document_id"] for r in eligible
                    if (r["ref_date"], r["version"], r["available_at"]) == newest}
            issuer_securities = [r for r in issuer_securities if r["document_id"] in docs]
        for ticker in security_links_asof(issuer_securities, cnpj, asof):
            if ticker in result and result[ticker]["cnpj"] != cnpj:
                raise ValueError(f"ambiguous contemporaneous ticker: {ticker}")
            result[ticker] = latest[0]
    return result


class _CapitalCells(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.active = None

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            self.active = dict(attrs).get("id")
            if self.active:
                self.cells[self.active] = ""

    def handle_data(self, data):
        if self.active:
            self.cells[self.active] += data

    def handle_endtag(self, tag):
        if tag == "td":
            self.active = None


def capital_from_viewer(payload, metadata, source):
    """Original CVM DFP capital page, including its own share scale.

    CSV monetary scales are unrelated. In particular, ABEV's capital page is
    in thousands while BBAS's is in units. Rounded thousands remain labelled
    as rounded observations, not exact physical integer share counts.
    """
    text = payload.decode("utf-8-sig")
    plain = unescape(re.sub(r"<[^>]*>", " ", text))
    scales = re.findall(r"Número de Ações\s*\((Unidade|Mil)\)", plain)
    if len(scales) != 1:
        raise ValueError("missing or ambiguous capital share scale")
    scale = {"Unidade": 1, "Mil": 1000}[scales[0]]
    basis = iso_date(metadata["ref_date"])
    if basis[8:10] + "/" + basis[5:7] + "/" + basis[:4] not in plain:
        raise ValueError("capital page reference date mismatch")
    parser = _CapitalCells()
    parser.feed(text)
    ids = {
        "ordinary": "QtdAordCapiItgz_1", "preferred": "QtdAprfCapiItgz_1",
        "total": "QtdTotAcaoCapiItgz_1", "treasury_ordinary": "QtdAordTeso_1",
        "treasury_preferred": "QtdAprfTeso_1", "treasury_total": "QtdTotAcaoTeso_1",
    }
    counts = {}
    for name, cell in ids.items():
        value = parser.cells.get(cell, "").strip()
        if not re.fullmatch(r"\d{1,3}(?:\.\d{3})*|\d+", value):
            raise ValueError(f"missing or invalid capital cell: {cell}")
        counts[name] = int(value.replace(".", "")) * scale
    for prefix in ("", "treasury_"):
        if counts[prefix + "ordinary"] + counts[prefix + "preferred"] != counts[prefix + "total"]:
            raise ValueError("capital class sum mismatch")
    if counts["total"] <= 0 or any(counts["treasury_" + k] > counts[k] for k in ("ordinary", "preferred")):
        raise ValueError("invalid treasury or issued capital")
    return {
        **metadata, **counts, "basis_date": basis, "share_scale": scales[0],
        "rounding_unit_shares": scale, "source": source,
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "outstanding_ordinary": counts["ordinary"] - counts["treasury_ordinary"],
        "outstanding_preferred": counts["preferred"] - counts["treasury_preferred"],
        "eligible_for_valuation": False,
        "remaining_gate": "class-price equivalence and intervening capital events",
    }
