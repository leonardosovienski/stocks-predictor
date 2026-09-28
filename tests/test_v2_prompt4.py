"""Protocolo v2 — Prompt 4: régua nova sobre artefatos históricos (sem reexecução), pré-registro, holdout selado e
deduplicação."""

import hashlib
import json
import random
from pathlib import Path

import pytest

from stocks_predictor.v2 import synthetic
from stocks_predictor.v2.baselines import EqualWeightUniverse, RandomPortfolio
from stocks_predictor.v2.costs import CostModel, LiquidityRule
from stocks_predictor.v2.dataset import PITDataset
from stocks_predictor.v2.engine import ProtocolConfig
from stocks_predictor.v2.execution import ExecutionConvention
from stocks_predictor.v2.manifest import LedgerError, TrialLedger, run_evaluation
from stocks_predictor.v2.preregistration import (PREREG_FIELDS, dedup_check, open_holdout, preregister,
                                                 require_preregistration, seal_holdout)
from stocks_predictor.v2.reassessment import (biases_for, implied_denominator, main, parse_verdict_report,
                                              reassess, rescaled_dsr)

ROOT = Path(__file__).resolve().parents[1]
H11 = (ROOT / "reports/h11_verdict_adhoc.md").read_text(encoding="utf-8")
H1 = (ROOT / "reports/h1_verdict_20260712T091903477689-41cc24.md").read_text(encoding="utf-8")
TRIALS = json.loads((ROOT / "trials.json").read_text())
SHARPES = [t["sharpe"] for t in TRIALS]


# -- régua nova sobre o artefato ---------------------------------------------------------------------
def test_verdict_reports_are_parsed_without_inventing_fields():
    r = parse_verdict_report(H11)
    assert r["sessions"] == 1218 and r["dsr"] == 0.843 and r["n_hist"] == 10 and r["sr0_hist"] == 0.0277
    assert r["sharpe_ann"] == {"strategy": 0.9167, "benchmark": 0.566}
    assert r["ic_low"] == -0.0378 and r["ic_high"] == 0.7914 and r["verdict"].startswith("não comprovada")
    h1 = parse_verdict_report(H1)
    assert h1["dsr"] is None and h1["n_hist"] is None and h1["sessions"] == 2092  # H1 não publicou DSR


def test_implied_denominator_roundtrips_the_historical_dsr():
    rng = random.Random(4)
    for _ in range(50):
        sr, sr0, t, d = rng.uniform(-0.05, 0.08), rng.uniform(0.0, 0.04), rng.randint(500, 3000), rng.uniform(0.8, 1.3)
        dsr = rescaled_dsr(sr, sr0, t, d)
        if 0.02 < abs(dsr - 0.5) and 1e-9 < dsr < 1 - 1e-9:
            assert implied_denominator(dsr, sr, sr0, t) == pytest.approx(d, rel=1e-6)


def test_every_published_dsr_is_reproduced_and_the_new_ruler_is_more_conservative():
    for path in sorted((ROOT / "reports").glob("h*_verdict*.md")):
        report = parse_verdict_report(path.read_text(encoding="utf-8"))
        name = "H" + path.name.split("_")[0][1:]
        trial = next(t for t in TRIALS if t["name"].split("-")[0].upper() == name)
        out = reassess(report, sr_per_session=trial["sharpe"], trial_sharpes=SHARPES, n_grid=[102, 150, 204, 510])
        if report["dsr"] is not None:
            again = rescaled_dsr(trial["sharpe"], report["sr0_hist"], report["sessions"], out["denominator"])
            assert again == pytest.approx(report["dsr"], abs=5e-5), name
        assert out["more_conservative"], name
        assert out["worst"]["n"] == 510 and out["worst"]["dsr"] < 0.95, name


def test_protocol_incompatibilities_are_recorded_per_hypothesis():
    names = {b["bias"] for b in biases_for("H7")}
    assert {"execucao_no_fechamento_do_sinal", "fundamento_com_embargo_estimado", "retorno_so_preco"} <= names
    assert "retorno_so_preco" not in {b["bias"] for b in biases_for("H11")}
    assert biases_for("H17") == []


