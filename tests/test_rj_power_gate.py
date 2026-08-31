"""Power gate do judge (revisão externa, ponto 9): o smoke test original só
verificava "roda sem erro e nem tudo vira significativo" — fraco demais para
travar hipótese real. Aqui:

1. SENSIBILIDADE: planta um effect size CONHECIDO em muitas réplicas
   sintéticas independentes; o judge precisa detectar (significant_after_fdr)
   numa fração alta delas. Um pedágio sem poder não detectaria nem o óbvio.
2. ESPECIFICIDADE: gera muitas réplicas de RUÍDO PURO (nenhuma família tem
   sinal real); a taxa de falso positivo pós-FDR, agregada nas réplicas,
   precisa ficar compatível com o alpha nominal do FDR — não sistematicamente
   acima (o que indicaria um judge que "acha" padrão onde não há).

Usa n_boot REDUZIDO (`FAST_N_BOOT`) só para manter o gate rápido o
suficiente para rodar em CI a cada mudança — é um gate APROXIMADO, não
substitui o judge real (n_boot=10000 do config.yaml) na hipótese oficial.
Este arquivo é a trava equivalente ao `testing.harness.attest_pipeline_power`
do domínio de ações, adaptada à ausência de measurement.trials aqui (ponto
9 do HANDOFF: pendente formalizar como atestado versionado quando a
primeira hipótese real for aberta).
"""
import copy
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "stocks_predictor"))

import rj_judge as judge
import rj_families as families
import yaml

FAST_N_BOOT = 300     # reduzido só para o gate rodar rápido; hipótese real usa config.yaml


def load_fast_config():
    cfg_path = pathlib.Path(__file__).parent.parent / "config_rj.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg = copy.deepcopy(cfg)
    cfg["judge"]["n_boot"] = FAST_N_BOOT
    return cfg


def make_universe(rng, n_companies=20, planted_effect=0.0, family="drawdown"):
    """n_companies/2 em cada grupo. `planted_effect` desloca a MÉDIA do
    grupo-rally na família indicada; 0.0 = ruído puro em todas as famílias."""
    names = list(families.REGISTRY.keys())
    units_by_family = {name: [] for name in names}
    for i in range(n_companies):
        ticker = f"SYN{i:03d}3"
        group = 1 if i < n_companies // 2 else 0
        for name in names:
            if name == "rj_stage":
                cats = ["requested", "plan_presented", "plan_approved", "exited"]
                val = cats[rng.randrange(len(cats))]
            else:
                base = rng.gauss(0.0, 1.0)
                if name == family:
                    base += planted_effect if group == 1 else 0.0
                val = base
            units_by_family[name].append((ticker, val, group))
    return units_by_family


def test_sensitivity_detects_planted_effect():
    """Effect size grande (2.5 desvios-padrão de separação) plantado em
    'drawdown', repetido em 30 universos sintéticos independentes. Exige
    detecção (significant_after_fdr) em pelo menos 70% deles — limiar
    conservador dado n_boot reduzido; a hipótese real usa n_boot=10000."""
    cfg = load_fast_config()
    n_reps, n_detected = 30, 0
    for rep in range(n_reps):
        rng = random.Random(1000 + rep)
        units = make_universe(rng, n_companies=24, planted_effect=2.5, family="drawdown")
        verdicts = judge.run_all_families(units, cfg)
        if verdicts["drawdown"]["significant_after_fdr"]:
            n_detected += 1
    rate = n_detected / n_reps
    assert rate >= 0.70, f"sensibilidade insuficiente: detectou {rate:.0%} de {n_reps} réplicas com efeito plantado"


def test_specificity_false_positive_rate_near_nominal():
    """Ruído puro em TODAS as famílias, repetido em 40 universos
    independentes. Taxa de falso positivo pós-FDR, agregada nas 8 famílias x
    40 réplicas, não pode ficar sistematicamente acima do alpha nominal
    (10%) por uma margem grande — um judge que "acha" padrão em ruído
    inflaria isso."""
    cfg = load_fast_config()
    alpha = cfg["judge"]["fdr_alpha"]
    n_reps = 40
    n_tests, n_false_positive = 0, 0
    for rep in range(n_reps):
        rng = random.Random(2000 + rep)
        units = make_universe(rng, n_companies=24, planted_effect=0.0, family="none")
        verdicts = judge.run_all_families(units, cfg)
        for name, v in verdicts.items():
            n_tests += 1
            if v["significant_after_fdr"]:
                n_false_positive += 1
    fp_rate = n_false_positive / n_tests
    # margem generosa (3x nominal) porque FDR com m=8 e n_boot reduzido tem
    # variância alta por réplica — o alvo é "não sistematicamente estourado",
    # não igualdade exata ao alpha nominal.
    assert fp_rate <= 3 * alpha, (
        f"taxa de falso positivo pós-FDR ({fp_rate:.1%}) muito acima do "
        f"alpha nominal ({alpha:.0%}) em {n_reps} réplicas de ruído puro — "
        "judge pode estar achando padrão onde não há")


if __name__ == "__main__":
    test_sensitivity_detects_planted_effect()
    print("power gate: sensibilidade OK")
    test_specificity_false_positive_rate_near_nominal()
    print("power gate: especificidade OK")
