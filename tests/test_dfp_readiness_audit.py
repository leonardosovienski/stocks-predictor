"""Real CVM fields exercise provenance joins, not strategy performance."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from tools.audit_dfp_readiness import audit_dfp_zip, monetary_reais


FIXTURE = Path(__file__).parent / "fixtures" / "cvm_dfp_2023"


def source_zip():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path in FIXTURE.glob("*.csv"):
            archive.writestr(path.name, path.read_bytes())
    return buffer.getvalue()


def test_real_export_monetary_units_are_reais():
    # AMBEV's raw DRE field, not a parser-shaped synthetic number.
    assert monetary_reais("79736856.0000000000", "MIL", "REAL") == 79736856000
    assert monetary_reais("79736856.0000000000", "UNIDADE", "REAL") == 79736856


@pytest.mark.parametrize("number,scale,currency", [
    ("NaN", "MIL", "REAL"), ("Infinity", "MIL", "REAL"),
    ("79.736.856,00", "MIL", "REAL"), ("1", "UNKNOWN", "REAL"),
    ("1", "MIL", "USD"),
])
def test_unverified_numeric_conventions_cannot_pass(number, scale, currency):
    with pytest.raises(ValueError):
        monetary_reais(number, scale, currency)


def test_real_revised_document_cannot_borrow_first_delivery_date():
    report = audit_dfp_zip(source_zip(), 2023)
    assert report["status"] == "NOT_READY"
    assert report["proof_authorized"] is False
    assert {issue["code"] for issue in report["issues"]} == {
        "MONETARY_UNIT_MISMATCH", "VERSION_DATE_MISMATCH"}
    dre = report["statements"]["DRE_con"]
    energisa = next(row for row in dre["date_examples"] if row["cnpj"] == "00864214000106")
    assert energisa["version"] == "3"
    assert energisa["version_received_at"] == "2024-03-15"
    assert energisa["assigned_known_at"] == "2024-03-12"


def test_fixture_fields_have_declared_source_hashes():
    provenance = json.loads((FIXTURE / "provenance.json").read_text(encoding="utf-8"))
    for item in provenance["files"]:
        assert hashlib.sha256((FIXTURE / item["name"]).read_bytes()).hexdigest() == item["sha256"]


def test_missing_version_metadata_is_an_audit_error():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("dfp_cia_aberta_2023.csv", "CNPJ_CIA;DT_REFER;DT_RECEB\n")
    with pytest.raises(ValueError, match="missing columns"):
        audit_dfp_zip(buffer.getvalue(), 2023)


def test_malformed_delivery_date_cannot_pass():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("dfp_cia_aberta_2023.csv",
                         "CNPJ_CIA;DT_REFER;VERSAO;DT_RECEB\n"
                         "00.864.214/0001-06;2023-12-31;3;2024-99-99\n")
    with pytest.raises(ValueError):
        audit_dfp_zip(buffer.getvalue(), 2023)


def test_cli_is_read_only_and_returns_failure_for_real_defects(tmp_path):
    path = tmp_path / "dfp.zip"
    path.write_bytes(source_zip())
    before = path.read_bytes()
    tool = Path(__file__).resolve().parents[1] / "tools" / "audit_dfp_readiness.py"
    result = subprocess.run([sys.executable, str(tool), "--zip", str(path), "--year", "2023"],
                            cwd=tmp_path, capture_output=True, check=False)
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "NOT_READY"
    assert path.read_bytes() == before
    assert list(tmp_path.iterdir()) == [path]
