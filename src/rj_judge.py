"""Judge do domínio RJ: testa as 8 famílias contra rally-vs-controle.

Por que NÃO reaproveita `trials_gate.py`/DSR do stocks-predictor tal como
está: o DSR ali é Sharpe-específico — desconta múltiplas tentativas sobre uma
SÉRIE DE RETORNOS por período. Aqui a unidade é diferença de médias entre
grupo-rally e grupo-controle num corte transversal (sem série temporal de
retorno por família). Reaproveita-se o QUE IMPORTA do vendor: o motor de
bootstrap não-paramétrico (`measurement.bootstrap.bootstrap_ci`, scheme=
'cluster') para o IC do effect size, e o PRINCÍPIO do trials_gate (nunca
reportar 1 achado sem descontar quantas foram testadas) via FDR de
Benjamini-Hochberg entre as 8 famílias em vez de DSR.

Unidade de reamostragem: EMPRESA (cluster_key=ticker), não episódio. Na
análise primária (1 episódio/empresa) isso degenera em iid — mas protege
automaticamente a análise secundária, se/quando episódios múltiplos da mesma
empresa entrarem no mesmo teste (protocolo "empresa -> episódios").
"""
import random
import statistics
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "vendor"))
from predictor_core.measurement.bootstrap import bootstrap_ci


def _mean_diff(units):
    """units: lista de (ticker, valor, grupo) — grupo 1=rally, 0=controle."""
    g1 = [v for _, v, g in units if g == 1]
    g0 = [v for _, v, g in units if g == 0]
    if not g1 or not g0:
        return None
    return statistics.mean(g1) - statistics.mean(g0)


def permutation_pvalue(units, n_perm: int = 10000, seed: int = 42) -> float | None:
    """P-valor de 2 lados: proporção de permutações do rótulo grupo com
    |diff| >= |diff observado|. Permuta rótulos entre EMPRESAS (uma por
    unidade na análise primária) — não entre episódios soltos."""
    obs = _mean_diff(units)
    if obs is None:
        return None
    rng = random.Random(seed)
    vals = [v for _, v, _ in units]
    groups = [g for _, _, g in units]
    n_ge = 0
    for _ in range(n_perm):
        shuffled = groups[:]
        rng.shuffle(shuffled)
        d = _mean_diff(list(zip((u[0] for u in units), vals, shuffled)))
        if d is not None and abs(d) >= abs(obs):
            n_ge += 1
    return n_ge / n_perm


def family_verdict(units, direction_expected: str, cfg: dict) -> dict:
    """units: [(ticker, valor, grupo)] de UMA família, análise primária.
    Retorna effect size, IC bootstrap por cluster, p-valor de permutação, e
    se a direção observada bate com a pré-registrada (direction_expected).

    Sem rótulo decorativo pré-FDR (revisão externa, ponto 5): "candidata" a
    partir de p<0.5 não é indício de nada — reporta só effect/CI/p aqui;
    `apply_fdr` decide `significant_after_fdr`, o único veredito binário
    que importa depois de descontar as 8 tentativas."""
    b = cfg["judge"]
    obs = _mean_diff(units)
    if obs is None or len(units) < 4:
        return {"n": len(units), "effect": None, "ci": (None, None),
                "p_value": None, "direction_match": None}

    def stat(resampled):
        return _mean_diff(resampled)

    lo, hi, _ = bootstrap_ci(
        units, stat, scheme=b["bootstrap_scheme"],
        n_boot=b["n_boot"], confidence=b["confidence"], seed=b["seed"],
        cluster_key=lambda u: u[0])
    p = permutation_pvalue(units, n_perm=b["n_boot"], seed=b["seed"])

    if direction_expected in ("ambiguous", "categorical"):
        direction_match = None
    else:
        expected_sign = 1 if direction_expected == "positive" else -1
        direction_match = (obs * expected_sign) > 0

    return {"n": len(units), "effect": obs, "ci": (lo, hi), "p_value": p,
            "direction_match": direction_match}


def _cramers_v(units) -> float:
    """V de Cramér para (categoria, grupo) — força de associação categórica,
    sem assumir ordem entre categorias (revisão externa, ponto 4: rj_stage
    não é ordinal linear)."""
    cats = sorted({v for _, v, _ in units})
    groups = sorted({g for _, _, g in units})
    n = len(units)
    if n == 0 or len(cats) < 2 or len(groups) < 2:
        return 0.0
    table = {(c, g): 0 for c in cats for g in groups}
    for _, v, g in units:
        table[(v, g)] += 1
    row_tot = {c: sum(table[(c, g)] for g in groups) for c in cats}
    col_tot = {g: sum(table[(c, g)] for c in cats) for g in groups}
    chi2 = 0.0
    for c in cats:
        for g in groups:
            exp = row_tot[c] * col_tot[g] / n
            if exp > 0:
                chi2 += (table[(c, g)] - exp) ** 2 / exp
    k = min(len(cats), len(groups))
    return (chi2 / (n * (k - 1))) ** 0.5 if k > 1 else 0.0


