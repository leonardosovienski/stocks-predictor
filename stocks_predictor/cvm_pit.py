"""Versioned CVM derivations. Legacy fundamentals are never updated here.

Date-only receipt metadata becomes usable on the following calendar day:
the archive does not establish that the filing was public before the close.
FRE reference dates are labels, not the effective date of a share count.
"""

from collections import defaultdict
import csv
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import logging
import math
from pathlib import PurePosixPath
import zipfile

if __package__:
    from . import ingest_cvm
else:
    import ingest_cvm


FINANCIAL_FIELDS = (
    "ativo_total",
    "passivo_total",
    "patrimonio_liquido",
    "lucro_liquido",
    "receita_liquida",
    "fluxo_caixa_operacional",
    "roe",
    "leverage",
    "net_margin",
    "accruals",
)


def iso_date(value):
    value = value.strip()
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError(f"expected ISO calendar date: {value!r}")
    return value


def receipt_dates(value):
    # Keep the observed date AND the conservative daily availability cutoff.
    received = iso_date(value.strip()[:10])
    return received, (date.fromisoformat(received) + timedelta(days=1)).isoformat()


def monetary_reais(value, scale, currency):
    if currency.strip().upper() != "REAL":
        raise ValueError(f"unverified currency: {currency!r}")
    multiplier = {"MIL": Decimal(1000), "UNIDADE": Decimal(1)}.get(scale.strip().upper())
    if multiplier is None:
        raise ValueError(f"unverified monetary scale: {scale!r}")
    try:
        number = Decimal(value.strip())
    except InvalidOperation as exc:
        raise ValueError(f"invalid CVM decimal: {value!r}") from exc
    result = number * multiplier
    if not result.is_finite() or not math.isfinite(float(result)):
        raise ValueError("non-finite CVM monetary value")
    return result


def zip_rows(payload, basename, required):
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [n for n in archive.namelist() if PurePosixPath(n).name == basename]
        if len(names) != 1:
            raise ValueError(f"expected one ZIP member {basename}, got {len(names)}")
        with archive.open(names[0]) as stream:
            reader = csv.DictReader(io.TextIOWrapper(stream, encoding="latin-1"), delimiter=";")
            if not required.issubset(reader.fieldnames or []):
                raise ValueError(f"{basename}: missing columns {required - set(reader.fieldnames or [])}")
            result = []
            for row in reader:
                if None in row or any(v is None for v in row.values()):
                    raise ValueError(f"{basename}: malformed CSV row")
                result.append(row)
            return result


def digits(value):
    return "".join(c for c in value if c.isdigit())


def dfp_key(row):
    cnpj = digits(row["CNPJ_CIA"])
    if len(cnpj) != 14:
        raise ValueError("invalid CNPJ")
    version = int(row["VERSAO"])
    if version < 1:
        raise ValueError("invalid DFP version")
    return cnpj, iso_date(row["DT_REFER"]), version


def dfp_received_dates(payload, year, *, ambiguous=None):
    rows = zip_rows(payload, f"dfp_cia_aberta_{year}.csv", {"CNPJ_CIA", "DT_REFER", "VERSAO", "DT_RECEB"})
    out = {}
    for row in rows:
        key, received = dfp_key(row), receipt_dates(row["DT_RECEB"])
        if received[0] < key[1]:
            raise ValueError(f"DFP received before its fiscal period ended: {key}")
        if key in out and out[key] != received:
            if ambiguous is None:
                raise ValueError(f"conflicting receipt dates for {key}")
            ambiguous.add(key)
        out[key] = received
    for key in ambiguous or ():
        out.pop(key, None)
    return out


def statement_rows(rows, statement):
    """Strict public statement parser; fields match the official DFP layout."""
    iterator = iter(rows)
    header = next(iterator, [])
    required = {
        "CNPJ_CIA",
        "DENOM_CIA",
        "DT_REFER",
        "VERSAO",
        "MOEDA",
        "ESCALA_MOEDA",
        "ORDEM_EXERC",
        "CD_CONTA",
        "DS_CONTA",
        "VL_CONTA",
    }
    if not required.issubset(header):
        raise ValueError(f"DFP {statement}: missing columns {required - set(header)}")
    out = []
    for values in iterator:
        if len(values) != len(header):
            raise ValueError(f"DFP {statement}: malformed row")
        row = dict(zip(header, values))
        if ingest_cvm._norm(row["ORDEM_EXERC"]) != "ultimo":
            continue
        cnpj, ref, version = dfp_key(row)
        if not row["VL_CONTA"].strip():
            continue
        out.append(
            {
                "company": row["DENOM_CIA"].strip(),
                "cnpj": cnpj,
                "ref_date": ref,
                "version": version,
                "statement": statement,
                "account_code": row["CD_CONTA"].strip(),
                "account_desc": row["DS_CONTA"].strip(),
                "value": float(monetary_reais(row["VL_CONTA"], row["ESCALA_MOEDA"], row["MOEDA"])),
            }
        )
    if not out:
        raise ValueError(f"DFP {statement}: no current-period rows")
    return out


