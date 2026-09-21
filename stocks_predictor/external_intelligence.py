"""Research-only external intelligence acquisition, normalization and lineage.

This module owns CVM/B3-specific semantics.  It does not expose observations to
the factor, ranking, portfolio, paper or BIG_WINNER pipelines.
"""
from __future__ import annotations

import argparse
import csv
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import tempfile
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import zipfile
from zoneinfo import ZoneInfo

from predictor_core.kernel import infra


SCHEMA_VERSION = "external-intelligence/1"
RECEIPT_VERSION = "external-intelligence-receipt/1"
COLLECTOR_VERSION = "1"
MAX_SOURCE_BYTES = 64 * 1024 * 1024
SAO_PAULO = ZoneInfo("America/Sao_Paulo")

B3_TABLES = {
    "BTBLendingOpenPosition": (
        "b3-lending-open-position",
        (
            "RptDt", "DtRef", "TckrSymb", "ISIN", "Company", "Type", "Market",
            "StockBalance", "AvgPric", "Balance",
        ),
    ),
    "BTBLoanBalance": (
        "b3-loan-balance",
        (
            "RptDt", "DtRef", "TckrSymb", "ISIN", "Company", "Market",
            "QtyCtrctsDay", "ValCtrctsDay", "DnrMinRate", "DnrAvrgRate", "DnrMaxRate",
            "TkrMinRate", "TkrAvrgRate", "TkrMaxRate", "BRLValue", "Dnr", "Tkr",
        ),
    ),
}
B3_PAGE_SIZE = 1000

VLMO_MAIN = (
    "CNPJ_Companhia", "Nome_Companhia", "Data_Referencia", "Versao", "Codigo_CVM",
    "Categoria", "Tipo", "Data_Entrega", "Tipo_Apresentacao", "Motivo_Reapresentacao",
    "Protocolo_Entrega", "Link_Download",
)
VLMO_DETAIL = (
    "CNPJ_Companhia", "Nome_Companhia", "Data_Referencia", "Versao", "Tipo_Empresa",
    "Empresa", "Tipo_Cargo", "Tipo_Movimentacao", "Descricao_Movimentacao", "Tipo_Operacao",
    "Tipo_Ativo", "Caracteristica_Valor_Mobiliario", "Intermediario", "Data_Movimentacao",
    "Quantidade", "Preco_Unitario", "Volume",
)
BUYBACK_MAIN = (
    "ID_Programa", "CNPJ_Companhia", "Nome_Companhia", "Data_Deliberacao", "Data_Final_Prazo",
    "Situacao", "Tipo_Operacao", "Motivo", "Finalidade_Compra", "Quantidade_Acoes_Ordinarias",
    "Quantidade_Acoes_Preferenciais",
)
BUYBACK_INTERMEDIARIES = ("ID_Programa", "CNPJ_Intermediario", "Intermediario")
BUYBACK_QUANTITIES = (
    "ID_Programa", "Tipo_Acao", "Classe_Acao", "Quantidade_Circulacao", "Quantidade_Operacao",
)
IPE_COLUMNS = (
    "CNPJ_Companhia", "Nome_Companhia", "Codigo_CVM", "Data_Referencia", "Categoria", "Tipo",
    "Especie", "Assunto", "Data_Entrega", "Tipo_Apresentacao", "Protocolo_Entrega", "Versao",
    "Link_Download",
)