def categorical_family_verdict(units, cfg: dict) -> dict:
    """Versão categórica de family_verdict — usa V de Cramér em vez de
    diferença de médias, e permutação de rótulo para o p-valor. Rota
    separada para famílias em `families.CATEGORICAL_FAMILIES` (hoje só
    rj_stage). direction_match sempre None: associação categórica não tem
    "sinal" a bater com direção esperada."""
    if len(units) < 4:
        return {"n": len(units), "effect": None, "ci": (None, None),
                "p_value": None, "direction_match": None}
    obs_v = _cramers_v(units)
    rng = random.Random(cfg["judge"]["seed"])
    tickers = [u[0] for u in units]
    vals = [u[1] for u in units]
    groups = [u[2] for u in units]
    n_ge, n_perm = 0, cfg["judge"]["n_boot"]
    for _ in range(n_perm):
        shuffled = groups[:]
        rng.shuffle(shuffled)
        v = _cramers_v(list(zip(tickers, vals, shuffled)))
        if v >= obs_v:
            n_ge += 1
    p = n_ge / n_perm
    return {"n": len(units), "effect": obs_v, "ci": (None, None),
            "p_value": p, "direction_match": None}


def apply_fdr(verdicts: dict, alpha: float, families_for_fdr: set | None = None) -> dict:
    """Benjamini-Hochberg sobre os p-valores das famílias PREDITIVAS com
    dado (revisão externa, 2ª rodada, ponto 1: famílias descritivas — hoje
    só volume_dynamics_contemporaneous — ficam FORA do denominador do FDR;
    contá-las inflaria "quantas tentativas houve" com uma família que nem é
    executável, e ao mesmo tempo o pré-registro diz "8 famílias" enquanto o
    registry tem 9 entradas). `families_for_fdr=None` usa todas as chaves
    de `verdicts` (comportamento antigo, mantido para quem chamar direto).
    Marca `significant_after_fdr` em cada verdict elegível; famílias fora do
    conjunto de FDR recebem `significant_after_fdr=None` (não aplicável, não
    "não significativa")."""
    eligible = families_for_fdr if families_for_fdr is not None else set(verdicts.keys())
    items = [(name, v["p_value"]) for name, v in verdicts.items()
             if name in eligible and v.get("p_value") is not None]
    items.sort(key=lambda x: x[1])
    m = len(items)
    threshold_rank = 0
    for rank, (name, p) in enumerate(items, start=1):
        if p <= (rank / m) * alpha:
            threshold_rank = rank
    significant_names = {name for name, _ in items[:threshold_rank]}
    for name, v in verdicts.items():
        if name in eligible:
            v["significant_after_fdr"] = name in significant_names
        else:
            v["significant_after_fdr"] = None  # descritiva — FDR não se aplica
    return verdicts


def leave_one_company_out(units, direction_expected: str) -> dict:
    """Análise de INFLUÊNCIA/ESTABILIDADE (revisão externa, ponto 6 — nome
    antigo "validação" era enganoso). Mede se o SINAL do effect size muda ao
    remover uma empresa por vez — útil para saber se, por exemplo, AMER3 ou
    OIBR3 sozinhas carregam o resultado. NÃO é validação preditiva: não
    responde "eu previria a empresa deixada de fora?" — isso exigiria um
    modelo treinado em N-1 e testado na excluída, que só faz sentido quando
    houver modelo propriamente dito (não apenas comparação de médias)."""
    base = _mean_diff(units)
    if base is None or len(units) < 5:
        return {"stability": None, "n_iterations": 0,
                "note": "N insuficiente para leave-one-company-out (<5); "
                        "isto é análise de influência, não validação preditiva"}
    base_sign = 1 if base > 0 else (-1 if base < 0 else 0)
    tickers = sorted({u[0] for u in units})
    matches = 0
    for tk in tickers:
        subset = [u for u in units if u[0] != tk]
        d = _mean_diff(subset)
        if d is None:
            continue
        sign = 1 if d > 0 else (-1 if d < 0 else 0)
        if sign == base_sign:
            matches += 1
    return {"stability": matches / len(tickers), "n_iterations": len(tickers),
            "base_sign": base_sign,
            "note": "influência/estabilidade do sinal — não é validação preditiva"}


def run_all_families(units_by_family: dict, cfg: dict) -> dict:
    """units_by_family: {nome_familia: [(ticker, valor, grupo), ...]}.
    Roda verdict + influência por família (roteando categóricas para o
    teste de associação), depois aplica FDR SÓ sobre as 8 preditivas
    (`families.PREDICTIVE_FAMILIES`) — a descritiva
    (`volume_dynamics_contemporaneous`) é computada e reportada, mas fica
    fora do denominador do FDR (correção do ponto 1, 2ª revisão)."""
    import rj_families as families_mod
    fam_cfg = cfg["families"]
    verdicts = {}
    for name, units in units_by_family.items():
        is_categorical = name in getattr(families_mod, "CATEGORICAL_FAMILIES", set())
        direction = fam_cfg.get(name, {}).get("direction_expected", "ambiguous")
        if is_categorical:
            v = categorical_family_verdict(units, cfg)
        else:
            v = family_verdict(units, direction, cfg)
        v["loco"] = (None if is_categorical
                     else leave_one_company_out(units, direction))
        v["descriptive_only"] = name in getattr(families_mod, "DESCRIPTIVE_ONLY_FAMILIES", set())
        verdicts[name] = v
    predictive = getattr(families_mod, "PREDICTIVE_FAMILIES", set(units_by_family.keys()))
    return apply_fdr(verdicts, cfg["judge"]["fdr_alpha"], families_for_fdr=predictive)
