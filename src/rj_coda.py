"""Tratamento CoDa (compositional data) de razões contábeis — para a futura
família de distress contábil.

O problema (documentado no projeto de replicação de Altman que serviu de
referência): razões contábeis (ativo, passivo, lucro...) vivem no simplex —
somam a um total — e bases de demonstrativos brasileiros têm MUITOS zeros
(linha não reportada != zero econômico). As opções ruins usuais: descartar a
empresa (com N~30, cada linha perdida é poder estatístico jogado fora) ou
imputar zero (fabrica distress artificial — um zero de "lucro retido" não
reportado não é prejuízo acumulado).

A rota CoDa:
1. `impute_zeros`: substitui zeros pela metade do menor valor positivo da
   COLUNA (detection limit multiplicativo simples) — registrado, nunca
   silencioso: retorna também a máscara do que foi imputado.
2. `clr`: log-razão centrada — leva as razões do simplex para espaço real
   onde médias, distâncias e testes fazem sentido (média aritmética de
   razões no simplex é geometricamente errada).

Uso: distress contábil comparável ENTRE empresas sem jogar fora as que têm
dado parcial. Não alimenta as 8 famílias pré-registradas — só as next-gen.
"""
import math


def impute_zeros(matrix: list[list[float]], delta: float = 0.5) -> dict:
    """Substitui zeros/None por delta * (menor positivo da coluna).

    Retorna {"data": matriz imputada, "mask": posições imputadas,
    "dropped_cols": colunas sem nenhum positivo (não imputáveis — ficam como
    estão e o chamador decide)}. A máscara é parte do resultado: qualquer
    análise downstream deve poder auditar quanto do dado é imputado."""
    if not matrix:
        return {"data": [], "mask": [], "dropped_cols": []}
    n_cols = len(matrix[0])
    mins = []
    for c in range(n_cols):
        positives = [row[c] for row in matrix
                     if row[c] is not None and row[c] > 0]
        mins.append(min(positives) if positives else None)
    data, mask = [], []
    for r, row in enumerate(matrix):
        new_row = list(row)
        for c in range(n_cols):
            if (row[c] is None or row[c] == 0) and mins[c] is not None:
                new_row[c] = delta * mins[c]
                mask.append((r, c))
        data.append(new_row)
    dropped = [c for c in range(n_cols) if mins[c] is None]
    return {"data": data, "mask": mask, "dropped_cols": dropped}


def clr(row: list[float]) -> list[float] | None:
    """Centered log-ratio: ln(x_i / média geométrica(x)). Exige tudo > 0
    (rodar impute_zeros antes). Retorna None se algum valor for <= 0 —
    fail-closed, nunca log de zero silencioso."""
    if not row or any(x is None or x <= 0 for x in row):
        return None
    log_mean = sum(math.log(x) for x in row) / len(row)
    return [math.log(x) - log_mean for x in row]


def clr_matrix(matrix: list[list[float]], delta: float = 0.5) -> dict:
    """Pipeline completo: imputa zeros (com máscara auditável) e aplica CLR
    linha a linha. Linhas que continuam inválidas após imputação (coluna
    inteira sem positivo) viram None e são contadas."""
    imp = impute_zeros(matrix, delta=delta)
    out, failed = [], 0
    for row in imp["data"]:
        v = clr(row)
        if v is None:
            failed += 1
        out.append(v)
    return {"data": out, "mask": imp["mask"], "dropped_cols": imp["dropped_cols"],
            "rows_failed": failed}
