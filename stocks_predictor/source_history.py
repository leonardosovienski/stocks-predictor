"""Offline, issuer-level source observations. These are not factor inputs.

An FCA identifier is available only after its own filing. A reported capital
approval date is preserved verbatim; it is never substituted for a verified
effective share-count date. Authorized capital is not issued capital.
"""

from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

if __package__:
    from .cvm_pit import digits, iso_date, receipt_dates, zip_rows
else:
    from cvm_pit import digits, iso_date, receipt_dates, zip_rows


def document_metadata(payload, kind, year):
    required = {"ID_DOC", "CNPJ_CIA", "DT_REFER", "VERSAO", "DT_RECEB"}
    result = {}
    for row in zip_rows(payload, f"{kind}_cia_aberta_{year}.csv", required):
        doc = row["ID_DOC"].strip()
        item = {
            "cnpj": digits(row["CNPJ_CIA"]),
            "ref_date": iso_date(row["DT_REFER"]),
            "version": int(row["VERSAO"]),
            "received_at": receipt_dates(row["DT_RECEB"])[0],
            "available_at": receipt_dates(row["DT_RECEB"])[1],
        }
        if not doc or len(item["cnpj"]) != 14 or item["version"] < 1:
            raise ValueError("invalid document identity")
        if doc in result and result[doc] != item:
            raise ValueError(f"conflicting metadata for {kind}/{doc}")
        result[doc] = item
    return result


def match_document(row, metadata):
    doc = row["ID_Documento"].strip()
    observed = metadata.get(doc)
    if observed is None:
        raise ValueError(f"missing document metadata: {doc}")
    if (digits(row["CNPJ_Companhia"]), iso_date(row["Data_Referencia"]), int(row["Versao"])) != (
        observed["cnpj"],
        observed["ref_date"],
        observed["version"],
    ):
        raise ValueError(f"document identity mismatch: {doc}")
    return {"document_id": doc, **observed}


def derive_fca_securities(payload, year, *, issues=None):
    metadata = document_metadata(payload, "fca", year)
    issues = issues if issues is not None else []
    sha = hashlib.sha256(payload).hexdigest()
    rows = zip_rows(
        payload,
        f"fca_cia_aberta_valor_mobiliario_{year}.csv",
        {
            "ID_Documento",
            "CNPJ_Companhia",
            "Data_Referencia",
            "Versao",
            "Codigo_Negociacao",
            "Valor_Mobiliario",
            "Data_Inicio_Negociacao",
            "Data_Fim_Negociacao",
            "Composicao_BDR_Unit",
        },
    )
    result = []
    for index, row in enumerate(rows, 2):
        ticker = row["Codigo_Negociacao"].strip()
        if not re.fullmatch(r"[A-Z]{4}\d{1,2}", ticker):
            issues.append(
                {
                    "document_key": json.dumps(["FCA", row["ID_Documento"], index]),
                    "reason": "MISSING_OR_UNSUPPORTED_SECURITY_CODE",
                }
            )
            continue
        item = match_document(row, metadata)
        start = row["Data_Inicio_Negociacao"].strip()
        end = row["Data_Fim_Negociacao"].strip()
        if not start or (end and end < start):
            issues.append(
                {
                    "document_key": json.dumps(["FCA", item["document_id"], index]),
                    "reason": "INVALID_TRADING_INTERVAL",
                }
            )
            continue
        result.append(
            {
                **item,
                "ticker": ticker,
                "security_type": row["Valor_Mobiliario"],
                "unit_composition": row["Composicao_BDR_Unit"],
                "trading_start": iso_date(start),
                "trading_end": iso_date(end) if end else None,
                "source": f"CVM FCA {year}",
                "source_sha256": sha,
                "source_row": index,
            }
        )
    return result


def security_links_asof(records, cnpj, asof):
    """Only a filing already available can establish a security relationship."""
    iso_date(asof)
    eligible = [r for r in records if r["cnpj"] == cnpj and r["available_at"] <= asof]
    if not eligible:
        return []
    latest = max((r["ref_date"], r["version"], r["available_at"]) for r in eligible)
    return sorted(
        {
            r["ticker"]
            for r in eligible
            if (r["ref_date"], r["version"], r["available_at"]) == latest
            and r["trading_start"] <= asof
            and (r["trading_end"] is None or asof <= r["trading_end"])
        }
    )


def share_integer(value):
    if not value.strip():
        return None
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid reported share count") from exc
    if not number.is_finite() or number < 0 or number != number.to_integral_value():
        raise ValueError("invalid reported share count")
    return int(number)


def derive_reported_capital(payload, year, *, issues=None):
    metadata = document_metadata(payload, "fre", year)
    issues = issues if issues is not None else []
    sha = hashlib.sha256(payload).hexdigest()
    rows = zip_rows(
        payload,
        f"fre_cia_aberta_capital_social_{year}.csv",
        {
            "ID_Documento",
            "CNPJ_Companhia",
            "Data_Referencia",
            "Versao",
            "Tipo_Capital",
            "ID_Capital_Social",
            "Quantidade_Acoes_Ordinarias",
            "Quantidade_Acoes_Preferenciais",
            "Quantidade_Total_Acoes",
            "Data_Autorizacao_Aprovacao",
        },
    )
    result = []
    for row in rows:
        if row["Tipo_Capital"].strip() != "Capital Emitido":
            continue
        identity = match_document(row, metadata)
        try:
            on = share_integer(row["Quantidade_Acoes_Ordinarias"])
            pn = share_integer(row["Quantidade_Acoes_Preferenciais"])
            total_field = share_integer(row["Quantidade_Total_Acoes"])
            class_sum = on + pn if on is not None and pn is not None else None
            if total_field and class_sum is not None and total_field != class_sum:
                raise ValueError("reported total differs from ON + PN")
            total = total_field or class_sum
            if not total:
                raise ValueError("missing positive issued capital")
        except ValueError as exc:
            issues.append(
                {
                    "document_key": json.dumps(
                        ["CAPITAL", identity["document_id"], row["ID_Capital_Social"]]
                    ),
                    "reason": str(exc),
                }
            )
            continue
        result.append(
            {
                **identity,
                "capital_record_id": row["ID_Capital_Social"],
                "reported_ordinary": on,
                "reported_preferred": pn,
                "reported_total_field": total_field,
                "reported_total": total,
                "count_method": "reported_total" if total_field else "reported_ON_plus_PN",
                "capital_approval_date": row["Data_Autorizacao_Aprovacao"] or None,
                "basis_date": None,
                "eligible_for_valuation": False,
                "source": f"CVM FRE capital social {year}",
                "source_sha256": sha,
            }
        )
    return result