EXTERNAL_MIGRATIONS: list[tuple[str, str]] = [
    ("external_0001_foundation", """
        CREATE TABLE external_raw_objects (
            sha256 TEXT PRIMARY KEY CHECK(length(sha256)=64),
            relative_path TEXT NOT NULL UNIQUE,
            byte_length INTEGER NOT NULL CHECK(byte_length>=0),
            first_stored_at TEXT NOT NULL
        );
        CREATE TABLE external_source_versions (
            source_version_id TEXT PRIMARY KEY,
            publisher TEXT NOT NULL,
            dataset TEXT NOT NULL,
            logical_period TEXT NOT NULL,
            source_url TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            source_observed_at TEXT NOT NULL,
            http_etag TEXT,
            http_last_modified TEXT,
            sha256 TEXT NOT NULL REFERENCES external_raw_objects(sha256),
            byte_length INTEGER NOT NULL CHECK(byte_length>=0),
            parser_version TEXT NOT NULL,
            supersedes_source_version_id TEXT REFERENCES external_source_versions(source_version_id),
            UNIQUE(publisher,dataset,logical_period,sha256,parser_version)
        );
        CREATE INDEX external_source_period
            ON external_source_versions(publisher,dataset,logical_period,fetched_at);
        CREATE TABLE external_security_links (
            link_id TEXT PRIMARY KEY,
            company_cnpj TEXT NOT NULL CHECK(length(company_cnpj)=14),
            ticker TEXT NOT NULL,
            isin TEXT,
            trading_start TEXT NOT NULL,
            trading_end TEXT,
            information_available_date TEXT NOT NULL,
            source_version_id TEXT NOT NULL REFERENCES external_source_versions(source_version_id),
            CHECK(trading_end IS NULL OR trading_end>=trading_start)
        );
        CREATE INDEX external_security_asof
            ON external_security_links(company_cnpj,information_available_date,trading_start,trading_end);
        CREATE TABLE external_observations (
            observation_id TEXT PRIMARY KEY,
            source_version_id TEXT NOT NULL REFERENCES external_source_versions(source_version_id),
            family TEXT NOT NULL,
            natural_key TEXT NOT NULL,
            company_cnpj TEXT,
            ticker TEXT,
            isin TEXT,
            reference_at TEXT,
            event_at TEXT,
            received_at TEXT,
            available_at TEXT NOT NULL,
            first_seen_at TEXT NOT NULL,
            tradable_session TEXT,
            pit_status TEXT NOT NULL CHECK(pit_status IN ('PIT_STRICT','PIT_RECONSTRUCTED','HISTORICAL_ONLY')),
            temporal_reason TEXT NOT NULL,
            identity_status TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            UNIQUE(source_version_id,family,natural_key),
            CHECK(received_at IS NULL OR received_at<=substr(available_at,1,10))
        );
        CREATE INDEX external_observation_family_time
            ON external_observations(family,reference_at,available_at);
        CREATE TABLE external_observation_securities (
            observation_id TEXT NOT NULL REFERENCES external_observations(observation_id),
            link_id TEXT NOT NULL REFERENCES external_security_links(link_id),
            PRIMARY KEY(observation_id,link_id)
        );
        CREATE TABLE external_receipts (
            receipt_id TEXT PRIMARY KEY,
            source_version_id TEXT,
            command TEXT NOT NULL,
            status TEXT NOT NULL,
            receipt_json TEXT NOT NULL
        );
        CREATE TRIGGER external_raw_no_update BEFORE UPDATE ON external_raw_objects BEGIN
            SELECT RAISE(ABORT,'external raw objects are immutable'); END;
        CREATE TRIGGER external_raw_no_delete BEFORE DELETE ON external_raw_objects BEGIN
            SELECT RAISE(ABORT,'external raw objects are immutable'); END;
        CREATE TRIGGER external_versions_no_update BEFORE UPDATE ON external_source_versions BEGIN
            SELECT RAISE(ABORT,'external source versions are immutable'); END;
        CREATE TRIGGER external_versions_no_delete BEFORE DELETE ON external_source_versions BEGIN
            SELECT RAISE(ABORT,'external source versions are immutable'); END;
        CREATE TRIGGER external_observations_no_update BEFORE UPDATE ON external_observations BEGIN
            SELECT RAISE(ABORT,'external observations are immutable'); END;
        CREATE TRIGGER external_observations_no_delete BEFORE DELETE ON external_observations BEGIN
            SELECT RAISE(ABORT,'external observations are immutable'); END;
        CREATE TRIGGER external_links_no_update BEFORE UPDATE ON external_security_links BEGIN
            SELECT RAISE(ABORT,'external security links are immutable'); END;
        CREATE TRIGGER external_links_no_delete BEFORE DELETE ON external_security_links BEGIN
            SELECT RAISE(ABORT,'external security links are immutable'); END;
    """),
    ("external_0002_rejections", """
        CREATE TABLE external_rejections (
            rejection_id TEXT PRIMARY KEY,
            source_version_id TEXT NOT NULL REFERENCES external_source_versions(source_version_id),
            family TEXT NOT NULL,
            natural_key TEXT NOT NULL,
            reason TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE TRIGGER external_rejections_no_update BEFORE UPDATE ON external_rejections BEGIN
            SELECT RAISE(ABORT,'external rejections are immutable'); END;
        CREATE TRIGGER external_rejections_no_delete BEFORE DELETE ON external_rejections BEGIN
            SELECT RAISE(ABORT,'external rejections are immutable'); END;
    """),
    ("external_0003_receipt_immutability", """
        CREATE TRIGGER IF NOT EXISTS external_receipts_no_update
        BEFORE UPDATE ON external_receipts BEGIN
            SELECT RAISE(ABORT,'external receipts are immutable'); END;
        CREATE TRIGGER IF NOT EXISTS external_receipts_no_delete
        BEFORE DELETE ON external_receipts BEGIN
            SELECT RAISE(ABORT,'external receipts are immutable'); END;
    """),
]


class ExternalIntelligenceError(ValueError):
    status = "INTEGRITY_ERROR"


class SchemaDriftError(ExternalIntelligenceError):
    status = "SCHEMA_DRIFT"


class TemporalError(ExternalIntelligenceError):
    status = "TEMPORAL_ERROR"


class IdentityError(ExternalIntelligenceError):
    status = "IDENTITY_ERROR"


class SourceUnavailableError(ExternalIntelligenceError):
    status = "SOURCE_UNAVAILABLE"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest_identity(*parts: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(list(parts)).encode("utf-8")).hexdigest()


def utc_timestamp(value: str) -> str:
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TemporalError(f"invalid timestamp: {value!r}") from exc
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise TemporalError("timestamp requires an explicit UTC offset")
    return stamp.astimezone(UTC).isoformat().replace("+00:00", "Z")


def iso_date(value: str) -> str:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise TemporalError(f"invalid ISO date: {value!r}") from exc
    if parsed.isoformat() != value:
        raise TemporalError(f"invalid ISO date: {value!r}")
    return value


def digits(value: str) -> str:
    result = "".join(char for char in value if char.isdigit())
    if len(result) != 14:
        raise IdentityError(f"invalid CNPJ: {value!r}")
    return result


def decimal_text(value: Any, *, optional: bool = False, integer: bool = False) -> str | None:
    if value is None or str(value).strip() == "":
        if optional:
            return None
        raise SchemaDriftError("required numeric value is empty")
    text = str(value).strip()
    if "," in text:
        if "." in text:
            text = text.replace(".", "")
        text = text.replace(",", ".")
    try:
        number = Decimal(text)
    except InvalidOperation as exc:
        raise SchemaDriftError(f"invalid decimal: {value!r}") from exc
    if not number.is_finite() or (integer and number != number.to_integral_value()):
        raise SchemaDriftError(f"invalid numeric value: {value!r}")
    return str(number)