def test_reassessment_cli_writes_one_ledger_record_per_artifact(tmp_path, capsys):
    rows = [{"data": f"{d:02d}/01/2019", "valor": "0.024620"} for d in range(2, 5)]
    raw = tmp_path / "sgs12.json"
    raw.write_text(json.dumps(rows))
    Path(str(raw) + ".receipt.json").write_text(json.dumps({"sha256": hashlib.sha256(raw.read_bytes()).hexdigest()}))
    output, ledger = tmp_path / "out.json", tmp_path / "ledger.jsonl"
    argv = ["--reports", str(ROOT / "reports"), "--trials", str(ROOT / "trials.json"), "--riskfree", f"bcb-sgs-12:{raw}",
            "--policy", str(ROOT / "policy/stocks-evaluation-policy-v1.json"), "--ledger", str(ledger),
            "--output", str(output)]
    assert main(argv) == 0
    out = json.loads(output.read_text())
    assert len(out["rows"]) == 15 and out["n_trials"]["n_known"] == 71 + 0 + 15
    assert all(r["status_after"].startswith("NOT_SUPPORTED mantido") for r in out["rows"])
    assert out["policy"]["policy_path"] == "policy/stocks-evaluation-policy-v1.json"  # sem diretório pessoal
    kinds = [r["kind"] for r in TrialLedger(ledger).records]
    assert kinds == ["REASSESSMENT"] * 15
    capsys.readouterr()
    with pytest.raises(SystemExit):
        main(argv)


# -- pré-registro, holdout e deduplicação --------------------------------------------------------------
def prereg(**overrides):
    record = {k: f"valor de {k}" for k in PREREG_FIELDS}
    record |= {"hypothesis_id": "stocks:NEW-001", "policy": {"version": "1.0.0", "sha256": "0" * 64},
               "max_variants": 1, "seeds": [7], "secondary_metrics": ["ic"],
               "criteria": {"GO": "a", "NO_GO": "b", "NO_DECISION": "c"}}
    return record | overrides


def test_preregistration_is_required_complete_and_immutable(tmp_path):
    ledger = TrialLedger(tmp_path / "ledger.jsonl")
    with pytest.raises(LedgerError, match="sem pré-registro"):
        require_preregistration(ledger, "stocks:NEW-001")
    with pytest.raises(LedgerError, match="campos exatos"):
        preregister(ledger, prereg(description=""))
    with pytest.raises(LedgerError, match="GO"):
        preregister(ledger, prereg(criteria={"GO": "a"}))
    preregister(ledger, prereg())
    assert require_preregistration(ledger, "stocks:NEW-001")["kind"] == "PREREGISTERED"
    with pytest.raises(LedgerError, match="imutável"):
        preregister(ledger, prereg(description="outra"))
    assert ledger.open_runs() == [] and len(ledger.started()) == 0


def test_holdout_opens_once_and_only_with_human_approval(tmp_path):
    ledger = TrialLedger(tmp_path / "ledger.jsonl")
    seal = seal_holdout(ledger, holdout_id="h1", interval=["2026-09-10", "2027-09-10"], content="FUTURE",
                        conditions="aprovação humana depois do fim do intervalo")
    assert len(seal["payload"]["seal_sha256"]) == 64
    with pytest.raises(LedgerError, match="imutável"):
        seal_holdout(ledger, holdout_id="h1", interval=["2026-09-10", "2027-09-10"], content="FUTURE", conditions="x")
    with pytest.raises(LedgerError, match="aprovação"):
        open_holdout(ledger, "h1", {"approved_by": "dono"}, "a" * 64)
    approval = {"approved_by": "dono", "approved_at": "2027-09-11T12:00:00Z", "reason": "avaliação final",
                "channel": "chat"}
    open_holdout(ledger, "h1", approval, "a" * 64)
    with pytest.raises(LedgerError, match="segunda consulta"):
        open_holdout(ledger, "h1", approval, "a" * 64)
    with pytest.raises(LedgerError, match="não selado"):
        open_holdout(ledger, "outro", approval, "a" * 64)
    with pytest.raises(LedgerError, match="não permitido"):
        ledger.append_record("STARTED", "x", {})


