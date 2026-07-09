"""predictor-core.testing — utilitários de teste da plataforma (não são runtime).

Ferramentas que os domínios usam SÓ na suíte (pytest). Nada aqui é importado pelo
caminho de produção. `secrets` transforma um vazamento de segredo na telemetria em
falha de pytest antes do commit.
"""
