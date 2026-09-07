"""Real archive fixtures and causal identity boundaries, no return observations."""

import hashlib
import io
import json
from pathlib import Path
import zipfile

import pytest

import cvm_pit
import db
import source_history
from tests.test_repairs_cvm import fre_zip
from tools.rebuild_source_history import stage_records

FIXTURE = Path(__file__).parent / "fixtures/cvm_source_history"


def source_zip(kind, year):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path in FIXTURE.glob(f"{kind}_*_{year}.csv"):
            archive.writestr(path.name, path.read_bytes())
    return buffer.getvalue()


def test_real_zero_float_companies_do_not_destroy_2016_import(tmp_path):
    payload = source_zip("fre", 2016)
    issues = []
    rows = cvm_pit.derive_fre_shares(payload, 2016, issues=issues)
    assert len(rows) == 1
    assert rows[0]["company"] == "bco_brasil_s.a."
    assert {x["reason"] for x in issues} == {"INVALID_TOTAL_SHARES"}
    assert {json.loads(x["document_key"])[1] for x in issues} == {"65854", "63380"}
    conn = db.get_connection(tmp_path / "s.db")
    assert cvm_pit.ingest_fre_shares(conn, 2016, {"bco_brasil_s.a.": "BBAS3"}, payload) == 1
    assert cvm_pit.ingest_fre_shares(conn, 2016, {"bco_brasil_s.a.": "BBAS3"}, payload) == 0
    assert conn.execute("SELECT COUNT(*) FROM ingestion_issues").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM fundamentals").fetchone()[0] == 0


@pytest.mark.parametrize("bad", [0, -1, "NaN", "inf"])
def test_nonpositive_or_nonfinite_shares_are_document_local_rejections(bad):
    issues = []
    rows = cvm_pit.derive_fre_shares(fre_zip((bad, 200)), 2020, issues=issues)
    assert [r["document_id"] for r in rows] == ["2"]
    assert issues == [{"document_key": '["FRE", "1"]', "reason": "INVALID_TOTAL_SHARES"}]


def test_all_invalid_share_documents_still_fail_loud():
    with pytest.raises(ValueError, match="TOTAL"):
        cvm_pit.derive_fre_shares(fre_zip((0, 0)), 2020)


def test_exact_bbas_reported_capital_is_not_a_certified_share_basis():
    payload = source_zip("fre", 2023)
    rows = source_history.derive_reported_capital(payload, 2023)
    assert len(rows) == 1  # Excludes subscribed/paid records rather than tripling capital.
    row = rows[0]
    assert row["reported_total"] == 5_730_834_040
    assert row["reported_total_field"] == 0
    assert row["count_method"] == "reported_ON_plus_PN"
    assert row["capital_approval_date"] == "2023-04-27"
    assert row["received_at"] == "2024-05-16"
    assert row["basis_date"] is None and row["eligible_for_valuation"] is False
    estimate = cvm_pit.derive_fre_shares(payload, 2023)[0]["shares_outstanding"]
    assert abs(estimate - row["reported_total"]) > 34_000


def test_fca_document_availability_and_unit_composition_are_preserved():
    rows = source_history.derive_fca_securities(source_zip("fca", 2023), 2023)
    eng = next(r for r in rows if r["ticker"] == "ENGI11")
    assert eng["unit_composition"] == "1 ação ordinária e 4 ações preferenciais"
    assert eng["cnpj"] == "00864214000106"
    assert source_history.security_links_asof(rows, eng["cnpj"], eng["received_at"]) == []
    assert "ENGI11" in source_history.security_links_asof(rows, eng["cnpj"], eng["available_at"])
    ended = {**eng, "trading_end": eng["available_at"]}
    assert source_history.security_links_asof([ended], eng["cnpj"], "2026-09-07") == []


def test_foreign_document_identity_cannot_supply_metadata():
    rows = source_history.document_metadata(source_zip("fre", 2023), "fre", 2023)
    with pytest.raises(ValueError, match="identity mismatch"):
        source_history.match_document(
            {
                "ID_Documento": "137597",
                "CNPJ_Companhia": "07.526.557/0001-00",
                "Data_Referencia": "2023-12-31",
                "Versao": "19",
            },
            rows,
        )


def test_audit_staging_is_idempotent_and_cannot_supply_factor_inputs(tmp_path):
    conn = db.get_connection(tmp_path / "s.db")
    rows = source_history.derive_reported_capital(source_zip("fre", 2023), 2023)
    assert stage_records(conn, "FRE_ISSUED_CAPITAL", 2023, rows) == 1
    assert stage_records(conn, "FRE_ISSUED_CAPITAL", 2023, rows) == 0
    assert cvm_pit.value_signals(conn, ["BBAS3"], "2024-06-01", "lucro_liquido") == {}
    for table in ("shares_pit", "fundamentals_pit", "cash_events", "cash_event_coverage"):
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_source_fixture_hashes():
    provenance = json.loads((FIXTURE / "provenance.json").read_text(encoding="utf-8"))
    for item in provenance["files"]:
        assert hashlib.sha256((FIXTURE / item["name"]).read_bytes()).hexdigest() == item["sha256"]


def test_history_rebuild_preserves_operational_tables_and_refuses_existing_output(tmp_path):
    from tests.test_dfp_readiness_audit import source_zip as dfp_zip
    from tools.rebuild_source_history import rebuild

    source = tmp_path / "source.db"
    conn = db.get_connection(source)
    conn.execute(
        "INSERT INTO fundamentals(ticker,ref_date,source,accruals) VALUES ('OLD3','2020-12-31','old',0.1)"
    )
    conn.commit()
    conn.close()
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    (tmp_path / "dfp_cia_aberta_2023.zip").write_bytes(dfp_zip())
    for kind in ("fre", "fca"):
        (tmp_path / f"{kind}_cia_aberta_2023.zip").write_bytes(source_zip(kind, 2023))
    output = tmp_path / "copy.db"
    result = rebuild(source, output, tmp_path, [2023], tmp_path / "exports")
    assert result["source_unchanged"] and result["signal_tables_populated"] is False
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    conn = db.get_connection(output)
    assert [tuple(r) for r in conn.execute("SELECT ticker,accruals FROM fundamentals")] == [("OLD3", 0.1)]
    assert conn.execute("SELECT COUNT(*) FROM research_source_documents WHERE kind='DFP'").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM shares_pit").fetchone()[0] == 0
    conn.close()
    with pytest.raises(ValueError, match="NEW"):
        rebuild(source, output, tmp_path, [2023], tmp_path / "exports")
