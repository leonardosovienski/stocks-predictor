"""H2+ — trava de poder (controle positivo) + Experiment Registry do domínio.

Um NO-GO só é interpretável se o pipeline provou que detectaria edge plantado
(testing.harness). Este módulo:

1. gera os braços sintéticos (edge / ruído) PAREADOS no formato que o
   `backtest.judge` real consome;
2. emite o atestado (`attest`) que destrava a criação de trials novas no
   Experiment Registry (`measurement.trials`);
3. registra as tentativas (H1 retroativa + H2) e aplica o DSR ao veredito da
   H2 — o desconto por múltiplas tentativas, obrigatório a partir da 2ª
   hipótese (diretriz do HANDOFF, 2026-07-12).

Escreve APENAS `trials.json` + o atestado irmão (arquivos de governança,
VERSIONADOS de propósito) — nunca no banco (§9b/§11 intactos).
"""
import json
import math
import pathlib
import statistics

import backtest
from predictor_core.measurement import trials
from predictor_core.testing import harness, synth

ROOT = pathlib.Path(__file__).parent.parent
METRIC = "sharpe_diff_ci95"

# Sharpe POR-PERÍODO da H1 (a unidade que o registro/DSR usam): 0.1592
# anualizado no veredito final (run 20260712T091903477689-41cc24) / sqrt(252).
H1_SHARPE_PER_PERIOD = 0.1592 / math.sqrt(252)
H2_TEST_PERIOD = ["2018-01-01", "2026-07-03"]


def trials_path_from(cfg, override=None):
    """Path do trials.json: override > config. Relativo é ancorado no ROOT."""
    p = pathlib.Path(override or cfg.get("h2_criteria", {}).get("trials_path", "trials.json"))
    return p if p.is_absolute() else ROOT / p


def _judge_verdict(pair, cfg):
    """Adapta o pedágio real ao contrato do harness ({'verdict': ...})."""
    strat, bench = pair
    v = backtest.judge(strat, bench, cfg)
    ok = v["veredito"] == "COMPROVADA"
    return {"verdict": "COMPROVADA" if ok else "não comprovada", "detail": v}


def edge_pair(n=1260, seed=7):
    """(strat, bench) com edge PLANTADO: strat = bench + 20 bps/dia. Um pedágio
    com poder TEM que devolver COMPROVADA aqui (sensibilidade)."""
    bench = synth.ar1_series(n, phi=0.2, sigma=0.012, seed=seed, mu=0.0003)
    return synth.edge_injected(bench, 0.002), bench


def noise_pair(n=1260, seed=7):
    """(strat, bench) independentes, mesma distribuição, edge NENHUM. Um pedágio
    honesto NÃO pode devolver COMPROVADA aqui (especificidade)."""
    strat = synth.ar1_series(n, phi=0.2, sigma=0.012, seed=seed + 1000, mu=0.0003)
    bench = synth.ar1_series(n, phi=0.2, sigma=0.012, seed=seed + 2000, mu=0.0003)
    return strat, bench


def attest(cfg, trials_path=None, note=""):
    """Controle positivo sobre o judge REAL + atestado irmão do trials.json.
    Falha alto (PipelineHasNoPowerError) sem gravar nada."""
    tp = trials_path_from(cfg, trials_path)
    tp.parent.mkdir(parents=True, exist_ok=True)
    return harness.attest_pipeline_power(
        lambda pair: _judge_verdict(pair, cfg),
        edge_pair, noise_pair,
        attestation_path=trials.attestation_path_for(tp),
        note=note or "controle positivo do pedágio (judge real, séries sintéticas pareadas)",
        edge_verdict="COMPROVADA", null_verdict="não comprovada",
        metric=METRIC)


def _params_from(cfg, keys):
    return {f"{s}.{k}": cfg.get(s, {}).get(k) for s, k in keys}


def _attested_fingerprint(registry_path: pathlib.Path) -> str | None:
    """Lê o fingerprint emitido pelo harness do Core 2.3.

    Trial nova continua fail-closed: se o arquivo estiver ausente/inválido, devolvemos
    None e o próprio Core rejeita o registro. Não fabricamos fingerprint no consumer.
    """
    path = trials.attestation_path_for(registry_path)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = record.get("pipeline_fingerprint")
    return value if isinstance(value, str) and value else None