def validate_source_url(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ExternalIntelligenceError("source URL must be credential-free HTTPS")
    if re.search(r"(?:token|secret|password|api[_-]?key)=", parsed.query, re.I):
        raise ExternalIntelligenceError("source URL query contains a credential-like field")
    return url


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = infra.connect(path)
    try:
        infra.run_migrations(conn, EXTERNAL_MIGRATIONS)
        conn.execute("PRAGMA foreign_keys=ON")
    except BaseException:
        conn.close()
        raise
    return conn


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise ExternalIntelligenceError(f"content-addressed path conflict: {path}")
        return
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def preserve_raw(raw_root: Path, payload: bytes, stored_at: str) -> dict[str, Any]:
    if len(payload) > MAX_SOURCE_BYTES:
        raise ExternalIntelligenceError("source exceeds the 64 MiB acquisition limit")
    digest = hashlib.sha256(payload).hexdigest()
    relative = Path("sha256") / digest[:2] / digest
    _atomic_bytes(raw_root / relative, payload)
    return {
        "sha256": digest,
        "relative_path": relative.as_posix(),
        "byte_length": len(payload),
        "first_stored_at": utc_timestamp(stored_at),
    }


def _http_date(headers: Any) -> str:
    raw = headers.get("Date")
    if not raw:
        raise SourceUnavailableError("official response omitted its HTTP Date header")
    parsed = parsedate_to_datetime(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")


def fetch_bytes(url: str, *, body: bytes | None = None, timeout: float = 60) -> dict[str, Any]:
    url = validate_source_url(url)
    headers = {"Accept": "application/json" if body is not None else "application/zip"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers, method="POST" if body is not None else "GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read(MAX_SOURCE_BYTES + 1)
            if len(payload) > MAX_SOURCE_BYTES:
                raise ExternalIntelligenceError("source exceeds the 64 MiB acquisition limit")
            return {
                "payload": payload,
                "fetched_at": _http_date(response.headers),
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
            }
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SourceUnavailableError(f"official source request failed: {type(exc).__name__}") from exc


def source_file(path: Path, observed_at: str) -> dict[str, Any]:
    payload = path.read_bytes()
    if len(payload) > MAX_SOURCE_BYTES:
        raise ExternalIntelligenceError("source exceeds the 64 MiB acquisition limit")
    return {"payload": payload, "fetched_at": utc_timestamp(observed_at), "etag": None, "last_modified": None}


def trading_sessions(path: Path | None) -> list[str]:
    if path is None:
        return []
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    conn = sqlite3.connect(resolved.as_uri() + "?mode=ro", uri=True)
    try:
        rows = conn.execute("SELECT DISTINCT date FROM prices_raw ORDER BY date").fetchall()
    finally:
        conn.close()
    return [iso_date(row[0]) for row in rows]


def resolve_tradable_session(available_at: str, sessions: Iterable[str]) -> tuple[str | None, str]:
    local_date = datetime.fromisoformat(utc_timestamp(available_at).replace("Z", "+00:00")).astimezone(
        SAO_PAULO
    ).date().isoformat()
    candidates = sorted({iso_date(item) for item in sessions if item > local_date})
    if not candidates:
        return None, "NO_SUBSEQUENT_OBSERVED_B3_SESSION"
    return candidates[0], "FIRST_SUBSEQUENT_OBSERVED_B3_SESSION"


def _rows_from_zip(payload: bytes, basename: str, expected: tuple[str, ...]) -> list[dict[str, str]]:
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = [name for name in archive.namelist() if PurePosixPath(name).name == basename]
            if len(names) != 1:
                raise SchemaDriftError(f"expected exactly one ZIP member {basename}")
            with archive.open(names[0]) as binary:
                reader = csv.DictReader(io.TextIOWrapper(binary, encoding="latin-1"), delimiter=";")
                if tuple(reader.fieldnames or ()) != expected:
                    raise SchemaDriftError(
                        f"{basename}: columns changed; expected {list(expected)!r}, got {reader.fieldnames!r}"
                    )
                rows = []
                for row in reader:
                    if None in row or any(value is None for value in row.values()):
                        raise SchemaDriftError(f"{basename}: malformed CSV row")
                    rows.append(row)
                return rows
    except zipfile.BadZipFile as exc:
        raise SchemaDriftError("source is not a valid ZIP archive") from exc


def _json_payload(payload: bytes) -> Any:
    try:
        return json.loads(payload.decode("utf-8"), parse_float=Decimal, parse_constant=lambda x: (_ for _ in ()).throw(
            SchemaDriftError(f"non-finite JSON number: {x}")
        ))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SchemaDriftError("official JSON response is malformed or not UTF-8") from exc


def _source_version(
    conn: sqlite3.Connection,
    raw_root: Path,
    acquired: dict[str, Any],
    *,
    publisher: str,
    dataset: str,
    logical_period: str,
    source_url: str,
    parser_version: str,
) -> tuple[str, bool]:
    source_url = validate_source_url(source_url)
    fetched_at = utc_timestamp(acquired["fetched_at"])
    raw = preserve_raw(raw_root, acquired["payload"], fetched_at)
    identity = digest_identity(publisher, dataset, logical_period, raw["sha256"], parser_version)
    prior = conn.execute(
        "SELECT source_version_id FROM external_source_versions"
        " WHERE publisher=? AND dataset=? AND logical_period=? AND sha256<>?"
        " ORDER BY fetched_at DESC,source_version_id DESC LIMIT 1",
        (publisher, dataset, logical_period, raw["sha256"]),
    ).fetchone()
    existed = conn.execute(
        "SELECT 1 FROM external_source_versions WHERE source_version_id=?", (identity,)
    ).fetchone() is not None
    conn.execute(
        "INSERT OR IGNORE INTO external_raw_objects VALUES (?,?,?,?)",
        (raw["sha256"], raw["relative_path"], raw["byte_length"], raw["first_stored_at"]),
    )
    conn.execute(
        "INSERT OR IGNORE INTO external_source_versions"
        " (source_version_id,publisher,dataset,logical_period,source_url,fetched_at,source_observed_at,"
        " http_etag,http_last_modified,sha256,byte_length,parser_version,supersedes_source_version_id)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            identity, publisher, dataset, logical_period, source_url, fetched_at, fetched_at,
            acquired.get("etag"), acquired.get("last_modified"), raw["sha256"], raw["byte_length"],
            parser_version, prior[0] if prior else None,
        ),
    )
    return identity, existed


def _observation(
    conn: sqlite3.Connection,
    *,
    source_version_id: str,
    family: str,
    natural_key: Any,
    payload: dict[str, Any],
    available_at: str,
    sessions: list[str],
    company_cnpj: str | None = None,
    ticker: str | None = None,
    isin: str | None = None,
    reference_at: str | None = None,
    event_at: str | None = None,
    received_at: str | None = None,
    identity_status: str = "COMPANY_ONLY_UNRESOLVED",
) -> bool:
    available_at = utc_timestamp(available_at)
    if reference_at is not None:
        reference_at = iso_date(reference_at[:10])
    if event_at is not None:
        event_at = iso_date(event_at[:10])
    if received_at is not None:
        received_at = iso_date(received_at[:10])
        if received_at > available_at[:10]:
            raise TemporalError("received date is after collector first-seen time")
    tradable, reason = resolve_tradable_session(available_at, sessions)
    key = canonical_json(natural_key)
    observation_id = digest_identity(family, key, source_version_id)
    before = conn.total_changes
    conn.execute(
        "INSERT OR IGNORE INTO external_observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            observation_id, source_version_id, family, key, company_cnpj, ticker, isin, reference_at,
            event_at, received_at, available_at, available_at, tradable, "PIT_STRICT",
            "COLLECTOR_FIRST_SEEN;" + reason, identity_status, canonical_json(payload),
        ),
    )
    if company_cnpj and not ticker:
        _link_observation(conn, observation_id, company_cnpj, reference_at or event_at, available_at[:10])
    return conn.total_changes > before


def _link_observation(
    conn: sqlite3.Connection, observation_id: str, cnpj: str, security_date: str | None, known_date: str
) -> None:
    if security_date is None:
        return
    rows = conn.execute(
        "SELECT link_id FROM external_security_links WHERE company_cnpj=?"
        " AND information_available_date<=? AND trading_start<=?"
        " AND (trading_end IS NULL OR trading_end>=?) ORDER BY link_id",
        (cnpj, known_date, security_date, security_date),
    ).fetchall()
    for (link_id,) in rows:
        conn.execute(
            "INSERT OR IGNORE INTO external_observation_securities VALUES (?,?)",
            (observation_id, link_id),
        )


def _result(source_versions: list[str], read: int, persisted: int, rejected: int = 0) -> dict[str, Any]:
    return {
        "status": "SUCCESS",
        "source_version_ids": source_versions,
        "rows_read": read,
        "rows_rejected": rejected,
        "rows_persisted": persisted,
        "scientific_evidence_status": "NOT_EVALUATED",
        "economic_evidence_status": "NOT_EVALUATED",
        "research_only": True,
    }


def _reject(
    conn: sqlite3.Connection,
    *,
    source_version_id: str,
    family: str,
    natural_key: Any,
    reason: str,
    payload: dict[str, Any],
) -> None:
    key = canonical_json(natural_key)
    rejection_id = digest_identity(source_version_id, family, key, reason)
    conn.execute(
        "INSERT OR IGNORE INTO external_rejections VALUES (?,?,?,?,?,?)",
        (rejection_id, source_version_id, family, key, reason, canonical_json(payload)),
    )


def ingest_b3_lending(
    conn: sqlite3.Connection,
    raw_root: Path,
    reference_date: str,
    acquired_by_table: dict[str, dict[str, Any] | list[dict[str, Any]]],
    sessions: list[str],
) -> dict[str, Any]:
    reference_date = iso_date(reference_date)
    source_versions: list[str] = []
    rows_read = persisted = 0
    conn.execute("SAVEPOINT external_b3")
    try:
        for table_name, acquired_value in acquired_by_table.items():
            if table_name not in B3_TABLES:
                raise SchemaDriftError(f"unsupported B3 table {table_name}")
            dataset, expected = B3_TABLES[table_name]
            pages = acquired_value if isinstance(acquired_value, list) else [acquired_value]
            expected_table_version: int | None = None
            for page_number, acquired in enumerate(pages, 1):
                document = _json_payload(acquired["payload"])
                table = document.get("table") if isinstance(document, dict) else None
                if not isinstance(table, dict) or table.get("name") != table_name:
                    raise SchemaDriftError(f"B3 response does not contain table {table_name}")
                columns = tuple(column.get("name") for column in table.get("columns", []))
                if columns != expected:
                    raise SchemaDriftError(f"{table_name}: column contract changed")
                if table.get("pageCount") != len(pages) or document.get("status") not in (4, 5):
                    raise SchemaDriftError(f"{table_name}: incomplete or unpublished response")
                table_version = table.get("version")
                if not isinstance(table_version, int) or isinstance(table_version, bool) or table_version < 1:
                    raise SchemaDriftError(f"{table_name}: invalid table version")
                if expected_table_version is None:
                    expected_table_version = table_version
                elif table_version != expected_table_version:
                    raise SchemaDriftError(f"{table_name}: table version changed during pagination")
                logical_period = f"{reference_date}/page-{page_number:04d}-of-{len(pages):04d}"
                version_id, _ = _source_version(
                    conn, raw_root, acquired, publisher="B3", dataset=dataset,
                    logical_period=logical_period,
                    source_url=(
                        f"https://arquivos.b3.com.br/bdi/table/{table_name}/{reference_date}/"
                        f"{reference_date}/{page_number}/{B3_PAGE_SIZE}"
                    ),
                    parser_version=f"b3-bdi-{table_name}/1",
                )
                source_versions.append(version_id)
                for values in table.get("values", []):
                    if not isinstance(values, list) or len(values) != len(expected):
                        raise SchemaDriftError(f"{table_name}: malformed row")
                    row = dict(zip(expected, values))
                    if str(row["DtRef"])[:10] != reference_date or str(row["RptDt"])[:10] != reference_date:
                        raise TemporalError(f"{table_name}: row date differs from requested period")
                    ticker, isin = str(row["TckrSymb"]).strip(), str(row["ISIN"]).strip()
                    if not re.fullmatch(r"[A-Z0-9]{5,12}", ticker) or not re.fullmatch(
                        r"[A-Z]{2}[A-Z0-9]{9}\d", isin
                    ):
                        raise IdentityError(f"{table_name}: invalid ticker or ISIN")
                    normalized = {
                        key: (decimal_text(value, optional=True) if key not in expected[:7] else value)
                        for key, value in row.items()
                    }
                    natural = [reference_date, ticker, isin, row.get("Type"), row["Market"]]
                    if _observation(
                        conn, source_version_id=version_id, family=dataset, natural_key=natural,
                        payload=normalized, available_at=acquired["fetched_at"], sessions=sessions,
                        ticker=ticker, isin=isin, reference_at=reference_date,
                        identity_status="DIRECT_B3_TICKER_ISIN",
                    ):
                        persisted += 1
                    rows_read += 1
        conn.execute("RELEASE external_b3")
    except BaseException:
        conn.execute("ROLLBACK TO external_b3")
        conn.execute("RELEASE external_b3")
        raise
    return _result(source_versions, rows_read, persisted)


def ingest_vlmo(
    conn: sqlite3.Connection, raw_root: Path, year: int, acquired: dict[str, Any], sessions: list[str]
) -> dict[str, Any]:
    main = _rows_from_zip(acquired["payload"], f"vlmo_cia_aberta_{year}.csv", VLMO_MAIN)
    details = _rows_from_zip(acquired["payload"], f"vlmo_cia_aberta_con_{year}.csv", VLMO_DETAIL)
    documents: dict[tuple[str, str, int], dict[str, str]] = {}
    for row in main:
        key = (digits(row["CNPJ_Companhia"]), iso_date(row["Data_Referencia"]), int(row["Versao"]))
        if key in documents:
            raise SchemaDriftError(f"duplicate VLMO document identity: {key}")
        documents[key] = row
    conn.execute("SAVEPOINT external_vlmo")
    try:
        version_id, _ = _source_version(
            conn, raw_root, acquired, publisher="CVM", dataset="VLMO", logical_period=str(year),
            source_url=f"https://dados.cvm.gov.br/dados/cia_aberta/DOC/VLMO/DADOS/vlmo_cia_aberta_{year}.zip",
            parser_version="cvm-vlmo/1",
        )
        persisted = 0
        for index, row in enumerate(details, 2):
            cnpj = digits(row["CNPJ_Companhia"])
            reference = iso_date(row["Data_Referencia"])
            key = (cnpj, reference, int(row["Versao"]))
            document = documents.get(key)
            if document is None:
                raise SchemaDriftError(f"VLMO detail has no document metadata: {key}")
            received = iso_date(document["Data_Entrega"][:10])
            movement = iso_date(row["Data_Movimentacao"][:10]) if row["Data_Movimentacao"].strip() else None
            normalized = {
                "document_protocol": document["Protocolo_Entrega"].strip(),
                "document_version": key[2],
                "company": document["Nome_Companhia"].strip(),
                "management_group": row["Tipo_Cargo"].strip(),
                "related_entity_type": row["Tipo_Empresa"].strip(),
                "related_entity": row["Empresa"].strip(),
                "movement_type": row["Tipo_Movimentacao"].strip(),
                "movement_description": row["Descricao_Movimentacao"].strip(),
                "operation_type": row["Tipo_Operacao"].strip(),
                "asset_type": row["Tipo_Ativo"].strip(),
                "security_characteristic": row["Caracteristica_Valor_Mobiliario"].strip(),
                "intermediary": row["Intermediario"].strip(),
                "movement_date": movement,
                "quantity": decimal_text(row["Quantidade"], optional=True),
                "unit_price": decimal_text(row["Preco_Unitario"], optional=True),
                "volume": decimal_text(row["Volume"], optional=True),
                "download_reference": document["Link_Download"].strip(),
                "source_row": index,
            }
            natural = [document["Protocolo_Entrega"], index, hashlib.sha256(canonical_json(normalized).encode()).hexdigest()]
            if _observation(
                conn, source_version_id=version_id, family="cvm-vlmo", natural_key=natural,
                payload=normalized, available_at=acquired["fetched_at"], sessions=sessions,
                company_cnpj=cnpj, reference_at=reference, event_at=movement, received_at=received,
            ):
                persisted += 1
        conn.execute("RELEASE external_vlmo")
    except BaseException:
        conn.execute("ROLLBACK TO external_vlmo")
        conn.execute("RELEASE external_vlmo")
        raise
    return _result([version_id], len(details), persisted)


def ingest_buyback(
    conn: sqlite3.Connection, raw_root: Path, acquired: dict[str, Any], sessions: list[str]
) -> dict[str, Any]:
    main = _rows_from_zip(acquired["payload"], "cia_aberta_recompra_acoes.csv", BUYBACK_MAIN)
    intermediaries = _rows_from_zip(
        acquired["payload"], "cia_aberta_recompra_acoes_intermediarios.csv", BUYBACK_INTERMEDIARIES
    )
    quantities = _rows_from_zip(
        acquired["payload"], "cia_aberta_recompra_acoes_quantidades.csv", BUYBACK_QUANTITIES
    )
    by_program_i: dict[str, list[dict[str, str]]] = {}
    by_program_q: dict[str, list[dict[str, str]]] = {}
    for row in intermediaries:
        by_program_i.setdefault(row["ID_Programa"], []).append(row)
    for row in quantities:
        by_program_q.setdefault(row["ID_Programa"], []).append(row)
    conn.execute("SAVEPOINT external_buyback")
    try:
        period = acquired["fetched_at"][:10]
        version_id, _ = _source_version(
            conn, raw_root, acquired, publisher="CVM", dataset="RECOMPRA_ACOES", logical_period=period,
            source_url="https://dados.cvm.gov.br/dados/CIA_ABERTA/EVENTOS/RECOMPRA_ACOES/DADOS/cia_aberta_recompra_acoes.zip",
            parser_version="cvm-buyback/1",
        )
        persisted = rejected = 0
        for row in main:
            program = row["ID_Programa"].strip()
            if not program:
                raise IdentityError("buyback program has no identity")
            cnpj = digits(row["CNPJ_Companhia"])
            start = iso_date(row["Data_Deliberacao"])
            end = iso_date(row["Data_Final_Prazo"]) if row["Data_Final_Prazo"].strip() else None
            if end and end < start:
                _reject(
                    conn, source_version_id=version_id, family="cvm-buyback", natural_key=program,
                    reason="PROGRAM_END_BEFORE_DELIBERATION", payload=row,
                )
                rejected += 1
                continue
            normalized_quantities = []
            for item in by_program_q.get(program, []):
                normalized_quantities.append({
                    "share_type": item["Tipo_Acao"].strip(),
                    "share_class": item["Classe_Acao"].strip() or None,
                    "quantity_outstanding": decimal_text(item["Quantidade_Circulacao"], optional=True, integer=True),
                    "quantity_operation": decimal_text(item["Quantidade_Operacao"], optional=True, integer=True),
                })
            normalized = {
                "program_id": program,
                "company": row["Nome_Companhia"].strip(),
                "program_start": start,
                "program_end": end,
                "status": row["Situacao"].strip(),
                "operation_type": row["Tipo_Operacao"].strip() or None,
                "reason": row["Motivo"].strip() or None,
                "purpose": row["Finalidade_Compra"].strip() or None,
                "authorized_ordinary_quantity": decimal_text(
                    row["Quantidade_Acoes_Ordinarias"], optional=True, integer=True
                ),
                "authorized_preferred_quantity": decimal_text(
                    row["Quantidade_Acoes_Preferenciais"], optional=True, integer=True
                ),
                "quantities": sorted(normalized_quantities, key=canonical_json),
                "intermediaries": sorted(
                    ({"cnpj": digits(item["CNPJ_Intermediario"]), "name": item["Intermediario"].strip()}
                     for item in by_program_i.get(program, [])),
                    key=canonical_json,
                ),
                "executed_quantity": None,
                "executed_value": None,
            }
            if _observation(
                conn, source_version_id=version_id, family="cvm-buyback", natural_key=program,
                payload=normalized, available_at=acquired["fetched_at"], sessions=sessions,
                company_cnpj=cnpj, reference_at=start,
            ):
                persisted += 1
        conn.execute("RELEASE external_buyback")
    except BaseException:
        conn.execute("ROLLBACK TO external_buyback")
        conn.execute("RELEASE external_buyback")
        raise
    return _result([version_id], len(main), persisted, rejected)


def ingest_ipe(
    conn: sqlite3.Connection, raw_root: Path, year: int, acquired: dict[str, Any], sessions: list[str]
) -> dict[str, Any]:
    rows = _rows_from_zip(acquired["payload"], f"ipe_cia_aberta_{year}.csv", IPE_COLUMNS)
    conn.execute("SAVEPOINT external_ipe")
    try:
        version_id, source_existed = _source_version(
            conn, raw_root, acquired, publisher="CVM", dataset="IPE_METADATA", logical_period=str(year),
            source_url=f"https://dados.cvm.gov.br/dados/cia_aberta/DOC/IPE/DADOS/ipe_cia_aberta_{year}.zip",
            parser_version="cvm-ipe-metadata/1",
        )
        persisted = rejected = 0
        collection_year = datetime.fromisoformat(
            utc_timestamp(acquired["fetched_at"]).replace("Z", "+00:00")
        ).astimezone(SAO_PAULO).year
        for source_row, row in enumerate(rows, 2):
            cnpj = digits(row["CNPJ_Companhia"])
            reference = iso_date(row["Data_Referencia"][:10])
            received = iso_date(row["Data_Entrega"][:10])
            if date.fromisoformat(reference).year > collection_year + 50:
                _reject(
                    conn, source_version_id=version_id, family="cvm-ipe-metadata",
                    natural_key=["IMPLAUSIBLE_REFERENCE_DATE", source_row],
                    reason="REFERENCE_DATE_MORE_THAN_50_YEARS_AFTER_COLLECTION", payload=row,
                )
                rejected += 1
                continue
            version = int(row["Versao"])
            protocol = row["Protocolo_Entrega"].strip()
            download_reference = row["Link_Download"].strip()
            if version < 1:
                raise IdentityError("invalid IPE document identity")
            if protocol:
                natural_key: list[Any] = ["PROTOCOL", protocol, version]
                identity_basis = "CVM_PROTOCOL_VERSION"
            else:
                natural_key = [
                    "OFFICIAL_COMPOSITE", cnpj, reference, received, row["Categoria"].strip(),
                    row["Tipo"].strip(), row["Especie"].strip(), row["Assunto"].strip(),
                    version, download_reference,
                ]
                identity_basis = "OFFICIAL_METADATA_COMPOSITE_NO_PROTOCOL"
            normalized = {
                "document_id": protocol or None,
                "document_version": version,
                "document_identity_basis": identity_basis,
                "company": row["Nome_Companhia"].strip(),
                "cvm_code": row["Codigo_CVM"].strip(),
                "category": row["Categoria"].strip(),
                "type": row["Tipo"].strip(),
                "species": row["Especie"].strip(),
                "subject": row["Assunto"].strip(),
                "presentation_type": row["Tipo_Apresentacao"].strip(),
                "download_reference": download_reference,
                "semantic_classification": "NOT_IMPLEMENTED",
            }
            inserted = _observation(
                conn, source_version_id=version_id, family="cvm-ipe-metadata",
                natural_key=natural_key, payload=normalized, available_at=acquired["fetched_at"],
                sessions=sessions, company_cnpj=cnpj, reference_at=reference, received_at=received,
            )
            if inserted:
                persisted += 1
            elif not source_existed:
                _reject(
                    conn, source_version_id=version_id, family="cvm-ipe-metadata",
                    natural_key=["DUPLICATE_SOURCE_ROW", source_row, natural_key],
                    reason="DUPLICATE_DOCUMENT_IDENTITY_IN_SOURCE", payload=row,
                )
                rejected += 1
        conn.execute("RELEASE external_ipe")
    except BaseException:
        conn.execute("ROLLBACK TO external_ipe")
        conn.execute("RELEASE external_ipe")
        raise
    return _result([version_id], len(rows), persisted, rejected)


def ingest_fca_identity(
    conn: sqlite3.Connection, raw_root: Path, year: int, acquired: dict[str, Any]
) -> dict[str, Any]:
    from .source_history import derive_fca_securities

    records = derive_fca_securities(acquired["payload"], year)
    conn.execute("SAVEPOINT external_fca_identity")
    try:
        version_id, source_existed = _source_version(
            conn, raw_root, acquired, publisher="CVM", dataset="FCA_SECURITY_IDENTITY",
            logical_period=str(year),
            source_url=f"https://dados.cvm.gov.br/dados/cia_aberta/DOC/FCA/DADOS/fca_cia_aberta_{year}.zip",
            parser_version="cvm-fca-security-identity/1",
        )
        persisted = rejected = 0
        for record in records:
            link_id = digest_identity(
                record["cnpj"], record["ticker"], record["trading_start"], record["trading_end"],
                record["available_at"], version_id,
            )
            before = conn.total_changes
            conn.execute(
                "INSERT OR IGNORE INTO external_security_links VALUES (?,?,?,?,?,?,?,?)",
                (
                    link_id, record["cnpj"], record["ticker"], None, record["trading_start"],
                    record["trading_end"], record["available_at"], version_id,
                ),
            )
            inserted = conn.total_changes > before
            persisted += inserted
            if not inserted and not source_existed:
                _reject(
                    conn, source_version_id=version_id, family="cvm-fca-security-identity",
                    natural_key=["DUPLICATE_SOURCE_ROW", record["source_row"], link_id],
                    reason="DUPLICATE_SECURITY_INTERVAL_IN_SOURCE", payload=record,
                )
                rejected += 1
        conn.execute("RELEASE external_fca_identity")
    except BaseException:
        conn.execute("ROLLBACK TO external_fca_identity")
        conn.execute("RELEASE external_fca_identity")
        raise
    return _result([version_id], len(records), int(persisted), rejected)


def verify(conn: sqlite3.Connection, raw_root: Path) -> dict[str, Any]:
    issues: list[str] = []
    versions = conn.execute(
        "SELECT source_version_id,publisher,dataset,logical_period,sha256,relative_path,"
        " external_raw_objects.byte_length,"
        " supersedes_source_version_id FROM external_source_versions JOIN external_raw_objects USING(sha256)"
        " ORDER BY source_version_id"
    ).fetchall()
    known = {row[0] for row in versions}
    for source_id, publisher, dataset, period, digest, relative, length, supersedes in versions:
        path = raw_root / relative
        if not path.is_file():
            issues.append(f"RAW_MISSING:{source_id}")
            continue
        payload = path.read_bytes()
        if len(payload) != length or hashlib.sha256(payload).hexdigest() != digest:
            issues.append(f"RAW_HASH_MISMATCH:{source_id}")
        if supersedes and supersedes not in known:
            issues.append(f"SUPERSEDES_MISSING:{source_id}")
        if supersedes:
            prior = conn.execute(
                "SELECT publisher,dataset,logical_period FROM external_source_versions WHERE source_version_id=?",
                (supersedes,),
            ).fetchone()
            if prior != (publisher, dataset, period):
                issues.append(f"SUPERSEDES_PERIOD_MISMATCH:{source_id}")
    observations = conn.execute(
        "SELECT observation_id,source_version_id,reference_at,event_at,received_at,available_at,"
        " first_seen_at,tradable_session,ticker,isin,identity_status,payload_json FROM external_observations"
    ).fetchall()
    for row in observations:
        observation_id, source_id, reference, event, received, available, first_seen, tradable = row[:8]
        if source_id not in known:
            issues.append(f"LINEAGE_MISSING:{observation_id}")
        try:
            utc_timestamp(available)
            utc_timestamp(first_seen)
            for value in (reference, event, received, tradable):
                if value:
                    iso_date(value)
            json.loads(row[11])
        except (ValueError, json.JSONDecodeError):
            issues.append(f"OBSERVATION_INVALID:{observation_id}")
        if received and received > available[:10]:
            issues.append(f"TEMPORAL_ORDER:{observation_id}")
        if tradable and tradable <= datetime.fromisoformat(available.replace("Z", "+00:00")).astimezone(
            SAO_PAULO
        ).date().isoformat():
            issues.append(f"TRADABLE_SESSION_ORDER:{observation_id}")
        if row[10] == "DIRECT_B3_TICKER_ISIN" and (not row[8] or not row[9]):
            issues.append(f"DIRECT_IDENTITY_INCOMPLETE:{observation_id}")
    result = {
        "status": "SUCCESS" if not issues else "INTEGRITY_ERROR",
        "schema_version": SCHEMA_VERSION,
        "source_versions": len(versions),
        "observations": len(observations),
        "rejections": conn.execute("SELECT COUNT(*) FROM external_rejections").fetchone()[0],
        "security_links": conn.execute("SELECT COUNT(*) FROM external_security_links").fetchone()[0],
        "issues": issues,
        "staging_is_factor_input": False,
        "big_winner_tables_touched": False,
    }
    return result


def status(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT dataset,logical_period,fetched_at,source_version_id,sha256 FROM external_source_versions"
        " ORDER BY dataset,logical_period DESC,fetched_at DESC"
    ).fetchall()
    result = []
    for dataset in sorted({row[0] for row in rows}):
        latest = next(row for row in rows if row[0] == dataset)
        count, reference, available, pit = conn.execute(
            "SELECT COUNT(*),MAX(reference_at),MAX(available_at),"
            " CASE WHEN COUNT(*)=0 THEN 'NOT_APPLICABLE'"
            " WHEN COUNT(DISTINCT pit_status)=1 THEN MIN(pit_status) ELSE 'MIXED' END"
            " FROM external_observations o JOIN external_source_versions s USING(source_version_id)"
            " WHERE s.dataset=?",
            (dataset,),
        ).fetchone()
        rejected = conn.execute(
            "SELECT COUNT(*) FROM external_rejections r"
            " JOIN external_source_versions s USING(source_version_id) WHERE s.dataset=?",
            (dataset,),
        ).fetchone()[0]
        result.append({
            "source": dataset,
            "last_logical_period": latest[1],
            "last_collection": latest[2],
            "last_source_version": latest[3],
            "last_hash": latest[4],
            "row_count": count,
            "rejected_row_count": rejected,
            "latest_reference_at": reference,
            "latest_available_at": available,
            "pit_status": pit,
            "health": "SUCCESS",
        })
    return {"status": "SUCCESS", "schema_version": SCHEMA_VERSION, "sources": result}


def _write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    payload = (json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def add_cli(root: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    external = root.add_parser("external", help="Research-only CVM/B3 external intelligence")
    actions = external.add_subparsers(dest="external_action", required=True)
    collect = actions.add_parser("collect")
    collectors = collect.add_subparsers(dest="collector", required=True)
    for name in ("b3-lending", "cvm-vlmo", "cvm-buyback", "cvm-ipe", "cvm-fca-identity"):
        command = collectors.add_parser(name)
        command.add_argument("--db", type=Path, required=True)
        command.add_argument("--raw-root", type=Path, required=True)
        command.add_argument("--receipt", type=Path, required=True)
        command.add_argument("--source-file", type=Path)
        command.add_argument("--observed-at")
        command.add_argument("--trading-db", type=Path)
        command.add_argument("--timeout", type=float, default=60)
        if name == "b3-lending":
            command.add_argument("--reference-date", required=True)
        elif name in ("cvm-vlmo", "cvm-ipe", "cvm-fca-identity"):
            command.add_argument("--year", type=int, required=True)
    for action in ("verify", "status"):
        command = actions.add_parser(action)
        command.add_argument("--db", type=Path, required=True)
        command.add_argument("--raw-root", type=Path, required=action == "verify")
        command.add_argument("--receipt", type=Path)


def _collect(args: argparse.Namespace, conn: sqlite3.Connection) -> dict[str, Any]:
    sessions = trading_sessions(args.trading_db)
    if args.collector == "b3-lending":
        if args.source_file:
            raise ValueError("b3-lending uses two official responses and does not accept one --source-file")
        acquired: dict[str, list[dict[str, Any]]] = {}
        for table_name in B3_TABLES:
            base = (
                f"https://arquivos.b3.com.br/bdi/table/{table_name}/{args.reference_date}/"
                f"{args.reference_date}"
            )
            first = fetch_bytes(f"{base}/1/{B3_PAGE_SIZE}", body=b"{}", timeout=args.timeout)
            first_document = _json_payload(first["payload"])
            first_table = first_document.get("table") if isinstance(first_document, dict) else None
            page_count = first_table.get("pageCount") if isinstance(first_table, dict) else None
            if not isinstance(page_count, int) or isinstance(page_count, bool) or not 1 <= page_count <= 100:
                raise SchemaDriftError(f"{table_name}: invalid page count")
            pages = [first]
            for page_number in range(2, page_count + 1):
                pages.append(fetch_bytes(
                    f"{base}/{page_number}/{B3_PAGE_SIZE}", body=b"{}", timeout=args.timeout
                ))
            acquired[table_name] = pages
        return ingest_b3_lending(conn, args.raw_root, args.reference_date, acquired, sessions)
    if args.source_file:
        if not args.observed_at:
            raise ValueError("--observed-at is required with --source-file")
        acquired_one = source_file(args.source_file, args.observed_at)
    else:
        if args.collector == "cvm-vlmo":
            url = f"https://dados.cvm.gov.br/dados/cia_aberta/DOC/VLMO/DADOS/vlmo_cia_aberta_{args.year}.zip"
        elif args.collector == "cvm-buyback":
            url = "https://dados.cvm.gov.br/dados/CIA_ABERTA/EVENTOS/RECOMPRA_ACOES/DADOS/cia_aberta_recompra_acoes.zip"
        elif args.collector == "cvm-ipe":
            url = f"https://dados.cvm.gov.br/dados/cia_aberta/DOC/IPE/DADOS/ipe_cia_aberta_{args.year}.zip"
        else:
            url = f"https://dados.cvm.gov.br/dados/cia_aberta/DOC/FCA/DADOS/fca_cia_aberta_{args.year}.zip"
        acquired_one = fetch_bytes(url, timeout=args.timeout)
    if args.collector == "cvm-vlmo":
        return ingest_vlmo(conn, args.raw_root, args.year, acquired_one, sessions)
    if args.collector == "cvm-buyback":
        return ingest_buyback(conn, args.raw_root, acquired_one, sessions)
    if args.collector == "cvm-ipe":
        return ingest_ipe(conn, args.raw_root, args.year, acquired_one, sessions)
    return ingest_fca_identity(conn, args.raw_root, args.year, acquired_one)


def run_cli(args: argparse.Namespace) -> int:
    started = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    receipt_path = getattr(args, "receipt", None)
    command = "external " + args.external_action
    if getattr(args, "collector", None):
        command += " " + args.collector
    try:
        conn = connect(args.db)
        try:
            if args.external_action == "collect":
                result = _collect(args, conn)
                conn.commit()
            elif args.external_action == "verify":
                result = verify(conn, args.raw_root)
            else:
                result = status(conn)
        finally:
            conn.close()
        exit_code = 0 if result.get("status", "SUCCESS") == "SUCCESS" else 4
    except SourceUnavailableError as exc:
        result, exit_code = {"status": exc.status, "failure_class": type(exc).__name__, "message": str(exc)}, 2
    except ExternalIntelligenceError as exc:
        result, exit_code = {"status": exc.status, "failure_class": type(exc).__name__, "message": str(exc)}, 3
    except (OSError, sqlite3.Error, TypeError, ValueError, KeyError) as exc:
        result, exit_code = {
            "status": "INTEGRITY_ERROR", "failure_class": type(exc).__name__, "message": str(exc)
        }, 4
    finished = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    receipt = {
        "receipt_schema_version": RECEIPT_VERSION,
        "command": command,
        "collector_version": COLLECTOR_VERSION,
        "started_at": started,
        "finished_at": finished,
        **result,
    }
    receipt["receipt_id"] = digest_identity(command, result)
    if exit_code == 0:
        registered = connect(args.db)
        try:
            source_versions = result.get("source_version_ids", [])
            source_version_id = source_versions[0] if source_versions else None
            registered.execute(
                "INSERT OR IGNORE INTO external_receipts VALUES (?,?,?,?,?)",
                (receipt["receipt_id"], source_version_id, command, receipt["status"], canonical_json(receipt)),
            )
            registered.commit()
        finally:
            registered.close()
    if receipt_path:
        _write_receipt(receipt_path, receipt)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return exit_code
