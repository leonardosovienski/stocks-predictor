"""Estado científico legível por máquina (research/scientific_state.json), lido pela CAIN num commit fixado."""

import importlib.util
import json
from pathlib import Path
import re
import socket

from stocks_predictor.research_admission import closed_hypotheses

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("export_scientific_state", ROOT / "tools/export_scientific_state.py")
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)
STATE_PATH = ROOT / exporter.OUTPUT
STATE = json.loads(STATE_PATH.read_text(encoding="utf-8"))


def test_versioned_state_is_exactly_what_the_sources_generate():
    """Mudou estado, tentativa, congelamento, reavaliação, índice ou política: o arquivo precisa ser regravado."""
    assert STATE_PATH.read_text(encoding="utf-8") == exporter.render(exporter.build())
    assert exporter.main(["--check"]) == 0


def test_check_fails_when_the_file_drifts(tmp_path, capsys):
    drifted = dict(STATE, hypotheses={**STATE["hypotheses"], "H11": "OPEN"})
    path = tmp_path / "scientific_state.json"
    path.write_text(exporter.render(drifted), encoding="utf-8")
    assert exporter.main(["--check", "--output", str(path)]) == 1
    assert "diverge das fontes" in capsys.readouterr().err


def test_states_are_literal_and_every_state_has_a_declared_meaning():
    assert STATE["schema"] == "stocks-scientific-state/1" and STATE["domain"] == "stocks"
    assert STATE["hypotheses"] == {k.split(":", 1)[1]: v for k, v in closed_hypotheses().items()}
    assert set(STATE["hypotheses"].values()) <= set(STATE["vocabulary"])
    closed = {h for h, s in STATE["hypotheses"].items() if STATE["vocabulary"][s]["closed"]}
    assert closed == {f"H{n}" for n in (*range(1, 17), 20, 21, 22)}  # H17–H19 pausadas, não encerradas


def test_attempts_and_frozen_families_come_from_the_registries():
    trials = {row["trial_id"]: row for row in json.loads((ROOT / "trials_v2.json").read_text(encoding="utf-8"))}
    for hypothesis, trial in STATE["hypothesis_trials"].items():
        assert trials[trial]["hypothesis_id"] == hypothesis
    assert "H3" not in STATE["hypothesis_trials"]  # H3 não tem linha no registro: nada é inventado
    # H10 tem dois nomes de família no repositório; os dois ficam encerrados
    assert {"quality_roe_leverage_double_filter", "quality_roe_leverage_intersection"} <= set(STATE["frozen_families"])
    assert "previous_result" in STATE["reopen_policy"]["text"]


def test_reassessment_cites_reports_by_repository_path_and_hash():
    assert len(STATE["reassessment"]) == 15
    for row in STATE["reassessment"].values():
        assert row["report"].startswith("reports/")
        assert exporter.lf_sha256(ROOT / row["report"]) == row["report_sha256"]


def test_sources_are_hashed_and_nothing_personal_or_absolute_is_published():
    for source in STATE["sources"]:
        assert exporter.lf_sha256(ROOT / source["path"]) == source["sha256_lf"]
    text = STATE_PATH.read_text(encoding="utf-8")
    assert socket.gethostname() not in text
    assert not re.search(r"/home/|/Users/|[A-Za-z]:\\\\", text)