def derive_dfp(payload, year, *, issues=None):
    """All available statement versions, joined only to their own receipt date."""
    ambiguous = set()
    dates = dfp_received_dates(payload, year, ambiguous=ambiguous)
    issues = issues if issues is not None else []
    rejected = set()
    groups = defaultdict(lambda: defaultdict(list))
    for statement in ("BPA_con", "BPP_con", "DRE_con", "DFC_MI_con"):
        name = f"dfp_cia_aberta_{statement}_{year}.csv"
        # Absence is explicit; malformed present files always fail.
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            if statement == "DFC_MI_con" and name not in [PurePosixPath(n).name for n in archive.namelist()]:
                continue
        raw = zip_rows(payload, name, {"VERSAO", "MOEDA", "ESCALA_MOEDA"})
        if not raw:
            raise ValueError(f"empty {name}")
        parsed = statement_rows([list(raw[0])] + [list(r.values()) for r in raw], statement)
        for row in parsed:
            key = row["cnpj"], row["ref_date"], row["version"]
            if key not in dates:
                if key not in rejected:
                    reason = "AMBIGUOUS_RECEIPT" if key in ambiguous else "MISSING_DOCUMENT_VERSION"
                    issues.append({"document_key": json.dumps(key), "reason": reason})
                    logging.warning("DFP document excluded: %s %s", key, reason)
                    rejected.add(key)
                continue
            groups[key][statement].append(row)
    result = []
    sha = hashlib.sha256(payload).hexdigest()
    for (cnpj, ref, version), statements in sorted(groups.items()):
        all_rows = [r for rows in statements.values() for r in rows]
        names = {ingest_cvm._norm(r["company"]) for r in all_rows}
        if len(names) != 1:
            raise ValueError(f"inconsistent company names in document {cnpj}/{version}")

        # Account extraction runs within ONE CNPJ / period / version; no cross-version fallback.
        def pick(statement, code, required=(), any_words=()):
            found = ingest_cvm._pick_account(statements.get(statement, []), code, required, any_words)
            return found.get((next(iter(names)), ref))

        a = pick("BPA_con", "1", ("ativo_total",))
        p = pick("BPP_con", "2", ("passivo_total",))
        e = pick("BPP_con", "2.03", ("patrimonio_liquido",))
        l = pick("DRE_con", None, ("periodo",), ("lucro", "prejuizo"))
        revenue = pick("DRE_con", "3.01", ("receita",))
        cash = pick("DFC_MI_con", "6.01", ("caixa", "operacion"))

        def ratio(numerator, denominator):
            return (
                numerator / denominator
                if numerator is not None and denominator is not None and denominator > 0
                else None
            )

        received, available = dates[cnpj, ref, version]
        result.append(
            {
                "company": next(iter(names)),
                "cnpj": cnpj,
                "ref_date": ref,
                "document_version": version,
                "received_at": received,
                "available_at": available,
                "source": f"CVM DFP {year}",
                "source_sha256": sha,
                "ativo_total": a,
                "passivo_total": p,
                "patrimonio_liquido": e,
                "lucro_liquido": l,
                "receita_liquida": revenue,
                "fluxo_caixa_operacional": cash,
                "roe": ratio(l, e),
                "leverage": ratio(p - e if p is not None and e is not None else None, a),
                "net_margin": ratio(l, revenue),
                "accruals": ratio(l - cash if l is not None and cash is not None else None, a),
            }
        )
    return result


