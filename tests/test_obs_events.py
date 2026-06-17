"""Telemetria JSONL do predictor_core — testada na cópia VENDORIZADA (prova do loop
core -> sync -> consumidor com uma feature real). Envelope rígido de 7 chaves."""
import json

import pytest

from predictor_core import obs


def test_envelope_has_exactly_seven_keys(tmp_path):
    p = tmp_path / "events.jsonl"
    rec = obs.emit_event(
        "stocks", "toll_passed", run_id="run_1", code_version="abc123",
        metrics={"psr": 0.96, "bootstrap_ic_lower": 0.02}, metadata={"status": "ok"},
        path=p, timestamp="2026-06-16T00:00:00+00:00")
    assert len(obs.ENVELOPE_KEYS) == 7
    assert set(rec.keys()) == set(obs.ENVELOPE_KEYS)
    line = json.loads(p.read_text(encoding="utf-8").strip())
    assert line["domain"] == "stocks" and line["event"] == "toll_passed"
    assert line["metrics"]["psr"] == 0.96
    assert line["timestamp"] == "2026-06-16T00:00:00+00:00"


def test_optional_keys_present_even_when_unset(tmp_path):
    rec = obs.emit_event("wc", "data_fetched", path=tmp_path / "e.jsonl")
    for k in obs.ENVELOPE_KEYS:
        assert k in rec                      # envelope fixo: chave sempre existe
    assert rec["run_id"] is None and rec["code_version"] is None
    assert rec["metrics"] == {} and rec["metadata"] == {}


def test_appends_multiple_lines(tmp_path):
    p = tmp_path / "e.jsonl"
    obs.emit_event("stocks", "a", path=p)
    obs.emit_event("stocks", "b", path=p)
    assert len(obs.read_events(p)) == 2


def test_metrics_must_be_numeric(tmp_path):
    with pytest.raises(TypeError):
        obs.emit_event("stocks", "x", metrics={"status": "ok"}, path=tmp_path / "e.jsonl")


def test_domain_and_event_required(tmp_path):
    p = tmp_path / "e.jsonl"
    with pytest.raises(ValueError):
        obs.emit_event("", "x", path=p)
    with pytest.raises(ValueError):
        obs.emit_event("stocks", "", path=p)


def test_read_events_missing_file_is_empty(tmp_path):
    assert obs.read_events(tmp_path / "nope.jsonl") == []
