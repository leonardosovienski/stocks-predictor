"""Análise de poder PROSPECTIVA do judge RJ (complemento do power gate).

O power gate (`tests/test_rj_power_gate.py`) prova que a MECÂNICA funciona:
detecta effect size plantado e não infla falso positivo em ruído. O que ele
NÃO responde é a pergunta que decide se vale coletar dado real:

    "Com o N que o universo RJ da B3 consegue entregar (~20-40 empresas),
     qual o MENOR effect size que este desenho consegue detectar com
     poder razoável, depois do FDR sobre as 8 famílias?"

Este módulo responde por simulação de Monte Carlo usando o PRÓPRIO judge
(`rj_judge.run_all_families`) como peça — não uma reimplementação analítica
que poderia divergir da máquina real. Nenhum parâmetro [RJ-FROZEN] é tocado:
a simulação só varia N e effect size; n_boot, alpha e o conjunto de famílias
saem do config vigente (ou de um override explícito passado pelo chamador,
para rodar rápido em CI).

Uso típico (CLI):
    python src/rj_power.py --config config_rj.yaml --n-companies 20 30 40 \
        --effects 0.5 1.0 1.5 2.0 --reps 50 --fast

Saída: tabela poder x (N, effect size) + MDE (menor effect com poder >= 80%).
Se o MDE no N disponível for grande demais para ser plausível, a conclusão
honesta é que o estudo, como desenhado, tende ao NO-GO por falta de poder —
e isso é informação ANTES de gastar meses coletando dado.
"""
import argparse
import copy
import random

import rj_families as families
import rj_judge as judge


def simulate_power(cfg: dict, n_companies: int, planted_effect: float,
                   n_reps: int = 50, seed: int = 0,
                   family: str = "drawdown") -> float:
    """Fração de réplicas em que `family` sai significant_after_fdr com
    `planted_effect` (em desvios-padrão) plantado no grupo-rally.

    Réplicas usam seeds distintas e determinísticas (seed + rep) — resultado
    reproduzível bit a bit para a mesma (cfg, N, effect, reps, seed)."""
    if n_reps < 1:
        raise ValueError(f"n_reps deve ser >= 1 (recebido: {n_reps})")
    names = list(families.REGISTRY.keys())
    n_detected = 0
    for rep in range(n_reps):
        rng = random.Random(seed + rep)
        units_by_family = {name: [] for name in names}
        for i in range(n_companies):
            ticker = f"PWR{i:03d}3"
            group = 1 if i < n_companies // 2 else 0
            for name in names:
                if name in families.CATEGORICAL_FAMILIES:
                    # categórica sem sinal: distribuição uniforme nos dois
                    # grupos — mede o poder das CONTÍNUAS sem contaminar com
                    # uma família que não recebe efeito plantado neste grid.
                    cats = ["requested", "plan_presented", "plan_approved", "exited"]
                    val = cats[rng.randrange(len(cats))]
                else:
                    val = rng.gauss(0.0, 1.0)
                    if name == family and group == 1:
                        val += planted_effect
                units_by_family[name].append((ticker, val, group))
        verdicts = judge.run_all_families(units_by_family, cfg)
        if verdicts[family]["significant_after_fdr"]:
            n_detected += 1
    return n_detected / n_reps


def power_grid(cfg: dict, n_companies_list: list[int],
               effect_sizes: list[float], n_reps: int = 50,
               seed: int = 0, family: str = "drawdown") -> dict:
    """{(n, effect): poder} — a matriz que responde "vale coletar dado?"."""
    return {(n, d): simulate_power(cfg, n, d, n_reps, seed, family)
            for n in n_companies_list for d in effect_sizes}


def minimum_detectable_effect(grid: dict, n_companies: int,
                              target_power: float = 0.80) -> float | None:
    """Menor effect size do grid com poder >= target_power no N dado.
    None = nem o maior efeito simulado atinge o alvo — recado claro de que
    o N disponível não sustenta o desenho como está."""
    candidates = sorted(d for (n, d), p in grid.items()
                        if n == n_companies and p >= target_power)
    return candidates[0] if candidates else None


def format_grid(grid: dict, n_companies_list: list[int],
                effect_sizes: list[float]) -> str:
    header = "N\\effect | " + " | ".join(f"{d:+.1f}sd" for d in effect_sizes)
    lines = [header, "-" * len(header)]
    for n in n_companies_list:
        row = [f"{grid[(n, d)]:6.0%}" for d in effect_sizes]
        lines.append(f"{n:8d} | " + "  | ".join(row))
    return "\n".join(lines)


def main(argv=None) -> int:
    import pathlib
    import yaml

    ap = argparse.ArgumentParser(description="Poder prospectivo do judge RJ")
    ap.add_argument("--config", default=str(
        pathlib.Path(__file__).parent.parent / "config_rj.yaml"))
    ap.add_argument("--n-companies", type=int, nargs="+", default=[20, 30, 40])
    ap.add_argument("--effects", type=float, nargs="+",
                    default=[0.5, 1.0, 1.5, 2.0])
    ap.add_argument("--reps", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--fast", action="store_true",
                    help="n_boot reduzido (300) para rodar em minutos; "
                         "aproximação — a hipótese real usa o config vigente")
    args = ap.parse_args(argv)

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if args.fast:
        cfg = copy.deepcopy(cfg)
        cfg["judge"]["n_boot"] = 300

    grid = power_grid(cfg, args.n_companies, args.effects,
                      n_reps=args.reps, seed=args.seed)
    print(format_grid(grid, args.n_companies, args.effects))
    print()
    for n in args.n_companies:
        mde = minimum_detectable_effect(grid, n)
        if mde is None:
            print(f"N={n}: MDE >= 80% de poder NÃO alcançado no grid "
                  f"(maior efeito simulado: {max(args.effects):+.1f}sd)")
        else:
            print(f"N={n}: MDE = {mde:+.1f} desvios-padrão")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