def append_rows(conn, table, rows, identity):
    """Atomic, immutable derivations; identical imports are idempotent, conflicts fail."""
    if table not in {
        "fundamentals_pit",
        "shares_pit",
        "cash_events",
        "cash_event_coverage",
        "ingestion_issues",
        "stock_bonus_events",
    }:
        raise ValueError("unsupported derivation table")
    count = 0
    conn.execute("SAVEPOINT cvm_derivation")
    try:
        for row in rows:
            columns = list(row)
            where = " AND ".join(f"{key}=?" for key in identity)
            prior = conn.execute(
                f"SELECT {','.join(columns)} FROM {table} WHERE {where}", [row[key] for key in identity]
            ).fetchone()
            values = tuple(row.values())
            if prior is not None:
                if tuple(prior) != values:
                    raise ValueError(f"conflicting immutable {table} record: {[row[k] for k in identity]}")
                continue
            conn.execute(
                f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})", values
            )
            count += 1
        conn.execute("RELEASE cvm_derivation")
    except Exception:
        conn.execute("ROLLBACK TO cvm_derivation")
        conn.execute("RELEASE cvm_derivation")
        raise
    return count


def ingest_dfp(conn, year, companies=None, ticker_of=None, zbytes=None):
    if zbytes is None:
        zbytes = ingest_cvm.download_zip(ingest_cvm.DFP_URL.format(year=year))
    records = []
    issues = []
    for row in derive_dfp(zbytes, year, issues=issues):
        if companies is not None and row["company"] not in companies:
            continue
        ticker = (ticker_of or {}).get(row["company"])
        if ticker:
            records.append({"ticker": ticker, **{k: v for k, v in row.items() if k != "company"}})
    conn.execute("SAVEPOINT dfp_import")
    try:
        count = append_rows(
            conn,
            "fundamentals_pit",
            records,
            ("ticker", "cnpj", "ref_date", "document_version", "source_sha256"),
        )
        append_rows(
            conn,
            "ingestion_issues",
            [{**r, "source_sha256": hashlib.sha256(zbytes).hexdigest()} for r in issues],
            ("source_sha256", "document_key", "reason"),
        )
        conn.execute("RELEASE dfp_import")
        return count
    except Exception:
        conn.execute("ROLLBACK TO dfp_import")
        conn.execute("RELEASE dfp_import")
        raise


def derive_fre_shares(payload, year, basis_by_document=None, *, issues=None):
    """Preserve ID_DOC versions. Unknown share/price basis stays ineligible."""
    main = zip_rows(payload, f"fre_cia_aberta_{year}.csv", {"ID_DOC", "DT_RECEB"})
    received = {}
    for row in main:
        key, val = row["ID_DOC"].strip(), receipt_dates(row["DT_RECEB"])
        if key in received and received[key] != val:
            raise ValueError(f"conflicting FRE receipt for {key}")
        received[key] = val
    raw = zip_rows(
        payload,
        f"fre_cia_aberta_distribuicao_capital_{year}.csv",
        {"ID_Documento", "Nome_Companhia", "Data_Referencia"},
    )
    if not raw:
        raise ValueError("empty FRE capital file")
    rows = ingest_cvm.parse_fre_float_rows([list(raw[0])] + [list(r.values()) for r in raw])
    unique = {}
    issues = issues if issues is not None else []
    rejected = set()
    for row in rows:
        doc = row["doc_id"]
        if doc not in received:
            raise ValueError(f"FRE capital has no matching ID_DOC: {doc}")
        shares = row["shares_outstanding"]
        if shares is None or not math.isfinite(shares) or shares <= 0:
            reason = "MISSING_TOTAL_SHARES" if shares is None else "INVALID_TOTAL_SHARES"
            issue = {"document_key": json.dumps(["FRE", doc]), "reason": reason}
            if issue not in issues:
                issues.append(issue)
            rejected.add(doc)
            continue
        basis = (basis_by_document or {}).get(doc, {})
        basis_date = basis.get("basis_date")
        if basis_date:
            iso_date(basis_date)
            if basis_date > received[doc][0] or not basis.get("basis_source"):
                raise ValueError("share basis requires dated source no later than receipt")
        record = {
            "company": ingest_cvm._norm(row["company"]),
            "ref_date": iso_date(row["ref_date"]),
            "document_id": doc,
            "received_at": received[doc][0],
            "available_at": received[doc][1],
            "shares_outstanding": shares,
            "basis_date": basis_date,
            "basis_source": basis.get("basis_source"),
            "price_basis_source": basis.get("price_basis_source"),
            "source": f"CVM FRE {year}",
            "source_sha256": hashlib.sha256(payload).hexdigest(),
        }
        if doc in unique and unique[doc] != record:
            raise ValueError(f"conflicting share counts within FRE document {doc}")
        unique[doc] = record
    for doc in rejected:
        unique.pop(doc, None)
    if not unique:
        raise ValueError("FRE: nenhuma linha com quantidade TOTAL de ações")
    return sorted(unique.values(), key=lambda r: (r["company"], r["available_at"], r["document_id"]))


