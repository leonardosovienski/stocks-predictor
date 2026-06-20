"""ESTUDO DE CALIBRAÇÃO DA LENTE 2 — compara métodos de IC sob AR(1).

Objetivo: achar uma régua GENÉRICA (serve para média, Sharpe-diff, Spearman) cuja
cobertura empírica fique em 95% ± 2pp sobre >=500 séries AR(1), em múltiplos níveis de
autocorrelação. NÃO altera H1 nem experimentos — só estuda o estimador de intervalo.

Diagnóstico da falha atual: a sub-cobertura cresce com phi E o nº de blocos cai (n/L).
Com n=228 e L=21 há só ~11 blocos — o percentil sub-cobre nesse regime de poucos blocos.

Candidatos (todos derivados da MESMA distribuição bootstrap da função real do core,
então o custo é o mesmo; muda só como o intervalo é extraído):
  - PERCENTIL  : [q2.5, q97.5]  (a régua ATUAL)
  - BASIC      : [2θ̂−q97.5, 2θ̂−q2.5]  (intervalo "básico"/refletido)
  - T-BLOCOS   : θ̂ ± t(df)·sd(boot), df = nº de blocos − 1  (alarga c/ poucos blocos)
Variando L ∈ {8,15,21,30} e método ∈ {moving, stationary}.

Estatística testada: a MÉDIA (teste canônico do DESIGN §M5a; valida a geometria).
Verdade = 0. Alvo de cobertura = 95% (tolerância ±2pp). 500 sims → erro MC ~±1.4pp.
"""
import sys, pathlib, random, statistics, time
sys.path.insert(0, str(pathlib.Path(__file__).parent / "vendor"))
from predictor_core.stats import block_bootstrap_ci
from scipy.stats import t as student_t

TRUE = 0.0
N = 228
N_BOOT = 800
N_SIMS = 500
PHIS = (0.0, 0.3, 0.6, 0.8)
LS = (8, 15, 21, 30)


def ar1(n, phi, rng, burn=300):
    x = 0.0
    for _ in range(burn):
        x = phi * x + rng.gauss(0, 1.0)
    out = []
    for _ in range(n):
        x = phi * x + rng.gauss(0, 1.0)
        out.append(x)
    return out


def intervals_from_dist(theta, dist, n, block, conf=0.95):
    """Extrai 3 tipos de IC da MESMA distribuição bootstrap."""
    d = sorted(dist)
    m = len(d)
    a = (1 - conf) / 2
    qlo, qhi = d[max(0, int(a * m))], d[min(m - 1, int((1 - a) * m))]
    # percentil (atual)
    perc = (qlo, qhi)
    # basic / refletido
    basic = (2 * theta - qhi, 2 * theta - qlo)
    # t-blocos: usa sd da dist + multiplicador t com df = nº de blocos − 1
    sd = statistics.pstdev(d) if m > 1 else 0.0
    nblocks = max(2, n // block)
    tmult = student_t.ppf(1 - a, nblocks - 1)
    tblk = (theta - tmult * sd, theta + tmult * sd)
    return {"percentil": perc, "basic": basic, "t-blocos": tblk}


def covers(iv):
    return iv[0] is not None and iv[0] <= TRUE <= iv[1]


def run(method, L):
    rng = random.Random(7 + int(L) + int(method == "stationary") * 1000)
    cov = {k: 0 for k in ("percentil", "basic", "t-blocos")}
    wid = {k: [] for k in cov}
    t0 = time.time()
    res = {}
    for phi in PHIS:
        c = {k: 0 for k in cov}
        w = {k: [] for k in cov}
        for i in range(N_SIMS):
            s = ar1(N, phi, rng)
            theta = sum(s) / len(s)
            _, _, dist = block_bootstrap_ci(s, lambda z: sum(z) / len(z),
                                            block_length=L, n_boot=N_BOOT, seed=i, method=method)
            if not dist:
                continue
            ivs = intervals_from_dist(theta, dist, N, L)
            for k, iv in ivs.items():
                if covers(iv):
                    c[k] += 1
                if iv[0] is not None:
                    w[k].append(iv[1] - iv[0])
        res[phi] = {k: (c[k] / N_SIMS, statistics.mean(w[k]) if w[k] else float("nan")) for k in cov}
    return res, time.time() - t0


print(f"ESTUDO LENTE 2 — n={N}, n_boot={N_BOOT}, sims={N_SIMS}. Alvo 95%±2pp. Verdade=0.\n")
print(f"{'método':>10} {'L':>3} {'phi':>4} | {'percentil':>16} {'basic':>16} {'t-blocos':>16}")
print("-" * 78)
best = []
for method in ("moving", "stationary"):
    for L in LS:
        res, dt = run(method, L)
        for phi in PHIS:
            row = res[phi]
            def fmt(k):
                cov, w = row[k]
                flag = "*" if 0.93 <= cov <= 0.97 else " "
                return f"{cov:>6.1%}{flag}(w{w:>5.2f})"
            print(f"{method:>10} {L:>3} {phi:>4} | {fmt('percentil'):>16} {fmt('basic'):>16} {fmt('t-blocos'):>16}")
            for k in ("percentil", "basic", "t-blocos"):
                cov, w = row[k]
                if 0.93 <= cov <= 0.97:
                    best.append((method, L, phi, k, cov, w))
        print(f"{'':>10} {L:>3} {'':>4} | custo: {dt:.1f}s para {len(PHIS)*N_SIMS} sims")
print("\n* = dentro de 95%±2pp. Vencedor = método/L/intervalo que fica * em TODOS os phi.")
# resume quais (método,L,intervalo) acertam em TODOS os phi
from collections import defaultdict
hits = defaultdict(set)
for method, L, phi, k, cov, w in best:
    hits[(method, L, k)].add(phi)
print("\nCandidatos que cobrem ~95% em TODOS os phi testados:")
allphi = set(PHIS)
winners = [key for key, phis in hits.items() if phis == allphi]
if winners:
    for method, L, k in winners:
        print(f"  ✓ {method} L={L} intervalo={k}")
else:
    print("  NENHUM cobre todos os phi — reportar o que chega mais perto.")
    # melhor: maior nº de phi acertados
    for key, phis in sorted(hits.items(), key=lambda x: -len(x[1]))[:5]:
        print(f"  ~ {key[0]} L={key[1]} {key[2]}: acerta {len(phis)}/{len(PHIS)} phi ({sorted(phis)})")
