"""O veredito não pode sair de um DSR que não descontou nada (2026-09-07).

`predictor_core.measurement.trials.deflated_sharpe_ratio` degenera em PSR puro
quando `E[max SR]` não pode ser estimado — `sr0` vira 0 e o "Deflated" Sharpe
deixa de descontar por número de tentativas. O Core 3.2.0 expôs isso no retorno
(`sr0_estimable`, `deflation_applied`) e adicionou `strict=True`.

`strict`, sozinho, cobre UM dos dois caminhos: menos de duas tentativas com
sharpe numérico. O outro caminho — N tentativas com sharpe IDÊNTICO, logo
V[SR] = 0 e `sr0` = 0 — mantém `sr0_estimable=True`, NÃO levanta com `strict`,
e devolve um DSR alto que não descontou tentativa nenhuma. Estes testes fixam
os dois como fail-closed no domínio, que é quem depende do desconto para
emitir veredito.

Nenhum veredito já emitido muda: o `trials.json` real tem 15 sharpes numéricos
distintos, logo V[SR] > 0 e o desconto sempre se aplicou.
"""
import pytest

import trials_gate
from config import H2_FROZEN_KEYS, load_config


def _cfg():
    cfg = load_config()
    cfg["bootstrap"] = {"n_boot": 200, "block_length": 21, "confidence": 0.95, "seed": 42}
    return cfg


def _strat(n=400):
    """Série determinística com desvio > 0 (senão per_period_sharpe é 0)."""
    return [0.001 + 0.002 * ((i % 7) - 3) for i in range(n)]


def _verdict_que_passaria(strat):
    """Veredito cujo IC95% da diferença de Sharpe é positivo — sem a guarda do
    desconto, este é exatamente o caso que viraria COMPROVADA."""
    return {"n": len(strat), "psr": 0.99, "sharpe_diff_ci": (0.10, 0.50),
            "veredito": "COMPROVADA"}


def test_menos_de_duas_tentativas_com_sharpe_nao_produz_veredito(tmp_path):
    """Um único sharpe numérico no registro: V[SR] não existe, `strict` levanta,
    e o domínio devolve não-comprovada dizendo o motivo — em vez de um DSR que
    parece descontado e é PSR."""
    cfg = _cfg()
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)

    strat = _strat()
    out = trials_gate.apply_dsr(
        _verdict_que_passaria(strat), strat, cfg, trials_path=tp,
        trial_name="solitaria", frozen_keys=H2_FROZEN_KEYS)

    assert out["veredito"].startswith("não comprovada")
    assert "não estimável" in out["veredito"]
    assert out["dsr"] is None
    assert out["deflation_applied"] is False


def test_tentativas_de_sharpe_identico_nao_produzem_comprovada(tmp_path):
    """N tentativas com o MESMO sharpe: V[SR] = 0, `sr0` = 0, `strict` NÃO
    levanta e o DSR sai alto sem ter descontado nada. É o buraco que `strict`
    não cobre, e o que esta guarda fecha."""
    cfg = _cfg()
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)

    strat = _strat()
    # O mesmo valor que `apply_dsr` vai gravar para a trial sob julgamento —
    # assim as três tentativas ficam idênticas e a variância zera.
    igual = round(trials_gate.per_period_sharpe(strat), 6)
    for nome in ("gemea-a", "gemea-b"):
        trials_gate.register_hypothesis(cfg, nome, H2_FROZEN_KEYS, "sharpe idêntico",
                                        sharpe=igual, trials_path=tp)

    out = trials_gate.apply_dsr(
        _verdict_que_passaria(strat), strat, cfg, trials_path=tp,
        trial_name="gemea-c", frozen_keys=H2_FROZEN_KEYS)

    assert out["sr0"] == 0.0, "cenário inválido: a variância não zerou"
    assert out["deflation_applied"] is False
    assert out["dsr"] is not None and out["dsr"] > 0.95, (
        "cenário inválido: sem um DSR alto o teste não prova que a guarda "
        "(e não o limiar) é o que barra o veredito")
    assert out["veredito"].startswith("não comprovada")
    assert "desconto do DSR NÃO aplicado" in out["veredito"]


def test_registro_real_tem_desconto_estimavel():
    """Guarda de regressão sobre o ledger REAL: as 15 tentativas registradas têm
    sharpe numérico e não são todas iguais. Se um dia isto quebrar, a guarda
    acima passa a barrar rodadas de verdade — e aí é bug de registro, não de
    critério."""
    from predictor_core.measurement import trials

    reg = trials.TrialRegistry(trials_gate.ROOT / "trials.json")
    sharpes = [s for s in reg.sharpes() if s is not None]
    assert len(sharpes) >= 2
    assert len(set(sharpes)) >= 2, "todas as tentativas com o mesmo sharpe zeraria V[SR]"


def test_serie_vazia_continua_sem_veredito_estatistico(tmp_path):
    """Regressão: sem série não há o que descontar, e `apply_dsr` devolve o
    veredito de entrada intacto (SEM DADOS), sem tocar no registro."""
    cfg = _cfg()
    tp = tmp_path / "trials.json"
    entrada = {"n": 0, "psr": None, "sharpe_diff_ci": (None, None),
               "veredito": "SEM DADOS (pipeline vazio — histórico insuficiente)"}
    assert trials_gate.apply_dsr([], [], cfg, trials_path=tp) == []
    assert trials_gate.apply_dsr(entrada, [], cfg, trials_path=tp) is entrada
    assert not tp.exists()


@pytest.mark.parametrize("campo", ["n_sharpes", "deflation_applied", "sharpe_coverage"])
def test_diagnostico_do_desconto_chega_ao_veredito(tmp_path, campo):
    """O diagnóstico que o Core 3.2.0 passou a devolver precisa chegar a quem lê
    o veredito — era o ganho que justificou a migração e não estava ligado."""
    cfg = _cfg()
    tp = tmp_path / "trials.json"
    trials_gate.attest(cfg, trials_path=tp)
    trials_gate.register_baseline_trials(cfg, trials_path=tp)

    strat = _strat()
    out = trials_gate.apply_dsr(_verdict_que_passaria(strat), strat, cfg,
                                trials_path=tp, trial_name="h2-lowvol-252")
    assert campo in out