def ingest_fre_shares(conn, year, ticker_of=None, zbytes=None, *, basis_by_document=None):
    if zbytes is None:
        zbytes = ingest_cvm.download_zip(ingest_cvm.FRE_URL.format(year=year))
    records = []
    issues = []
    for row in derive_fre_shares(zbytes, year, basis_by_document, issues=issues):
        ticker = (ticker_of or {}).get(row["company"])
        if ticker:
            records.append({"ticker": ticker, **{k: v for k, v in row.items() if k != "company"}})
    conn.execute("SAVEPOINT fre_import")
    try:
        count = append_rows(conn, "shares_pit", records, ("ticker", "document_id", "source_sha256"))
        append_rows(
            conn,
            "ingestion_issues",
            [{**r, "source_sha256": hashlib.sha256(zbytes).hexdigest()} for r in issues],
            ("source_sha256", "document_key", "reason"),
        )
        conn.execute("RELEASE fre_import")
        return count
    except Exception:
        conn.execute("ROLLBACK TO fre_import")
        conn.execute("RELEASE fre_import")
        raise


def fundamental_values(conn, tickers, asof, column):
    if column not in FINANCIAL_FIELDS:
        raise ValueError("unsupported financial field")
    iso_date(asof)
    result = {}
    for ticker in tickers:
        # Do NOT filter NULL before selecting the newest eligible version.
        rows = conn.execute(
            f"SELECT ref_date, document_version, {column} FROM fundamentals_pit"
            " WHERE ticker=? AND available_at<=? AND ref_date<=?"
            " ORDER BY ref_date DESC, document_version DESC",
            (ticker, asof, asof),
        ).fetchall()
        if not rows:
            continue
        latest = rows[0][:2]
        values = {r[2] for r in rows if r[:2] == latest}
        if len(values) != 1:
            raise ValueError(f"conflicting PIT fundamentals for {ticker}")
        value = values.pop()
        if value is not None and math.isfinite(value):
            result[ticker] = value
    return result


def shares_on_price_base(conn, ticker, shares, basis_date, asof):
    if not basis_date or shares is None or not math.isfinite(shares) or shares <= 0:
        return None
    iso_date(basis_date)
    if basis_date > asof:
        return None
    for (factor,) in conn.execute(
        "SELECT factor FROM adjustments WHERE ticker=?"
        " AND approved_by IS NOT NULL AND type IN ('split','grupamento')"
        " AND ex_date>? AND ex_date<=? ORDER BY ex_date",
        (ticker, basis_date, asof),
    ):
        if not math.isfinite(factor) or factor <= 0:
            raise ValueError("invalid approved split factor")
        shares /= factor
    return shares


def value_signals(conn, tickers, asof, column):
    if __package__:
        from . import factor
    else:
        import factor

    tickers = list(tickers)
    values = fundamental_values(conn, tickers, asof, column)
    result = {}
    for ticker in tickers:
        rows = conn.execute(
            "SELECT shares_outstanding, basis_date, basis_source, price_basis_source, available_at"
            " FROM shares_pit WHERE ticker=? AND available_at<=?"
            " ORDER BY available_at DESC",
            (ticker, asof),
        ).fetchall()
        if not rows:
            continue
        latest = rows[0][4]
        candidates = {tuple(r[:4]) for r in rows if r[4] == latest}
        if len(candidates) != 1:
            raise ValueError(f"ambiguous share documents for {ticker}")
        shares, basis, source, price_basis = candidates.pop()
        if not (basis and source and price_basis):
            continue
        shares = shares_on_price_base(conn, ticker, shares, basis, asof)
        price = factor._price_at(conn, ticker, asof)
        value = values.get(ticker)
        if shares and price and math.isfinite(price) and value is not None and value > 0:
            result[ticker] = value / (price * shares)
    return result


def summary(payload, year):
    issues = []
    rows = derive_dfp(payload, year, issues=issues)
    return {
        "year": year,
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "documents": len(rows),
        "currency": "BRL",
        "unit": "reais",
        "rejected_documents": issues,
        "financial_field_counts": {k: sum(r[k] is not None for r in rows) for k in FINANCIAL_FIELDS},
        "performance_observed": False,
        "proof_authorized": False,
        "parser_version": 2,
        "derivation_sha256": hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest(),
    }
