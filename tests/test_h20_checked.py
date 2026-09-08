"""Adversarial metadata tests; no market returns or protected data."""
import hashlib
import json

import pytest

from stocks_predictor import h20_checked as checker


def fixture(tmp_path, monkeypatch):
    base = tmp_path / "inputs"
    base.mkdir()
    evidence = base / "evidence.json"
    evidence.write_text('{"cash_coverage":[]}', encoding="utf-8")
    manifest = base / "SHA256.json"
    manifest.write_text(json.dumps({"evidence.json": checker.digest(evidence)}), encoding="utf-8")
    gate = tmp_path / "gate.json"
    gate.write_text('{"status":"BLOCKED","profit":null}', encoding="utf-8")
    monkeypatch.setattr(checker, "MANIFEST_SHA", checker.digest(manifest))
    monkeypatch.setattr(checker, "GATE_SHA", checker.digest(gate))
    return base, gate


def test_valid_evidence_and_gate_pass(tmp_path, monkeypatch):
    base, gate = fixture(tmp_path, monkeypatch)
    assert checker.verify_evidence(base, gate) == 1


def test_forged_financial_gate_is_rejected(tmp_path, monkeypatch):
    base, gate = fixture(tmp_path, monkeypatch)
    gate.write_text('{"status":"COMPLETE","profit":123}', encoding="utf-8")
    with pytest.raises(ValueError, match="financial gate changed"):
        checker.verify_evidence(base, gate)


def test_changed_inventory_is_rejected_even_if_manifest_itself_is_unchanged(tmp_path, monkeypatch):
    base, gate = fixture(tmp_path, monkeypatch)
    (base/"evidence.json").write_text('{"cash_coverage":[{"verified":true}]}', encoding="utf-8")
    with pytest.raises(ValueError, match="checksum mismatch"):
        checker.verify_evidence(base, gate)


def test_rehashed_altered_manifest_is_still_rejected(tmp_path, monkeypatch):
    base, gate = fixture(tmp_path, monkeypatch)
    (base/"SHA256.json").write_text('{"evidence.json":"' + hashlib.sha256(b'changed').hexdigest() + '"}', encoding="utf-8")
    with pytest.raises(ValueError, match="manifest changed"):
        checker.verify_evidence(base, gate)


def test_missing_payload_is_rejected(tmp_path, monkeypatch):
    base, gate = fixture(tmp_path, monkeypatch)
    (base/"evidence.json").unlink()
    with pytest.raises(ValueError, match="manifest path"):
        checker.verify_evidence(base, gate)


def test_invalid_gate_rejected_before_loading_old_measurement(tmp_path, monkeypatch):
    def fail(*args):
        raise ValueError("stop before loading")
    monkeypatch.setattr(checker, "verify_evidence", fail)
    with pytest.raises(ValueError, match="stop before loading"):
        checker.run_checked(tmp_path, tmp_path/"absent.json")
