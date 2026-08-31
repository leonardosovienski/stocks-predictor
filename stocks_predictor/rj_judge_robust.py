"""Robustez estatística do judge RJ — além do BH-FDR pré-registrado.

Duas adições, ambas ROBUSTEZ (não substituem o julgamento oficial, que é o
Benjamini-Hochberg congelado em config_rj.yaml):

1. `romano_wolf_stepdown`: correção de múltiplos testes por permutação
   CONJUNTA dos rótulos entre as famílias — controla FWER e calibra o cutoff
   na correlação real entre as estatísticas (a família de métodos que
   Harvey-Liu defendem para a "factor zoo": cutoffs data-driven em vez de
   fórmula universal). Se BH e Romano-Wolf concordam, o veredito é mais
   forte; se divergem, o relatório diz isso explicitamente.

2. `apply_oos_haircut`: atenuação out-of-sample de ~36% documentada por
   Harvey-Liu para descobertas que sobrevivem à correção de múltiplos
   testes. Regra declarada para a etapa ECONÔMICA futura (sizing de
   hipótese, nunca de capital real enquanto capital_permission=FORBIDDEN).
"""
import random
import statistics

import rj_families as families
from rj_judge import permutation_pvalue_from_count


def _t_stat(units) -> float | None:
    """t-like: diferença de médias / erro-padrão combinado (Welch)."""
    g1 = [v for _, v, g in units if g == 1]
    g0 = [v for _, v, g in units if g == 0]
    if len(g1) < 2 or len(g0) < 2:
        return None
    m1, m0 = statistics.mean(g1), statistics.mean(g0)
    v1 = statistics.variance(g1) / len(g1)
    v0 = statistics.variance(g0) / len(g0)
    se = (v1 + v0) ** 0.5
    return (m1 - m0) / se if se > 0 else None


def romano_wolf_stepdown(units_by_family: dict, n_perm: int = 5000,
                         seed: int = 42,
                         alpha: float = 0.10) -> dict:
    """P-valores ajustados Romano-Wolf sobre as famílias PREDITIVAS com dado.

    A cada permutação, embaralha os rótulos de TODAS as famílias com a MESMA
    permutação (preserva a correlação cruzada entre estatísticas — é ela que
    o BH ignora) e guarda o max|t| da permutação. p_ajustado de cada família
    = fração de permutações cujo max|t| >= |t_obs| (versão single-step;
    stepdown estrito refinaria ainda mais, com ganho marginal aqui).
    """
    names = [n for n in families.PREDICTIVE_FAMILIES
             if units_by_family.get(n) and n not in families.CATEGORICAL_FAMILIES]
    t_obs = {n: _t_stat(units_by_family[n]) for n in names}
    t_obs = {n: t for n, t in t_obs.items() if t is not None}
    if not t_obs:
        return {}
    rng = random.Random(seed)
    # permutação CONJUNTA quando todas as famílias têm exatamente as mesmas
    # units na mesma ordem (caso comum na análise primária: 1 episódio por
    # empresa): uma única permutação dos rótulos aplicada a todas — preserva
    # a correlação cruzada entre estatísticas, que é o que o BH ignora.
    # Fallback documentado: conjuntos de units diferentes (família com dado
    # faltante) => permutações independentes (aproximação; a correlação
    # cruzada fica subestimada e o ajuste, mais conservador).
    # Comparar só a IDENTIDADE/ORDEM dos tickers (não o valor, que difere por
    # construção entre famílias — comparar (ticker, valor) fazia same_units
    # dar False quase sempre, mesmo quando todas as famílias usam exatamente
    # as mesmas empresas, e a permutação conjunta nunca era exercitada).
    unit_sets = {n: tuple(u[0] for u in units_by_family[n]) for n in t_obs}
    same_units = len(set(unit_sets.values())) == 1
    ge_count = {n: 0 for n in t_obs}
    for _ in range(n_perm):
        shared_perm: list | None = None
        max_t = 0.0
        for n in t_obs:
            units = units_by_family[n]
            groups = [g for _, _, g in units]
            if same_units:
                if shared_perm is None:
                    shared_perm = list(range(len(groups)))
                    rng.shuffle(shared_perm)
                shuffled = [groups[i] for i in shared_perm]
            else:
                shuffled = groups[:]
                rng.shuffle(shuffled)
            t = _t_stat([(u[0], u[1], g) for u, g in zip(units, shuffled)])
            if t is not None:
                max_t = max(max_t, abs(t))
        for n, t in t_obs.items():
            if max_t >= abs(t):
                ge_count[n] += 1
    # permutation_pvalue_from_count: mesma convenção (n_ge+1)/(n_perm+1) do
    # judge (rj_judge.py) — ponto único de verdade da fórmula (achado de
    # revisão de código 2026-08-28), não altera alpha nem o BH oficial.
    p_rw = {n: permutation_pvalue_from_count(ge_count[n], n_perm) for n in t_obs}
    return {n: {"t_obs": t_obs[n], "p_romanowolf": p_rw[n],
                "significant_romanowolf": p_rw[n] <= alpha}
            for n in t_obs}


def robustness_report(units_by_family: dict, verdicts_bh: dict,
                      n_perm: int = 5000, seed: int = 42,
                      alpha: float = 0.10) -> dict:
    """Cruzamento BH x Romano-Wolf por família. O campo `concordant` é o
    resumo que importa: False em qualquer família significativa = o veredito
    depende do método de correção e deve ser reportado como frágil."""
    rw = romano_wolf_stepdown(units_by_family, n_perm=n_perm, seed=seed,
                              alpha=alpha)
    report = {}
    for name, rw_res in rw.items():
        bh_sig = (verdicts_bh.get(name) or {}).get("significant_after_fdr")
        # bh_sig=None = FDR não se aplica a esta família (descritiva/sem
        # p-valor) — "concorda?" não faz sentido: None, não False.
        concordant = (None if bh_sig is None
                      else rw_res["significant_romanowolf"] == bool(bh_sig))
        report[name] = {**rw_res, "significant_bh_fdr": bh_sig,
                        "concordant": concordant}
    return report


OOS_ATTENUATION = 0.36   # Harvey-Liu: descobertas perdem ~36% fora da amostra


def apply_oos_haircut(effect_size: float,
                      attenuation: float = OOS_ATTENUATION) -> float:
    """Effect size esperado fora da amostra = effect * (1 - attenuation).

    Uso exclusivo da etapa ECONÔMICA futura (estimar se um sinal sobrevive a
    custos depois da atenuação). Nunca reescreve o effect reportado — é uma
    projeção pessimista para planejamento, não uma correção do passado."""
    return effect_size * (1.0 - attenuation)
