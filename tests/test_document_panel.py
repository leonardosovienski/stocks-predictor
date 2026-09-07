import copy
import hashlib
import json
from pathlib import Path

import pytest

import document_panel


FIXTURE = Path(__file__).parent / "fixtures/real_integration"


@pytest.mark.parametrize("doc,total,treasury,scale", [
    ("134335", 15_753_833_000, 4_384_000, "Mil"),
    ("133944", 2_865_417_020, 11_640_980, "Unidade"),
    ("134790", 2_039_086_540, 3_772_375, "Unidade"),
])
def test_original_capital_pages_keep_their_own_scale(doc, total, treasury, scale):
    payload = (FIXTURE / f"capital-{doc}.html").read_bytes()
    manifest = json.loads((FIXTURE / "provenance.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(payload).hexdigest() == manifest[f"capital-{doc}.html"]["sha256"]
    row = document_panel.capital_from_viewer(payload, {"ref_date": "2023-12-31", "document_id": doc}, "CVM")
    assert row["total"] == total
    assert row["treasury_total"] == treasury
    assert row["share_scale"] == scale
    assert row["basis_date"] == "2023-12-31"
    assert row["outstanding_ordinary"] + row["outstanding_preferred"] == total - treasury
    assert not row["eligible_for_valuation"]  # Counts alone cannot certify a market cap.


def test_capital_rejects_wrong_period_and_absent_scale():
    payload = (FIXTURE / "capital-134335.html").read_bytes()
    with pytest.raises(ValueError, match="reference date"):
        document_panel.capital_from_viewer(payload, {"ref_date": "2022-12-31"}, "CVM")
    with pytest.raises(ValueError, match="scale"):
        document_panel.capital_from_viewer(payload.replace(b"(Mil)", b"(?)"), {"ref_date": "2023-12-31"}, "CVM")


def example():
    financials = [{"cnpj": "1", "ref_date": "2023-12-31", "document_version": 1,
                   "available_at": "2024-03-01", "accruals": 0.1}]
    securities = [{"cnpj": "1", "ref_date": "2024-01-01", "version": 1,
                   "available_at": "2024-04-01", "ticker": "AAAA3", "trading_start": "2010-01-01",
                   "trading_end": None, "document_id": "FCA1"}]
    return financials, securities


def test_both_documents_must_already_be_available():
    financials, securities = example()
    assert document_panel.fundamentals_asof(financials, securities, "2024-03-31") == {}
    assert document_panel.fundamentals_asof(financials, securities, "2024-04-01")["AAAA3"]["accruals"] == 0.1
    newer = {**financials[0], "document_version": 2, "available_at": "2024-07-01", "accruals": None}
    financials.append(newer)
    assert document_panel.fundamentals_asof(financials, securities, "2024-06-30")["AAAA3"]["accruals"] == 0.1
    assert document_panel.fundamentals_asof(financials, securities, "2024-07-01")["AAAA3"]["accruals"] is None


def test_latest_blank_security_document_does_not_resurrect_old_ticker():
    financials, securities = example()
    metadata = [securities[0], {**securities[0], "document_id": "FCA2", "version": 2,
                               "available_at": "2024-05-01"}]
    assert document_panel.fundamentals_asof(financials, securities, "2024-04-30", security_metadata=metadata)
    assert document_panel.fundamentals_asof(financials, securities, "2024-05-01", security_metadata=metadata) == {}


def test_future_filings_cannot_change_past_panel():
    financials, securities = example()
    before = document_panel.fundamentals_asof(financials, securities, "2024-04-01")
    financials.append({**financials[0], "document_version": 99, "available_at": "2025-01-01", "accruals": -999})
    assert before == document_panel.fundamentals_asof(financials, securities, "2024-04-01")
    ambiguous = copy.deepcopy(financials[0])
    ambiguous["accruals"] = 2
    with pytest.raises(ValueError, match="conflicting issuer"):
        document_panel.fundamentals_asof(financials + [ambiguous], securities, "2024-04-01")
