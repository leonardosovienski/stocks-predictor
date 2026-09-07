"""Corrected public pipeline, tested independently of historical regression APIs."""

import csv
import io
import hashlib
import json
import subprocess
import sys
import zipfile

import pytest

import cvm_pit
import db
import factor
import ingest_cvm
from tests.test_dfp_readiness_audit import source_zip


def test_real_ambev_units_and_energisa_version_reach_new_table(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    conn.execute(
        "INSERT INTO fundamentals(ticker,ref_date,source,receita_liquida)"
        " VALUES ('ABEV3','2023-12-31','historical',7.9736856e17)"
    )
    conn.commit()
    before = list(conn.execute("SELECT * FROM fundamentals"))
    payload = source_zip()
    assert (
        ingest_cvm.ingest_dfp_year(
            conn, 2023, ticker_of={"ambev_s.a.": "ABEV3", "energisa_s.a.": "ENGI11"}, zbytes=payload
        )
        == 2
    )
    abev = conn.execute("SELECT receita_liquida FROM fundamentals_pit WHERE ticker='ABEV3'").fetchone()
    assert abev[0] == 79_736_856_000
    eng = conn.execute(
        "SELECT document_version,received_at,available_at FROM fundamentals_pit WHERE ticker='ENGI11'"
    ).fetchone()
    assert tuple(eng) == (3, "2024-03-15", "2024-03-16")
    assert cvm_pit.fundamental_values(conn, ["ENGI11"], "2024-03-14", "receita_liquida") == {}
    assert cvm_pit.fundamental_values(conn, ["ENGI11"], "2024-03-15", "receita_liquida") == {}
    assert cvm_pit.fundamental_values(conn, ["ENGI11"], "2024-03-16", "receita_liquida") == {
        "ENGI11": 28_531_858_000
    }
    assert (
        ingest_cvm.ingest_dfp_year(
            conn, 2023, ticker_of={"ambev_s.a.": "ABEV3", "energisa_s.a.": "ENGI11"}, zbytes=payload
        )
        == 0
    )
    assert list(conn.execute("SELECT * FROM fundamentals")) == before


def test_public_receipt_parser_keys_by_version():
    result = ingest_cvm.parse_dfp_received_dates(source_zip(), 2023)
    assert result["00864214000106", "2023-12-31", 3] == "2024-03-15"
    assert result["00864214000106", "2023-12-31", 1] == "2024-03-12"


def test_no_fallback_to_bad_legacy_fundamentals(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    conn.execute(
        "INSERT INTO fundamentals(ticker,ref_date,source,accruals,known_at)"
        " VALUES ('AAAA3','2020-12-31','legacy',0.4,'2021-02-01')"
    )
    assert factor.accruals_signals(conn, ["AAAA3"], "2021-07-01") == {}
    assert factor.earnings_yield_signals(conn, ["AAAA3"], "2021-07-01") == {}


def insert_dfp(conn, version, received, **values):
    row = dict(
        ticker="AAAA3",
        cnpj="00000000000001",
        ref_date="2020-12-31",
        document_version=version,
        received_at=received,
        available_at=cvm_pit.receipt_dates(received)[1],
        source="fixture",
        source_sha256="a" * 64,
        **values,
    )
    cvm_pit.append_rows(conn, "fundamentals_pit", [row], ("ticker", "document_version", "source_sha256"))


def test_versions_are_available_independently_and_null_revision_does_not_backfill(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    insert_dfp(conn, 1, "2021-02-01", accruals=0.1)
    insert_dfp(conn, 2, "2021-03-01", accruals=0.2)
    insert_dfp(conn, 3, "2021-04-01", accruals=None)
    assert factor.accruals_signals(conn, ["AAAA3"], "2021-02-15") == {"AAAA3": 0.1}
    assert factor.accruals_signals(conn, ["AAAA3"], "2021-03-02") == {"AAAA3": 0.2}
    assert factor.accruals_signals(conn, ["AAAA3"], "2021-04-02") == {}


def test_missing_actual_share_basis_cannot_double_apply_bbas_split(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    conn.execute(
        "INSERT INTO adjustments(ticker,ex_date,factor,type,source,approved_by)"
        " VALUES ('BBAS3','2024-04-16',0.5,'split','historical','operator')"
    )
    shares = 5_730_799_931.446
    assert factor._shares_on_price_base(conn, "BBAS3", shares, None, "2024-05-31") is None
    assert factor._shares_on_price_base(conn, "BBAS3", shares, "2024-05-16", "2024-05-31") == shares
    assert factor._shares_on_price_base(conn, "BBAS3", shares / 2, "2024-04-01", "2024-05-31") == shares


def fre_zip(counts=(100, 200), dates=("2021-02-01", "2021-03-01")):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "fre_cia_aberta_2020.csv",
            "ID_DOC;DT_RECEB\n" + "\n".join(f"{i};{d}" for i, d in enumerate(dates, 1)),
        )
        archive.writestr(
            "fre_cia_aberta_distribuicao_capital_2020.csv",
            "ID_Documento;Nome_Companhia;Data_Referencia;Quantidade_Total_Acoes;Quantidade_Acoes_Circulacao\n"
            + "\n".join(f"{i};CIA X;2020-12-31;{c};{c}" for i, c in enumerate(counts, 1)),
        )
    return buffer.getvalue()


def test_fre_keeps_count_and_receipt_of_each_document(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    payload = fre_zip()
    assert ingest_cvm.ingest_fre_shares_year(conn, 2020, {"cia_x": "AAAA3"}, payload) == 2
    assert ingest_cvm.ingest_fre_shares_year(conn, 2020, {"cia_x": "AAAA3"}, payload) == 0
    rows = conn.execute(
        "SELECT document_id,shares_outstanding,available_at,basis_date FROM shares_pit ORDER BY document_id"
    ).fetchall()
    assert [tuple(r) for r in rows] == [("1", 100, "2021-02-02", None), ("2", 200, "2021-03-02", None)]
    assert conn.execute("SELECT COUNT(*) FROM fundamentals").fetchone()[0] == 0


def add_price(conn, ticker="AAAA3", day="2021-02-15", opening=10, closing=10, quote_factor=1):
    conn.execute(
        "INSERT INTO prices_raw(date,ticker,bdi_code,market_type,open,high,low,close,volume_fin,qty,quote_factor,source_file)"
        " VALUES (?,?, '02','010',?,?,?,?,100000,10000,?,'synthetic')",
        (day, ticker, opening, max(opening, closing), min(opening, closing), closing, quote_factor),
    )


def test_value_signal_joins_independent_dates_and_verified_price_basis(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    insert_dfp(conn, 1, "2021-01-15", lucro_liquido=100, patrimonio_liquido=500)
    basis = {
        "1": {
            "basis_date": "2021-02-01",
            "basis_source": "fixture capital statement",
            "price_basis_source": "fixture single share class",
        }
    }
    ingest_cvm.ingest_fre_shares_year(conn, 2020, {"cia_x": "AAAA3"}, fre_zip(), basis_by_document=basis)
    add_price(conn)
    assert factor.earnings_yield_signals(conn, ["AAAA3"], "2021-02-15") == {"AAAA3": 0.1}
    assert factor.book_to_market_signals(conn, ["AAAA3"], "2021-02-15") == {"AAAA3": 0.5}
    # A later observation with unknown basis supersedes the old count; do not carry it forward silently.
    assert factor.earnings_yield_signals(conn, ["AAAA3"], "2021-03-15") == {}


def test_conflicting_immutable_batch_is_atomic(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    insert_dfp(conn, 1, "2021-02-01", lucro_liquido=100)
    with pytest.raises(ValueError, match="conflicting immutable"):
        insert_dfp(conn, 1, "2021-02-01", lucro_liquido=200)
    assert conn.execute("SELECT lucro_liquido FROM fundamentals_pit").fetchone()[0] == 100


@pytest.mark.parametrize(
    "currency,scale,value",
    [("USD", "MIL", "1"), ("REAL", "?", "1"), ("REAL", "MIL", "NaN"), ("REAL", "MIL", "1.000,00")],
)
def test_public_parser_rejects_unsupported_units(currency, scale, value):
    with zipfile.ZipFile(io.BytesIO(source_zip())) as archive:
        rows = list(
            csv.reader(
                io.StringIO(archive.read("dfp_cia_aberta_DRE_con_2023.csv").decode("latin-1")), delimiter=";"
            )
        )
    rows[1][rows[0].index("MOEDA")] = currency
    rows[1][rows[0].index("ESCALA_MOEDA")] = scale
    rows[1][rows[0].index("VL_CONTA")] = value
    with pytest.raises(ValueError):
        ingest_cvm.parse_dfp_statement_rows(rows, "DRE_con")


def test_legacy_dividend_ingestion_is_not_a_public_total_return_source():
    with pytest.raises(ValueError, match="not a total-return source"):
        ingest_cvm.ingest_fre_dividends_year(None, 2023)


def test_package_import_of_corrected_parser_without_legacy_sys_path(tmp_path):
    path = tmp_path / "dfp.zip"
    path.write_bytes(source_zip())
    code = "from stocks_predictor import cvm_pit; from pathlib import Path; import sys; print(len(cvm_pit.derive_dfp(Path(sys.argv[1]).read_bytes(),2023)))"
    result = subprocess.run(
        [sys.executable, "-c", code, str(path)], capture_output=True, text=True, encoding="utf-8"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "2"


def test_copy_rebuilder_preserves_source_and_never_overwrites(tmp_path):
    from tools.rebuild_cvm_copy import rebuild

    source = tmp_path / "source.db"
    conn = db.get_connection(source)
    conn.execute(
        "INSERT INTO fundamentals(ticker,ref_date,source,accruals) VALUES ('OLD3','2020-12-31','old',0.1)"
    )
    conn.commit()
    conn.close()
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    raw = tmp_path / "dfp.zip"
    raw.write_bytes(source_zip())
    mapping = tmp_path / "mapping.json"
    mapping.write_text(json.dumps({"ambev_s.a.": "ABEV3", "energisa_s.a.": "ENGI11"}), encoding="utf-8")
    plan = {"years": [{"year": 2023, "dfp_zip": str(raw), "dfp_map": str(mapping)}]}
    output = tmp_path / "new.db"
    result = rebuild(source, output, plan)
    assert result["source_unchanged"] and result["performance_observed"] is False
    assert result["results"][0]["inserted"] == 2
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    new = db.get_connection(output)
    assert [tuple(r) for r in new.execute("SELECT ticker,accruals FROM fundamentals")] == [("OLD3", 0.1)]
    assert new.execute("SELECT COUNT(*) FROM fundamentals_pit").fetchone()[0] == 2
    new.close()
    with pytest.raises(ValueError, match="new file"):
        rebuild(source, output, plan)
    with pytest.raises(ValueError, match="new file"):
        rebuild(source, source, plan)


def test_missing_statement_version_is_excluded_with_persistent_reason(tmp_path):
    payload = source_zip()
    buffer = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(payload)) as old, zipfile.ZipFile(buffer, "w") as new:
        for name in old.namelist():
            content = old.read(name)
            if name == "dfp_cia_aberta_2023.csv":
                lines = content.decode("latin-1").splitlines()
                content = (
                    "\n".join(line for line in lines if "00.864.214/0001-06" not in line) + "\n"
                ).encode("latin-1")
            new.writestr(name, content)
    conn = db.get_connection(tmp_path / "s.db")
    n = ingest_cvm.ingest_dfp_year(
        conn, 2023, ticker_of={"energisa_s.a.": "ENGI11", "ambev_s.a.": "ABEV3"}, zbytes=buffer.getvalue()
    )
    assert n == 1
    assert [tuple(r) for r in conn.execute("SELECT reason FROM ingestion_issues")] == [
        ("MISSING_DOCUMENT_VERSION",)
    ]
    assert [tuple(r) for r in conn.execute("SELECT ticker FROM fundamentals_pit")] == [("ABEV3",)]
