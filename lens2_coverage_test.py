"""AUDITORIA DA LENTE 2 — teste de cobertura que o DESIGN §M5 aceite (a) exige.

NÃO altera nada. Mede empiricamente se o block_bootstrap_ci do predictor_core produz
IC95% calibrado sobre séries AR(1) (autocorrelacionadas), usando a FUNÇÃO REAL da
plataforma. Estatística testada = a MÉDIA (o teste canônico do design; valida a
geometria de reamostragem). Verdade conhecida = 0 (média estacionária do AR(1)).

Cobertura observada = fração das séries em que o IC95% contém a verdade (0).
- ~95% → calibrado. <93% → liberal (IC estreito demais, vereditos otimistas).
- >97% → conservador (IC largo demais, "não comprovada" fácil demais).

Compara com o ci_mean (iid) do core — que o design afirma ser INVÁLIDO para séries
autocorrelacionadas. Se o iid desaba e o block segura, a tese do design se confirma.
"""
import sys, pathlib, random, statistics
sys.path.insert(0, str(pathlib.Path(__file__).parent / "vendor"))
from predictor_core.stats import block_bootstrap_ci, ci_mean

TRUE_MEAN = 0.0
N = 228          # mesmo n da H1 real
BLOCK = 21       # mesmo bloco da H1 (config.yaml)
N_BOOT = 1000
N_SIMS = 600     # erro de Monte Carlo ~±1.5pp


def ar1(n, phi, rng, sigma=1.0, burn=300):
    x = 0.0
    for _ in range(burn):
        x = phi * x + rng.gauss(0, sigma)
    out = []
    for _ in range(n):
        x = phi * x + rng.gauss(0, sigma)
        out.append(x)
    return out


def cell(phi, method):
    rng = random.Random(20260619 + int(phi * 1000))
    cov_block = cov_iid = 0
    widths = []
    means = []
    for i in range(N_SIMS):
        s = ar1(N, phi, rng)
        means.append(sum(s) / len(s))
        lo, hi, _ = block_bootstrap_ci(s, lambda z: sum(z) / len(z),
                                       block_length=BLOCK, n_boot=N_BOOT, seed=i, method=method)
        if lo is not None and lo <= TRUE_MEAN <= hi:
            cov_block += 1
        if lo is not None:
            widths.append(hi - lo)
        lo2, hi2 = ci_mean(s, n_boot=N_BOOT, seed=i)
        if lo2 <= TRUE_MEAN <= hi2:
            cov_iid += 1
    return (cov_block / N_SIMS, cov_iid / N_SIMS,
            statistics.mean(widths), statistics.pstdev(means))


print(f"Teste de cobertura da LENTE 2 — n={N}, bloco={BLOCK}, n_boot={N_BOOT}, sims={N_SIMS}")
print(f"Verdade=0. Alvo=95%. (erro MC ~±1.5pp)\n")
print(f"{'phi':>5} | {'método':>10} | {'COBERTURA block':>15} | {'cobertura iid':>13} | {'larg.média':>10}")
print("-" * 70)
for phi in (0.0, 0.3, 0.6, 0.8):
    cb, ci, w, sd = cell(phi, "moving")
    veredito = ("CALIBRADO" if 0.93 <= cb <= 0.97 else
                "LIBERAL (estreito)" if cb < 0.93 else "CONSERVADOR (largo)")
    print(f"{phi:>5} | {'moving':>10} | {cb:>14.1%} | {ci:>12.1%} | {w:>10.3f}   -> {veredito}")
# stationary no phi mais duro, para comparar os dois métodos
cb, ci, w, sd = cell(0.6, "stationary")
print(f"{0.6:>5} | {'stationary':>10} | {cb:>14.1%} | {ci:>12.1%} | {w:>10.3f}")
print("\nLeitura: se 'block' fica ~95% e 'iid' desaba com phi alto, a régua é válida e a")
print("tese do design (iid inválido p/ autocorrelacionado) se confirma. Se 'block' também")
print("desaba (<93%), os IC da plataforma são estreitos demais -> vereditos não defensáveis.")