def register_baseline_trials(cfg, trials_path=None):
    """Registra as tentativas do denominador do DSR: H1 (retroativa, Sharpe
    por-período do veredito final) e H2 (sharpe=None até a rodada única;
    preservado pela guarda anti-clobber depois dela). Idempotente; a CRIAÇÃO
    exige o atestado do harness (trava de poder)."""
    from config import H1_FROZEN_KEYS, H2_FROZEN_KEYS
    reg = register_hypothesis(
        cfg, "h1-momentum-12-1", H1_FROZEN_KEYS,
        "retroativa: veredito final da H1 (run 20260712T091903477689-41cc24), "
        "Sharpe anualizado 0.1592 -> por-período /sqrt(252); não comprovada",
        sharpe=round(H1_SHARPE_PER_PERIOD, 6), trials_path=trials_path)
    register_hypothesis(
        cfg, "h2-lowvol-252", H2_FROZEN_KEYS,
        "pré-registro 2026-07-16 (HANDOFF); sharpe preenchido pela rodada única",
        trials_path=trials_path)
    return reg


def per_period_sharpe(xs):
    """Sharpe por-período (mesma convenção do judge/PSR): média/desvio, sem anualizar."""
    sd = statistics.pstdev(xs) if len(xs) > 1 else 0.0
    return statistics.mean(xs) / sd if sd else 0.0


def register_hypothesis(cfg, name, frozen_keys, notes, sharpe=None, trials_path=None):
    """Registra (ou atualiza) uma tentativa de hipótese deste domínio no
    registry. Criação exige o atestado do harness (trava de poder).

    Guarda anti-clobber: re-registrar com sharpe=None uma trial que JÁ TEM
    sharpe realizado preserva o valor (e as notes) existentes — o resultado de
    uma rodada única não pode ser apagado por um re-registro de baseline
    (bug corrigido 2026-07-18: os comandos H4/H5 zeravam o sharpe da H2)."""
    reg = trials.TrialRegistry(trials_path_from(cfg, trials_path))
    if sharpe is None:
        existing = next((t for t in reg.load() if t.get("name") == name), None)
        if existing and existing.get("sharpe") is not None:
            sharpe = existing["sharpe"]
            notes = existing.get("notes", notes)
    reg.register(
        name,
        params=_params_from(cfg, frozen_keys),
        sharpe=sharpe,
        metric=METRIC,
        notes=notes,
        test_period=H2_TEST_PERIOD,
        pipeline_fingerprint=_attested_fingerprint(reg.path),
    )
    return reg


def apply_dsr(verdict, strat, cfg, trials_path=None, trial_name="h2-lowvol-252",
              frozen_keys=None, criteria_section="h2_criteria",
              extra_failures=(), notes=None):
    """Critério DSR das hipóteses N>=2: DSR >= dsr_min, descontado por TODAS as
    tentativas do registro.

    Atualiza o sharpe realizado da trial no registro (update de trial existente
    — não exige atestado) e COMBINA os critérios pré-registrados: COMPROVADA
    sse IC95% da diferença de Sharpe > 0, DSR >= dsr_min E `extra_failures`
    vazio (critérios adicionais da hipótese — ex. drawdown na H4 — avaliados
    pelo chamador, que passa as razões das falhas)."""
    if not strat or verdict.get("psr") is None:
        return verdict  # SEM DADOS / amostra curta: não há o que descontar
    from config import H2_FROZEN_KEYS
    reg = register_hypothesis(
        cfg, trial_name, frozen_keys or H2_FROZEN_KEYS,
        notes or "rodada única (sharpe por-período realizado)",
        sharpe=round(per_period_sharpe(strat), 6), trials_path=trials_path)
    d = reg.deflated_sharpe(strat)
    dsr_min = cfg.get(criteria_section, {}).get("dsr_min", 0.95)
    lo = verdict.get("sharpe_diff_ci", (None, None))[0]
    ic_ok = lo is not None and lo > 0
    dsr_ok = d["dsr"] is not None and d["dsr"] >= dsr_min
    out = dict(verdict, dsr=d["dsr"], sr0=d["sr0"], n_trials=d["n_trials"])
    if ic_ok and dsr_ok and not extra_failures:
        out["veredito"] = "COMPROVADA"
    else:
        reasons = []
        if not ic_ok:
            reasons.append("IC cruza 0 / negativo")
        if not dsr_ok:
            reasons.append(f"DSR {d['dsr']:.4f} < {dsr_min}")
        reasons.extend(extra_failures)
        out["veredito"] = "não comprovada (" + "; ".join(reasons) + ")"
    return out