def test_dedup_rejects_redundant_candidates_only():
    rng = random.Random(2)
    base = [rng.gauss(0, 1) for _ in range(120)]
    other = [rng.gauss(0, 1) for _ in range(120)]
    near_copy = [x + rng.gauss(0, 0.01) for x in base]
    out = dedup_check(near_copy, {"momentum": base, "lowvol": other}, threshold=0.99, period=("2019-01", "2023-12"))
    assert out["status"] == "REJECTED_REDUNDANT" and out["most_similar"] == "momentum" and out["value"] >= 0.99
    assert dedup_check(other, {"momentum": base}, threshold=0.99, period=("a", "b"))["status"] == "DISTINCT"
    with pytest.raises(ValueError, match="desalinhada"):
        dedup_check(base, {"x": base[:10]}, threshold=0.99, period=("a", "b"))


# -- aplicação no ponto em que a avaliação roda -------------------------------------------------------
DS = PITDataset(synthetic.build())
CONFIG = ProtocolConfig(start="2020-07-01", end="2020-12-30", rebalance="monthly", execution=ExecutionConvention(),
                        costs=CostModel(0.0, 0.0, 3.0, 7.5, 7.5, 0.0, 0.5, 0.0),
                        liquidity=LiquidityRule(1e6, 63, 0.05), seed=3)
GIT = {"commit": "0" * 40, "dirty": False}


def test_evaluation_of_a_hypothesis_requires_preregistration_and_respects_max_variants(tmp_path):
    ledger = TrialLedger(tmp_path / "ledger.jsonl")
    with pytest.raises(LedgerError, match="sem pré-registro"):
        run_evaluation(ledger, DS, EqualWeightUniverse(), CONFIG, family="nova", git=GIT,
                       hypothesis_id="stocks:NEW-001")
    assert ledger.started() == []  # nada roda antes do pré-registro
    preregister(ledger, prereg(max_variants=1))
    first = run_evaluation(ledger, DS, EqualWeightUniverse(), CONFIG, family="nova", git=GIT,
                           hypothesis_id="stocks:NEW-001")
    assert first["preregistration"]["hypothesis_id"] == "stocks:NEW-001"
    run_evaluation(ledger, DS, EqualWeightUniverse(), CONFIG, family="nova", git=GIT,
                   hypothesis_id="stocks:NEW-001")  # repetir a mesma variante não é variante nova
    with pytest.raises(LedgerError, match="limite pré-registrado"):
        run_evaluation(ledger, DS, RandomPortfolio(3), CONFIG, family="nova", git=GIT,
                       hypothesis_id="stocks:NEW-001")


def test_sealed_holdout_blocks_evaluation_until_opened_and_then_allows_one_query(tmp_path):
    ledger = TrialLedger(tmp_path / "ledger.jsonl")
    seal_holdout(ledger, holdout_id="h", interval=["2020-10-01", "2021-06-30"], content="FUTURE", conditions="c")
    with pytest.raises(LedgerError, match="ainda não aberto"):
        run_evaluation(ledger, DS, EqualWeightUniverse(), CONFIG, family="x", git=GIT)
    early = ProtocolConfig(**{**CONFIG.__dict__, "end": "2020-09-30"})
    with pytest.raises(LedgerError, match="ainda não aberto"):  # o dataset contém o intervalo selado
        run_evaluation(ledger, DS, EqualWeightUniverse(), early, family="x", git=GIT)
    preregister(ledger, prereg())
    approval = {"approved_by": "dono", "approved_at": "2021-07-01T12:00:00Z", "reason": "r", "channel": "chat"}
    open_holdout(ledger, "h", approval, "a" * 64)
    with pytest.raises(LedgerError, match="só hipótese pré-registrada"):
        run_evaluation(ledger, DS, EqualWeightUniverse(), CONFIG, family="x", git=GIT)
    out = run_evaluation(ledger, DS, EqualWeightUniverse(), CONFIG, family="x", git=GIT,
                         hypothesis_id="stocks:NEW-001")
    assert out["holdout_access"] == "h"
    with pytest.raises(LedgerError, match="consulta única"):
        run_evaluation(ledger, DS, EqualWeightUniverse(), CONFIG, family="x", git=GIT,
                       hypothesis_id="stocks:NEW-001")
    preregister(ledger, prereg(hypothesis_id="stocks:NEW-002"))
    with pytest.raises(LedgerError, match="só hipótese pré-registrada antes da abertura"):
        run_evaluation(ledger, DS, EqualWeightUniverse(), CONFIG, family="x", git=GIT,
                       hypothesis_id="stocks:NEW-002")
