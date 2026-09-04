"""M5/M6 — relatório do veredito + telemetria estruturada.

Verifica a maquinaria de report: monta métricas, grava o Markdown datado por run_id, e
emite UM evento no envelope rígido (metrics só-numérico). Não asserta veredito.
"""
import report
from predictor_core import obs


_CFG = {"bootstrap": {"confidence": 0.95, "block_length": 21}}


def test_summarize_series_metrics():
    s = report.summarize_series([0.01, -0.02, 0.03, 0.00, 0.015])
    assert s["n"] == 5
    assert s["sharpe"] is None or isinstance(s["sharpe"], float)
    assert s["total_return"] is not None
    assert 0.0 <= s["max_drawdown"] <= 1.0


def test_summarize_empty_is_safe():
    s = report.summarize_series([])
    assert s["n"] == 0 and s["sharpe"] is None and s["max_drawdown"] is None


def test_write_report_grava_md_e_emite_telemetria(tmp_path, monkeypatch):
    verdict = {"n": 100, "psr": 0.42, "sharpe_diff_ci": (-0.1, 0.3),
               "veredito": "não comprovada (IC cruza 0 / negativo)"}
    strat = [0.001 * ((i % 7) - 3) for i in range(100)]
    bench = [0.001 * ((i % 5) - 2) for i in range(100)]
    events = tmp_path / "events.jsonl"

    monkeypatch.setenv(obs.EVENTS_ENV, str(events))
    path = report.write_report(verdict, strat, bench, _CFG,
                               run_id="RUNTEST", reports_dir=str(tmp_path))

    body = path.read_text(encoding="utf-8")
    assert path.name == "h1_verdict_RUNTEST.md"
    assert "veredito H1" in body and "Pedágio de 2 lentes" in body

    recs = obs.read_events(events)
    assert len(recs) == 1
    ev = recs[0]
    assert ev["event"] == "h1_verdict" and ev["run_id"] == "RUNTEST"
    # metrics é SÓ numérico (envelope rígido); veredito (texto) vai em metadata
    assert all(isinstance(v, (int, float)) for v in ev["metrics"].values())
    assert ev["metadata"]["veredito"].startswith("não comprovada")


def test_h6_and_h8_get_their_own_bias_note_not_h1s(tmp_path):
    """Achado de revisão de código 2026-08-28: `_BIAS_NOTE` só tinha H1/H2/H4/H5
    — o fallback `.get(hypothesis, _BIAS_NOTE["H1"])` imprimia silenciosamente
    a ressalva de viés da H1 (momentum puro) nos relatórios de H6/H8, errada
    para a H8 (perna baixa-vol tem viés na direção OPOSTA da H1)."""
    verdict = {"n": 10, "psr": 0.5, "sharpe_diff_ci": (-0.1, 0.1), "veredito": "x"}
    md6, _, _ = report.build_markdown(verdict, [0.01] * 10, [0.01] * 10, _CFG,
                                      hypothesis="H6")
    assert "momentum 6-1" in md6
    assert "MISTA" not in md6

    md8, _, _ = report.build_markdown(verdict, [0.01] * 10, [0.01] * 10, _CFG,
                                      hypothesis="H8")
    assert "MISTA" in md8
    assert "momentum 6-1" not in md8


def test_unknown_hypothesis_does_not_inherit_h1_bias_note(tmp_path):
    """Uma hipótese futura sem entrada em `_BIAS_NOTE` tem que avisar que a nota
    não foi documentada — nunca herdar silenciosamente o texto da H1. Usa um
    nome fora do range hoje registrado (H1-H9 já têm nota própria)."""
    verdict = {"n": 10, "psr": 0.5, "sharpe_diff_ci": (-0.1, 0.1), "veredito": "x"}
    md, _, _ = report.build_markdown(verdict, [0.01] * 10, [0.01] * 10, _CFG,
                                     hypothesis="H99")
    assert "NÃO documentada" in md
    assert "FAVORECE a estratégia de momentum" not in md


def test_dsr_threshold_shown_matches_hypothesis_own_criteria_not_h2s():
    """Achado de revisão de código 2026-08-28: o relatório caía para
    `h2_criteria` quando a seção `{h}_criteria` da hipótese não existia no
    config — divergindo do fallback REAL de `trials_gate.apply_dsr` (seção
    ausente -> {} -> dsr_min default 0.95). Config com h2_criteria.dsr_min
    diferente do default prova que o relatório não pode mais herdar o valor
    de outra hipótese."""
    cfg = {"bootstrap": {"confidence": 0.95, "block_length": 21},
          "h2_criteria": {"dsr_min": 0.80}}   # deliberadamente != 0.95
    verdict = {"n": 10, "psr": 0.5, "sharpe_diff_ci": (-0.1, 0.1), "veredito": "x",
              "dsr": 0.5, "n_trials": 9, "sr0": 0.01}
    md, _, _ = report.build_markdown(verdict, [0.01] * 10, [0.01] * 10, cfg,
                                     hypothesis="H9")   # sem h9_criteria no cfg
    assert "mínimo pré-registrado: 0.95" in md
    assert "0.8" not in md.split("mínimo pré-registrado:")[1][:6]


def test_nan_psr_nao_corrompe_telemetria(tmp_path, monkeypatch):
    """NaN passa isinstance(float) e json.dumps o serializa como 'NaN' — JSON inválido
    p/ qualquer parser estrito. O filtro de metrics tem que barrar não-finitos."""
    import json
    verdict = {"n": 100, "psr": float("nan"), "sharpe_diff_ci": (float("inf"), None),
               "veredito": "x"}
    events = tmp_path / "events.jsonl"
    monkeypatch.setenv(obs.EVENTS_ENV, str(events))
    report.write_report(verdict, [0.01] * 100, [0.01] * 100, _CFG,
                        run_id="NANTEST", reports_dir=str(tmp_path))
    for ln in events.read_text(encoding="utf-8").splitlines():
        rec = json.loads(ln, parse_constant=lambda c: (_ for _ in ()).throw(
            ValueError(f"constante não-JSON-estrito na telemetria: {c}")))
        assert "psr" not in rec["metrics"] and "ic_lower" not in rec["metrics"]
